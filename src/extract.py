"""Pull contact data out of InnerTube payloads.

Every extractor works by regex over the whole JSON text rather than by walking a
parsed structure. YouTube reshapes its response objects often; the string
literals we care about are stable. The payloads are normalised to compact JSON
(no space after ':') by innertube.call, so patterns never need \\s*.
"""
from __future__ import annotations

import re
import urllib.parse

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# Substrings that mark an address as boilerplate, a placeholder or an asset path
# rather than a real contact. Learned from the 350-channel measurement run plus
# the false positives seen when crawling linked sites (Sentry serves
# "example@yourdomain.com" in its docs markup, for instance).
REJECT_SUBSTRINGS = (
    "example.",
    "yourdomain",
    "@domain",
    "@email.",
    "sentry.io",
    "youtube.com",
    "gstatic",
    "ytimg",
    "schema.org",
    "wixpress",
    "@sentry-",
    "noreply",
    "no-reply",
    "donotreply",
    # Platform addresses harvested off a linked site are not the creator's
    # contact: @patreon.com, @substack.com and friends belong to the platform.
    "@patreon.com",
    "@substack.com",
    "@shopify.com",
    "@squarespace.com",
    "@wordpress.com",
    "@wix.com",
    "@teespring.com",
    "@bigcartel.com",
    # Standards-body and tooling addresses embedded in a site's own markup.
    # "public-schemaorg@w3.org" came back from a real channel's linked site and
    # would have been billed as a find.
    "@w3.org",
    "schemaorg",
    "@googlegroups.com",
    "@lists.",
    "@sentry.wixpress",
    "@jquery.com",
    "@cloudflare.com",
)
REJECT_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp",
    ".gif",
    ".css",
    ".js",
    ".json",
)

# Link targets that are social profiles, not a site worth crawling for contact.
SOCIAL_HOSTS = (
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "patreon.com",
    "discord.",
    "spotify.",
    "apple.com",
    "amazon.",
    "linktr.ee",
    "threads.net",
    "twitch.tv",
    "reddit.com",
)

# A contact address is worth more when it reads like a business inbox.
BUSINESS_HINTS = (
    "business",
    "contact",
    "partner",
    "sponsor",
    "collab",
    "media",
    "press",
    "booking",
    "management",
    "info",
    "hello",
    "inquir",
    "enquir",
)


# JSON escapes sit directly against the local part in these payloads, so a raw
# match picks them up: ">merch@x.com" became "u003emerch@x.com" and
# "\nDave@x.com" became "nDave@x.com". Neutralise the escapes before matching.
ESCAPE_RE = re.compile(r"\\+(?:u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|[nrtfvb/\"'\\])")


def clean_emails(text: str) -> set[str]:
    """Return the plausible contact addresses found anywhere in `text`."""
    found: set[str] = set()
    if not text:
        return found
    text = ESCAPE_RE.sub(" ", text)
    for raw in EMAIL_RE.findall(text):
        candidate = raw.strip(".,;:)(<>[]\"'").replace("\\u0040", "@")
        lowered = candidate.lower()
        if candidate.count("@") != 1:
            continue
        if len(candidate) > 60:
            continue
        if any(bad in lowered for bad in REJECT_SUBSTRINGS):
            continue
        if lowered.endswith(REJECT_SUFFIXES):
            continue
        # No stray-prefix stripping here on purpose. ESCAPE_RE already removes
        # the "\n"/">" that used to glue onto the local part, and a rule
        # like ^[nrt] would eat the first letter of real addresses such as
        # real@, rachel@, nick@, tom@, team@ and news@.
        if "." not in candidate.split("@", 1)[1]:
            continue
        found.add(candidate)
    return found


def rank_emails(emails: set[str]) -> list[str]:
    """Business-looking inboxes first, then shortest (usually the canonical one)."""

    def sort_key(email: str) -> tuple[int, int, str]:
        lowered = email.lower()
        is_business = 0 if any(hint in lowered for hint in BUSINESS_HINTS) else 1
        return (is_business, len(email), lowered)

    return sorted(emails, key=sort_key)


def channel_title(blob: str) -> str | None:
    match = re.search(r'"pageHeaderViewModel":.{0,400}?"content":"([^"]{1,80})"', blob)
    if match:
        return match.group(1)
    match = re.search(r'"channelMetadataRenderer":\{"title":"([^"]{1,80})"', blob)
    if match:
        return match.group(1)
    match = re.search(r'"title":\{"simpleText":"([^"]{1,80})"', blob)
    return match.group(1) if match else None


def _header_metadata(blob: str, unit: str) -> str | None:
    """Read a header metadata part, e.g. '21.4M subscribers' or '1.8K videos'.

    The About payload mentions "subscribers" dozens of times - every recommended
    channel carries its own count - so a bare search returns someone else's
    figure. The requested channel's own numbers live in the page header's
    metadataParts. Matching is also anchored on the opening quote because
    YouTube wraps display strings in directional marks (\\u2068) whose escape
    ends in digits and would otherwise glue onto the count: "\\u206821.4M" was
    being read as 206821.4M.
    """
    pattern = (
        r'"content":"([\d][\d.,]*\s*[KMB]?)\s+' + unit + r'"'
    )
    match = re.search(pattern, blob)
    if match:
        return match.group(1).strip()
    # Fallback: the accessibility label spells the magnitude out in words.
    match = re.search(
        r'"label":"([\d][\d.,]*)\s+(thousand|million|billion)\s+' + unit + r'"', blob
    )
    if match:
        suffix = {"thousand": "K", "million": "M", "billion": "B"}[match.group(2)]
        return f"{match.group(1)}{suffix}"
    return None


def subscriber_text(blob: str) -> str | None:
    return _header_metadata(blob, "subscribers")


def video_count_text(blob: str) -> str | None:
    return _header_metadata(blob, "videos")


def parse_count(text: str | None) -> int | None:
    """'1.2M subscribers' -> 1200000. Returns None when unparseable."""
    if not text:
        return None
    match = re.match(r"([\d.,]+)\s*([KMB]?)", text.strip().replace(",", "."))
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return int(value * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[match.group(2)])


# Link shorteners and affiliate/storefront hosts: a creator's About tab is full
# of these (geni.us, goo.gl, shop.* ...) and crawling them for a contact address
# wastes requests, so they sort last rather than being dropped outright.
LOW_VALUE_HOSTS = (
    "geni.us",
    "goo.gl",
    "bit.ly",
    "amzn.to",
    "lnk.to",
    "shop.",
    "store.",
    "merch",
    "/products/",
    "redirect",
    "utm_",
)


# Hosts that are never the creator's own site: YouTube's own domains, Google's
# asset and font CDNs, and the vocabularies quoted in the page markup. Matched
# on the host and its subdomains, not as a substring - an earlier prefix check
# let "i.ytimg.com", "m.youtube.com" and "www.gstatic.com" through, which both
# polluted the output and sent the site crawler after schema.org.
INFRA_HOSTS = (
    "youtube.com",
    "youtu.be",
    "ytimg.com",
    "ggpht.com",
    "googleusercontent.com",
    "gstatic.com",
    "googleapis.com",
    "google.com",
    "schema.org",
    "w3.org",
    "example.com",
    "localhost",
)


def _host_of(url: str) -> str:
    host = url.split("//", 1)[-1].split("/")[0].split("?")[0].split(":")[0]
    return host.lower().removeprefix("www.")


def _is_infra(url: str) -> bool:
    host = _host_of(url)
    return any(host == infra or host.endswith("." + infra) for infra in INFRA_HOSTS)


def external_links(blob: str, channel_name: str | None = None) -> list[str]:
    """Channel links, excluding social profiles, best candidate first.

    Links in the About tab are wrapped in YouTube's /redirect?q=<encoded> form,
    so the direct-URL pattern alone misses most of them. Ordering matters because
    the caller only follows the first couple: a link whose host echoes the
    channel name is far likelier to be the creator's own site, where a contact
    page lives, than an affiliate or storefront link.
    """
    urls: list[str] = [
        urllib.parse.unquote(match)
        for match in re.findall(r"q=(https?%3A%2F%2F[^\"&]{8,200})", blob)
    ]
    urls += re.findall(r'"(https?://[^"]{6,160})"', blob)
    # Payloads repeat the same link in several spellings - with and without a
    # trailing slash, and with different capitalisation of the host. Deduplicate
    # on a normalised key so one link is reported once, keeping the first
    # spelling seen.
    candidates: list[str] = []
    seen_keys: set[str] = set()
    for url in urls:
        if _is_infra(url) or any(host in url.lower() for host in SOCIAL_HOSTS):
            continue
        scheme, _, rest = url.partition("://")
        host, slash, path = rest.partition("/")
        key = f"{host.lower().removeprefix('www.')}/{path.rstrip('/').lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(url)

    name_token = ""
    if channel_name:
        name_token = re.sub(r"[^a-z0-9]", "", channel_name.lower())[:12]

    def sort_key(url: str) -> tuple[int, int, int]:
        lowered = url.lower()
        own_site = 0 if name_token and name_token[:6] and name_token[:6] in lowered else 1
        low_value = 1 if any(host in lowered for host in LOW_VALUE_HOSTS) else 0
        return (low_value, own_site, len(url))

    return sorted(candidates, key=sort_key)


def recent_video_ids(blob: str, limit: int = 3) -> list[str]:
    return list(dict.fromkeys(re.findall(r'"videoId":"([\w\-]{11})"', blob)))[:limit]


def video_description(player_blob: str) -> str:
    match = re.search(
        r'"shortDescription":"(.*?)","isCrawlable"', player_blob, re.S
    )
    return match.group(1) if match else ""


def search_result_channels(blob: str, limit: int = 20) -> list[dict]:
    """Channel ids (and subscriber text when present) from a channel search."""
    out: list[dict] = []
    seen: set[str] = set()
    for chunk in blob.split('"channelRenderer"')[1:]:
        head = chunk[:2500]
        match = re.search(r'"(?:channelId|browseId)":"(UC[\w\-]{20,24})"', head)
        if not match:
            continue
        channel_id = match.group(1)
        if channel_id in seen:
            continue
        seen.add(channel_id)
        # "subscriberCountText" in search results now carries the @handle, not a
        # count, so read the count from the metadata part that states its unit.
        subs = re.search(r'"content":"([\d][\d.,]*\s*[KMB]?)\s+subscribers"', head)
        if not subs:
            subs = re.search(
                r'"subscriberCountText":\{"simpleText":"([\d][^"]{0,24})"', head
            )
        out.append(
            {
                "channelId": channel_id,
                "subscriberText": subs.group(1).strip() if subs else None,
            }
        )
        if len(out) >= limit:
            break
    return out
