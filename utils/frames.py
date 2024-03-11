from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageColor
from textwrap3 import wrap
import base64
import re

from .content import get_clean_content


# Frames have to be less than 256kb
DOWNSCALE_RATIO = 0.7
FONT_SIZE = 60 * DOWNSCALE_RATIO
CHARS_PER_LINE = 60
WORDS_PER_PAGE = 120
PURPLE = (138, 99, 210)
CANVAS_SIZE = tuple(int(v) for v in [1910 * DOWNSCALE_RATIO, 1000 * DOWNSCALE_RATIO])


def get_all_frame_pages(article, source):
    pages = [
        (
            "\n".join(wrap(article.get("headline"), CHARS_PER_LINE / 1.3)) + "\n",
            "\n".join(wrap(article.get("subheading"), CHARS_PER_LINE))
            + f"\n\n\nInsights from {source[0]} - {source[2]}",
        )
    ]

    content = get_clean_content(article)
    content = re.sub("<h[1-3]>", "<h2>!heading:", content)
    content = "\n".join([c for c in content.split("\n") if c])
    content = re.sub("<[^<]+?>", "", content)

    for section in content.split("!heading:"):
        lines = re.sub(".$", "", section).split("\n")
        heading = lines[0]
        sentences = " ".join([v for v in lines[1:] if v]).split(".")
        word_count = len(heading.split(" "))
        page_words = []
        for sentence in sentences:
            sentence_words = sentence.strip().split(" ")
            if word_count + len(sentence_words) >= WORDS_PER_PAGE:
                page_content = "\n".join(wrap(" ".join(page_words), CHARS_PER_LINE))
                pages.append((heading, page_content))
                heading = None
                break
            sentence_words[-1] = f"{sentence_words[-1]}."
            page_words += sentence_words
            word_count += len(sentence_words)

        if page_words:
            page_content = "\n".join(wrap(" ".join(page_words), CHARS_PER_LINE))
            pages.append((heading, page_content))

    return [p for p in pages if p[0] and [1] != "..."]


def article_to_frame(article, source, page=0):
    try:
        page = int(page) if page else 0
        pages = get_all_frame_pages(article, source)
        if page >= len(pages):
            raise ValueError("Invalid page for article")

        heading, content = pages[page]
        font = ImageFont.truetype("static/georgia.ttf", size=FONT_SIZE)
        img = Image.new("RGB", CANVAS_SIZE, color=PURPLE)

        draw = ImageDraw.Draw(img)
        draw_point = (50, 50)
        if heading:
            header_font = ImageFont.truetype("static/georgia.ttf", size=FONT_SIZE * 1.3)
            draw.multiline_text(
                draw_point, heading, font=header_font, fill=(255, 255, 255)
            )
            draw_point = (
                draw_point[0],
                draw_point[1] + FONT_SIZE * 1.3 * (len(heading.split("\n"))) + 20,
            )
        draw.multiline_text(draw_point, content, font=font, fill=(255, 255, 255))

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_buffer = buffer.getvalue()

        image = "data:image/png;base64," + base64.b64encode(img_buffer).decode()

        return (
            image,
            str(page - 1) if page > 0 else None,
            str(page + 1) if page + 1 < len(pages) else None,
        )

    except Exception as e:
        print(f"Error generating article frame: {e}")
        return generate_error_frame()


def generate_error_frame():
    msg = [
        "Doh! Looks like we failed to find this article",
        "Reach out to @runninyeti.eth if this persists",
    ]

    font = ImageFont.truetype("static/georgia.ttf", size=FONT_SIZE * 2)
    img = Image.new("RGB", CANVAS_SIZE, color=PURPLE)

    draw = ImageDraw.Draw(img)
    draw_point = (50, 50)
    draw.multiline_text(
        draw_point,
        "\n\n".join(["\n".join(wrap(m, CHARS_PER_LINE / 2)) for m in msg]),
        font=font,
        fill=(255, 255, 255),
    )

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_buffer = buffer.getvalue()

    image = "data:image/png;base64," + base64.b64encode(img_buffer).decode()

    return (image, None, None)
