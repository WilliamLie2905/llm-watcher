import sqlite3

def init_db():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_name TEXT,
            published TEXT,
            transcript TEXT,
            topics TEXT,
            summary TEXT,
            claims TEXT,
            mentions TEXT,
            processed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def is_seen(video_id):
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM videos WHERE video_id = ? AND processed = 1", (video_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def insert_video(video_id, title, channel_name, published):
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO videos (video_id, title, channel_name, published)
        VALUES (?, ?, ?, ?)
    """, (video_id, title, channel_name, published))
    conn.commit()
    conn.close()

def update_video(video_id, transcript, topics, summary, claims, mentions):
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
        UPDATE videos
        SET transcript = ?, topics = ?, summary = ?, claims = ?, mentions = ?, processed = 1
        WHERE video_id = ?
    """, (transcript, topics, summary, claims, mentions, video_id))
    conn.commit()
    conn.close()

def get_unprocessed_with_transcripts():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
        SELECT video_id, title, channel_name, transcript
        FROM videos
        WHERE processed = 0 AND transcript != ''
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_transcript(video_id):
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("SELECT transcript FROM videos WHERE video_id = ? AND transcript != ''", (video_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_videos():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("SELECT * FROM videos ORDER BY published DESC")
    rows = c.fetchall()
    conn.close()
    return rows