from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
  video_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
  channel_id TEXT NOT NULL, channel_title TEXT NOT NULL, published_at TEXT,
  thumbnail_url TEXT, source TEXT NOT NULL, first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS video_formats (
  video_id TEXT NOT NULL REFERENCES videos(video_id), format_slug TEXT NOT NULL,
  query_term TEXT NOT NULL, PRIMARY KEY(video_id, format_slug, query_term)
);
CREATE TABLE IF NOT EXISTS queries (
  format_slug TEXT NOT NULL, query_term TEXT NOT NULL, page_token TEXT NOT NULL DEFAULT '',
  completed INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(format_slug, query_term)
);
CREATE TABLE IF NOT EXISTS channels (
  channel_id TEXT PRIMARY KEY, uploads_playlist_id TEXT, title TEXT, backfilled INTEGER NOT NULL DEFAULT 0
);
"""


class Store:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def query_state(self, fmt: str, term: str) -> tuple[str | None, bool]:
        row = self.conn.execute("SELECT page_token, completed FROM queries WHERE format_slug=? AND query_term=?", (fmt, term)).fetchone()
        return ((row["page_token"] or None, bool(row["completed"])) if row else (None, False))

    def save_query_state(self, fmt: str, term: str, token: str | None, completed: bool) -> None:
        self.conn.execute("INSERT INTO queries(format_slug,query_term,page_token,completed) VALUES(?,?,?,?) ON CONFLICT(format_slug,query_term) DO UPDATE SET page_token=excluded.page_token,completed=excluded.completed,updated_at=CURRENT_TIMESTAMP", (fmt, term, token or "", completed))
        self.conn.commit()

    def add_search_videos(self, items: Iterable[dict], fmt: str, term: str) -> int:
        count = 0
        for item in items:
            vid = item["id"].get("videoId")
            if not vid:
                continue
            s = item["snippet"]
            self.conn.execute("INSERT INTO videos(video_id,title,description,channel_id,channel_title,published_at,thumbnail_url,source) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(video_id) DO UPDATE SET title=excluded.title, description=excluded.description", (vid, s["title"], s.get("description", ""), s["channelId"], s["channelTitle"], s.get("publishedAt"), s.get("thumbnails", {}).get("medium", {}).get("url"), "search"))
            self.conn.execute("INSERT OR IGNORE INTO video_formats VALUES(?,?,?)", (vid, fmt, term))
            self.conn.execute("INSERT OR IGNORE INTO channels(channel_id,title) VALUES(?,?)", (s["channelId"], s["channelTitle"]))
            count += 1
        self.conn.commit()
        return count

    def pending_channels(self, limit: int) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM channels WHERE backfilled=0 LIMIT ?", (limit,)).fetchall()

    def mark_channel(self, channel_id: str, uploads: str | None, done: bool = True) -> None:
        self.conn.execute("UPDATE channels SET uploads_playlist_id=?, backfilled=? WHERE channel_id=?", (uploads, int(done), channel_id)); self.conn.commit()

    def add_channel_videos(self, items: Iterable[dict], channel: sqlite3.Row) -> int:
        count = 0
        for item in items:
            s = item["snippet"]; vid = s.get("resourceId", {}).get("videoId")
            if not vid: continue
            self.conn.execute("INSERT OR IGNORE INTO videos(video_id,title,description,channel_id,channel_title,published_at,thumbnail_url,source) VALUES(?,?,?,?,?,?,?,?)", (vid, s["title"], s.get("description", ""), channel["channel_id"], channel["title"] or "", s.get("publishedAt"), s.get("thumbnails", {}).get("medium", {}).get("url"), "channel_backfill")); count += 1
        self.conn.commit(); return count

    def export_rows(self) -> list[dict]:
        rows = self.conn.execute("SELECT v.*, group_concat(DISTINCT vf.format_slug) formats FROM videos v LEFT JOIN video_formats vf ON v.video_id=vf.video_id GROUP BY v.video_id ORDER BY first_seen_at DESC").fetchall()
        return [dict(row) for row in rows]
