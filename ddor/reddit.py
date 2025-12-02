from functools import cached_property

import requests
from requests.exceptions import HTTPError
from ratelimit import limits, sleep_and_retry

from .logger import log

class Reddit:
    URL_TEMPLATE = "http://www.reddit.com/r/{subreddit}/top/.json?t=day"
    HEADERS = {
        "User-Agent": "DailyRedditScript/1.0 (by u/yamatt)",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    @classmethod
    def from_config(cls, config: dict[str, str]):
        return cls()

    @cached_property
    def session(self):
        session = requests.Session()
        session.headers.update(self.HEADERS)
        return session

    @sleep_and_retry
    @limits(calls=30, period=60)
    def get_json(self, url):
        response = self.session.get(url)

        try:
            response.raise_for_status()
        except HTTPError as e:
            log.error("JSON REQUEST", success=False, status=response.status_code, message=response.text, request=response.request.headers)
            raise e

        return response.json()

    def get_subreddit(self, subreddit):
        return self.get_json(self.URL_TEMPLATE.format(subreddit=subreddit))

    def get_subreddit_top_posts(self, subreddit):
        return [
            post["data"] for post in self.get_subreddit(subreddit)["data"]["children"]
        ]
