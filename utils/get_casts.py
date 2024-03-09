import os
from google.cloud import bigquery
from .generate_article import GPT_MODEL

client = bigquery.Client()

MAX_POSTS = 100 if "gpt-4" in GPT_MODEL else 50


def get_casts(parent_url=None, start_date=None, end_date=None):
    if not parent_url:
        raise "No params provided"

    sql = generate_sql(parent_url=parent_url, start_date=start_date, end_date=end_date)

    """
    TODO: cache results of similar queries
          this will likely require intentionally timeboxing queries in some way :thinking:
    """

    query = client.query(sql)
    rows = query.result()

    return [r for r in rows]


def generate_sql(parent_url=None, start_date=None, end_date=None):
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
