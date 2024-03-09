import os
from google.cloud import bigquery

client = bigquery.Client()


def get_casts(channel):
    sql = generate_sql(channel)

    """
    TODO: cache results of similar queries
          this will likely require intentionally timeboxing queries in some way :thinking:
    """

    query = client.query(sql)
    rows = query.result()

    return rows


def generate_sql(channel=None, limit=100):

    if not channel:
        raise "No channel provided"

    return f"""

WITH
  root_casts AS (
  SELECT
    c.timestamp,
    c.hash,
    JSON_VALUE(p.data, '$.username') AS username,
    CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), SUBSTR(c.hash, 0, 10)) AS url,
    '' AS parent_cast_hash,
    c.text
  FROM
    `glossy-odyssey-366820.farcaster.casts` c
  LEFT JOIN
    `glossy-odyssey-366820.farcaster.profiles` p
  ON
    c.fid = p.fid
  WHERE
    parent_cast_url = '{channel}'
    AND JSON_VALUE(p.data, '$.username') IS NOT NULL
  ORDER BY
    c.timestamp DESC
  LIMIT
    {limit})
SELECT
  *
FROM
  root_casts
UNION ALL (
  SELECT
    c.timestamp,
    c.hash,
    JSON_VALUE(p.data, '$.username') AS username,
    CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), SUBSTR(c.hash, 0, 10)) AS url,
    c.parent_cast_hash,
    c.text
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
    AND JSON_VALUE(p.data, '$.username') IS NOT NULL)
ORDER BY
  timestamp DESC;

  """
