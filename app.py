from dotenv import load_dotenv

load_dotenv()

from utils.get_casts import get_casts
from utils.generate_article import generate_article
from utils.lookups import normalize_channel

if __name__ == "__main__":
    channel, parent_url = normalize_channel("/music")

    casts = get_casts(
        parent_url=parent_url,
        # start_date="2024-02-26",
        # end_date="2024-03-03"
    )

    article = generate_article(casts=casts, channel=channel)

    print(article)
