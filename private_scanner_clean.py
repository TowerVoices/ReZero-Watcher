import json
import os
import re
from datetime import datetime, timezone

import requests
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

DATABASE_DIR = "database"
COOKIES_FILE = "cookies.txt"
SENT_FILE = os.path.join(DATABASE_DIR, "_scheduled_sent.json")

WEBHOOKS = [
    os.getenv("DISCORD_WEBHOOK_URL"),
    os.getenv("DISCORD_WEBHOOK_URL_2"),
]
WEBHOOKS = [w.strip() for w in WEBHOOKS if w and w.strip()]

YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": False,
    "cookiefile": COOKIES_FILE,
}


def extract_video_id(value):
    """Extract a YouTube video ID from a URL or return an existing ID."""
    value = str(value).strip()

    # Normal watch URL
    m = re.search(r"(?:v=)([A-Za-z0-9_-]{11})", value)
    if m:
        return m.group(1)

    # youtu.be URL
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", value)
    if m:
        return m.group(1)

    # Shorts URL
    m = re.search(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})", value)
    if m:
        return m.group(1)

    # Already an ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    return None


def load_sent():
    os.makedirs(DATABASE_DIR, exist_ok=True)

    if not os.path.exists(SENT_FILE):
        return {}

    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_sent(data):
    os.makedirs(DATABASE_DIR, exist_ok=True)

    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_database_videos():
    """Read all videos from database/*.json, excluding the notification state file."""
    videos = []
    os.makedirs(DATABASE_DIR, exist_ok=True)

    for filename in os.listdir(DATABASE_DIR):
        if not filename.endswith(".json") or filename.startswith("_"):
            continue

        path = os.path.join(DATABASE_DIR, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        if not isinstance(data, list):
            continue

        playlist_name = os.path.splitext(filename)[0]

        for item in data:
            if not isinstance(item, dict):
                continue

            video_id = item.get("id")
            status = item.get("status")

            if video_id and status == "Private":
                videos.append({
                    "id": video_id,
                    "title": item.get("title") or "Unknown Title",
                    "playlist": playlist_name,
                })

    # Remove duplicate IDs while preserving the first occurrence.
    unique = {}
    for video in videos:
        unique.setdefault(video["id"], video)

    return list(unique.values())


def get_video_info(video_id):
    """Get metadata for a video using the same yt-dlp session/cookies."""
    opts = YTDLP_OPTS.copy()

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False,
            )
            return info, None
    except Exception as e:
        return None, str(e)


def get_scheduled_time(info):
    """
    Try the fields yt-dlp exposes for scheduled/release timing.
    Returns a UTC datetime or None.
    """
    if not info:
        return None

    # yt-dlp commonly exposes release_timestamp for scheduled content.
    timestamp = info.get("release_timestamp")

    if timestamp is None:
        # Some extractors may expose release_date instead.
        release_date = info.get("release_date")
        if release_date and re.fullmatch(r"\d{8}", str(release_date)):
            try:
                return datetime.strptime(
                    str(release_date), "%Y%m%d"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def classify_video(video_id):
    """
    Returns:
      SCHEDULED, PRIVATE, PUBLIC, or UNKNOWN
    """
    info, error = get_video_info(video_id)

    if info:
        scheduled_time = get_scheduled_time(info)

        # If yt-dlp exposes a future release time, treat it as scheduled.
        if scheduled_time is not None:
            return {
                "type": "SCHEDULED",
                "video_id": video_id,
                "title": info.get("title") or "Unknown Title",
                "scheduled_time": scheduled_time,
                "error": None,
                "verified": True,
            }

        # If we successfully extracted the video, it is accessible.
        availability = str(info.get("availability") or "").lower()
        is_private = availability == "private"

        if is_private:
            return {
                "type": "PRIVATE",
                "video_id": video_id,
                "title": info.get("title") or "Unknown Title",
                "scheduled_time": None,
                "error": None,
                "verified": True,
            }

        return {
            "type": "PUBLIC",
            "video_id": video_id,
            "title": info.get("title") or "Unknown Title",
            "scheduled_time": None,
            "error": None,
            "verified": True,
        }

    # We cannot safely call every inaccessible video "private".
    text = (error or "").lower()

    if "private" in text:
        return {
            "type": "PRIVATE",
            "video_id": video_id,
            "title": "Unknown Title",
            "scheduled_time": None,
            "error": error,
            "verified": False,
        }

    return {
        "type": "UNKNOWN",
        "video_id": video_id,
        "title": "Unknown Title",
        "scheduled_time": None,
        "error": error,
    }


def send_discord_scheduled(result, source="Database"):
    """Send Discord only for confirmed scheduled videos."""
    if result["type"] != "SCHEDULED":
        return False

    if not WEBHOOKS:
        print("⚠ No Discord webhook configured in .env")
        return False

    scheduled = result["scheduled_time"]
    scheduled_text = scheduled.strftime("%Y-%m-%d %H:%M:%S UTC")

    message = (
        "@everyone 📅 **Scheduled YouTube Video Detected**\n\n"
        f"**Source:** {source}\n"
        f"**Title:** {result['title']}\n"
        f"**ID:** `{result['video_id']}`\n"
        f"**Publish At:** `{scheduled_text}`\n\n"
        f"https://www.youtube.com/watch?v={result['video_id']}"
    )

    success = False

    for webhook in WEBHOOKS:
        try:
            response = requests.post(
                webhook,
                json={"content": message},
                timeout=15,
            )

            if response.status_code < 400:
                success = True
            else:
                print(
                    f"Discord Error ({response.status_code}): "
                    f"{response.text[:300]}"
                )
        except Exception as e:
            print(f"Discord Exception: {e}")

    return success


def scan_database():
    print("\n🔍 Scanning Private videos from watcher database...\n")

    videos = load_database_videos()

    if not videos:
        print("No Private videos found in database.")
        return

    sent = load_sent()
    checked = 0
    scheduled_count = 0

    for video in videos:
        checked += 1

        print(
            f"Checking: {video['id']} "
            f"({video['playlist']}) ... ",
            end="",
            flush=True,
        )

        result = classify_video(video["id"])

        if result["type"] == "SCHEDULED":
            scheduled_count += 1

            schedule_key = (
                f"{video['id']}|"
                f"{result['scheduled_time'].isoformat()}"
            )

            print(
                f"📅 SCHEDULED — "
                f"{result['scheduled_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            # Send only once for the same scheduled time.
            if not sent.get(schedule_key):
                if send_discord_scheduled(
                    result,
                    source=f"Database: {video['playlist']}",
                ):
                    sent[schedule_key] = True
                    save_sent(sent)
                    print("   ↳ Discord notification sent.")
            else:
                print("   ↳ Discord notification already sent.")

        elif result["type"] == "PRIVATE":
            print("🔒 PRIVATE - publishAt is not available; scheduling cannot be confirmed")

        elif result["type"] == "PUBLIC":
            print("🟢 PUBLIC")

        else:
            print("❓ UNKNOWN")

    print(
        f"\nDone. Checked: {checked} | "
        f"Scheduled: {scheduled_count}"
    )


def manual_check():
    print("\n🔗 Manual YouTube URL Check\n")

    url = input("Enter YouTube URL (or Video ID): ").strip()

    if not url:
        print("No URL entered.")
        return

    video_id = extract_video_id(url)

    if not video_id:
        print("❌ Could not extract a valid YouTube Video ID.")
        return

    print(f"\nVideo ID: {video_id}")
    print("Checking...\n")

    result = classify_video(video_id)

    if result["type"] == "SCHEDULED":
        scheduled = result["scheduled_time"]

        print("📅 SCHEDULED")
        print(f"Title: {result['title']}")
        print(
            "Publish At:",
            scheduled.strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        if send_discord_scheduled(result, source="Manual URL"):
            print("\n✅ Scheduled video sent to Discord.")
        else:
            print("\n⚠ Scheduled video detected, but Discord was not sent.")

    elif result["type"] == "PRIVATE":
        print("🔒 PRIVATE")
        print("YouTube confirmed that the video is private, but publishAt is not available.")
        print("Scheduling cannot be confirmed from the available data.")
        print("Nothing was sent to Discord.")

    elif result["type"] == "PUBLIC":
        print("🟢 PUBLIC")
        print("Nothing was sent to Discord.")

    else:
        print("❓ UNKNOWN")
        print("Could not safely determine whether it is scheduled.")
        if result["error"]:
            print(f"\nReason: {result['error']}")


def main():
    while True:
        print("\n" + "=" * 48)
        print("        YouTube Private Scanner")
        print("=" * 48)
        print("[1] Scan Database")
        print("[2] Check YouTube URL")
        print("[0] Exit")
        print("=" * 48)

        choice = input("Choose: ").strip()

        if choice == "1":
            scan_database()

        elif choice == "2":
            manual_check()

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("❌ Invalid choice.")


if __name__ == "__main__":
    main()