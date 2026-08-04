import requests
from bs4 import BeautifulSoup

STORY_URL = "https://re-zero-anime.jp/tv/story/"
BASE_URL = "https://re-zero-anime.jp/tv/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


def get_story_page():

    response = requests.get(
        STORY_URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.content,
        "html.parser"
    )


def get_latest_episode(soup):

    return soup.select_one(
        "article.content-entry"
    )


def get_episode_number(article):

    if article is None:
        return None

    node = article.select_one(
        "p.ep-label span"
    )

    if node is None:
        return None

    text = node.get_text(strip=True)

    return int(text.replace("#", ""))


def get_episode_title(article):

    if article is None:
        return ""

    node = article.select_one(
        "p.ep-subtitle"
    )

    if node is None:
        return ""

    return node.get_text(
        " ",
        strip=True
    )


def get_episode_images(article):

    if article is None:
        return []

    images = []

    for img in article.select(
        ".ep-slider-sceneImage img"
    ):

        src = (
            img.get("data-src")
            or img.get("src")
        )

        if not src:
            continue

        # رابط كامل
        if src.startswith("http"):

            full_url = src

        # ../assets/episode/77/1.webp
        elif src.startswith("../"):

            full_url = (
                BASE_URL +
                src.replace("../", "")
            )

        # /tv/assets/episode/77/1.webp
        elif src.startswith("/tv/"):

            full_url = (
                "https://re-zero-anime.jp" +
                src
            )

        # /assets/episode/77/1.webp
        elif src.startswith("/assets/"):

            full_url = (
                "https://re-zero-anime.jp/tv" +
                src
            )

        # assets/episode/77/1.webp
        else:

            full_url = (
                BASE_URL +
                src.lstrip("/")
            )

        if full_url not in images:
            images.append(full_url)

    return images
def get_hero_image(article):

    images = get_episode_images(article)

    if images:
        return images[0]

    return None


def get_gallery_images(article):

    images = get_episode_images(article)

    if len(images) <= 1:
        return []

    return images[1:]


def get_episode_list(soup):

    episodes = []

    for item in soup.select(
        "#BlockNavi li.bn a .label"
    ):

        text = item.get_text(strip=True)

        if text.isdigit():
            episodes.append(int(text))

    return episodes

def parse_story():

    soup = get_story_page()

    article = get_latest_episode(soup)

    images = get_episode_images(article)

    return {

        "episode": get_episode_number(article),

        "title": get_episode_title(article),

        "hero_image": images[0] if images else None,

        "gallery": images[1:] if len(images) > 1 else [],

        "images": images,

        "episodes": get_episode_list(soup)

    }