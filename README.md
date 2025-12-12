# DDOR

Daily Dose of... whatever you want! Get a curated RSS feed of top posts from your favorite Lemmy communities.

This tool was inspired by the YouTube channel Daily Dose of Internet that curates the best videos together every few days. It takes that model of a regular feed of what is actually the very best and with minimal addictive qualities, by outputting it as an RSS feed daily.

Originally built for Reddit, it now works with Lemmy - the federated, open-source link aggregator.

## Setup

### Choosing a Lemmy Instance

Lemmy is federated, meaning there are many instances (servers) you can connect to. Some popular instances include:
- `lemmy.world` - General purpose, largest instance
- `lemmy.ml` - The original instance
- `lemmy.dbzer0.com` - Privacy-focused
- `sh.itjust.works` - General purpose

You can browse communities across any instance, regardless of which one you use.

### Setting Environment Variables

Set the following environment variables:

```bash
# Required: The Lemmy instance URL
export DDOR_LEMMY_INSTANCE="https://lemmy.world"

# Optional: Authentication (only needed for private communities or rate limiting)
export DDOR_LEMMY_USERNAME="your_username"
export DDOR_LEMMY_PASSWORD="your_password"
```

**Note**: Authentication is optional. Most public communities can be accessed without logging in.

### Creating a Configuration File

Create a TOML configuration file specifying which communities to fetch:

```toml
[config]
name = "my-feed"
count = 20

[communities]
list = [
    "technology",
    "linux",
    "selfhosted",
    "privacy",
]
```

The community names should be the community name without the instance (e.g., `technology` not `technology@lemmy.world`).

## Usage

Run the tool with a config file and output directory:

```bash
uv run ddor config/yamatt.toml ./output
```
