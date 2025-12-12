from os.path import join

import click

from ddor.config import Config
from ddor.lemmy import Lemmy
from ddor.logger import log
from ddor.rss import RSSBuilder


@click.command()
@click.argument("config_path", type=click.Path(exists=True, readable=True))
@click.argument("output_directory", type=str)
def main(config_path, output_directory):
    # Load the config
    config = Config.from_path(config_path)
    lemmy = Lemmy.from_env()
    rss = RSSBuilder(
        title="Daily Lemmy Digest",
        description="Top posts from configured Lemmy communities.",
        host_url="https://yamatt.github.io/ddor/",
        feed_url=f"https://yamatt.github.io/ddor/{config.name}.rss",
    )

    # Fetch posts with per-community weights
    all_posts = []
    for community_config in config.communities:
        community_name = community_config["name"]
        weight = community_config["weight"]
        log.info("GETTING POSTS", community=community_name, weight=weight)
        posts = lemmy.get_community_top_posts(community_name)
        # Apply community weight to each post's engagement score
        for post in posts:
            post.community_weight = weight
        all_posts.extend(posts)

    # Sort by weighted engagement score
    all_posts.sort(key=lambda post: post.get_weighted_engagement_score(), reverse=True)

    rss_content = rss.build_feed(posts=all_posts[: config.count])

    output_file_name = f"{config.name}.rss"
    output_file_path = join(output_directory, output_file_name)

    with open(output_file_path, "wb") as f:
        f.write(rss_content)


if __name__ == "__main__":
    main()
