# DDOR

Reddit has been enshitified. There I said it.

It has infinite scroll, _recommendations_, and you can't find the stuff you're actually interested in.

I really like the YouTube channel Daily Dose of Internet that curates the best videos together every few days.

I thought I would take that model of a regular feed of what is actually the very best and with minimal addictive qualities, by outputting it as an RSS feed daily.

## Setup

### Getting Reddit API Credentials

This tool requires Reddit API credentials to fetch posts. Follow these steps to get your client ID and secret:

1. Go to https://www.reddit.com/prefs/apps
2. Scroll down and click **"create another app..."** (or "are you a developer? create an app...")
3. Fill in the form:
   - **name**: Choose a name for your app (e.g., "ddor")
   - **App type**: Select **"script"**
   - **description**: Optional
   - **about url**: Optional
   - **redirect uri**: Enter `http://localhost:8080` (required but not used for script apps)
4. Click **"create app"**
5. Your credentials will be displayed:
   - **Client ID**: The string under "personal use script" (below the app name)
   - **Client Secret**: The string next to "secret"

### Setting Environment Variables

Set the following environment variables with your credentials:

```bash
export DDOR_CLIENT_ID="your_client_id_here"
export DDOR_CLIENT_SECRET="your_client_secret_here"
```

## Usage

Run the tool with a config file and output directory:

```bash
uv run ddor config/yamatt.toml ./output
```
