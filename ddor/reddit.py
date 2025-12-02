import os
from functools import cached_property

import praw


class Reddit:
    USER_AGENT = "DailyRedditScript/1.0 (by u/yamatt)"

    @classmethod
    def from_env(cls):
        return cls(
            os.environ["DDOR_CLIENT_ID"],
            os.environ["DDOR_CLIENT_SECRET"],
        )

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    @cached_property
    def client(self):
        return praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.USER_AGENT,
        )

    @cached_property
    def subreddits(self):
        return [str(subreddit) for subreddit in self.client.user.subreddits(limit=None)]

    def get_subreddit_top_posts(self, subreddit, limit=20, time_filter="day"):
        return self.client.subreddit(subreddit).top(
            time_filter=time_filter, limit=limit
        )
