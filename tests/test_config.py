"""Tests for configuration handling."""

from tomllib import loads

import pytest

from ddor.config import Config


class TestConfig:
    """Test the Config class."""

    def test_max_concurrent_requests_default(self):
        """Test that max_concurrent_requests defaults to 3."""
        config_data = """
[config]
name = "test"
count = 10

[communities]
list = [
    { name = "test@lemmy.world", weight = 0 }
]
"""
        config = Config(loads(config_data))
        assert config.max_concurrent_requests == 3

    def test_max_concurrent_requests_custom(self):
        """Test that max_concurrent_requests can be customized."""
        config_data = """
[config]
name = "test"
count = 10
max_concurrent_requests = 5

[communities]
list = [
    { name = "test@lemmy.world", weight = 0 }
]
"""
        config = Config(loads(config_data))
        assert config.max_concurrent_requests == 5

    def test_all_config_properties(self):
        """Test that all config properties work correctly."""
        config_data = """
[config]
name = "my-feed"
count = 15
max_concurrent_requests = 4

[communities]
list = [
    { name = "tech@lemmy.world", weight = 1 },
    { name = "news@lemmy.ml", weight = -1 }
]
"""
        config = Config(loads(config_data))
        assert config.name == "my-feed"
        assert config.count == 15
        assert config.max_concurrent_requests == 4
        assert len(config.communities) == 2
        assert config.communities[0]["name"] == "tech@lemmy.world"
        assert config.communities[0]["weight"] == 1
        assert config.communities[1]["name"] == "news@lemmy.ml"
        assert config.communities[1]["weight"] == -1
