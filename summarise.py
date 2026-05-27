import json
import re
import ollama

MODEL = "llama3.2:1b"

SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "claims": {"type": "array", "items": {"type": "string"}},
        "mentions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["topics", "summary", "claims", "mentions"],
}

def _to_str_list(items):
    """Flatten whatever the model returns into a list of strings."""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(next(iter(item.values()), ""))
    return result

def summarise(transcript, channel_name, title):
    prompt = f"""Analyse this YouTube transcript and return ONLY a raw JSON object.

Channel: {channel_name}
Title: {title}
Transcript: {transcript[:3000]}

JSON keys (KEEP EACH LIST SHORT — max 3 items, max 15 words per item):
- topics: 2-3 main topics
- summary: ONE short sentence
- claims: up to 3 key claims
- mentions: up to 3 names/papers/tools

Be concise. Output the JSON now:"""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            format=SCHEMA,
            options={"num_predict": 800, "temperature": 0},
        )
        raw = response.message.content.strip()
        # find the opening brace
        start = raw.find("{")
        if start == -1:
            print(f"  No JSON found in response")
            return ("", "", "", "")
        # try matching to the last closing brace; if that fails, attempt to
        # repair a truncated tail by appending closing brackets
        candidate = raw[start:]
        end = candidate.rfind("}")
        if end != -1:
            candidate = candidate[: end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            # llama sometimes emits multiple objects glued with `},{` — merge them
            merged = re.sub(r"\}\s*,\s*\{", ",", candidate)
            try:
                data = json.loads(merged)
            except json.JSONDecodeError:
                # last resort: close any unclosed string, drop trailing junk,
                # then close any unbalanced brackets
                repaired = merged
                # if there's an odd number of unescaped quotes, the tail is an
                # unclosed string — trim it back to the last clean point
                unescaped_quotes = len(re.findall(r'(?<!\\)"', repaired))
                if unescaped_quotes % 2 == 1:
                    last_quote = repaired.rfind('"')
                    repaired = repaired[:last_quote]
                repaired = repaired.rstrip(",: \n\t")
                opens_obj = repaired.count("{") - repaired.count("}")
                opens_arr = repaired.count("[") - repaired.count("]")
                repaired += "]" * max(opens_arr, 0) + "}" * max(opens_obj, 0)
                data = json.loads(repaired)

        return (
            ", ".join(_to_str_list(data.get("topics", []))),
            data.get("summary", "") if isinstance(data.get("summary"), str) else "",
            ", ".join(_to_str_list(data.get("claims", []))),
            ", ".join(_to_str_list(data.get("mentions", []))),
        )

    except json.JSONDecodeError:
        print(f"  Could not parse response as JSON")
        return ("", "", "", "")
    except Exception as e:
        print(f"  Ollama error: {e}")
        return ("", "", "", "")
