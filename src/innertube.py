"""Minimal InnerTube (YouTube internal API) client.

Only the three endpoints we need: resolve_url, search, browse, player.
No API key of our own is required - the WEB client key is embedded in every
youtube.com page load and the endpoints answer anonymously.
"""
from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request

WEB_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
ABOUT_PARAMS = "EgVhYm91dPIGBAoCEgA%3D"
VIDEOS_PARAMS = "EgZ2aWRlb3PyBgQKAjoA"
CHANNEL_SEARCH_PARAMS = "EgIQAg%3D%3D"  # filter: channels only


class InnerTubeError(RuntimeError):
    pass


def _context(hl: str = "en", gl: str = "US") -> dict:
    return {
        "client": {
            "clientName": "WEB",
            "clientVersion": "2.20240726.00.00",
            "hl": hl,
            "gl": gl,
        }
    }


def call(path: str, body: dict, *, retries: int = 3, timeout: int = 30) -> str:
    """POST to an InnerTube endpoint and return the response as compact JSON text.

    We return text rather than a dict because every extractor works by regex over
    the whole payload: the response shape changes often, the strings we want do not.
    Separators are normalised so patterns never have to tolerate stray whitespace.
    """
    url = f"https://www.youtube.com/youtubei/v1/{path}?key={WEB_KEY}&prettyPrint=false"
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
        },
    )
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
            return json.dumps(payload, separators=(",", ":"))
        except Exception as exc:  # noqa: BLE001 - retried below, raised after
            last = exc
            if attempt < retries - 1:
                time.sleep((2**attempt) + random.random())
    raise InnerTubeError(f"{path} failed after {retries} attempts: {last}")


def resolve_channel(handle_or_url: str, **ctx) -> str | None:
    """Turn @handle, /c/custom or a full URL into a UC... channel id."""
    target = handle_or_url.strip()
    if target.startswith("UC") and len(target) >= 22:
        return target
    if not target.startswith("http"):
        target = f"https://www.youtube.com/{target.lstrip('/')}"
    blob = call("navigation/resolve_url", {"context": _context(**ctx), "url": target})
    try:
        return json.loads(blob)["endpoint"]["browseEndpoint"]["browseId"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return None


def about_tab(channel_id: str, **ctx) -> str:
    return call(
        "browse",
        {"context": _context(**ctx), "browseId": channel_id, "params": ABOUT_PARAMS},
    )


def videos_tab(channel_id: str, **ctx) -> str:
    return call(
        "browse",
        {"context": _context(**ctx), "browseId": channel_id, "params": VIDEOS_PARAMS},
    )


def player(video_id: str, **ctx) -> str:
    return call("player", {"context": _context(**ctx), "videoId": video_id})


def search_channels(query: str, **ctx) -> str:
    return call(
        "search",
        {
            "context": _context(**ctx),
            "query": query,
            "params": CHANNEL_SEARCH_PARAMS,
        },
    )
