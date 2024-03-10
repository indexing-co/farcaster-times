import os
from google.cloud import bigquery

from .constants import MAX_POSTS
from .cache import get_cached_daily_usernames, store_cached_daily_usernames

client = bigquery.Client()


def get_casts_by_channel(parent_url=None, start_date=None, end_date=None):
    if not parent_url:
        raise "No params provided"

    sql = generate_channel_casts_sql(
        parent_url=parent_url, start_date=start_date, end_date=end_date
    )

    """
    TODO: cache results of similar queries
          this will likely require intentionally timeboxing queries in some way :thinking:
    """

    query = client.query(sql)
    rows = query.result()

    return [r for r in rows]


def generate_channel_casts_sql(parent_url=None, start_date=None, end_date=None):
    if not parent_url:
        raise "Missing params for generating SQL"

    """
    TODO: reconfigure this a bit to have better limits :thinking:
          OR force everything to be by date
    """

    return f"""

WITH
  root_casts AS (
    SELECT
      c.timestamp,
      c.hash,
      JSON_VALUE(p.data, '$.username') AS username,
      CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), "/", SUBSTR(c.hash, 0, 10)) AS url,
      '' AS parent_cast_hash,
      c.text,
      (
        SELECT
          COUNT(*)
        FROM
          `glossy-odyssey-366820.farcaster.reactions`
        WHERE
          target_cast_hash = c.hash
      ) as reaction_count
    FROM
      `glossy-odyssey-366820.farcaster.casts` c
    LEFT JOIN
      `glossy-odyssey-366820.farcaster.profiles` p
    ON
      c.fid = p.fid
    WHERE
      parent_cast_url = '{parent_url}'
      AND JSON_VALUE(p.data, '$.username') IS NOT NULL
      {f"AND EXTRACT(DATE from c.timestamp) BETWEEN '{start_date}' and '{end_date}'" if start_date and end_date else ""}
  )
SELECT
  *
FROM
  root_casts
UNION ALL (
  SELECT
    c.timestamp,
    c.hash,
    JSON_VALUE(p.data, '$.username') AS username,
    CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), "/", SUBSTR(c.hash, 0, 10)) AS url,
    c.parent_cast_hash,
    c.text,
    (
      SELECT
        COUNT(*)
      FROM
        `glossy-odyssey-366820.farcaster.reactions`
      WHERE
        target_cast_hash = c.hash
    ) as reaction_count
  FROM
    `glossy-odyssey-366820.farcaster.casts` c
  LEFT JOIN
    `glossy-odyssey-366820.farcaster.profiles` p
  ON
    c.fid = p.fid
  WHERE
    c.parent_cast_hash IN (
      SELECT
        rc.hash
      FROM
        root_casts rc)
      AND JSON_VALUE(p.data, '$.username') IS NOT NULL
    )
ORDER BY
  reaction_count DESC
LIMIT {MAX_POSTS}
  """


def get_casts_by_username(username=None, start_date=None, end_date=None):
    if not username:
        raise ValueError("Username is required")

    sql = generate_username_casts_sql(
        username=username, start_date=start_date, end_date=end_date
    )

    query = client.query(sql)
    rows = query.result()

    return [r for r in rows]


def generate_username_casts_sql(username, start_date=None, end_date=None):
    return f"""
WITH user_fid AS (
    SELECT
        fid
    FROM
        `glossy-odyssey-366820.farcaster.profiles`
    WHERE
        JSON_VALUE(data, '$.username') = '{username}'
),
user_casts AS (
    SELECT
        c.timestamp,
        c.hash,
        '{username}' AS username,
        CONCAT('https://warpcast.com/', '{username}', "/", SUBSTR(c.hash, 0, 10)) AS url,
        c.parent_cast_hash,
        c.text,
        (
            SELECT
                COUNT(*)
            FROM
                `glossy-odyssey-366820.farcaster.reactions`
            WHERE
                target_cast_hash = c.hash
        ) AS reaction_count
    FROM
        `glossy-odyssey-366820.farcaster.casts` c
    JOIN
        user_fid uf ON c.fid = uf.fid
    WHERE {f"EXTRACT(DATE from c.timestamp) BETWEEN '{start_date}' and '{end_date}'" if start_date and end_date else ""}
)
SELECT
    *
FROM
    user_casts
ORDER BY
    reaction_count DESC, timestamp DESC
LIMIT {MAX_POSTS}
"""


def get_top_casts_by_channel(start_date=None, end_date=None):
    sql = generate_top_casts_by_channel_sql(start_date=start_date, end_date=end_date)

    query = client.query(sql)
    rows = query.result()

    return [r for r in rows]


def generate_top_casts_by_channel_sql(start_date=None, end_date=None):
    if not start_date or not end_date:
        raise ValueError("Start date and end date must be provided")

    sql = f"""
WITH
  casts AS (
    SELECT
      c.timestamp,
      c.hash,
      JSON_VALUE(p.data, '$.username') AS username,
      c.text,
      c.parent_cast_url,
      (SELECT COUNT(*) FROM `glossy-odyssey-366820.farcaster.reactions` WHERE target_cast_hash = c.hash) AS reaction_count
    FROM
      `glossy-odyssey-366820.farcaster.casts` c
    JOIN `glossy-odyssey-366820.farcaster.profiles` p ON c.fid = p.fid
    WHERE 
      c.timestamp BETWEEN '{start_date}' AND '{end_date}'
),
channel_ids AS (
    SELECT
        timestamp,
        hash,
        username,
        text,
        parent_cast_url,
        reaction_count,
        CASE
            WHEN parent_cast_url LIKE 'https://%' THEN REGEXP_EXTRACT(parent_cast_url, 'https://[^/]+/([^/]+)$')
            ELSE parent_cast_url
        END AS channel_id
    FROM casts
),
aggregated_by_channel AS (
    SELECT
        channel_id,
        COUNT(*) AS total_casts,
        SUM(reaction_count) AS total_reactions
    FROM channel_ids
    WHERE channel_id IS NOT NULL
    GROUP BY channel_id
    ORDER BY total_reactions DESC
    LIMIT 10
)
SELECT * FROM aggregated_by_channel;
"""

    return sql


def get_top_casts_by_username(start_date=None, end_date=None):
    cached = get_cached_daily_usernames(start_date)
    if cached:
        return cached

    sql = generate_top_casts_by_username_sql(start_date=start_date, end_date=end_date)

    query = client.query(sql)
    rows = query.result()

    usernames = [r.get("username") for r in rows if r.get("username") is not None]
    store_cached_daily_usernames(start_date, usernames)

    return usernames


def generate_top_casts_by_username_sql(start_date=None, end_date=None):
    if not start_date or not end_date:
        raise ValueError("Start date and end date must be provided")

    sql = f"""
WITH
  profile_casts AS (
    SELECT
      c.timestamp,
      c.hash,
      JSON_VALUE(p.data, '$.username') AS username,
      c.text,
      (SELECT COUNT(*) FROM `glossy-odyssey-366820.farcaster.reactions` WHERE target_cast_hash = c.hash) AS reaction_count
    FROM
      `glossy-odyssey-366820.farcaster.casts` c
    JOIN `glossy-odyssey-366820.farcaster.profiles` p ON c.fid = p.fid
    WHERE 
      c.timestamp BETWEEN '{start_date}' AND '{end_date}'
),
aggregated_by_profile AS (
    SELECT
        username,
        COUNT(*) AS total_casts,
        SUM(reaction_count) AS total_reactions
    FROM profile_casts
    GROUP BY username
    ORDER BY total_reactions DESC, total_casts DESC
    LIMIT 10
)
SELECT * FROM aggregated_by_profile;
"""
    return sql
