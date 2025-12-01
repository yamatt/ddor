from tomllib import load

class Config:
    @classmethod
    def from_path(cls, toml_file_path):
        return cls(
            load(open(toml_file_path, "r"))
        )

    def __init__(self, config):
        self.config = config
