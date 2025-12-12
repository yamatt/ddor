import os
from datetime import datetime

from pythorhead import Lemmy as LemmyClient


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

        # Fetch top posts from the community
        posts_response = client.post.list(
            community_id=community_id,
            sort="Top" + time_filter,  # e.g., "TopDay", "TopWeek"
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
