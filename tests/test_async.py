"""Tests for the main async functionality."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from ddor.__main__ import fetch_all_communities, fetch_community_posts


class TestAsyncFetching:
    """Test the async fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_community_posts(self):
        """Test fetching posts from a single community."""
        # Mock the Lemmy instance
        mock_lemmy = Mock()
        mock_post = Mock()
        mock_post.community_weight = 0
        mock_lemmy.get_community_top_posts.return_value = [mock_post]

        community_config = {"name": "technology@lemmy.world", "weight": 1}
        semaphore = asyncio.Semaphore(1)

        posts = await fetch_community_posts(mock_lemmy, community_config, semaphore)

        # Verify the mock was called
        mock_lemmy.get_community_top_posts.assert_called_once_with(
            "technology@lemmy.world"
        )

        # Verify weight was applied
        assert len(posts) == 1
        assert posts[0].community_weight == 1

    @pytest.mark.asyncio
    async def test_fetch_all_communities(self):
        """Test fetching posts from multiple communities concurrently."""
        # Mock the Lemmy instance
        mock_lemmy = Mock()

        def create_mock_posts():
            """Create fresh mock post objects for each call."""
            post1 = Mock()
            post1.community_weight = 0
            post2 = Mock()
            post2.community_weight = 0
            return [post1, post2]

        # Use side_effect to return new mock objects for each call
        mock_lemmy.get_community_top_posts.side_effect = [
            create_mock_posts(),
            create_mock_posts(),
        ]

        communities = [
            {"name": "tech@lemmy.world", "weight": 1},
            {"name": "news@lemmy.ml", "weight": 0},
        ]

        all_posts = await fetch_all_communities(
            mock_lemmy, communities, max_concurrent=2
        )

        # Verify all communities were fetched
        assert mock_lemmy.get_community_top_posts.call_count == 2

        # Verify we got all posts back (2 posts per community = 4 total)
        assert len(all_posts) == 4

        # Verify weights were applied (order may vary due to async)
        weights = [post.community_weight for post in all_posts]
        assert weights.count(1) == 2  # Two posts with weight 1
        assert weights.count(0) == 2  # Two posts with weight 0

    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        """Test that concurrency is properly limited."""
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_seen = 0

        def mock_get_posts(community_name):
            """Synchronous mock that simulates a slow network call."""
            import time

            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            time.sleep(0.1)  # Simulate network delay
            concurrent_count -= 1
            return []

        mock_lemmy = Mock()
        mock_lemmy.get_community_top_posts = mock_get_posts

        communities = [
            {"name": f"community{i}@lemmy.world", "weight": 0} for i in range(10)
        ]

        # Limit to 3 concurrent requests
        await fetch_all_communities(mock_lemmy, communities, max_concurrent=3)

        # Verify we never exceeded the limit
        assert max_concurrent_seen <= 3
        assert max_concurrent_seen > 0  # Ensure tracking worked
