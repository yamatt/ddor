import os
from functools import cached_property

from pythorhead import Lemmy as LemmyClient


class Lemmy:
    USER_AGENT = "DailyLemmyScript/1.0"

    @classmethod
    def from_env(cls):
        return cls(
            os.environ["DDOR_LEMMY_INSTANCE"],
            os.environ.get("DDOR_LEMMY_USERNAME"),
            os.environ.get("DDOR_LEMMY_PASSWORD"),
        )

    def __init__(self, instance_url: str, username: str = None, password: str = None):
        self.instance_url = instance_url
        self.username = username
        self.password = password

    @cached_property
    def client(self):
        client = LemmyClient(self.instance_url, request_timeout=30)
        if self.username and self.password:
            client.log_in(self.username, self.password)
        return client

    def get_community_top_posts(self, community_name, limit=20, time_filter="Day"):
        """
        Fetch top posts from a Lemmy community.

        Args:
            community_name: Name of the community (without the instance)
            limit: Maximum number of posts to fetch
            time_filter: Time period for top posts ('Day', 'Week', 'Month', 'Year', 'All')

        Returns:
            List of LemmyPost objects with compatible attributes
        """
        # Discover the community to get its ID
        community = self.client.discover_community(community_name)
        if not community:
            return []

        community_id = community.get("community", {}).get("id")
        if not community_id:
            return []

        # Fetch top posts from the community
        posts_response = self.client.post.list(
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
        return self._post.get("ap_id") or self._post.get("url", "")

    @property
    def score(self):
        return self._post.get("score", 0)

    @property
    def created_utc(self):
        # Lemmy uses ISO 8601 timestamps, need to convert to Unix timestamp
        from datetime import datetime

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
