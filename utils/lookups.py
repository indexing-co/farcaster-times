import json
import os

legacy_channels = json.load(open(os.getcwd() + "/data/legacy_channels.json"))

legacy_channel_map = {}
for c in legacy_channels:
    legacy_channel_map[c["channel_id"]] = c["parent_url"]


def normalize_channel(channel=""):
    if not channel:
        raise "No channel provided"

    if "/" in channel:
        channel = channel.split("/")[-1]

    channel = channel.lower()

    parent_url = (
        legacy_channel_map[channel]
        if channel in legacy_channel_map
        else f"https://warpcast.com/~/{channel}"
    )

    return channel, parent_url