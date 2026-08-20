from __future__ import annotations

import json
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/youtube/v3/"


class YouTube:
    def __init__(self, api_key: str): self.api_key = api_key
    def get(self, endpoint: str, **params) -> dict:
        params["key"] = self.api_key
        url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"YouTube API {e.code}: {e.read().decode('utf-8', 'replace')}") from e
    def search(self, term: str, token: str | None) -> dict:
        args = dict(part="snippet", q=term, type="video", maxResults=50, order="relevance")
        if token: args["pageToken"] = token
        return self.get("search", **args)
    def uploads_playlist(self, channel_id: str) -> str | None:
        data = self.get("channels", part="contentDetails", id=channel_id, maxResults=1)
        items = data.get("items", [])
        return items[0]["contentDetails"]["relatedPlaylists"].get("uploads") if items else None
    def playlist_items(self, playlist: str, token: str | None) -> dict:
        args = dict(part="snippet", playlistId=playlist, maxResults=50)
        if token: args["pageToken"] = token
        return self.get("playlistItems", **args)
