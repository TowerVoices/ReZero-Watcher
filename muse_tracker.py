import re
from googleapiclient.discovery import build


API_KEY = "AIzaSyDwg-REtlSXw01t3Wwaj1s_o-D7wg_1eWs"


def extract_playlist_id(url):
    match = re.search(r"list=([^&]+)", url)

    if match:
        return match.group(1)

    return None


def get_videos(playlist_id):

    youtube = build(
        "youtube",
        "v3",
        developerKey=API_KEY
    )

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )

    response = request.execute()

    for item in response["items"]:

        title = item["snippet"]["title"]

        video_id = item["contentDetails"]["videoId"]

        published = item["snippet"]["publishedAt"]

        print("=" * 50)
        print("Title:", title)
        print("Video ID:", video_id)
        print("Published:", published)
        print(
            "Link:",
            f"https://youtube.com/watch?v={video_id}"
        )


def main():

    print("=" * 50)
    print("Muse Asia YouTube Tracker")
    print("=" * 50)

    url = input(
        "\nضع رابط Playlist من YouTube:\n> "
    )

    playlist_id = extract_playlist_id(url)

    if not playlist_id:
        print("لم يتم العثور على Playlist ID")
        return

    print("\nPlaylist ID:", playlist_id)

    print("\nجاري جلب الحلقات...\n")

    get_videos(playlist_id)


if __name__ == "__main__":
    main()