import os
import json
import re
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def summarise(transcript, channel_name, title):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
You are analyzing a YouTube video transcript about AI and large language models.

Channel: {channel_name}
Title: {title}

Transcript (may be truncated):
{transcript[:8000]}

Return ONLY a JSON object with exactly these fields, no extra text, no markdown:
{{
  "topics": ["topic1", "topic2", "topic3"],
  "summary": "3 sentence plain english summary of what was actually discussed",
  "claims": ["key claim or position 1", "key claim or position 2"],
  "mentions": ["any other YouTubers, researchers, or papers mentioned"]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)

        time.sleep(1)

        return (
            ", ".join(data.get("topics", [])),
            data.get("summary", ""),
            ", ".join(data.get("claims", [])),
            ", ".join(data.get("mentions", [])),
        )

    except json.JSONDecodeError:
        print(f"  Could not parse response as JSON")
        return ("", "", "", "")
    except Exception as e:
        print(f"  OpenAI error: {e}")
        return ("", "", "", "")