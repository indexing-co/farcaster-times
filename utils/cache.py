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

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (hash, article) VALUES (%s, %s) ON CONFLICT(hash) DO UPDATE SET article = EXCLUDED.article",
        (hash, json.dumps(article)),
    )
    conn.commit()


def get_cached_daily_usernames(date):
    if not conn:
        return None

    cur = conn.cursor()
    cur.execute(f"SELECT usernames FROM daily_top_users WHERE day = '{date}T00:00:00Z'")
    rows = cur.fetchall()
    conn.commit()

    if rows:
        (usernames,) = rows[0]
        return usernames


def store_cached_daily_usernames(date, usernames):
    if not conn:
        return

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO daily_top_users (day, usernames) VALUES (%s, %s) ON CONFLICT (day) DO UPDATE SET usernames = EXCLUDED.usernames",
        (f"{date}T00:00:00Z", "{" + ",".join(usernames) + "}"),
    )
    conn.commit()
