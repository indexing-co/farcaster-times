from dotenv import load_dotenv

load_dotenv()

from utils.get_casts import get_casts
from utils.generate_article import generate_article

if __name__ == "__main__":
    casts = get_casts(
        channel="chain://eip155:7777777/erc721:0x4f86113fc3e9783cf3ec9a552cbb566716a57628",
        date="2024-03-01",
    )

    article = generate_article(casts=casts, channel_name="farcaster")

    print(article)
