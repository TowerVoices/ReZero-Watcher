import requests
import re


def extract_season_id(url):
    match = re.search(r"/play/(\d+)", url)

    if not match:
        raise ValueError("Invalid Bilibili URL")

    return match.group(1)


def get_episodes(season_id):

    url = (
        "https://api.bilibili.tv/intl/gateway/web/v2/ogv/play/episodes"
        f"?season_id={season_id}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def create_episode_link(season_id, episode_id):

    if not episode_id:
        return "NOT AVAILABLE"

    return (
        f"https://www.bilibili.tv/en/play/"
        f"{season_id}/{episode_id}"
    )


def parse_episodes(data):

    episodes = []

    sections = data.get("data", {}).get("sections", [])

    for section in sections:

        # تجاهل PV
        if section.get("ep_list_title") == "PV&More":
            continue

        for ep in section.get("episodes", []):

            episodes.append({
                "number": ep.get("short_title_display"),
                "title": ep.get("long_title_display"),
                "episode_id": ep.get("episode_id"),
                "publish_time": ep.get("publish_time"),
                "cover": ep.get("cover")
            })

    return episodes


def main():

    print("=" * 50)
    print("Bilibili Anime Tracker")
    print("=" * 50)

    url = input(
        "\nEnter Bilibili anime URL:\n> "
    )

    try:
        season_id = extract_season_id(url)

    except Exception as e:
        print("Error:", e)
        return


    print("\nSeason ID:", season_id)
    print("Fetching data...\n")


    try:
        data = get_episodes(season_id)

    except Exception as e:
        print("API Error:", e)
        return


    episodes = parse_episodes(data)


    print(
        f"Found {len(episodes)} episodes\n"
    )


    for ep in episodes:

        print("=" * 60)

        print("Episode:", ep["number"])
        print("Title:", ep["title"])
        print("Publish:", ep["publish_time"])

        if ep["episode_id"]:
            print(
                "Episode ID:",
                ep["episode_id"]
            )

            print(
                "Link:",
                create_episode_link(
                    season_id,
                    ep["episode_id"]
                )
            )

        else:
            print(
                "Episode ID: NOT AVAILABLE"
            )

            print(
                "Link: WAITING"
            )


if __name__ == "__main__":
    main()