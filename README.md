# Interaction Video Retrieval

Collect a broad, **unfiltered** corpus of YouTube videos with personalized, human-to-human interactions and publish it as a GitHub Pages catalog. The format bank in `config/formats.yaml` is the sole v1 taxonomy.

## Setup

1. Create a YouTube Data API v3 key in Google Cloud (enable **YouTube Data API v3**).
2. Set it for the current shell: ` $env:YOUTUBE_API_KEY = "..." `.
3. Run: `python -m interaction_videos collect --pages-per-query 3`.

Python 3.10+ is the only dependency. Run `python -m interaction_videos --help` for options.

## Typical workflow

```powershell
# Run one page of each focused query (81 `search.list` calls: 27 terms × 3).
python -m interaction_videos collect

# Resume later; prior pages, videos, and channel uploads are retained.
python -m interaction_videos collect

# Build the static site and JSON data for GitHub Pages.
python -m interaction_videos export --output docs
```

Commit and push `docs/`, then enable GitHub Pages with **Deploy from a branch** → `main` → `/docs`.

## Scaling notes

As of August 2026, YouTube documents a default **100 `search.list` calls per day** quota. A search page can return up to 50 videos. Each taxonomy term is expanded only into three focused searches: its exact phrase, exact phrase + `full session`, and exact phrase + `real session`. That produces 81 searches across the 27 supplied terms, safely below the default daily cap. There is deliberately no channel backfill: a good interaction video does not imply that the rest of its channel is relevant. The database makes runs resumable and deduplicated.

`--pages-per-query` gives each focused query a deliberately bounded slice. Do not increase it above `1` for the full bank without reducing the number of terms, because 27 terms × 3 expansions × 2 pages would exceed the default search quota. Search results are candidates, not a claim that every video is personalized interaction. This is intentional for the requested no-filter phase.

Gemini is not required for collection. Add it later as a separate annotation stage so any scoring/filtering never destroys your raw candidate set.
