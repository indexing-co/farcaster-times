import json
import os
from openai import OpenAI

from .cache import get_cached_article, store_cached_article
from .constants import GPT_MODEL
from .get_casts import get_casts_by_channel, get_casts_by_username
from .lookups import normalize_channel, generate_article_hash
from .upload_file import upload_to_pinata

client = OpenAI()


def generate_dalle_image(summary):
    response = client.images.generate(
        model="dall-e-3", prompt=summary, size="1024x1024", quality="standard", n=1
    )
    image_url = response.data[0].url
    return image_url


def generate_article(
    channel_or_username=None, start_date=None, end_date=None, type=None
):
    if not channel_or_username or not start_date or not end_date or not type:
        raise ValueError("Not enough info provided")

    identifier, parent_url, _ = normalize_channel(channel=channel_or_username)

    article_hash = generate_article_hash(
        channel_or_username=channel_or_username,
        start_date=start_date,
        end_date=end_date,
    )
    cached_article = get_cached_article(article_hash)
    if cached_article:
        return cached_article
    else:
        print("generating article for", channel_or_username, start_date, end_date)

    # Decide whether to fetch casts by channel or by username based on the presence of parent_url
    if type == "channel":
        casts = get_casts_by_channel(
            parent_url=parent_url, start_date=start_date, end_date=end_date
        )

    elif type == "username":
        casts = get_casts_by_username(
            username=identifier, start_date=start_date, end_date=end_date
        )

    if not casts or len(casts) == 0:
        raise ValueError("No casts found")

    response = client.chat.completions.create(
        model=GPT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a senior New York Times column writer.

You will be given a list of social media posts as for the day as JSON.
The `text` field represents the content and the `username` name field represents the author.
The `parent_hash` field indicates that the post is in response to another post, matching on its `hash` field.

Your job is to return a thoughtful article based on the provided posts.
Focus on specific themes from the posts provided, not generalizations.
Use at least 2 quotes from the provided posts.
Each article should be at least 500 words in length.

The response should be in JSON and include following fields: headline, subheading, summary, content.

The content should be formatted as a string with markdown. Link to quoted posts using their `url` field.
""",
            },
            {
                "role": "user",
                "content": json.dumps(
                    [
                        {
                            "text": c.text,
                            "username": c.username,
                            "hash": c.hash,
                            "parent_hash": c.parent_cast_hash,
                            "url": c.url,
                        }
                        for c in casts
                    ]
                ),
            },
        ],
    )

    article = json.loads(response.choices[0].message.content)

    summary = article["summary"]

    if os.getenv("PINATA_API_KEY"):
        dalle_url = generate_dalle_image(summary)
        ipfs_hash = upload_to_pinata(dalle_url)
        article["image_url"] = f"https://ipfs.io/ipfs/{ipfs_hash}"

    store_cached_article(hash=article_hash, article=article)

    return article
