import math
from datetime import datetime, timedelta
from urllib.parse import urlparse

from ddor.logger import log


class Post:
    """Wrapper class to make Lemmy posts compatible with the RSS builder."""

    BLOCKED_THUMBNAIL_DOMAINS = [
        "i.imgur.com",
    ]

    def __init__(self, post, community, creator, community_weight, instance):
        post = post["post"] if "post" in post else post
        self.post = post
        self._community = community
        self._creator = creator
        self.community_weight = community_weight
        self.instance = instance

    @property
    def _id(self):
        return self.post.get("id") or self.post.get("post_id")

    @property
    def title(self):
        return self.post["name"]

    @property
    def url(self):
        """
        Return the ActivityPub URL to the original post
        """
        return self.post["ap_id"]

    @property
    def destination_url(self):
        return self.post.get("url")

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
    def image_url(self):
        url = self.destination_url

        # Define our criteria for a valid image URL
        is_image_type = self.post.get("url_content_type", "").startswith("image/")
        has_image_ext = False
        if url:
            has_image_ext = any(
                url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]
            )

        # If it's a valid image and the domain isn't blocked, use it
        if is_image_type or has_image_ext:
            if urlparse(url).netloc not in self.BLOCKED_THUMBNAIL_DOMAINS:
                return url

        return self.thumbnail_url

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
    def is_nsfw(self) -> bool:
        return self.post.get("nsfw", False)

    @property
    def is_blocked(self) -> bool:
        """
        Used to check if the post is blocked, or links to blocked content.
        """
        return False

    @property
    def engagement(self) -> int:
        return self.upvotes + self.comments_count

    @property
    def bias_multiplier(self) -> float:
        return 1.0 + (self.community_weight * 0.5)

    def get_engagement_score(
        self, score_weight: float = 1.0, engagement_weight: float = 1.0
    ) -> float:
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

    def hacker_news_rank(self, gravity: float = 1.8, hours_delta: int = 2) -> float:
        return (self.score) / pow((self.published + timedelta(hours=2)), gravity)

    def lobster_rank(
        self, base: float = 0, hotness_window_seconds: int = 79200
    ) -> float:
        # 1. Sign: Determines if the score is positive, negative, or zero
        if self.score > 0:
            sign = 1
        elif self.score < 0:
            sign = -1
        else:
            sign = 0

        score = self.upvotes - self.downvotes

        order = math.log10(max(abs(score + 1) + self.comments_count, 1))

        age = self.published.timestamp() / hotness_window_seconds

        hotness = -1 * (base + (order * sign) + age)

        return hotness
