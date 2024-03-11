from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import sentry_sdk
from flask import Flask, render_template, request, redirect, url_for
import json
import os

load_dotenv()

from utils.constants import APP_URL
from utils.content import get_clean_content, get_source
from utils.frames import article_to_frame, generate_error_frame
from utils.get_casts import get_top_casts_by_username
from utils.generate_article import generate_article
from utils.lookups import normalize_channel, truncate_content

sentry_key = os.environ.get("SENTRY_DSN")
if sentry_key:
    sentry_sdk.init(
        dsn=sentry_key,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = Flask(__name__)

def create_app():
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 8080))

@app.get("/_ah/health")
def gcp_health():
    return "ok"

@app.route(
    "/",
    methods=["GET", "POST"],
)
def home():
    channel = request.args.get("channel")
    selected_date = request.args.get("selected_date")

    try:
        channel_or_username = request.json["untrustedData"]["inputText"]
        if channel_or_username:
            return redirect(
                url_for(
                    "article_by_month",
                    channel_or_username=channel_or_username,
                    year=2024,
                    month=3,  # TODO: make these fields dynamic
                ),
                code=302,
            )
    except:
        pass

    if not selected_date:
        today = datetime.today()
        selected_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    today = datetime.today()
    start_date = today - timedelta(days=1)
    end_date = start_date + timedelta(days=1)

    top_usernames = get_top_casts_by_username(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )
    articles = []
    for username in top_usernames:
        article = generate_article(
            channel_or_username=username,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            type="username",
        )
        truncated_content = truncate_content(
            (
                get_clean_content(article)
                if article.get("content")
                else "No article found for this date range."
            ),
            50,
            0,
        )
        article_data = {
            "headline": article.get("headline", "No article found"),
            "subheading": article.get("subheading", ""),
            "summary": article.get("summary", ""),
            "content": truncated_content,
            "channel_or_username": username,
            "source": get_source(
                username,
                start_date.year,
                start_date.month,
                start_date.day,
                "username",
            ),
            "url": f"/articles/@{username}/{start_date.year}/{start_date.month}/{start_date.day}",
        }
        articles.append(article_data)

    if not channel:
        return render_template(
            "home.html",
            app_url=APP_URL,
            channel="/farcaster",
            selected_date=selected_date,
            articles=articles,
        )

    normalized_identifier, _, __ = normalize_channel(channel=channel)
    year, month, day = selected_date.split("-")

    return redirect(
        url_for(
            "article_by_day",
            channel_or_username=normalized_identifier,
            year=year,
            month=month,
            day=day,
        )
    )

@app.route(
    "/articles/<string:channel_or_username>/<int:year>/<int:month>/<int:day>",
    methods=["GET", "POST"],
)
def article_by_day(channel_or_username, year, month, day):
    return render_article_template(channel_or_username, year, month, day)

@app.route(
    "/articles/<string:channel_or_username>/<int:year>/<int:month>",
    methods=["GET", "POST"],
)
def article_by_month(channel_or_username, year, month):
    return render_article_template(channel_or_username, year, month, None)

def render_article_template(channel_or_username, year, month, day):
    channel, _, type = normalize_channel(channel=channel_or_username)
    article_url = f"{APP_URL}/articles/{channel_or_username}/{year}/{month}"
    if day:
        article_url += f"/{day}"

    try:
        if not day:
            start_date = datetime(year, month, 1)
            end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        else:
            start_date = datetime(year, month, day)
            end_date = start_date + timedelta(days=1)

        article = generate_article(
            channel_or_username=channel,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            type=type,
        )

        source = get_source(channel, year, month, day if day else 0, type)
        frame = article_to_frame(article, source, request.args.get("page", 0))

        return render_template(
            "article.html",
            app_url=APP_URL,
            article_url=article_url,
            headline=article.get("headline", "No article found"),
            subheading=article.get("subheading", ""),
            summary=article.get("summary", ""),
            content=(
                get_clean_content(article)
                if article.get("content")
                else "No article found for this date range."
            ),
            image_url=article.get("image_url", ""),
            channel_or_username=channel,
            source=source,
            frame=frame,
            error=False,  # Indicates successful article retrieval
        )

    except Exception as e:
        print(f"Error generating article: {e}")
        return render_error_template(article_url, channel)

def render_error_template(article_url, channel):
    return render_template(
        "article.html",
        app_url=APP_URL,
        article_url=article_url,
        headline="No article found",
        subheading="",
        summary="",
        content="An error occurred while trying to generate the article. Please try again later.",
        image_url=None,
        channel_or_username=channel,
        frame=generate_error_frame(),
        source=["", "#", ""],  # Adjust as needed for month-based source
        error=True,  # Indicates an error occurred
    )
