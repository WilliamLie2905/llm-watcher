# LLM Channel Watcher

Automated YouTube watcher that follows five popular LLM-focused channels, transcribes their videos via captions, summarises each one with a local LLM (Ollama / llama3.2:1b), and publishes a searchable table to GitHub Pages.

**Live site:** https://williamlie2905.github.io/llm-watcher/
**Report:** [REPORT.md](REPORT.md)

## What it does

1. Polls the RSS feed of each tracked channel for new uploads.
2. Downloads YouTube auto-captions via `yt-dlp`.
3. Summarises the transcript with a local Ollama model into a 4-field JSON record (topics, summary, claims, mentions) using schema-constrained decoding.
4. Stores everything in SQLite, exports to `docs/videos.json`.
5. The static page in `docs/` renders the JSON as a sortable, filterable table.

## Channels tracked

- Andrej Karpathy
- Yannic Kilcher
- Lex Fridman
- AI Explained
- Dwarkesh Patel

## Run it

### One-time setup

```bash
pip install feedparser yt-dlp ollama python-dotenv
```

Install [Ollama](https://ollama.com/download), then pull the model:

```bash
ollama pull llama3.2:1b
```

### Each run

```bash
run.bat
```

This polls all channels, processes any new videos, and re-exports `docs/videos.json`. Push the repo and GitHub Pages auto-updates the live site.

## File layout

| File | Purpose |
|---|---|
| `watcher.py` | Main pipeline — feed polling, dedup, backlog resume |
| `captions.py` | yt-dlp wrapper + VTT parser |
| `summarise.py` | Ollama call with JSON-schema constrained output |
| `db.py` | SQLite helpers |
| `export.py` | Dumps the DB to `docs/videos.json` |
| `docs/index.html` | Public viewer (loads `videos.json` client-side) |
| `docs/videos.json` | Latest exported dataset |
| `run.bat` | One-line entry point |

## Costs

Zero — no API keys, no cloud. Ollama runs locally on CPU.
