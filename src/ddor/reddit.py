from functools import cached_property

from ratelimit import limits, sleep_and_retry
import requests


class Reddit:
    URL_TEMPLATE = f"http://www.reddit.com/r/{subreddit}/top/.json?t=day"
    USER_AGENT = "DailyRedditScript/1.0 (by u/yamatt)"
    HEADERS = {
        "User-Agent": USER_AGENT
    }

    @classmethod
    def from_config(cls, config: dict[str, str]):
        return cls()

    @cached_property
    def session(self):
        return requests.Session(headers=self.HEADERS)

    @sleep_and_retry
    @limits(calls=30, period=60)
    def get_json(self, url):
        response = self.session.get(url)

        response.raise_for_status()

        return response.json()

    def get_subreddit(self, subreddit):
        return self.get_json(self.URL_TEMPLATE.format(subreddit=subreddit))

    def get_subreddit_top_posts(self, subreddit):
        return [ post["data"] for post in self.get_subreddit(subreddit)["data"]["children"] ]

