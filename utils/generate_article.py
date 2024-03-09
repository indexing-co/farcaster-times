import json
from openai import OpenAI

client = OpenAI()


def generate_article(casts=[], channel_name=None):
    if not casts or not channel_name:
        raise "Not enough info provided"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a senior New York Times column writer. You write daily articles focused on "{channel_name}".

You will be given a list of social media posts as for the day as JSON. The `text` field represents the content and the `username` name field represents the author. The `parent_hash` field indicates that the post is in response to another post, matching on its `hash` field.

Your job is to return a headline worthy article based on the provided messages.

Focus on specific themes from the day, not generalizations.

Use quotes from the provided messages.

Each article should be between 500 and 1000 words in length.

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

    return response.choices[0].message.content
