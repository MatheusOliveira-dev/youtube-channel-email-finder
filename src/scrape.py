"""Channel scraping logic, with no dependency on the Apify SDK.

Keeping this module SDK-free is deliberate: it can be exercised straight from a
terminal (see tools/local_check.py) against live YouTube without an Apify
account, a container, or a platform run. main.py adds only the platform concerns
- reading input, charging events, pushing dataset items.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .enrich import emails_from_site
from .extract import (
    channel_title,
    clean_emails,
    external_links,
    parse_count,
    rank_emails,
    recent_video_ids,
    search_result_channels,
    subscriber_text,
    video_count_text,
    video_description,
)
from .innertube import (
    InnerTubeError,
    about_tab,
    player,
    resolve_channel,
    search_channels,
    videos_tab,
)

log = logging.getLogger(__name__)

CHANNEL_ID_PREFIX = "UC"


@dataclass
class Settings:
    mode: str = "channels"
    channels: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    max_channels_per_query: int = 20
    max_channels: int = 100
    min_subscribers: int | None = None
    max_subscribers: int | None = None
    scan_video_descriptions: bool = True
    enrich_from_linked_site: bool = True
    include_channels_without_email: bool = False
    language: str = "en"
    country: str = "US"
    concurrency: int = 5

    @classmethod
    def from_input(cls, data: dict | None) -> "Settings":
        data = data or {}
        settings = cls()
        settings.mode = data.get("mode") or "channels"
        settings.channels = [
            str(item).strip()
            for item in (data.get("channels") or [])
            if str(item).strip()
        ]
        settings.search_queries = [
            str(item).strip()
            for item in (data.get("searchQueries") or [])
            if str(item).strip()
        ]
        settings.max_channels_per_query = int(data.get("maxChannelsPerQuery") or 20)
        settings.max_channels = int(data.get("maxChannels") or 100)
        settings.min_subscribers = data.get("minSubscribers")
        settings.max_subscribers = data.get("maxSubscribers")
        settings.scan_video_descriptions = bool(data.get("scanVideoDescriptions", True))
        settings.enrich_from_linked_site = bool(data.get("enrichFromLinkedSite", True))
        settings.include_channels_without_email = bool(
            data.get("includeChannelsWithoutEmail", False)
        )
        settings.language = data.get("language") or "en"
        settings.country = data.get("country") or "US"
        settings.concurrency = max(1, min(10, int(data.get("concurrency") or 5)))
        return settings

    @property
    def ctx(self) -> dict:
        return {"hl": self.language, "gl": self.country}


def normalise_channel_ref(ref: str) -> str:
    """Return a UC... id when the reference already contains one, else the ref."""
    ref = ref.strip()
    if ref.startswith(CHANNEL_ID_PREFIX) and len(ref) >= 22 and "/" not in ref:
        return ref
    if "/channel/" in ref:
        tail = ref.split("/channel/", 1)[1]
        candidate = tail.split("/")[0].split("?")[0]
        if candidate.startswith(CHANNEL_ID_PREFIX):
            return candidate
    return ref


def warn_about_mode_mismatch(settings: Settings) -> list[str]:
    """Spot the case where the filled-in field does not match the chosen mode.

    The input form shows both the channel list and the keyword list whatever the
    mode is, because an Apify input schema cannot hide a field based on another
    field's value. Someone who fills the wrong one gets an empty run and no
    explanation, so say it plainly in the log instead.
    """
    warnings: list[str] = []
    if settings.mode == "search" and not settings.search_queries:
        if settings.channels:
            warnings.append(
                "Input mode is 'search' but no search queries were given, while "
                f"{len(settings.channels)} channel(s) were. Those are ignored in "
                "search mode. Switch the mode to 'channels', or fill in the "
                "keywords under 'Mode B'."
            )
        else:
            warnings.append("Input mode is 'search' but no search queries were given.")
    if settings.mode == "channels" and not settings.channels:
        if settings.search_queries:
            warnings.append(
                "Input mode is 'channels' but no channels were given, while "
                f"{len(settings.search_queries)} search query(ies) were. Those are "
                "ignored in channels mode. Switch the mode to 'search', or fill in "
                "the channels under 'Mode A'."
            )
        else:
            warnings.append("Input mode is 'channels' but no channels were given.")
    return warnings


def collect_targets(settings: Settings) -> list[dict]:
    """Build the channel worklist, from search queries or explicit references."""
    targets: list[dict] = []
    seen: set[str] = set()

    if settings.mode == "search":
        for query in settings.search_queries:
            try:
                blob = search_channels(query, **settings.ctx)
            except InnerTubeError as exc:
                log.warning("search failed for %r: %s", query, exc)
                continue
            for found in search_result_channels(
                blob, limit=settings.max_channels_per_query
            ):
                if found["channelId"] in seen:
                    continue
                seen.add(found["channelId"])
                targets.append({**found, "queryMatched": query})
                if len(targets) >= settings.max_channels:
                    return targets
        return targets

    for ref in settings.channels:
        normalised = normalise_channel_ref(ref)
        if normalised.startswith(CHANNEL_ID_PREFIX) and "/" not in normalised:
            channel_id = normalised
        else:
            try:
                channel_id = resolve_channel(normalised, **settings.ctx)
            except InnerTubeError as exc:
                log.warning("could not resolve %r: %s", ref, exc)
                continue
        if not channel_id or channel_id in seen:
            continue
        seen.add(channel_id)
        targets.append(
            {"channelId": channel_id, "subscriberText": None, "queryMatched": None}
        )
        if len(targets) >= settings.max_channels:
            break
    return targets


def within_subscriber_range(subscribers: int | None, settings: Settings) -> bool:
    """Channels with an unknown count are kept rather than dropped: the About tab
    renders the figure differently for some locales, and silently skipping them
    would look like a scraper bug to the buyer."""
    if subscribers is None:
        return True
    if settings.min_subscribers and subscribers < int(settings.min_subscribers):
        return False
    if settings.max_subscribers and subscribers > int(settings.max_subscribers):
        return False
    return True


def scrape_channel(target: dict, settings: Settings) -> dict | None:
    """Run the contact sources for one channel. None means filtered out.

    Sources run cheapest-first and stop at the first hit, so a channel that
    publishes its address in the About tab costs exactly one request.
    """
    channel_id = target["channelId"]

    about = about_tab(channel_id, **settings.ctx)
    subs_text = subscriber_text(about) or target.get("subscriberText")
    subscribers = parse_count(subs_text)
    if not within_subscriber_range(subscribers, settings):
        return None

    title = channel_title(about)
    emails = clean_emails(about)
    source = "about" if emails else None
    links = external_links(about, channel_name=title)

    if not emails and settings.scan_video_descriptions:
        try:
            videos = videos_tab(channel_id, **settings.ctx)
            for video_id in recent_video_ids(videos, limit=2):
                emails |= clean_emails(
                    video_description(player(video_id, **settings.ctx))
                )
                if emails:
                    source = "video_description"
                    break
        except InnerTubeError as exc:
            log.warning("%s: video scan failed: %s", channel_id, exc)

    source_url = None
    if not emails and settings.enrich_from_linked_site and links:
        emails, source_url = emails_from_site(links)
        if emails:
            source = "linked_site"

    ranked = rank_emails(emails)
    return {
        "channelId": channel_id,
        "channelUrl": f"https://www.youtube.com/channel/{channel_id}",
        "title": title,
        "subscribers": subscribers,
        "subscribersText": subs_text,
        "videoCountText": video_count_text(about),
        "emails": ranked,
        "primaryEmail": ranked[0] if ranked else None,
        "emailCount": len(ranked),
        "emailSource": source,
        "sourceUrl": source_url,
        "externalLinks": links[:5],
        "queryMatched": target.get("queryMatched"),
        "hasEmail": bool(ranked),
    }
