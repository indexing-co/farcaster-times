import os

APP_URL = os.environ.get("APP_URL")

# GPT_MODEL = "gpt-4-turbo-preview"
GPT_MODEL = "gpt-3.5-turbo"

MAX_POSTS = 100 if "gpt-4" in GPT_MODEL else 50
