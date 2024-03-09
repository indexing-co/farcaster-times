import json
import os
import psycopg2
import re

if os.environ.get("ARTICLE_DB"):
    conn = psycopg2.connect(os.environ.get("ARTICLE_DB"))


def get_cached_article(hash):
    if not conn:
        return None

    cur = conn.cursor()
    cur.execute(f"SELECT hash, article FROM articles WHERE hash = '{hash}'")
    rows = cur.fetchall()
    conn.commit()

    if rows:
        _hash, article = rows[0]
        return json.loads(article)


def store_cached_article(hash, article):
    if not conn:
        return

    # NOTE: probably need some sanitization here
    print(article)

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (hash, article) VALUES (%s, %s)",
        (hash, json.dumps(article)),
    )
    conn.commit()
