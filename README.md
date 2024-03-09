# the-farcaster-times
aka ROBO JOURNO

## Pages

### /
Crude home page that enables routing to other pages

### /articles/:channel_or_username/:year/:month/:day
View a particular day's article. Example:
/articles/music/2023/03/08

### /articles/:channel_or_username/:year/:month
View a particular month's article. Example:
/articles/farcascter/2023/02

## Running Locally

```bash
$ cp .env.sample .env
```

Update `.env` with your own credentials.

NOTE: This currently assumes you're already authenticated locally with Google Cloud

Finally, run:

```bash
$ pip install -r requirements.txt
$ flask run --debug
```
