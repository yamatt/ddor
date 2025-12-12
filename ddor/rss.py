import xml.etree.ElementTree as ET  # nosec
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import cached_property
from html import escape

# Register the atom namespace to use 'atom' prefix instead of 'ns0'
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")


class RSSBuilder:
    def __init__(
        self, title: str, description: str, host_url: str, feed_url: str = None
    ):
        self.title = title
        self.description = description
        self.host_url = host_url
        self.feed_url = feed_url or host_url

    @cached_property
    def rss(self):
        return ET.Element("rss", version="2.0")

    @cached_property
    def feed(self):
        channel = ET.SubElement(self.rss, "channel")

        ET.SubElement(channel, "title").text = self.title
        ET.SubElement(channel, "description").text = self.description
        ET.SubElement(channel, "link").text = self.host_url

        # Add atom:link with rel="self"
        atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
        atom_link.set("href", self.feed_url)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")

        return channel

    def _get_post_content(self, post):
        """Build HTML content with images and text from the post."""
        content_parts = []

        # Try to get the best image URL
        image_url = None

        # Check if the post URL is a direct image link
        if hasattr(post, "url") and post.url:
            url_lower = post.url.lower()
            if any(
                url_lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]
            ):
                image_url = post.url

        # Check for preview images if no direct image URL
        if not image_url and hasattr(post, "preview"):
            try:
                images = post.preview.get("images", [])
                if images:
                    # Get the source (highest resolution) image
                    image_url = images[0].get("source", {}).get("url", "")
                    # Reddit escapes URLs in preview, need to unescape
                    image_url = image_url.replace("&amp;", "&")
            except (AttributeError, KeyError, IndexError):
                pass

        # Add image if found
        if image_url:
            escaped_url = escape(image_url, quote=True)
            escaped_title = escape(post.title, quote=True)
            content_parts.append(
                f'<p><img src="{escaped_url}" alt="{escaped_title}"/></p>'
            )

        # Add selftext content if it exists
        if hasattr(post, "selftext") and post.selftext:
            # Convert line breaks to HTML paragraphs
            paragraphs = post.selftext.split("\n\n")
            for para in paragraphs:
                if para.strip():
                    content_parts.append(f"<p>{escape(para.strip())}</p>")

        return "".join(content_parts) if content_parts else None

    def add_post(self, feed, post):
        item = ET.SubElement(self.feed, "item")
        # Use generic format that works for both Reddit and Lemmy
        ET.SubElement(item, "title").text = f"[{post.subreddit}] {post.title}"
        ET.SubElement(item, "link").text = post.url
        ET.SubElement(item, "guid").text = post.url

        # Add content/description with images and text
        content = self._get_post_content(post)
        if content:
            ET.SubElement(item, "description").text = content

        pub_date = format_datetime(
            datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
        )
        ET.SubElement(item, "pubDate").text = pub_date

    def build_feed(self, posts: list):

        for post in posts:
            self.add_post(self.feed, post)

        return ET.tostring(self.rss, encoding="utf-8", xml_declaration=True)
