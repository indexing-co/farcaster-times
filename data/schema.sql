CREATE TABLE IF NOT EXISTS articles (
    hash text unique,
    article text
);

CREATE TABLE IF NOT EXISTS daily_top_users (
    day timestamptz unique,
    usernames text[]
);