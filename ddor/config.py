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
    def subreddit_names(self):
        return self.config["subreddits"]["list"]
