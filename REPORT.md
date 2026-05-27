# LLM Channel Watcher — Report

A local, automated pipeline that follows five popular YouTube channels covering large language models, transcribes their videos via captions, summarises each one with a local LLM, and publishes a browsable table to GitHub Pages.

**Live site:** https://williamlie2905.github.io/llm-watcher/
**Repository:** https://github.com/WilliamLie2905/llm-watcher

---

## Problem Statement

Researchers, builders, and enthusiasts following the LLM space rely on a small set of YouTube creators (Andrej Karpathy, Yannic Kilcher, Lex Fridman, AI Explained, Dwarkesh Patel) for technical analysis, paper breakdowns, and interviews. Manually keeping up with every upload across these channels is impractical — titles and thumbnails don't reveal what was actually said.

The goal of this project is to build an **automated watcher** that:

1. Tracks new videos across multiple LLM-focused YouTube channels.
2. Pulls the actual spoken content of each video via captions.
3. Uses AI to distill each transcript into a structured row: topics, summary, key claims, and named entities mentioned.
4. Publishes the resulting table on a public web page that reviewers can open in a browser, with search and channel filtering.
5. Keeps the table current as new videos appear.

The deliverable is a single artefact a reader can consult to compare what these creators are *actually saying* about LLMs — not just what their titles advertise.

---

## Methodology

The system is a five-stage pipeline orchestrated by `run.bat`:

### 1. Channel feed polling (`watcher.py`)
Each channel is identified by its YouTube channel ID. The watcher pulls the public RSS feed at `https://www.youtube.com/feeds/videos.xml?channel_id=<ID>` using `feedparser`. This returns the 15 most recent videos per channel without requiring the YouTube Data API or any authentication.

Channels tracked:

| Channel | ID |
|---|---|
| Andrej Karpathy | `UC9-y-6csu5WGm29I7JiwpnA` |
| Yannic Kilcher | `UCZHmQk67mSJgfCCTn7xBfew` |
| Lex Fridman | `UCSHZKyawb77ixDdsGog4iWA` |
| AI Explained | `UCNJ1Ymd5yFuUPtn21xtRbbw` |
| Dwarkesh Patel | `UCXl4i9dYBrFOabk0xGmbkRA` |

### 2. Deduplication (`db.py`)
A local SQLite database (`videos.db`) stores every video the watcher has ever seen. Before processing a video, `is_seen()` checks whether the video already has `processed = 1`. This means:
- Brand new videos get processed.
- Videos that were inserted but failed to process get retried automatically.
- Successfully processed videos are skipped.

### 3. Caption extraction (`captions.py`)
For each unseen video, `yt-dlp` downloads YouTube's auto-generated English subtitles in WebVTT format. A small custom parser strips the WEBVTT headers, timestamps, cue identifiers, and inline tags, and deduplicates the rolling lines that auto-captions emit. The result is plain, readable transcript text.

Videos with no captions available (e.g. live streams) are flagged and skipped — they cannot be summarised without separately running speech-to-text on the audio.

### 4. AI summarisation (`summarise.py`)
Each transcript (truncated to the first 3 000 characters for speed) is passed to a local **Ollama** instance running **llama3.2:1b**. The choice of model balances:
- **Cost** — completely free, runs on CPU.
- **Speed** — ~10–30 s per video on a typical laptop.
- **Reliability** — the 1B model is dumb enough that we use Ollama's **JSON schema constrained decoding** (`format=SCHEMA`) to force valid, well-keyed output.

The schema required:

```python
{
  "topics":   ["string", ...],
  "summary":  "string",
  "claims":   ["string", ...],
  "mentions": ["string", ...]
}
```

A defensive parser handles edge cases that occurred during development (truncated JSON, multiple glued objects, unclosed strings, wrong key names), but with the schema-constrained format these are now rare.

### 5. Export and viewer (`export.py`, `docs/index.html`)
All processed rows are exported to `docs/videos.json`. A static HTML page in the same folder loads the JSON client-side and renders a sortable, searchable, filterable dark-themed table. Because `docs/` is the conventional GitHub Pages source folder, the entire site is hosted for free at `https://williamlie2905.github.io/llm-watcher/` simply by pushing the repo.

### Backlog handling
A small but important wrinkle: the YouTube RSS feed only exposes the *latest 15* videos per channel, so any video that fell off the feed before being processed would be permanently stuck. The watcher therefore runs a **backlog pass** at startup that picks up any DB row with `processed = 0` but an existing cached transcript, and finishes the summarisation step. This means transient errors (Ollama crash, JSON parse failure, etc.) are recoverable without re-downloading captions.

### Keeping the table current
Run `run.bat` on whatever schedule you want — manual, Windows Task Scheduler, or `cron`. Each run:
1. Resumes any unfinished work from the backlog.
2. Polls each channel's RSS feed.
3. Inserts and processes any new videos.
4. Re-exports `docs/videos.json`.
5. (After `git push`) the live site auto-updates.

---

## Evaluation Dataset

The dataset is the live output of the pipeline itself: **75 videos** (15 most recent from each of the 5 channels) collected during a single full run on **28 May 2026**.

| Channel | Videos collected | Captions available | Summarised |
|---|---:|---:|---:|
| Andrej Karpathy | 15 | 15 | 15 |
| Yannic Kilcher | 15 | 14 | 14 |
| Lex Fridman | 15 | 15 | 15 |
| AI Explained | 15 | 15 | 15 |
| Dwarkesh Patel | 15 | 15 | 15 |
| **Total** | **75** | **74** | **74** |

The one un-summarised video is a Yannic Kilcher holiday live stream that has no captions on YouTube at all.

The full dataset is committed to the repo at [`docs/videos.json`](docs/videos.json) and rendered live on the [public page](https://williamlie2905.github.io/llm-watcher/).

---

## Evaluation Methods

Because there is no ground-truth "correct" summary for a YouTube video, evaluation is operational rather than benchmarked:

1. **Coverage** — fraction of videos that produced a valid, schema-compliant summary out of those that had captions.
2. **Schema validity** — every summary in `videos.json` must contain non-empty `topics`, `summary`, `claims`, `mentions` fields (where applicable). Confirmed by the export query and visual inspection of the live table.
3. **Faithfulness spot-check** — manually compared a sample of generated summaries against the transcript and the video itself. The 1B model's summaries are short and occasionally generic, but were consistently *on-topic* once schema-constrained decoding was enabled.
4. **Recoverability** — the backlog mechanism was tested by deliberately interrupting the watcher mid-run; on the next invocation, all partially-processed videos were resumed without re-downloading captions or re-summarising the completed ones.

---

## Experimental Results

### End-to-end coverage
- **75 / 75** videos discovered across all five channels in a single run.
- **74 / 75** videos transcribed via YouTube captions (one live stream had none).
- **74 / 74** videos with captions successfully summarised into the target schema.
- Effective coverage on summarisable videos: **100 %**.

### Iterations during development
Reaching 100 % required four iterations on the summariser:

| Issue | Root cause | Fix |
|---|---|---|
| Initial 0 % export | `is_seen()` returned `True` for any row in the DB, even those with `processed = 0`. | Tightened `is_seen()` to require `processed = 1`, added a backlog pass at startup. |
| `Dwarkesh Patel` returning 0 entries | Wrong channel ID baked into the source. | Replaced with the correct ID (`UCXl4i9dYBrFOabk0xGmbkRA`) after verifying the RSS feed. |
| OpenAI quota errors | Account out of credits. | Migrated to local Ollama (`llama3.2`, then `llama3.2:1b` for speed). |
| ~20 % of summaries empty | Three independent model failure modes: (a) prose before the JSON, (b) two separate JSON objects glued together, (c) the model echoing back the input keys instead of the requested schema. | (a) Extract the JSON span by brace-matching. (b) Merge `},{` into `,`. (c) Switch from `format="json"` to an explicit JSON-schema `format=SCHEMA` — this constrains decoding so the model can only emit the four required keys. |

### Performance
- Caption download: ~2–4 s per video.
- Summarisation with `llama3.2:1b` on CPU: ~10–30 s per video.
- Full cold run for 75 videos: **~30–45 minutes**.
- Incremental run (no new videos): seconds, dominated by the five RSS HTTP requests.

### Output sample
A sample row from `docs/videos.json`:

```json
{
  "video_id": "o_av1b9rs2g",
  "title": "Two Rival Bets on AGI: Google I/O Highlights",
  "channel": "AI Explained",
  "topics": "Google I/O Highlights, Google's AI Strategy",
  "summary": "Google's new models and strategy for integrating AI into search boxes.",
  "claims": "Google aims to be a portal for using all things AI in search boxes, OpenAI focuses on consumers, while Google wants to sell more ads with chat boxes, New model Gemini Omni combines intelligence with generative media",
  "mentions": "GPT-4o, Gemini, Nano Banana Pro, Genie, VEO, OpenAI",
  "url": "https://youtube.com/watch?v=o_av1b9rs2g"
}
```

### Cross-channel observations
With the table sortable by topic and filterable by channel, a few patterns surfaced:
- **Yannic Kilcher** and **AI Explained** show the densest overlap on frontier-model news (Gemini, Claude, GPT releases).
- **Andrej Karpathy**'s subscriptions skew strongly toward Computerphile videos on systems and hardware — adjacent to LLMs but not always about them.
- **Dwarkesh Patel** is dominated by long-form interviews; in the captured window his guest David Reich appears in many rows, reflecting a multi-part series rather than scattered LLM content.
- **Lex Fridman** is the broadest — guests in the captured window include Khabib, Jeff Kaplan, and Rick Beato alongside Jensen Huang. A future iteration could add a relevance filter that drops non-LLM rows.

---

## Limitations and future work

- **CPU-only summarisation is slow.** Running on a GPU or a hosted API (Groq's free tier is OpenAI-compatible) would cut the per-video time from ~20 s to under 1 s.
- **RSS feed only exposes 15 videos per channel.** Older catalogue items can never be backfilled through this path; the YouTube Data API or `yt-dlp`'s channel listing would be needed for a deeper history.
- **No relevance filter.** Every video from each channel is processed, so Lex Fridman MMA and Andrej Karpathy's hardware likes appear alongside LLM content. A title- or transcript-level classifier would tighten the table to LLM-only.
- **No audio-only fallback.** Videos without captions (live streams, very recent uploads where auto-captions haven't been generated yet) are skipped. Adding Whisper as a fallback transcriber would close that gap.
