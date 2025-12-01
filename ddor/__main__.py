from os.path import join
import tomllib

import click

from ddor.config import Config
from ddor.logger import log
from ddor.reddit import Reddit
from ddor.rss import RSSBuilder


@click.command()
@click.argument("config_path", type=click.Path(exists=True, readable=True))
@click.argument("output_directory", type=str)
def main(config_path, output_directory):
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
    for subreddit_name in config.subreddit_names:
        log.info("GETTING POSTS", subreddit=subreddit_name)
        all_posts.extend(reddit.get_subreddit_top_posts(subreddit_name))

    all_posts.sort(key=lambda post: post["score"], reverse=True)

    rss_content = rss.build_feed(posts=all_posts[config.count :])

    output_file_name = f"{config.name}.rss"
    output_file_path = join(output_directory, output_file_name)

    with open(output_file_path, "wb") as f:
        f.write(rss_content)


if __name__ == "__main__":
    main()
