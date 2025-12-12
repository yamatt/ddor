# DDOR

Daily Dose of... whatever you want! Get a curated RSS feed of top posts from your favorite Lemmy communities.

This tool was inspired by the YouTube channel Daily Dose of Internet that curates the best videos together every few days. It takes that model of a regular feed of what is actually the very best and with minimal addictive qualities, by outputting it as an RSS feed daily.

Originally built for Reddit, it now works with Lemmy - the federated, open-source link aggregator.

## Setup

### Choosing Lemmy Communities

Lemmy is federated, meaning there are many instances (servers) you can connect to. Some popular instances include:
- `lemmy.world` - General purpose, largest instance
- `lemmy.ml` - The original instance
- `lemmy.dbzer0.com` - Privacy-focused
- `sh.itjust.works` - General purpose

You can fetch posts from communities across **any instance** by specifying them in your config file.

### Creating a Configuration File

Create a TOML configuration file specifying which communities to fetch:

```toml
[config]
name = "my-feed"
count = 20
max_concurrent_requests = 4  # Optional: Number of concurrent network requests (default: 3)

[communities]
list = [
    "technology@lemmy.world",
    "linux@lemmy.ml",
    "selfhosted@lemmy.world",
    "privacy@lemmy.dbzer0.com",
]
```

**Configuration options**:
- `name`: Name for your RSS feed
- `count`: Maximum number of posts to include in the feed
- `max_concurrent_requests` (optional): Maximum number of communities to fetch simultaneously (default: 3, recommended: 3-4)

**Community format**: Communities must be specified as `community@instance.com` to indicate which Lemmy instance hosts that community. This allows you to aggregate content from communities across the federated network.

## Usage

Run the tool with a config file and output directory:

```bash
uv run ddor config/yamatt.toml ./output
```

You can specify a time period for top posts (default: Day):

```bash
uv run ddor config/yamatt.toml ./output --time-filter Week    # Last 7 days
uv run ddor config/yamatt.toml ./output --time-filter Month   # Last 30 days
uv run ddor config/yamatt.toml ./output --time-filter Year    # Last year
uv run ddor config/yamatt.toml ./output --time-filter All     # All time
```

## Running Tests

Run all tests with:

```bash
uv run pytest tests/ -v
```