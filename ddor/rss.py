import xml.etree.ElementTree as ET  # nosec
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import cached_property
from html import escape

from markdown import markdown
import nh3

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
            html_body = self.html_body(post)
            content_parts.append(f'<div class="post-body">{html_body}</div>')

        # Add instance name at the end
        if hasattr(post, "instance"):
            content_parts.append("<hr/>")
            content_parts.append(
                f"<p><small>{escape(post.instance.instance_url)}</small></p>"
            )

        return "".join(content_parts) if content_parts else None

    def html_body(self, post):
        # Using 'extra' extension allows for better handling of
        # Markdown inside HTML blocks and tables.
        raw_html = markdown(post.selftext, extensions=["extra"])

        # nh3 will strip any tags NOT in this set,
        # effectively neutralizing any HTML the user tried to sneak in.
        return nh3.clean(raw_html)

    def add_post(self, feed, post):
        item = ET.SubElement(self.feed, "item")
        # Use generic format that works for both Reddit and Lemmy
        ET.SubElement(item, "title").text = f"[{post.community_name}] {post.title}"
        ET.SubElement(item, "link").text = post.url
        ET.SubElement(item, "guid").text = post.url

        # Add content/description with images and text
        content = self._get_post_content(post)
        if content:
            ET.SubElement(item, "description").text = content

        if post.published:
            # Use RFC 2822 format for pubDate (e.g., 'Mon, 02 Jan 2006 15:04:05 +0000')
            ET.SubElement(item, "pubDate").text = format_datetime(post.published)

    def build_feed(self, posts: list):
        # Add posts in reverse order so the first post is at the top of the RSS feed
        for post in reversed(posts):
            self.add_post(self.feed, post)

        return ET.tostring(self.rss, encoding="utf-8", xml_declaration=True)
