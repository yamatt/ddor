import math
from datetime import datetime

from ddor.logger import log


class Post:
    """Wrapper class to make Lemmy posts compatible with the RSS builder."""

    def __init__(self, post, community, creator, community_weight, instance):
        post = post["post"] if "post" in post else post
        self.post = post
        self._community = community
        self._creator = creator
        self.community_weight = community_weight
        self.instance = instance

    @property
    def _id(self):
        return (
            self.post["id"]
            if "id" in self.post
            else self.post["post_view"]["post"]["id"]
        )

    @property
    def title(self):
        return self.post["name"]

    @property
    def url(self):
        # Prefer the post's AP ID (ActivityPub ID) or URL
        ap_id = self.post["ap_id"]
        if ap_id:
            return ap_id
        return self.post["url"]

    @property
    def published(self) -> datetime:
        published = self.post.get("published")

        if published:
            # Parse ISO 8601 timestamp and convert to Unix timestamp
            return datetime.fromisoformat(published.replace("Z", "+00:00"))

    @property
    def community_name(self):
        return self._community.get("name", "")

    @property
    def subreddit(self):
        return self.community_name

    @property
    def instance_url(self):
        return self.instance.instance_url

    @property
    def selftext(self):
        """Return post body text if available."""
        return self.post.get("body", "")

    @property
    def thumbnail_url(self):
        return self.post.get("thumbnail_url")

    @property
    def preview(self):
        """Return preview data if thumbnail exists."""
        thumbnail_url = self.thumbnail_url
        if thumbnail_url:
            return {"images": [{"source": {"url": thumbnail_url}}]}
        return None

    @property
    def engagement(self):
        return self.upvotes + self.comments

    @property
    def bias_multiplier(self):
        return 1.0 + (self.community_weight * 0.5)

    def get_engagement_score(self, score_weight=1.0, engagement_weight=1.0):
        """
        Calculate a weighted engagement score combining upvotes and comments.

        Args:
            score_weight: Weight for the upvote score (default: 1.0)
            engagement_weight: Weight for engagement (upvotes + comments) (default: 1.0)

        Returns:
            float: Weighted engagement score
        """
        if self.score == 0 and self.engagement == 0:
            return 0

        # Normalize to avoid large numbers skewing results
        # Using log scale for engagement to prevent comment spam from dominating

        engagement_normalized = math.log(self.engagement + 1)  # +1 to avoid log(0)
        score_normalized = self.score

        weighted_score = (score_normalized * score_weight) + (
            engagement_normalized * engagement_weight
        )

        return weighted_score * self.bias_multiplier
