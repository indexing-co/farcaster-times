from datetime import datetime
import markdown


def get_clean_content(article):
    content = article["content"]

    # the start of trying to clean up GPT nonsense
    if article["headline"] in content:
        content = content.split(article["headline"])[1]

    content = markdown.markdown(content)

    return content


def get_source(channel_or_username, year, month, day):
    date = datetime(year, month, day or 1)
    time_frame = date.strftime("%B %Y") if not day else date.strftime("%B %d, %Y")

    if channel_or_username[0] == "@":
        return (
            channel_or_username,
            f"https://warpcast.com/{channel_or_username[1:]}",
            time_frame,
        )

    return (
        f"/{channel_or_username}",
        f"https://warpcast.com/~/channel/{channel_or_username}",
        time_frame,
    )
