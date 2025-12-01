import xml.etree.ElementTree as ET  # nosec
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import cached_property


class RSSBuilder:
    def __init__(self, title: str, description: str, host_url: str):
        self.title = title
        self.description = description
        self.host_url = host_url

    @cached_property
    def feed(self):
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        ET.SubElement(channel, "title").text = self.title
        ET.SubElement(channel, "description").text = self.description
        ET.SubElement(channel, "link").text = self.host_url

        return channel

    def add_post(self, feed, post):
        item = ET.SubElement(self.feed, "item")
        ET.SubElement(item, "title").text = f"[r/{post['subreddit']}] {post['title']}"
        ET.SubElement(item, "link").text = post["url"]
        ET.SubElement(item, "guid").text = post["url"]

        pub_date = format_datetime(
            datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
        )
        ET.SubElement(item, "pubDate").text = pub_date

    def build_feed(self, posts: list):

        for post in posts:
            self.add_post(self.feed, post)

        return ET.tostring(self.feed, encoding="utf-8", xml_declaration=True)
