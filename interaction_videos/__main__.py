from __future__ import annotations

import argparse, json, os
from pathlib import Path
from .config import load_formats
from .db import Store
from .youtube import YouTube


def collect(args):
    key = os.getenv("YOUTUBE_API_KEY")
    if not key: raise SystemExit("Set YOUTUBE_API_KEY before collecting.")
    store, api = Store(args.database), YouTube(key)
    added = 0
    try:
        for fmt in load_formats(args.formats):
            for term in fmt.query_terms:
                token, complete = store.query_state(fmt.slug, term)
                if complete: continue
                for _ in range(args.pages_per_query):
                    page = api.search(term, token); added += store.add_search_videos(page.get("items", []), fmt.slug, term)
                    token = page.get("nextPageToken")
                    if not token: store.save_query_state(fmt.slug, term, None, True); break
                    store.save_query_state(fmt.slug, term, token, False)
        for channel in store.pending_channels(args.channels_per_run):
            playlist = api.uploads_playlist(channel["channel_id"])
            if not playlist: store.mark_channel(channel["channel_id"], None); continue
            token = None; remaining = args.channel_videos
            while remaining > 0:
                page = api.playlist_items(playlist, token); added += store.add_channel_videos(page.get("items", []), channel)
                remaining -= len(page.get("items", [])); token = page.get("nextPageToken")
                if not token: break
            store.mark_channel(channel["channel_id"], playlist)
    finally: store.close()
    print(f"Collected/observed {added} records (duplicates are retained only once).")


def export(args):
    store = Store(args.database); rows = store.export_rows(); store.close()
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    data_dir = output / "data"; data_dir.mkdir(exist_ok=True)
    pages = [rows[i:i + args.page_size] for i in range(0, len(rows), args.page_size)]
    for index, page in enumerate(pages, 1):
        (data_dir / f"page-{index:05d}.json").write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    manifest = {"total": len(rows), "page_size": args.page_size, "pages": len(pages),
                "formats": sorted({f for row in rows for f in (row.get("formats") or "").split(",") if f})}
    (output / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    root = Path(__file__).parent.parent / "site"
    for name in ("index.html", "app.js", "style.css"):
        (output / name).write_text((root / name).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Exported {len(rows):,} videos to {output}")


parser = argparse.ArgumentParser(description="Broad-recall YouTube interaction video collector")
sub = parser.add_subparsers(required=True)
p = sub.add_parser("collect"); p.add_argument("--database", default="corpus.sqlite3"); p.add_argument("--formats", default="config/formats.yaml"); p.add_argument("--pages-per-query", type=int, default=1); p.add_argument("--channels-per-run", type=int, default=50); p.add_argument("--channel-videos", type=int, default=100); p.set_defaults(func=collect)
p = sub.add_parser("export"); p.add_argument("--database", default="corpus.sqlite3"); p.add_argument("--output", default="docs"); p.add_argument("--page-size", type=int, default=500); p.set_defaults(func=export)
args = parser.parse_args(); args.func(args)
