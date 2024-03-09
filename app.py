from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import markdown

load_dotenv()

from utils.get_casts import get_casts
from utils.generate_article import generate_article
from utils.lookups import normalize_channel

app = Flask(__name__)


@app.route("/")
def home():
    channel = request.args.get("channel")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        today = datetime.today()
        start_date = ((today - timedelta(days=1)).strftime("%Y-%m-%d"),)
        end_date = (today.strftime("%Y-%m-%d"),)

    if not channel:
        return render_template(
            "home.html", channel="/farcaster", start_date=start_date, end_date=end_date
        )

    channel, parent_url = normalize_channel(channel=channel)

    return redirect(
        url_for("article", channel=channel, start_date=start_date, end_date=end_date)
    )


@app.route("/article/<string:channel>/<string:start_date>/<string:end_date>")
def article(channel, start_date, end_date):
    article = generate_article(
        channel=channel, start_date=start_date, end_date=end_date
    )

    return render_template(
        "article.html",
        headline=article["headline"],
        subheading=article["subheading"],
        summary=article["summary"],
        content=markdown.markdown(article["content"]),
    )
