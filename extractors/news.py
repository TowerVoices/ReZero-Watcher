import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

NEWS_URL = "https://re-zero-anime.jp/tv/news/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    )
}

NEWS_LIMIT = 1

def get_news_page():

    response = requests.get(
        NEWS_URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.content,
        "html.parser"
    )

def parse_news():

    soup = get_news_page()

    news = []

    articles = soup.select(
        "section.content-entry"
    )[:NEWS_LIMIT]

    for article in articles:

        title = ""
        date = ""
        link = ""
        image = None

        # -----------------------
        # Title
        # -----------------------

        h = article.select_one(
            ".entry-title"
        )

        if h:

            title = h.get_text(
                " ",
                strip=True
            )

        # -----------------------
        # Date
        # -----------------------

        d = article.select_one(
            ".entry-date"
        )

        if d:

            date = d.get_text(
                " ",
                strip=True
            )

        # -----------------------
        # Link
        # -----------------------

        section_id = article.get("id")

        if section_id:

            link = NEWS_URL + "#" + section_id

        # -----------------------
        # Image
        # -----------------------

        img = article.select_one(
            ".entry-body img"
        )

        if img:

            src = (
                img.get("data-src")
                or img.get("src")
            )

            if src:

                image = urljoin(
                    NEWS_URL,
                    src
                )

        # -----------------------

        news.append({

            "id": section_id,

            "title": title,

            "date": date,

            "url": link,

            "image": image

        })

    return news

def get_news_detail(url):

    response = requests.get(
        NEWS_URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    section = None

    if "#" in url:

        section = soup.select_one(
            url.split("#")[-1].join(["#", ""])
        )

    if section is None:

        return {

            "content": [],

            "image": None

        }

    content = []

    image = None

    # -----------------------
    # Paragraphs
    # -----------------------

    for p in section.select(
        ".entry-body p"
    ):

        text = p.get_text(
            " ",
            strip=True
        )

        if text:

            content.append(text)

    # -----------------------
    # Main Image
    # -----------------------

    img = section.select_one(
        ".entry-body img"
    )

    if img:

        src = (
            img.get("data-src")
            or img.get("src")
        )

        if src:

            image = urljoin(
                NEWS_URL,
                src
            )

    return {

        "content": content,

        "image": image

    }


def parse_news_with_details():

    news = parse_news()

    for item in news:

        try:

            detail = get_news_detail(
                item["url"]
            )

            item["content"] = detail["content"]

            if detail["image"]:

                item["image"] = detail["image"]

        except Exception:

            item["content"] = []

    return news


if __name__ == "__main__":

    news = parse_news_with_details()

    print("=" * 70)

    print(
        f"Latest News: {len(news)}"
    )

    print("=" * 70)

    for item in news:

        print(f"Date : {item['date']}")
        print(f"Title: {item['title']}")
        print(f"URL  : {item['url']}")
        print(f"Image: {item['image']}")
        print(f"Paragraphs: {len(item['content'])}")

        print("-" * 70)