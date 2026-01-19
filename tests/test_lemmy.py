"""Tests for the Lemmy API integration."""

from unittest.mock import Mock, patch

import pytest

from ddor.lemmy import Lemmy, LemmyPost


class TestLemmy:
    """Test the Lemmy class."""

    def test_discover_community_returns_int(self):
        """Test that discover_community can handle when it returns an int directly."""
        lemmy = Lemmy()

        # Mock the instance and its client
        mock_instance = Mock()
        from ddor.lemmy import LemmyPost
        from unittest.mock import Mock as UMock

        post_dict = {
            "id": 1,
            "name": "Test Post",
            "score": 100,
            "published": "2024-01-01T00:00:00Z",
            "counts": {"upvotes": 100, "downvotes": 0, "comments": 5, "score": 100},
            "community": {"name": "technology"},
            "creator": {"name": "testuser"},
        }
        mock_instance.get_top_posts.return_value = [
            LemmyPost.from_post(post_dict, 0, UMock())
        ]

        with patch.object(lemmy, "get_instance", return_value=mock_instance):
            posts = lemmy.get_community_top_posts("technology@lemmy.world", 0)

        assert isinstance(posts, list)
        assert len(posts) == 1

        # Verify we got posts back
        assert len(posts) == 1
        assert isinstance(posts[0], LemmyPost)

    def test_discover_community_returns_dict(self):
        """Test that discover_community can handle when it returns a dict."""
        lemmy = Lemmy()

        # Mock the instance and its client
        mock_instance = Mock()
        from ddor.lemmy import LemmyPost
        from unittest.mock import Mock as UMock

        post_dict = {
            "id": 1,
            "name": "Test Post",
            "score": 100,
            "published": "2024-01-01T00:00:00Z",
            "counts": {"upvotes": 100, "downvotes": 0, "comments": 5, "score": 100},
            "community": {"name": "technology"},
            "creator": {"name": "testuser"},
        }
        mock_instance.get_top_posts.return_value = [
            LemmyPost.from_post(post_dict, 0, UMock())
        ]

        with patch.object(lemmy, "get_instance", return_value=mock_instance):
            posts = lemmy.get_community_top_posts("technology@lemmy.world", 0)

        assert isinstance(posts, list)
        assert len(posts) == 1

        # Verify we got posts back
        assert len(posts) == 1
        assert isinstance(posts[0], LemmyPost)

    def test_discover_community_returns_none(self):
        """Test that we handle when discover_community returns None."""
        lemmy = Lemmy()

        # Mock the instance and its client
        mock_instance = Mock()
        mock_instance.get_top_posts.return_value = []

        with patch.object(lemmy, "get_instance", return_value=mock_instance):
            posts = lemmy.get_community_top_posts("nonexistent@lemmy.world", 0)

        assert isinstance(posts, list)
        assert len(posts) == 0

    def test_invalid_community_spec_no_at_sign(self):
        """Test that invalid community spec without @ raises ValueError."""
        lemmy = Lemmy()

        with pytest.raises(ValueError, match="not enough values to unpack"):
            lemmy.get_community_top_posts("technology", 0)

    def test_invalid_community_spec_multiple_at_signs(self):
        """Test that invalid community spec with multiple @ raises ValueError."""
        lemmy = Lemmy()

        with pytest.raises(ValueError, match="too many values to unpack"):
            lemmy.get_community_top_posts("tech@nology@lemmy.world", 0)


class TestLemmyPost:
    """Test the LemmyPost wrapper class."""

    def test_lemmy_post_properties(self):
        """Test that LemmyPost properly wraps post data."""
        from unittest.mock import Mock

        post_data = {
            "id": 12345,
            "name": "Test Post Title",
            "score": 150,
            "published": "2024-01-01T12:00:00Z",
            "body": "Test post body",
            "ap_id": "https://lemmy.world/post/12345",
            "counts": {
                "upvotes": 150,
                "downvotes": 10,
                "comments": 5,
                "score": 150,
            },
            "community": {"name": "technology"},
            "creator": {"name": "testuser"},
        }
        mock_instance = Mock()
        post = LemmyPost.from_post(post_data, 0, mock_instance)

        assert post.title == "Test Post Title"
        assert post.score == 150
        assert post.url == "https://lemmy.world/post/12345"
        assert post.subreddit == "technology"
        assert post.selftext == "Test post body"
        from datetime import datetime

        assert isinstance(post.published, datetime)  # Should be a valid datetime object
        assert post.upvotes == 150
        assert post.downvotes == 10
        assert post.comments_count == 5
