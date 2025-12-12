from tomllib import load


class Config:
    @classmethod
    def from_path(cls, toml_file_path):
        return cls(load(open(toml_file_path, "rb")))

    def __init__(self, config):
        self.config = config

    @property
    def name(self):
        return self.config["config"]["name"]

    @property
    def count(self):
        return self.config["config"]["count"]

    @property
    def max_concurrent_requests(self):
        """Get max concurrent requests, defaults to 3 if not specified."""
        return self.config["config"].get("max_concurrent_requests", 3)

    @property
    def communities(self):
        """Get community configurations as list of dicts with name and weight.

        Format: {name = "community@instance", weight = 0}

        Weight: -1 to 1 (0 = no bias, 1 = increase bias, -1 = decrease bias)
        """
        communities_config = self.config["communities"]["list"]
        result = []

        for item in communities_config:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Invalid community format: {item}. "
                    "Each community must be a dict with 'name' and 'weight' keys. "
                    'Example: {{name = "technology@lemmy.world", weight = 0}}'
                )

            result.append(
                {
                    "name": item["name"].strip(),
                    "weight": item.get("weight", 0),
                }
            )

        return result

    @property
    def community_names(self):
        """Get community names in format 'community@instance.com'."""
        return [c["name"] for c in self.communities]
