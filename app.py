from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import os

load_dotenv()

from utils.constants import APP_URL
from utils.content import get_clean_content, get_source
from utils.generate_article import generate_article
from utils.lookups import normalize_channel

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

    if not channel:
        return render_template(
            "home.html",
            app_url=APP_URL,
            channel="/farcaster",
            selected_date=selected_date,
        )

    channel, parent_url = normalize_channel(channel=channel)
    year, month, day = selected_date.split("-")

    return redirect(
        url_for(
            "article_by_day",
            channel_or_username=channel,
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

        article = generate_article(
            channel_or_username=channel_or_username,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        
        return render_template(
            "article.html",
            app_url=APP_URL,
            headline=article.get("headline", "No article found"),
            subheading=article.get("subheading", ""),
            summary=article.get("summary", ""),
            content=get_clean_content(article) if article.get("content") else "No article found for this date range.",
            channel_or_username=channel_or_username,
            source=get_source(channel_or_username, year, month, day),
            error=False  # Indicates successful article retrieval
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
            channel_or_username=channel_or_username,
            source=["", "#", ""],
            error=True  # Indicates an error occurred
        )

@app.route("/articles/<string:channel_or_username>/<int:year>/<int:month>")
def article_by_month(channel_or_username, year, month):
    try:
        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)

        article = generate_article(
            channel_or_username=channel_or_username,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        return render_template(
            "article.html",
            app_url=APP_URL,
            headline=article.get("headline", "No article found"),
            subheading=article.get("subheading", ""),
            summary=article.get("summary", ""),
            content=get_clean_content(article) if article.get("content") else "No article found for this month.",
            channel_or_username=channel_or_username,
            source=get_source(channel_or_username, year, month, 0),
            error=False  # Indicates successful article retrieval
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
            channel_or_username=channel_or_username,
            source=["", "#", ""],  # Adjust as needed for month-based source
            error=True  # Indicates an error occurred
        )
