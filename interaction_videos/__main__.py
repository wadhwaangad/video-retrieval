from __future__ import annotations

import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path
from .config import load_formats
from .db import Store
from .queries import expand
from .youtube import YouTube


def collect(args):
    key = os.getenv("YOUTUBE_API_KEY")
    if not key: raise SystemExit("Set YOUTUBE_API_KEY before collecting.")
    store, api = Store(args.database), YouTube(key)
    added = calls = 0
    years = args.year or [None]
    try:
        for fmt in load_formats(args.formats):
            for taxonomy_term, search_query in expand(fmt):
                for year in years:
                    state_key = search_query if year is None else f"{search_query} | year:{year}"
                    token, complete = store.query_state(fmt.slug, state_key)
                    if complete: continue
                    after = before = None
                    if year:
                        after, before = f"{year}-01-01T00:00:00Z", f"{year + 1}-01-01T00:00:00Z"
                    for _ in range(args.pages_per_query):
                        if calls >= args.max_searches:
                            print(f"Stopped at the --max-searches limit ({args.max_searches}). Resume tomorrow.")
                            return
                        page = api.search(search_query, token, after, before); calls += 1
                        added += store.add_search_videos(page.get("items", []), fmt.slug, taxonomy_term)
                        token = page.get("nextPageToken")
                        if not token: store.save_query_state(fmt.slug, state_key, None, True); break
                        store.save_query_state(fmt.slug, state_key, token, False)
    finally: store.close()
    print(f"Collected/observed {added} records (duplicates are retained only once).")


def export(args):
    store = Store(args.database); rows = store.export_rows(); store.close()
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    data_dir = output / "data"; data_dir.mkdir(exist_ok=True)
    pages = [rows[i:i + args.page_size] for i in range(0, len(rows), args.page_size)]
    for index, page in enumerate(pages, 1):
        (data_dir / f"page-{index:05d}.json").write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    formats = sorted({f for row in rows for f in (row.get("formats") or "").split(",") if f})
    format_pages, format_totals = {}, {}
    for format_slug in formats:
        format_rows = [row for row in rows if format_slug in (row.get("formats") or "").split(",")]
        format_totals[format_slug] = len(format_rows)
        chunks = [format_rows[i:i + args.page_size] for i in range(0, len(format_rows), args.page_size)]
        format_pages[format_slug] = len(chunks)
        format_dir = data_dir / "formats" / format_slug; format_dir.mkdir(parents=True, exist_ok=True)
        for index, page in enumerate(chunks, 1):
            (format_dir / f"page-{index:05d}.json").write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    manifest = {"total": len(rows), "page_size": args.page_size, "pages": len(pages), "formats": formats,
                "format_pages": format_pages, "format_totals": format_totals}
    (output / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    root = Path(__file__).parent.parent / "site"
    for name in ("index.html", "app.js", "style.css"):
        (output / name).write_text((root / name).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Exported {len(rows):,} videos to {output}")


parser = argparse.ArgumentParser(description="Broad-recall YouTube interaction video collector")
sub = parser.add_subparsers(required=True)
p = sub.add_parser("collect"); p.add_argument("--database", default="corpus.sqlite3"); p.add_argument("--formats", default="config/formats.yaml"); p.add_argument("--pages-per-query", type=int, default=1); p.add_argument("--year", type=int, action="append", help="Limit searches to a calendar year; may be repeated."); p.add_argument("--max-searches", type=int, default=90, help="Safety cap below YouTube's default daily 100-search limit."); p.set_defaults(func=collect)
p = sub.add_parser("export"); p.add_argument("--database", default="corpus.sqlite3"); p.add_argument("--output", default="docs"); p.add_argument("--page-size", type=int, default=500); p.set_defaults(func=export)
args = parser.parse_args(); args.func(args)
