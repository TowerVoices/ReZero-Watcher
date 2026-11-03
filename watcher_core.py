import json
import os
import requests
import yt_dlp
import time
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv


# تحميل متغيرات البيئة
load_dotenv()

WATCHLIST = "watchlist.json"
DATABASE = "database"

# Only these values are treated as confirmed visibility states.
CONFIRMED_STATUSES = {"Public", "Private", "Members"}
STATUS_RECORD_VERSION = 3  # Baseline created by strict, single-pass status checks.

cookies_alert_sent = False

# ==========================================
# 1. إعدادات الألوان لتجميل الشاشة (Console)
# ==========================================
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==========================================
# 2. كتم تحذيرات وأخطاء yt_dlp المزعجة
# ==========================================
class SilentLogger(object):
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

# ==========================================
# إعدادات yt_dlp
# ==========================================
YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
    "logger": SilentLogger(), 
    "cookiefile": "cookies.txt",
    "sleep_interval_requests": 2, 
    "sleep_interval": 3,
    "max_sleep_interval": 7
}

# ==========================================
# الدوال الأساسية
# ==========================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def send_discord(message):
    # جلب روابط الويب هوك من ملف .env للسيرفرين
    webhooks = [
        os.getenv("DISCORD_WEBHOOK_URL"),
        os.getenv("DISCORD_WEBHOOK_URL_2")
    ]
    
    # فلترة القائمة للتأكد من وجود روابط صحيحة
    valid_webhooks = [w for w in webhooks if w and w.strip()]

    if not valid_webhooks:
        return
        
    # إرسال الرسالة إلى كل الروابط المتاحة
    for webhook in valid_webhooks:
        try:
            r = requests.post(webhook, json={"content": message}, timeout=15)
            if r.status_code >= 400:
                print(f"Discord Error ({webhook[:30]}...):", r.status_code)
                print(r.text)
        except Exception as e:
            print("Discord Exception:", e)
            
def load_watchlist():

    if not os.path.exists(WATCHLIST):

        print(
            f"{Color.RED}"
            f"✖ Error: {WATCHLIST} not found."
            f"{Color.RESET}"
        )

        return {}

    with open(WATCHLIST, "r", encoding="utf-8") as f:

        return json.load(f)


def load_database(name):

    os.makedirs(DATABASE, exist_ok=True)

    path = os.path.join(
        DATABASE,
        f"{name}.json"
    )

    if not os.path.exists(path):

        return []

    with open(path, "r", encoding="utf-8") as f:

        data = json.load(f)

        return [
            x for x in data
            if isinstance(x, dict)
            and "id" in x
        ]


def save_database(name, data):

    os.makedirs(DATABASE, exist_ok=True)

    path = os.path.join(
        DATABASE,
        f"{name}.json"
    )

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
        
def check_video_status(video_id):
    """Return a confirmed visibility status, or an uncertainty state."""
    global cookies_alert_sent

    single_opts = YTDLP_OPTS.copy()
    single_opts["extract_flat"] = False

    try:
        with yt_dlp.YoutubeDL(single_opts) as ydl:
            info = ydl.extract_info(
                f"https://youtu.be/{video_id}",
                download=False
            )

        # yt-dlp may expose an explicit availability value.
        availability = str((info or {}).get("availability") or "").lower()

        if availability == "private":
            return "Private"
        if availability in {"subscriber_only", "premium_only"}:
            return "Members"
        if availability in {"public", "unlisted"}:
            return "Public"
        if availability == "needs_auth":
            # Authentication/age restrictions are not proof of privacy.
            print(
                f"\n   {Color.YELLOW}yt-dlp availability=needs_auth; "
                f"visibility is not confirmed.{Color.RESET}"
            )
            return "Unknown Error"

        # A successful single-video extraction with no restrictive marker
        # is treated as Public, matching the original script's behavior.
        return "Public"

    except Exception as e:
        error = " ".join(str(e).lower().split())

        if (
            "sign in to confirm you're not a bot" in error
            or "sign in to confirm you’re not a bot" in error
            or "cookie file is not in netscape format" in error
            or "cookies are no longer valid" in error
        ):
            if not cookies_alert_sent:
                send_discord(
                    "@everyone 🚨 **YouTube Session Expired / Bot Detected**\n\n"
                    "The current session is blocked or expired.\n"
                    "Please update your YOUTUBE_COOKIES."
                )
                cookies_alert_sent = True

            return "Cookies Expired"

        # YouTube/yt-dlp's explicit private-video denial is a specific
        # message. Never infer privacy from a generic occurrence of
        # the word "private" (for example, in unrelated request/error text).
        # A successful metadata response with availability="private" is
        # handled above; here accept only the canonical denial phrase.
        if (
            "private video. sign in if you've been granted access to this video" in error
            or "private video. sign in if you have been granted access to this video" in error
        ):
            return "Private"

        if (
            "members-only" in error
            or "members only" in error
            or "available to this channel's members" in error
        ):
            return "Members"

        if "429" in error or "too many requests" in error:
            return "Rate Limited"

        if (
            "network" in error
            or "timeout" in error
            or "urlopen error" in error
            or "http error 403" in error
            or "http error 500" in error
            or "http error 502" in error
            or "http error 503" in error
        ):
            return "Network Error"

        # Geo-blocks, age gates, copyright blocks, and generic unavailable
        # errors do not establish Public/Private visibility. Print the cause
        # so an Unknown result can be diagnosed from the Actions log.
        print(
            f"\n   {Color.YELLOW}Unconfirmed yt-dlp response for "
            f"{video_id}: {error[:240]}{Color.RESET}"
        )
        return "Unknown Error"

def scan_playlist_fast(name, url):

    old = load_database(name)

    if not old:
        return True

    try:

        opts = YTDLP_OPTS.copy()
        opts["playlistend"] = 1

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get("entries", [])

        if not entries:
            return False

        latest_id = entries[0].get("id")

        if not latest_id:
            return False

        if latest_id == old[0]["id"]:

            print(
                f"{Color.BLUE}"
                f"✓ {name}: First video unchanged."
                f"{Color.RESET}"
            )

            return False

        print(
            f"{Color.YELLOW}"
            f"⚡ {name}: First video changed."
            f"{Color.RESET}"
        )

        return True

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Fast Scan Failed ({name}): {e}"
            f"{Color.RESET}"
        )

        return True



def scan_playlist(name, url):
    print(
        f"{Color.CYAN}➤ Scanning Playlist:{Color.RESET} "
        f"{Color.BOLD}{name}{Color.RESET} ...\n",
        end="",
        flush=True
    )

    old = load_database(name)
    old_by_id = {item["id"]: item for item in old}
    old_ids = set(old_by_id)
    current = []

    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" not in info:
            raise Exception("Playlist has no entries.")

        entries = info["entries"]
        total_videos = len(entries)

        for index, entry in enumerate(entries):
            video_id = entry.get("id")
            if not video_id:
                continue

            title = entry.get("title")
            if not title or str(title).strip() == "":
                title = "Unknown Title"

            print(
                f" ⏳ Checking ({index + 1}/{total_videos}): {video_id} ... ",
                end="",
                flush=True
            )

            old_video_data = old_by_id.get(video_id)
            old_status = (old_video_data or {}).get("status", "Unknown")
            has_trusted_baseline = (
                old_video_data is not None
                and old_video_data.get("status_version") == STATUS_RECORD_VERSION
                and old_status in CONFIRMED_STATUSES
            )

            # Check every video, including previously Public ones.
            detected_status = check_video_status(video_id)

            if detected_status == "Cookies Expired":
                print(f"{Color.RED}Bot Blocked! Scan aborted; database not updated.{Color.RESET}")
                return

            if detected_status not in CONFIRMED_STATUSES:
                # Preserve only a baseline created by this strict checker.
                # Legacy/unverified Private values are not evidence and are
                # cleared to Unknown until a fresh status can be established.
                if has_trusted_baseline:
                    status = old_status
                    status_version = STATUS_RECORD_VERSION
                    print(f"[{status}] (Unconfirmed check; trusted previous state preserved)")
                else:
                    status = "Unknown"
                    status_version = 1
                    print("[Unknown] (Unconfirmed check; discarded unverified legacy state)")

            elif not has_trusted_baseline:
                # One-time migration: old records did not record whether their
                # state came from a reliable check. Establish a fresh baseline
                # silently instead of reporting e.g. a false Private -> Public.
                status = detected_status
                status_version = STATUS_RECORD_VERSION
                if old_video_data:
                    print(
                        f"[{status}] (Baseline reset; ignored unverified old state: "
                        f"{old_status})"
                    )
                else:
                    print(f"[{status}] (Baseline established)")

            elif detected_status == old_status:
                status = detected_status
                status_version = STATUS_RECORD_VERSION
                print(f"[{status}]")

            else:
                # One successful, explicit result is enough. Do not issue a
                # second request: the root protection is strict classification
                # in check_video_status(), not repeated scanning.
                status = detected_status
                status_version = STATUS_RECORD_VERSION
                print(f"[{status}] (Confirmed status change)")

            # Retain the previous good title if the playlist response omits it.
            if (
                (not title or title == "Unknown Title")
                and old_video_data
                and old_video_data.get("title")
            ):
                title = old_video_data["title"]

            current.append({
                "id": video_id,
                "title": title,
                "status": status,
                "status_version": status_version,
            })

            if index < total_videos - 1:
                time.sleep(random.uniform(3, 6))

    except Exception as e:
        print(f"{Color.RED}Failed! Database not updated.{Color.RESET}")
        print(e)
        send_discord(
            f"❌ **Playlist Scan Failed**\n\n"
            f"**Playlist:** {name}\n\n"
            f"**Reason:**\n```{e}```"
        )
        return

    print(f"\n{Color.GREEN}Done! ({len(current)} videos){Color.RESET}\n")

    new_ids = {item["id"] for item in current}
    changes = 0

    # 1. New videos.
    for video in current:
        if video["id"] not in old_ids:
            changes += 1
            safe_title = str(video.get("title") or "Unknown Title")
            print(
                f"  {Color.GREEN}[+] NEW VIDEO:{Color.RESET} "
                f"{safe_title[:50]}... ({video['status']})"
            )
            send_discord(
                f"@everyone 🟢 **New Video**\n\n"
                f"**Playlist:** {name}\n"
                f"**Status:** {video['status']}\n\n"
                f"**Title:**\n{safe_title}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 2. Visibility changes are reported only when BOTH states are confirmed.
    for video in current:
        old_video = old_by_id.get(video["id"])
        if not old_video:
            continue

        old_status = old_video.get("status", "Unknown")
        new_status = video["status"]

        if (
            old_video.get("status_version") == STATUS_RECORD_VERSION
            and video.get("status_version") == STATUS_RECORD_VERSION
            and old_status in CONFIRMED_STATUSES
            and new_status in CONFIRMED_STATUSES
            and old_status != new_status
        ):
            changes += 1
            safe_title = str(video.get("title") or "Unknown Title")
            print(
                f"  {Color.YELLOW}[~] STATUS CHANGED:{Color.RESET} "
                f"{safe_title[:50]}... [{old_status} ➜ {new_status}]"
            )
            send_discord(
                f"@everyone 🟡 **Video Status Changed**\n\n"
                f"**Playlist:** {name}\n\n"
                f"**Title:**\n{safe_title}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"**Status:**\n{old_status} ➜ {new_status}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 3. Videos missing from a successfully retrieved playlist.
    for video in old:
        if video["id"] not in new_ids:
            changes += 1
            safe_title = str(video.get("title") or "Unknown Title")
            old_status = video.get("status", "Unknown")
            print(
                f"  {Color.RED}[-] REMOVED:{Color.RESET} "
                f"{safe_title[:50]}... (Was: {old_status})"
            )
            send_discord(
                f"@everyone 🔴 **Video Removed**\n\n"
                f"**Playlist:** {name}\n\n"
                f"**Last Status:** {old_status}\n\n"
                f"**Title:**\n{safe_title}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    if changes == 0:
        print(f"  {Color.BLUE}✓ No confirmed changes detected.{Color.RESET}")

    print("-" * 50)
    save_database(name, current)

def run():

    print(
        f"\n{Color.BOLD}{Color.CYAN}"
        "⚡ Starting Fast Playlist Inspection..."
        f"{Color.RESET}\n"
    )

    watchlist = load_watchlist()

    playlists = watchlist.get(
        "youtube_playlists",
        []
    )

    if not playlists:

        print(
            f"{Color.YELLOW}"
            "⚠ No playlists found in watchlist.json."
            f"{Color.RESET}"
        )

        return

    for playlist in playlists:

        playlist_id = playlist.get(
            "playlist_id"
        )

        if not playlist_id:
            continue

        url = (
            f"https://www.youtube.com/"
            f"playlist?list={playlist_id}"
        )

        # فحص سريع
        if scan_playlist_fast(
            playlist["name"],
            url
        ):

            print(
                f"{Color.YELLOW}"
                f"⚡ Change detected in {playlist['name']}."
                f"{Color.RESET}"
            )

            # إذا تغير أول فيديو نفذ الفحص الكامل
            scan_playlist(
                playlist["name"],
                url
            )

    print(
        f"\n{Color.GREEN}{Color.BOLD}"
        "✔ Fast scan completed!"
        f"{Color.RESET}\n"
    )

def run_full():

    print(
        f"\n{Color.BOLD}{Color.YELLOW}"
        "🔍 Starting Full Playlist Inspection..."
        f"{Color.RESET}\n"
    )

    watchlist = load_watchlist()

    playlists = watchlist.get(
        "youtube_playlists",
        []
    )

    if not playlists:

        print(
            f"{Color.YELLOW}"
            "⚠ No playlists found."
            f"{Color.RESET}"
        )

        return

    for playlist in playlists:

        playlist_id = playlist.get(
            "playlist_id"
        )

        if not playlist_id:
            continue

        url = (
            f"https://www.youtube.com/"
            f"playlist?list={playlist_id}"
        )

        scan_playlist(
            playlist["name"],
            url
        )

    print(
        f"\n{Color.GREEN}{Color.BOLD}"
        "✔ Full scan completed!"
        f"{Color.RESET}\n"
    )


def export_ids():
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    os.makedirs("output", exist_ok=True)
    filename = "output/all_ids.txt"

    print(f"\n{Color.CYAN}Exporting IDs to {filename} (Using Local Database)...{Color.RESET}\n")

    with open(filename, "w", encoding="utf-8") as out:
        for playlist in playlists:
            print(f"{Color.YELLOW}Exporting:{Color.RESET} {playlist['name']} ", end="", flush=True)
            
            out.write(f"{playlist['name']}\n")
            out.write("=" * 60 + "\n")

            local_data = load_database(playlist['name'])
            
            if local_data:
                for video in local_data:
                    status = video.get("status", "Unknown")
                    video_id = video.get("id")
                    
                    if status == "Public": icon = "🟢"
                    elif status == "Private": icon = "🔒"
                    elif status == "Unavailable": icon = "⚫"
                    elif status == "Members": icon = "👑"
                    else: icon = "❓"

                    line = f"{video_id:<15} {icon} {status}"
                    out.write(line + "\n")
            else:
                out.write("No videos scanned yet. Please run scanner first.\n")

            out.write("\n")
            print(f"{Color.GREEN}✔ Done!{Color.RESET}")

    print(f"\n{Color.GREEN}{Color.BOLD}✔ Export completed! File saved at: {filename}{Color.RESET}\n")

