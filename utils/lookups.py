import hashlib
import json
import os

legacy_channels = json.load(open(os.getcwd() + "/data/legacy_channels.json"))

legacy_channel_map = {}
for c in legacy_channels:
    legacy_channel_map[c["channel_id"]] = c["parent_url"]


def normalize_channel(channel=""):
    if not channel:
        raise ValueError("No channel provided")

    # Check if input is a username (starts with '@')
    if "@" in channel:
        username = channel.strip("@")
        return username, None  # No parent_url needed for usernames

    # Handling channels, with backward compatibility for legacy channels
    elif "/" in channel:
        channel = channel.split("/")[-1]

    channel = channel.lower()

    # Fetch parent_url from legacy channels or construct it for newer channels
    parent_url = (
        legacy_channel_map[channel]
        if channel in legacy_channel_map
        else f"https://warpcast.com/~/{channel}"
    )

    return channel, parent_url

def generate_article_hash(channel_or_username=None, start_date=None, end_date=None):
    m = hashlib.sha256()
    m.update(channel_or_username.encode("utf-8"))
    m.update(start_date.encode("utf-8"))
    m.update(end_date.encode("utf-8"))

    return m.hexdigest()
