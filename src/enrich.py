"""Follow a channel's linked site looking for a contact address.

This is the third and weakest of the three sources, so it is strictly bounded:
at most a couple of links per channel, small read limit, short timeouts, and it
stops as soon as something is found. The channel's own About tab and its recent
video descriptions are cheaper and are tried first by the caller.
"""
from __future__ import annotations

import urllib.error
import urllib.request

from .extract import clean_emails

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
CONTACT_PATHS = ("/contact", "/contact-us", "/about", "/impressum")
MAX_READ_BYTES = 400_000


def _fetch(url: str, timeout: int) -> tuple[str, str]:
    """Return (html, final_url). Empty html on any failure - never raises."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type and "text" not in content_type:
                return "", response.geturl()
            body = response.read(MAX_READ_BYTES).decode("utf-8", "replace")
            return body, response.geturl()
    except Exception:  # noqa: BLE001 - a dead link is a normal outcome here
        return "", url


def _origin(url: str) -> str | None:
    if not url.startswith("http"):
        return None
    parts = url.split("/", 3)
    return f"{parts[0]}//{parts[2]}" if len(parts) >= 3 else None


# Mailbox providers: a creator legitimately uses these, and the address will
# never match their site's domain.
GENERIC_MAIL_HOSTS = (
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "proton.me",
    "protonmail.com",
    "icloud.com",
    "me.com",
    "gmx.com",
    "zoho.com",
    "aol.com",
    "mail.com",
    "yandex.com",
)


def _registrable(host: str) -> str:
    """Rough 'example.co.uk' / 'example.com' from a host. Good enough to compare
    a site against an address found on it."""
    host = host.lower().split(":")[0].removeprefix("www.")
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    # Treat a two-label public suffix (co.uk, com.br) as part of the name.
    if len(parts[-2]) <= 3 and len(parts[-1]) <= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _belongs_to_site(email: str, site_url: str) -> bool:
    """Keep an address found on a site only when it plausibly belongs to it.

    Pages carry third-party addresses from the tools that built them - form
    builders, shops, analytics, standards bodies. Those are not the creator's
    contact, and under per-find billing each one would be charged as a hit. An
    address is kept when its domain matches the site it was found on, or when it
    is at a mailbox provider.
    """
    domain = email.rsplit("@", 1)[-1].lower()
    if any(domain == host or domain.endswith("." + host) for host in GENERIC_MAIL_HOSTS):
        return True
    host = site_url.split("//", 1)[-1].split("/")[0]
    return _registrable(domain) == _registrable(host)


def emails_from_site(
    links: list[str],
    *,
    max_links: int = 2,
    timeout: int = 8,
    try_contact_pages: bool = True,
) -> tuple[set[str], str | None]:
    """Crawl up to `max_links` linked sites; return (emails, url_that_worked).

    Shortened links (bit.ly and friends) resolve on their own through the
    redirect that urlopen follows, which is why we read the final URL back
    before deriving contact-page candidates from it.
    """
    for link in links[:max_links]:
        html, final_url = _fetch(link, timeout)
        if html:
            found = {
                email
                for email in clean_emails(html)
                if _belongs_to_site(email, final_url)
            }
            if found:
                return found, final_url
        if not try_contact_pages:
            continue
        origin = _origin(final_url)
        if not origin:
            continue
        for path in CONTACT_PATHS:
            page_url = origin + path
            page, _ = _fetch(page_url, timeout)
            if not page:
                continue
            found = {
                email
                for email in clean_emails(page)
                if _belongs_to_site(email, page_url)
            }
            if found:
                return found, page_url
    return set(), None
