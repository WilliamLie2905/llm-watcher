import os
import time
import feedparser
from dotenv import load_dotenv
from db import init_db, is_seen, insert_video, update_video
from captions import get_captions
from summarise import summarise

load_dotenv()

CHANNELS = {
    "UC9-y-6csu5WGm29I7JiwpnA": "Andrej Karpathy",
    "UCZHmQk67mSJgfCCTn7xBfew": "Yannic Kilcher",
    "UCSHZKyawb77ixDdsGog4iWA": "Lex Fridman",
    "UCNJ1Ymd5yFuUPtn21xtRbbw": "AI Explained",
    "UCqudUAv40T3pQbafP3RrJnA": "Dwarkesh Patel",
}

def fetch_videos(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    videos = []
    for entry in feed.entries:
        video_id = entry.get("yt_videoid")
        title = entry.get("title", "")
        published = entry.get("published", "")
        if video_id:
            videos.append((video_id, title, published))
    return videos

def run():
    print("Initialising database...")
    init_db()

    for channel_id, channel_name in CHANNELS.items():
        print(f"\nChecking {channel_name}...")
        try:
            videos = fetch_videos(channel_id)
        except Exception as e:
            print(f"  Error fetching feed: {e}")
            continue

        for video_id, title, published in videos:
            if is_seen(video_id):
                print(f"  Already processed: {title[:50]}")
                continue

            print(f"  New video: {title[:50]}")
            insert_video(video_id, title, channel_name, published)

            print(f"  Getting captions...")
            transcript = get_captions(video_id)

            if not transcript:
                print(f"  No captions found, skipping summarisation")
                update_video(video_id, "", "", "", "", "")
                continue

            print(f"  Summarising with OpenAI...")
            topics, summary, claims, mentions = summarise(
                transcript, channel_name, title
            )

            update_video(video_id, transcript, topics, summary, claims, mentions)
            print(f"  Done: {title[:50]}")

            # be polite to the API
            time.sleep(2)

    print("\nAll done!")

if __name__ == "__main__":
    run()