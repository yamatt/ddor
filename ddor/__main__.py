import asyncio
from enum import Enum
from os.path import join

import click

from ddor.config import Config
from ddor.lemmy import Lemmy
from ddor.logger import log
from ddor.rss import RSSBuilder


class TimeFilter(str, Enum):
    """Time period for top posts."""

    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"
    ALL = "All"


async def fetch_community_posts(
    lemmy,
    community_config,
    semaphore,
    time_filter=TimeFilter.DAY.value,
    allow_nsfw=False,
    allow_blocked=False,
):
    """Fetch posts from a single community with semaphore-controlled concurrency."""
    community_name = community_config["name"]
    weight = community_config["weight"]

    async with semaphore:
        log.info(
            "GETTING POSTS",
            community=community_name,
            weight=weight,
            time_filter=time_filter,
        )
        # Run the synchronous get_community_top_posts in a thread pool
        loop = asyncio.get_running_loop()
        posts = await loop.run_in_executor(
            None, lemmy.get_community_top_posts, community_name, weight, 20, time_filter
        )

        # Warn if no posts were returned
        if not posts:
            log.warning("NO POSTS RETURNED", community=community_name, weight=weight)

        return posts


async def fetch_all_communities(
    lemmy,
    communities,
    max_concurrent,
    time_filter,
    allow_nsfw=False,
    allow_blocked=False,
):
    """Fetch posts from all communities concurrently with controlled concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [
        fetch_community_posts(lemmy, community_config, semaphore, time_filter)
        for community_config in communities
    ]
    results = await asyncio.gather(*tasks)
    # Flatten the list of lists
    all_posts = []
    for posts in results:
        all_posts.extend(posts)
    return all_posts


@click.command()
@click.argument("config_path", type=click.Path(exists=True, readable=True))
@click.argument("output_directory", type=str)
@click.option(
    "--time-filter",
    type=click.Choice([tf.value for tf in TimeFilter], case_sensitive=False),
    default=TimeFilter.DAY.value,
    help="Time period for top posts (default: Day)",
)
def main(config_path, output_directory, time_filter):
    # Load the config
    config = Config.from_path(config_path)
    lemmy = Lemmy.from_env()
    rss = RSSBuilder(
        title="Daily Lemmy Digest",
        description="Top posts from configured Lemmy communities.",
        host_url="https://yamatt.github.io/ddor/",
        feed_url=f"https://yamatt.github.io/ddor/{config.name}.rss",
    )

    # Fetch posts from all communities concurrently
    log.info(
        "FETCHING POSTS",
        total_communities=len(config.communities),
        max_concurrent=config.max_concurrent_requests,
        time_filter=time_filter,
    )
    all_posts = asyncio.run(
        fetch_all_communities(
            lemmy, config.communities, config.max_concurrent_requests, time_filter
        )
    )

    post_visibility_rate = (config.count / len(all_posts)) * 100
    post_loss_rate = 100 - post_visibility_rate
    log.info(
        "POST VISIBILITY",
        total_posts=len(all_posts),
        post_visibility_rate=round(post_visibility_rate, 2),
        post_loss_rate=round(post_loss_rate, 2),
    )

    # Sort by weighted engagement score
    log.info("SORTING POSTS", total_posts=len(all_posts))
    all_posts.sort(key=lambda post: post.get_engagement_score(), reverse=True)

    top_posts = all_posts[: config.count]

    for post in top_posts:
        log.debug(
            "SELECTED POST",
            title=post.title,
            community=post.community_name,
            instance=post.instance.instance_url,
            url=post.url,
            score=post.score,
            comments=post.comments,
            weighted=post.community_weight,
            engagement_score=post.get_engagement_score(),
        )

    rss_content = rss.build_feed(posts=top_posts)

    output_file_name = f"{config.name}.rss"
    output_file_path = join(output_directory, output_file_name)

    log.info("WRITING RSS", path=output_file_path)
    with open(output_file_path, "wb") as f:
        f.write(rss_content)


if __name__ == "__main__":
    main()
