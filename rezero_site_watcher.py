import json
import os
import requests
from dotenv import load_dotenv

from extractors.story import parse_story
from extractors.news import parse_news_with_details
# ==========================================
# 1. Load Environment
# ==========================================

load_dotenv()

DATABASE = "database"

# ==========================================
# 2. Console Colors
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
# 3. General Functions
# ==========================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# ==========================================
# 4. Discord
# ==========================================
def send_discord(message, image_url=None):

    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        return

    try:

        response = requests.post(
            webhook,
            json={
                "content": message
            },
            timeout=15
        )

        response.raise_for_status()

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Discord Error: {e}"
            f"{Color.RESET}"
        )

# ==========================================
# 5. Database
# ==========================================

def load_database(name):

    os.makedirs(DATABASE, exist_ok=True)

    path = os.path.join(
        DATABASE,
        f"{name}.json"
    )

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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

# ==========================================
# Download Manager
# ==========================================
def download_image(url, folder):

    if not url:
        return None

    os.makedirs(folder, exist_ok=True)

    filename = os.path.basename(
        url.split("?")[0]
    )

    path = os.path.join(
        folder,
        filename
    )

    if os.path.exists(path):
        return path

    try:

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        with open(path, "wb") as f:
            f.write(response.content)

        return path

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Download Error: {e}"
            f"{Color.RESET}"
        )

        return None

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Download Error: {e}"
            f"{Color.RESET}"
        )

        return None

def upload_images_to_discord(image_paths):

    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        return

    if not image_paths:
        return

    files = {}

    opened_files = []

    try:

        for index, path in enumerate(image_paths):

            if not os.path.exists(path):
                continue

            f = open(path, "rb")

            opened_files.append(f)

            files[f"file{index}"] = (
                os.path.basename(path),
                f,
                "image/webp"
            )

        if not files:
            return

        response = requests.post(

            webhook,

            files=files,

            timeout=60

        )

        response.raise_for_status()

        print(
            f"{Color.GREEN}"
            f"Uploaded {len(files)} images to Discord."
            f"{Color.RESET}"
        )

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Discord Upload Error: {e}"
            f"{Color.RESET}"
        )

    finally:

        for f in opened_files:
            f.close()
# ==========================================
# 6. STORY
# ==========================================

def first_story_scan():

    data = parse_story()

    save_database(
        "story",
        [data]
    )

    print(
        f"{Color.GREEN}"
        "✔ Story database created."
        f"{Color.RESET}"
    )


def compare_story(old_data, new_data):

    old = old_data[0]

    folder = os.path.join(
        "downloads",
        "story",
        f"episode_{new_data['episode']}"
    )

    # -------------------------
    # Episode
    # -------------------------

    if old["episode"] != new_data["episode"]:

        print(
            f"{Color.GREEN}"
            f"[NEW EPISODE] #{new_data['episode']}"
            f"{Color.RESET}"
        )

        send_discord(
            f"""@everyone 🎬 New Story Episode

Episode: {new_data["episode"]}

Title: {new_data["title"]}

https://re-zero-anime.jp/tv/story/
"""
        )

        print(
            f"{Color.CYAN}"
            "Downloading Story Images..."
            f"{Color.RESET}"
        )

        downloaded = []

        for image in new_data.get("images", []):

            path = download_image(
                image,
                folder
            )

            if path:
                downloaded.append(path)

        print(
            f"{Color.GREEN}"
            f"Downloaded {len(downloaded)} images."
            f"{Color.RESET}"
        )

        if downloaded:

            print(
                f"{Color.CYAN}"
                f"Uploading {len(downloaded)} images to Discord..."
                f"{Color.RESET}"
            )

            upload_images_to_discord(
                downloaded
            )

            print(
                f"{Color.GREEN}"
                "Upload Complete."
                f"{Color.RESET}"
            )

    # -------------------------
    # Title
    # -------------------------

    elif old["title"] != new_data["title"]:

        print(
            f"{Color.YELLOW}"
            "Story title updated."
            f"{Color.RESET}"
        )

    # -------------------------
    # Hero Image
    # -------------------------

    if old.get("hero_image") != new_data.get("hero_image"):

        print(
            f"{Color.YELLOW}"
            "Hero image updated."
            f"{Color.RESET}"
        )

    # -------------------------
    # Gallery Images
    # -------------------------

    old_gallery = set(
        old.get("gallery", [])
    )

    new_gallery = set(
        new_data.get("gallery", [])
    )

    added = list(
        new_gallery - old_gallery
    )

    removed = list(
        old_gallery - new_gallery
    )

    if added:

        print(
            f"{Color.GREEN}"
            f"+{len(added)} New Gallery Images"
            f"{Color.RESET}"
        )

    if removed:

        print(
            f"{Color.RED}"
            f"-{len(removed)} Images Removed"
            f"{Color.RESET}"
        )
def check_story():

    print(
        f"{Color.CYAN}"
        "Scanning Story..."
        f"{Color.RESET}"
    )

    database = load_database(
        "story"
    )

    if not database:

        first_story_scan()

        return

    current = parse_story()

    compare_story(
        database,
        current
    )

    save_database(
        "story",
        [current]
    )

    print(
        f"{Color.GREEN}"
        "Story Scan Finished."
        f"{Color.RESET}"
    )
# ==========================================
# 7. NEWS
# ==========================================

def first_news_scan():

    print(f"{Color.YELLOW}First News Scan...{Color.RESET}")

    news = parse_news_with_details()

    save_database("news", news)

    print(
        f"{Color.GREEN}"
        f"✔ Saved {len(news)} news."
        f"{Color.RESET}"
    )

def compare_news(old_news, new_news):

    old_ids = {
        item["id"]
        for item in old_news
    }

    changes = 0

    for news in new_news:

        if news["id"] in old_ids:
            continue

        changes += 1

        print(
            f"{Color.GREEN}"
            f"[NEW NEWS] {news['title']}"
            f"{Color.RESET}"
        )

        send_discord(
            f"""@everyone 📰 New Official News

Title: {news["title"]}

Date: {news["date"]}

Link: {news["url"]}
""",
            news.get("image")
        )

        # -------------------------
        # Download Image
        # -------------------------

        image = news.get("image")

        if image:

            folder = os.path.join(
                "downloads",
                "news",
                news["date"].replace(".", "-")
            )

            print(
                f"{Color.CYAN}"
                "Downloading News Image..."
                f"{Color.RESET}"
            )

            path = download_image(
                image,
                folder
            )

            if path:

                print(
                    f"{Color.GREEN}"
                    "Image downloaded."
                    f"{Color.RESET}"
                )

                print(
                    f"{Color.CYAN}"
                    "Uploading Image..."
                    f"{Color.RESET}"
                )

                upload_images_to_discord(
                    [path]
                )

                print(
                    f"{Color.GREEN}"
                    "Upload Complete."
                    f"{Color.RESET}"
                )

    if changes == 0:

        print(
            f"{Color.BLUE}"
            "✓ No new news."
            f"{Color.RESET}"
        )


def check_news():

    print(
        f"{Color.CYAN}"
        "Scanning News..."
        f"{Color.RESET}"
    )

    database = load_database("news")

    if not database:

        first_news_scan()

        return

    current = parse_news_with_details()

    compare_news(
        database,
        current
    )

    save_database(
        "news",
        current
    )

    print(
        f"{Color.GREEN}"
        "News Scan Finished."
        f"{Color.RESET}"
    )

# ==========================================
# 8. Scan Everything
# ==========================================

def run():

    print(
        f"\n{Color.BOLD}"
        "Starting Re:Zero Site Inspection..."
        f"{Color.RESET}\n"
    )

    print("-" * 45)

    try:
        check_story()
    except Exception as e:
        print(f"{Color.RED}Story Error:{Color.RESET} {e}")

    print("-" * 45)

    try:
        check_news()
    except Exception as e:
        print(f"{Color.RED}News Error:{Color.RESET} {e}")

    print("-" * 45)

    print(
        f"{Color.GREEN}"
        "✔ Scan Complete."
        f"{Color.RESET}"
    )

# ==========================================
# 9. Main Menu
# ==========================================

if __name__ == "__main__":

    clear_screen()

    while True:

        print(f"{Color.CYAN}{Color.BOLD}")
        print("=" * 45)
        print("        RE:ZERO SITE WATCHER")
        print("=" * 45)
        print(Color.RESET)

        print(f"{Color.GREEN}1.{Color.RESET} Scan Story")
        print(f"{Color.YELLOW}2.{Color.RESET} Scan News")
        print(f"{Color.BLUE}3.{Color.RESET} Scan Everything")
        print(f"{Color.RED}4.{Color.RESET} Exit")

        print()

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":
            check_story()

        elif choice == "2":
            check_news()

        elif choice == "3":
            run()

        elif choice == "4":
            break

        else:
            print(
                f"{Color.RED}"
                "Invalid choice."
                f"{Color.RESET}"
            )

        input("\nPress Enter...")
        clear_screen()