import click
import tomllib

from .config import Config
from .reddit import Reddit
from .rss import RSSBuilder


@click.command()
@click.argument(
    "config_path",
    required=True,
    type=click.Path(exists=True, readable=True),
    help="Path to the TOML configuration files.",
)
def main(config_paths):
    # Load the config
    config = Config.from_path(config_path)
    reddit = Reddit()
    rss = RSSBuilder(
        title="Daily Reddit Digest",
        description="Top posts from configured subreddits.",
        host_url="https://github.io/yamatt/ddor/",
    )

    # Fetch posts
    all_posts = []
    for subreddit_name in subreddits:
        all_posts.extend(reddit.get_subreddit(subreddit_name))

    # Sort all posts by score desc
    all_posts.sort(key=lambda p: p["score"], reverse=True)

    # Build RSS feed
    rss_content = rss.build_feed(posts=all_posts[config.config["config"]["count"] :])

    # Save feed
    with open(config.config["config"]["name"], "w") as f:
        f.write(rss_content)


if __name__ == "__main__":
    main()
