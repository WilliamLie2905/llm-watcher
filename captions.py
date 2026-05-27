import yt_dlp
import os
import re

def get_captions(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "vtt",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": f"captions/{video_id}",
    }

    os.makedirs("captions", exist_ok=True)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"  yt-dlp error: {e}")
        return None

    # look for the downloaded .vtt file
    for fname in os.listdir("captions"):
        if video_id in fname and fname.endswith(".vtt"):
            path = os.path.join("captions", fname)
            text = parse_vtt(path)
            os.remove(path)  # clean up after reading
            return text

    return None

def parse_vtt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # strip the WEBVTT header and timestamp lines
    lines = content.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if re.match(r"^\d{2}:\d{2}.*-->", line):
            continue
        if re.match(r"^\d+$", line):
            continue
        # strip inline tags like <00:00:01.000><c>
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_lines.append(line)

    # deduplicate consecutive repeated lines (common in auto-captions)
    deduped = []
    for line in text_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return " ".join(deduped)