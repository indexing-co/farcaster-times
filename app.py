from dotenv import load_dotenv

load_dotenv()

from utils.get_casts import get_casts

if __name__ == "__main__":
    for cast in get_casts(
        channel="chain://eip155:7777777/erc721:0x4f86113fc3e9783cf3ec9a552cbb566716a57628"
    ):
        print(cast.text)
