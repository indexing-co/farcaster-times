from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import os

from utils.get_casts import get_top_casts_by_username

load_dotenv()

from utils.constants import APP_URL
from utils.content import get_clean_content, get_source
from utils.generate_article import generate_article
from utils.lookups import normalize_channel, truncate_content

app = Flask(__name__)


def create_app():
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 8080))


@app.get("/_ah/health")
def gcp_health():
    return "ok"


@app.route("/")
def home():
    channel = request.args.get("channel")
    selected_date = request.args.get("selected_date")

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

    normalized_channel, _, type = normalize_channel(channel=channel)
    year, month, day = selected_date.split("-")

    if type == "username":
        return redirect(
            url_for(
                "article_by_day",
                channel_or_username=channel,
                year=year,
                month=month,
                day=day,
            )
        )

    return redirect(
        url_for(
            "article_by_day",
            channel_or_username=normalized_channel,
            year=year,
            month=month,
            day=day,
        )
    )


@app.route("/articles/<string:channel_or_username>/<int:year>/<int:month>/<int:day>")
def article_by_day(channel_or_username, year, month, day):
    try:
        start_date = datetime(year, month, day)
        end_date = start_date + timedelta(days=1)
        channel, _, type = normalize_channel(channel=channel_or_username)

        article = generate_article(
            channel_or_username=channel,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            type=type,
        )

        return render_template(
            "article.html",
            app_url=APP_URL,
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
            source=get_source(channel, year, month, day, type),
            error=False,  # Indicates successful article retrieval
        )

    except Exception as e:
        print(f"Error generating article: {e}")
        return render_template(
            "article.html",
            app_url=APP_URL,
            headline="No article found",
            subheading="",
            summary="",
            content="An error occurred while trying to generate the article. Please try again later.",
            image_url="",
            channel_or_username=channel,
            source=["", "#", ""],
            error=True,  # Indicates an error occurred
        )


@app.route("/articles/<string:channel_or_username>/<int:year>/<int:month>")
def article_by_month(channel_or_username, year, month):
    try:
        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        channel, _, type = normalize_channel(channel=channel_or_username)

        article = generate_article(
            channel_or_username=channel,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            type=type,
        )

        return render_template(
            "article.html",
            app_url=APP_URL,
            headline=article.get("headline", "No article found"),
            subheading=article.get("subheading", ""),
            summary=article.get("summary", ""),
            content=(
                get_clean_content(article)
                if article.get("content")
                else "No article found for this month."
            ),
            image_url=article.get("image_url", ""),
            channel_or_username=channel,
            source=get_source(channel, year, month, 0, type),
            error=False,  # Indicates successful article retrieval
        )

    except Exception as e:
        print(f"Error generating article: {e}")
        return render_template(
            "article.html",
            app_url=APP_URL,
            headline="No article found",
            subheading="",
            summary="",
            content="An error occurred while trying to generate the article. Please try again later.",
            image_url="",
            channel_or_username=channel,
            source=["", "#", ""],  # Adjust as needed for month-based source
            error=True,  # Indicates an error occurred
        )
