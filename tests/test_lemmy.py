"""Tests for the Lemmy API integration."""

from unittest.mock import Mock, patch

import pytest

from ddor.lemmy import Lemmy, LemmyPost


class TestLemmy:
    """Test the Lemmy class."""

    def test_discover_community_returns_int(self):
        """Test that discover_community can handle when it returns an int directly."""
        lemmy = Lemmy()

        # Mock the client and its methods
        mock_client = Mock()
        mock_client.discover_community.return_value = 12345  # Returns int directly
        mock_client.post.list.return_value = [
            {
                "post": {
                    "name": "Test Post",
                    "score": 100,
                    "published": "2024-01-01T00:00:00Z",
                },
                "community": {"name": "technology"},
                "creator": {"name": "testuser"},
            }
        ]

        with patch.object(lemmy, "_get_client", return_value=mock_client):
            posts = lemmy.get_community_top_posts("technology@lemmy.world")

        # Verify the client methods were called correctly
        mock_client.discover_community.assert_called_once_with("technology")
        mock_client.post.list.assert_called_once_with(
            community_id=12345, sort="TopDay", limit=20
        )

        # Verify we got posts back
        assert len(posts) == 1
        assert isinstance(posts[0], LemmyPost)

    def test_discover_community_returns_dict(self):
        """Test that discover_community can handle when it returns a dict."""
        lemmy = Lemmy()

        # Mock the client and its methods
        mock_client = Mock()
        mock_client.discover_community.return_value = {"community": {"id": 67890}}
        mock_client.post.list.return_value = [
            {
                "post": {
                    "name": "Test Post",
                    "score": 100,
                    "published": "2024-01-01T00:00:00Z",
                },
                "community": {"name": "technology"},
                "creator": {"name": "testuser"},
            }
        ]

        with patch.object(lemmy, "_get_client", return_value=mock_client):
            posts = lemmy.get_community_top_posts("technology@lemmy.world")

        # Verify the client methods were called correctly
        mock_client.discover_community.assert_called_once_with("technology")
        mock_client.post.list.assert_called_once_with(
            community_id=67890, sort="TopDay", limit=20
        )

        # Verify we got posts back
        assert len(posts) == 1
        assert isinstance(posts[0], LemmyPost)

    def test_discover_community_returns_none(self):
        """Test that we handle when discover_community returns None."""
        lemmy = Lemmy()

        # Mock the client
        mock_client = Mock()
        mock_client.discover_community.return_value = None

        with patch.object(lemmy, "_get_client", return_value=mock_client):
            posts = lemmy.get_community_top_posts("nonexistent@lemmy.world")

        # Verify we got no posts back
        assert len(posts) == 0
        # post.list should not be called
        mock_client.post.list.assert_not_called()

    def test_invalid_community_spec_no_at_sign(self):
        """Test that invalid community spec without @ raises ValueError."""
        lemmy = Lemmy()

        with pytest.raises(
            ValueError, match="must be in format 'community@instance.com'"
        ):
            lemmy.get_community_top_posts("technology")

    def test_invalid_community_spec_multiple_at_signs(self):
        """Test that invalid community spec with multiple @ raises ValueError."""
        lemmy = Lemmy()

        with pytest.raises(ValueError, match="invalid format"):
            lemmy.get_community_top_posts("tech@nology@lemmy.world")


class TestLemmyPost:
    """Test the LemmyPost wrapper class."""

    def test_lemmy_post_properties(self):
        """Test that LemmyPost properly wraps post data."""
        post_data = {
            "post": {
                "name": "Test Post Title",
                "score": 150,
                "published": "2024-01-01T12:00:00Z",
                "body": "Test post body",
                "ap_id": "https://lemmy.world/post/12345",
            },
            "community": {"name": "technology"},
            "creator": {"name": "testuser"},
        }

        post = LemmyPost(post_data)

        assert post.title == "Test Post Title"
        assert post.score == 150
        assert post.url == "https://lemmy.world/post/12345"
        assert post.subreddit == "technology"
        assert post.selftext == "Test post body"
        assert post.created_utc > 0  # Should be a valid timestamp
