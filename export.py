import sqlite3
import json
import os

def export():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
        SELECT video_id, title, channel_name, published,
               topics, summary, claims, mentions
        FROM videos
        WHERE processed = 1
        ORDER BY published DESC
    """)
    rows = c.fetchall()
    conn.close()

    videos = []
    for row in rows:
        videos.append({
            "video_id": row[0],
            "title": row[1],
            "channel": row[2],
            "published": row[3],
            "topics": row[4],
            "summary": row[5],
            "claims": row[6],
            "mentions": row[7],
            "url": f"https://youtube.com/watch?v={row[0]}"
        })

    os.makedirs("docs", exist_ok=True)
    with open("docs/videos.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(videos)} videos to docs/videos.json")

if __name__ == "__main__":
    export()