import markdown


def get_clean_content(article):
    content = article["content"]

    # the start of trying to clean up GPT nonsense
    if article["headline"] in content:
        content = content.split(article["headline"])[1]

    content = markdown.markdown(content)

    return content


def get_source(channel_or_username):
    if channel_or_username[0] == "@":
        return channel_or_username, f"https://warpcast.com/{channel_or_username[1:]}"

    return (
        f"/{channel_or_username}",
        f"https://warpcast.com/~/channel/{channel_or_username}",
    )
