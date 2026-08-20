# Interaction Video Retrieval

Collect a broad, **unfiltered** corpus of YouTube videos with personalized, human-to-human interactions and publish it as a GitHub Pages catalog. The format bank in `config/formats.yaml` is the sole v1 taxonomy.

## Setup

1. Create a YouTube Data API v3 key in Google Cloud (enable **YouTube Data API v3**).
2. Set it for the current shell: ` $env:YOUTUBE_API_KEY = "..." `.
3. Run: `python -m interaction_videos collect --pages-per-query 3`.

Python 3.10+ is the only dependency. Run `python -m interaction_videos --help` for options.

## Typical workflow

```powershell
# Expand every taxonomy query, retain every result, and backfill discovered channels.
python -m interaction_videos collect --pages-per-query 3 --channel-videos 100

# Resume later; prior pages, videos, and channel uploads are retained.
python -m interaction_videos collect --pages-per-query 3

# Build the static site and JSON data for GitHub Pages.
python -m interaction_videos export --output docs
```

Commit and push `docs/`, then enable GitHub Pages with **Deploy from a branch** → `main` → `/docs`.

## Scaling notes

As of August 2026, YouTube documents a default **100 `search.list` calls per day** quota and a separate 10,000-unit daily allocation for other endpoints. A search page can return up to 50 videos, so a fresh run over this 27-term bank should use no more than `--pages-per-query 3` (81 searches). Channel uploads are collected from each discovered channel's uploads playlist and cost far less, so they are the main corpus multiplier. Run this continuously with different query variants, regional markets, and channels to accumulate toward 100k+ candidates. The database makes all runs resumable and deduplicated.

`--page-limit` gives each query a deliberately bounded slice. Increase it in later rounds only when you want deeper recall. Search results are candidates, not a claim that every video is personalized interaction. This is intentional for the requested no-filter phase.

Gemini is not required for collection. Add it later as a separate annotation stage so any scoring/filtering never destroys your raw candidate set.
