import json
from openai import OpenAI

client = OpenAI()

# GPT_MODEL = "gpt-4-turbo-preview"
GPT_MODEL = "gpt-3.5-turbo"


def generate_article(casts=[], channel=None):
    if not casts or not channel:
        raise "Not enough info provided"

    response = client.chat.completions.create(
        model=GPT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a senior New York Times column writer. You write headline articles focused on "{channel}".

You will be given a list of social media posts as for the day as JSON.
The `text` field represents the content and the `username` name field represents the author.
The `parent_hash` field indicates that the post is in response to another post, matching on its `hash` field.

Your job is to return a thoughtful article based on the provided posts.
Focus on specific themes from the posts provided, not generalizations.
Use quotes from the provided posts.
Each article should be at least 500 words in length.

The response should be in JSON and include following fields: headline, subheading, summary, content, dalle_prompt_for_thumbnail_image.

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

    return json.loads(response.choices[0].message.content)
