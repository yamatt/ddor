from datetime import datetime

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
    def upvotes(self):
        # Lemmy posts use 'score' for upvotes if 'upvotes' is missing
        return self.counts["upvotes"]

    @property
    def downvotes(self):
        return self.post["counts"]["downvotes"]

    @property
    def comments(self):
        # Lemmy posts use 'comments' or 'num_comments' if available
        return self.counts["comments"]

    @property
    def score(self):
        return self.counts["score"]

    @property
    def counts(self):
        # Try to get counts from the post dict
        if "counts" in self.post:
            return self.post["counts"]
        if "post_view" in self.post and "counts" in self.post["post_view"]:
            return self.post["post_view"]["counts"]

        # If counts are missing, fetch from the instance using post ID
        post_id = self.post.get("id") or self.post.get("post_id")
        if post_id is None:
            raise KeyError("Cannot fetch counts: post ID is missing from post data.")
        # Fetch the full post from the instance
        log.info(
            "FETCHING FULL POST FOR COUNTS",
            post=post_id,
            instance=self.instance.instance_url,
        )
        full_post = self.instance.get_post(post_id)
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

        # Fetch top posts from the community
        posts = self.client.post.list(
            community_id=community_id,
            sort=time_filter,
            limit=limit,
        )

        # Convert Lemmy posts to a compatible format
        return [
            LemmyPost.from_post(post, self.community_weight, self) for post in posts
        ]

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
        return instance.get_top_posts(
            community_name=community,
            limit=limit,
            time_filter=sort_type,
        )
