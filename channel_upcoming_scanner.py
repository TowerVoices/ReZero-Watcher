import json
import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_channel_page(channel_url):
    try:
        response = requests.get(
            channel_url,
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def extract_initial_data(html):
    """
    Extract ytInitialData from the HTML.
    YouTube changes its surrounding page structure from time to time,
    so we try several known forms.
    """
    patterns = [
        r"var ytInitialData\s*=\s*({.*?});</script>",
        r"ytInitialData\s*=\s*({.*?});</script>",
        r'window\["ytInitialData"\]\s*=\s*({.*?});</script>',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            continue

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

    # Fallback: locate the first balanced JSON object after ytInitialData.
    marker = "ytInitialData"
    marker_pos = html.find(marker)

    if marker_pos != -1:
        start = html.find("{", marker_pos)

        if start != -1:
            depth = 0
            in_string = False
            escape = False

            for index in range(start, len(html)):
                char = html[index]

                if in_string:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == '"':
                        in_string = False
                    continue

                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1

                    if depth == 0:
                        try:
                            return json.loads(html[start:index + 1])
                        except json.JSONDecodeError:
                            break

    print("Could not find ytInitialData.")
    print("YouTube may have changed the page structure.")
    return None


def walk_objects(value):
    """
    Recursively walk every dict/list inside ytInitialData.
    This avoids relying on a single hard-coded YouTube JSON path.
    """
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from walk_objects(child)

    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def get_text(data):
    """
    Read text from YouTube's common simpleText/runs formats.
    """
    if not isinstance(data, dict):
        return ""

    simple_text = data.get("simpleText")
    if simple_text:
        return str(simple_text).strip()

    runs = data.get("runs")
    if isinstance(runs, list):
        return "".join(
            str(run.get("text", ""))
            for run in runs
            if isinstance(run, dict)
        ).strip()

    return ""


def extract_videos(data):
    """
    Find videoRenderer objects anywhere inside ytInitialData.
    This is more robust than depending on richGridRenderer being
    at one exact location.
    """
    videos = []
    seen = set()

    for obj in walk_objects(data):
        video = obj.get("videoRenderer")

        if not isinstance(video, dict):
            continue

        video_id = video.get("videoId")

        if not video_id or video_id in seen:
            continue

        seen.add(video_id)

        title = get_text(video.get("title")) or "Unknown Title"

        upcoming_data = video.get("upcomingEventData")
        scheduled_time = None

        if isinstance(upcoming_data, dict):
            scheduled_time = (
                upcoming_data.get("startTime")
                or upcoming_data.get("scheduledStartTime")
            )

        videos.append(
            {
                "id": video_id,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "upcoming": isinstance(upcoming_data, dict),
                "scheduled_time": scheduled_time,
            }
        )

    return videos


def print_results(videos):
    print("\n" + "=" * 70)
    print(f"Found {len(videos)} visible video entries")
    print("=" * 70)

    if not videos:
        print("No videoRenderer entries were found in the page data.")
        return

    for number, video in enumerate(videos, start=1):
        print(f"\n[{number}]")
        print(f"Title: {video['title']}")
        print(f"ID: {video['id']}")
        print(f"URL: {video['url']}")

        if video["upcoming"]:
            print("Upcoming/Premiere: YES")

            if video["scheduled_time"]:
                print(
                    f"Scheduled Time: {video['scheduled_time']}"
                )
        else:
            print("Upcoming/Premiere: NO")

    print("\n" + "=" * 70)


def scan_channel():
    print("\n" + "=" * 70)
    print("Manual YouTube Channel Scanner")
    print("=" * 70)

    channel_url = input("Enter Channel URL: ").strip()

    if not channel_url:
        print("No URL entered.")
        return

    if "youtube.com" not in channel_url:
        print("Invalid YouTube URL.")
        return

    print("\nFetching channel...")

    html = get_channel_page(channel_url)

    if not html:
        return

    data = extract_initial_data(html)

    if not data:
        return

    videos = extract_videos(data)
    print_results(videos)


def main():
    while True:
        print("\n" + "=" * 70)
        print("YouTube Channel Scanner")
        print("=" * 70)
        print("[1] Scan Channel")
        print("[0] Exit")
        print("=" * 70)

        choice = input("Choose: ").strip()

        if choice == "1":
            scan_channel()

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()