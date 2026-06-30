from datetime import datetime
from functools import cached_property

from pythorhead import Lemmy as LemmyClient
from pythorhead.types import SortType

from ddor.ddor import Post
from ddor.logger import log


class LemmyPost(Post):
    """Wrapper class to make Lemmy posts compatible with the RSS builder."""

    @classmethod
    def from_post(cls, post: dict, community_weight: float, instance: "LemmyInstance"):
        return cls(
            post=post,
            community=post.get("community", {}),
            creator=post.get("creator", {}),
            community_weight=community_weight,  # Per-community weight bias
            instance=instance,
        )

    @property
    def upvotes(self) -> int:
        # Lemmy posts use 'score' for upvotes if 'upvotes' is missing
        try:
            return self.post["counts"]["upvotes"]
        except Exception:
            log.error(
                "UPVOTES NOT FOUND",
                post=self._id,
                instance=self.instance.instance_url,
            )
            return 0

    @property
    def downvotes(self) -> int:
        try:
            return self.post["counts"]["downvotes"]
        except Exception:
            log.error(
                "DOWNVOTES NOT FOUND",
                post=self._id,
                instance=self.instance.instance_url,
            )
            return 0

    @property
    def comments_count(self) -> int:
        # Lemmy posts use 'comments' or 'num_comments' if available
        try:
            return self.counts["comments"]
        except Exception:
            log.error(
                "COMMENTS COUNT NOT FOUND",
                post=self._id,
                instance=self.instance.instance_url,
            )
            return 0

    @property
    def score(self) -> int:
        try:
            return self.counts["score"]
        except Exception:
            log.error(
                "SCORE NOT FOUND",
                post=self._id,
                instance=self.instance.instance_url,
            )
            return 0

    def get_full_post(self):
        """Fetch the full post data from the instance."""
        log.info(
            "FETCHING FULL POST",
            post=self._id,
            instance=self.instance.instance_url,
        )
        if self.instance.post_exists(self._id):
            return self.instance.get_post(self._id)
        raise ValueError(
            f"Post with ID {self._id} not found on instance {self.instance.instance_url}."
        )

    @cached_property
    def counts(self):
        # Try to get counts from the post dict
        if "counts" in self.post:
            return self.post["counts"]
        if "post_view" in self.post and "counts" in self.post["post_view"]:
            return self.post["post_view"]["counts"]

        try:
            full_post = self.get_full_post()
        except ValueError as e:
            log.error(
                "FULL POST COUNT FETCH FAILED",
                post=self._id,
                instance=self.instance.instance_url,
                error=str(e),
            )
            raise
        # Update self.post with the fetched data for future accesses
        if "counts" in full_post.post:
            self.post["counts"] = full_post.post["counts"]
            return self.post["counts"]
        if "post_view" in full_post.post and "counts" in full_post.post["post_view"]:
            self.post["post_view"] = full_post.post["post_view"]
            return self.post["post_view"]["counts"]
        raise KeyError("Counts not found in post data or fetched post.")


class LemmyInstance:
    """Represents a Lemmy instance."""

    REQUEST_TIMEOUT = 30  # seconds

    def from_domain(cls, instance_domain: str):
        instance_url = (
            f"https://{instance_domain}"
            if not instance_domain.startswith("http")
            else instance_domain
        )
        return cls(instance_url)

    def __init__(self, instance_url: str, community_weight: float = 0.0):
        self.instance_url = instance_url
        self.community_weight = community_weight

    @property
    def client(self):
        """Get a Lemmy client for this instance."""
        return LemmyClient(self.instance_url, request_timeout=self.REQUEST_TIMEOUT)

    def get_top_posts(
        self,
        community_name: str,
        limit: int = 20,
        time_filter: SortType = SortType.TopDay,
        full_post: bool = False,
        allow_nsfw: bool = False,
        allow_blocked: bool = False,
    ) -> list[LemmyPost]:
        """
        Fetch top posts from a Lemmy community.

        Args:
            community_spec: Community specification in format "community@instance.com"
            limit: Maximum number of posts to fetch
            time_filter: Time period for top posts ('Day', 'Week', 'Month', 'Year', 'All')

        Returns:
            List of LemmyPost objects with compatible attributes
        """

        # Discover the community to get its ID
        community_id = self.client.discover_community(community_name)
        if not community_id:
            raise ValueError(
                f"Community '{community_name}' not found on instance {self.instance_url}."
            )

        # Convert Lemmy posts to a compatible format
        posts = [
            LemmyPost.from_post(post, self.community_weight, self)
            for post in self.client.post.list(
                community_id=community_id,
                sort=time_filter,
                limit=limit,
            )
        ]

        # Filter posts based on NSFW and blocked status
        for post in posts:
            if not allow_nsfw and post.is_nsfw:
                posts.remove(post)
            if not allow_blocked and post.is_blocked:
                posts.remove(post)

        if not full_post:
            return posts

        for post in posts:
            post.counts  # Trigger counts fetching

        return posts

    def post_exists(self, post_id: int) -> bool:
        """Check if a post exists on this instance."""
        try:
            self.client.post.get(post_id=post_id)
            return True
        except Exception as e:
            log.warning(
                "POST NOT FOUND",
                post=post_id,
                instance=self.instance_url,
                error=str(e),
            )
            return False

    def get_post(self, post_id: int) -> LemmyPost:
        """Fetch a single post by its ID on this instance."""
        return LemmyPost.from_post(
            self.client.post.get(post_id=post_id),
            community_weight=self.community_weight,
            instance=self,
        )


class Lemmy:

    SORT_MAP = {
        "Day": SortType.TopDay,
        "Week": SortType.TopWeek,
        "Month": SortType.TopMonth,
        "Year": SortType.TopYear,
        "All": SortType.TopAll,
    }

    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self._clients = {}  # Cache clients for different instances

    def get_instance(self, instance_url: str, community_weight: float = 0.0):
        """Get or create a client for a specific instance."""
        if instance_url not in self._clients:
            client = LemmyInstance(instance_url, community_weight)
            self._clients[instance_url] = client
        return self._clients[instance_url]

    def get_community_top_posts(
        self, community_spec, community_weight, limit=20, time_filter="Day"
    ):

        community, instance_domain = community_spec.split("@")
        instance = self.get_instance(f"https://{instance_domain}", community_weight)
        sort_type = self.SORT_MAP.get(time_filter, SortType.TopDay)
        try:
            top_posts = instance.get_top_posts(
                community_name=community,
                limit=limit,
                time_filter=sort_type,
                full_post=True,
            )
        except ValueError as e:
            log.error(
                "COMMUNITY NOT FOUND",
                community=community_spec,
                error=str(e),
            )
            return []
        return top_posts
