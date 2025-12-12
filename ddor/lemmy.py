import os
from datetime import datetime

from pythorhead import Lemmy as LemmyClient
from pythorhead.types import SortType


class Lemmy:
    USER_AGENT = "DailyLemmyScript/1.0"

    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self._clients = {}  # Cache clients for different instances

    def _get_client(self, instance_url: str):
        """Get or create a client for a specific instance."""
        if instance_url not in self._clients:
            client = LemmyClient(instance_url, request_timeout=30)
            self._clients[instance_url] = client
        return self._clients[instance_url]

    def get_community_top_posts(self, community_spec, limit=20, time_filter="Day"):
        """
        Fetch top posts from a Lemmy community.

        Args:
            community_spec: Community specification in format "community@instance.com"
            limit: Maximum number of posts to fetch
            time_filter: Time period for top posts ('Day', 'Week', 'Month', 'Year', 'All')

        Returns:
            List of LemmyPost objects with compatible attributes
        """
        # Parse community specification
        if "@" not in community_spec:
            raise ValueError(
                f"Community '{community_spec}' must be in format 'community@instance.com'. "
                f"Example: 'technology@lemmy.world'"
            )

        parts = community_spec.split("@")
        if len(parts) != 2:
            raise ValueError(
                f"Community '{community_spec}' has invalid format. "
                f"Expected exactly one '@' symbol. Example: 'technology@lemmy.world'"
            )

        community_name, instance_domain = parts

        # Validate that community name and instance domain are not empty
        if not community_name or not instance_domain:
            raise ValueError(
                f"Community '{community_spec}' is invalid. "
                f"Both community name and instance must be provided."
            )

        # Basic validation for instance domain (alphanumeric, dots, hyphens)
        if not all(c.isalnum() or c in ".-" for c in instance_domain):
            raise ValueError(
                f"Instance domain '{instance_domain}' contains invalid characters. "
                f"Expected format: 'instance.com'"
            )

        instance_url = (
            f"https://{instance_domain}"
            if not instance_domain.startswith("http")
            else instance_domain
        )

        # Get the appropriate client
        client = self._get_client(instance_url)

        # Discover the community to get its ID
        community = client.discover_community(community_name)
        if not community:
            return []

        # discover_community returns the community ID directly as an int
        if isinstance(community, int):
            community_id = community
        else:
            # Fallback for dictionary response format
            community_id = community.get("community", {}).get("id")

        if not community_id:
            return []

        # Map time_filter to SortType enum
        sort_map = {
            "Day": SortType.TopDay,
            "Week": SortType.TopWeek,
            "Month": SortType.TopMonth,
            "Year": SortType.TopYear,
            "All": SortType.TopAll,
        }
        sort_type = sort_map.get(time_filter, SortType.TopDay)

        # Fetch top posts from the community
        posts_response = client.post.list(
            community_id=community_id,
            sort=sort_type,
            limit=limit,
        )

        # Convert Lemmy posts to a compatible format
        return [LemmyPost(post) for post in posts_response]


class LemmyPost:
    """Wrapper class to make Lemmy posts compatible with the RSS builder."""

    def __init__(self, post_data):
        self._data = post_data
        self._post = post_data.get("post", {})
        self._community = post_data.get("community", {})
        self._creator = post_data.get("creator", {})
        self.community_weight = 0  # Per-community weight bias

    @property
    def title(self):
        return self._post.get("name", "")

    @property
    def url(self):
        # Prefer the post's AP ID (ActivityPub ID) or URL
        ap_id = self._post.get("ap_id")
        if ap_id:
            return ap_id
        return self._post.get("url", "")

    @property
    def score(self):
        return self._post.get("score", 0)

    @property
    def created_utc(self):
        # Lemmy uses ISO 8601 timestamps, need to convert to Unix timestamp
        published = self._post.get("published", "")
        if published:
            # Parse ISO 8601 timestamp and convert to Unix timestamp
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            return dt.timestamp()
        return 0

    @property
    def subreddit(self):
        """Return community name for compatibility with RSS builder."""
        return self._community.get("name", "")

    @property
    def instance(self):
        """Return the Lemmy instance domain (e.g., lemmy.world)."""
        # Try to extract from the post's AP ID first
        ap_id = self._post.get("ap_id", "")
        if ap_id and "://" in ap_id:
            # AP ID format: https://instance.com/post/12345
            domain = ap_id.split("://")[1].split("/")[0]
            return domain

        # Fallback to community's actor_id
        actor_id = self._community.get("actor_id", "")
        if actor_id and "://" in actor_id:
            # Actor ID format: https://instance.com/c/community
            domain = actor_id.split("://")[1].split("/")[0]
            return domain

        return "unknown"

    @property
    def selftext(self):
        """Return post body text if available."""
        return self._post.get("body", "")

    @property
    def preview(self):
        """Return preview data if thumbnail exists."""
        thumbnail_url = self._post.get("thumbnail_url")
        if thumbnail_url:
            return {"images": [{"source": {"url": thumbnail_url}}]}
        return None

    def get_engagement_score(self, score_weight=1.0, engagement_weight=1.0):
        """
        Calculate a weighted engagement score combining upvotes and comments.

        Args:
            score_weight: Weight for the upvote score (default: 1.0)
            engagement_weight: Weight for engagement (upvotes + comments) (default: 1.0)

        Returns:
            float: Weighted engagement score
        """
        upvotes = self._post.get("upvotes", 0) or 0
        downvotes = self._post.get("downvotes", 0) or 0
        comments = self._post.get("comments", 0) or 0

        # Fall back to score if upvotes/downvotes not available
        if upvotes == 0 and downvotes == 0:
            upvotes = max(0, self.score)

        # Calculate engagement: (upvotes + comments) normalized
        engagement = upvotes + comments

        # Combined score: weighted average of score and engagement
        score = self.score

        if score == 0 and engagement == 0:
            return 0

        # Normalize to avoid large numbers skewing results
        # Using log scale for engagement to prevent comment spam from dominating
        import math

        engagement_normalized = math.log(engagement + 1)  # +1 to avoid log(0)
        score_normalized = score

        weighted_score = (score_normalized * score_weight) + (
            engagement_normalized * engagement_weight
        )
        return weighted_score

    def get_weighted_engagement_score(self, score_weight=1.0, engagement_weight=1.0):
        """
        Get engagement score with community weight bias applied.

        Args:
            score_weight: Weight for the upvote score (default: 1.0)
            engagement_weight: Weight for engagement (upvotes + comments) (default: 1.0)

        Returns:
            float: Weighted engagement score with community bias
        """
        base_score = self.get_engagement_score(score_weight, engagement_weight)

        if base_score == 0:
            return 0

        # Apply community weight bias (0 = no bias, 1 = boost, -1 = suppress)
        # Formula: score * (1 + weight * 0.5) allows ±50% adjustment
        bias_multiplier = 1.0 + (self.community_weight * 0.5)
        return base_score * bias_multiplier
