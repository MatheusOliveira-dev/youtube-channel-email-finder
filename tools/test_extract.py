"""Offline checks for the extraction rules. No network, runs in a second.

    python -m tools.test_extract

Every case here is a real failure seen while testing against live channels, so
this doubles as a regression record.
"""
from __future__ import annotations

import sys

from src.enrich import _belongs_to_site, _registrable
from src.extract import (
    clean_emails,
    parse_count,
    rank_emails,
    subscriber_text,
    video_count_text,
)

# (email, site it was found on, keep?) - a third-party address lifted off a
# creator's site would be billed as a find, so these are revenue-critical.
SITE_CASES: list[tuple[str, str, bool]] = [
    ("hello@tally.so", "https://drshereeneidriss.com/contact", False),
    ("hello@drshereeneidriss.com", "https://drshereeneidriss.com/contact", True),
    ("hi@sub.drshereeneidriss.com", "https://drshereeneidriss.com/", True),
    ("creator@gmail.com", "https://anysite.com/", True),
    ("x@mail.creator.co.uk", "https://www.creator.co.uk/contact", True),
    ("noise@hubspot.com", "https://creator.com/", False),
    ("a@creator.com.br", "https://www.creator.com.br/", True),
]

CASES: list[tuple[str, str, set[str]]] = [
    # JSON escapes glued to the local part (seen on a van-life channel).
    ("escaped >", r">merch@example-creator.com", {"merch@example-creator.com"}),
    ("escaped newline", r"\nDave@vanlifemeow.com", {"Dave@vanlifemeow.com"}),
    ("escaped, uppercase next", r"\nBusiness@Foo.com", {"Business@Foo.com"}),
    # Addresses starting with n/r/t must survive intact: an earlier prefix-strip
    # heuristic turned real@ into eal@.
    ("leading r", "real@creator.com", {"real@creator.com"}),
    ("leading n", "nick@creator.com", {"nick@creator.com"}),
    (
        "leading t",
        "team@creator.com news@creator.com tom@creator.com",
        {"team@creator.com", "news@creator.com", "tom@creator.com"},
    ),
    # Platform inboxes are not the creator's contact.
    ("platform dropped", "merch@patreon.com and real@creator.com", {"real@creator.com"}),
    # Docs placeholders picked up when crawling a linked site.
    ("placeholder dropped", "example@yourdomain.com hi@real.com", {"hi@real.com"}),
    # Retina asset filenames look like addresses.
    ("asset dropped", "logo@2x.png ok@site.com", {"ok@site.com"}),
    ("short domain", "hi@x.co", {"hi@x.co"}),
    ("no tld dropped", "someone@localhost", set()),
    # Standards-body address from a site's schema.org markup, seen on a real
    # personal-finance channel's linked site; it would have been billed.
    (
        "w3.org dropped",
        "public-schemaorg@w3.org hello@creator.com",
        {"hello@creator.com"},
    ),
    ("empty", "", set()),
]


def main() -> int:
    failures = 0

    for label, text, expected in CASES:
        actual = clean_emails(text)
        if actual != expected:
            failures += 1
            print(f"FAIL {label}\n     text={text!r}\n     got={sorted(actual)}"
                  f"\n     want={sorted(expected)}")
        else:
            print(f"ok   {label}")

    # Ranking: business-looking inboxes first.
    ranked = rank_emails({"dave@x.com", "business@x.com", "zz@x.com"})
    if ranked[0] != "business@x.com":
        failures += 1
        print(f"FAIL ranking: got {ranked}")
    else:
        print("ok   ranking prefers business inbox")

    # Counts.
    count_cases = [("21.4M", 21_400_000), ("463K", 463_000), ("1.17M", 1_170_000),
                   ("548", 548), (None, None), ("", None)]
    for text, expected_count in count_cases:
        actual_count = parse_count(text)
        if actual_count != expected_count:
            failures += 1
            print(f"FAIL parse_count({text!r}) -> {actual_count}, want {expected_count}")
    else:
        print("ok   parse_count")

    # The header-anchored subscriber read must ignore other channels' counts.
    # Shape mirrors the real payload: a recommended channel's accessibility
    # label appears before the requested channel's own metadata part.
    blob = (
        '"subscriberCountText":{"accessibility":{"accessibilityData":'
        '{"label":"463 thousand subscribers"}}},'
        '"metadataParts":[{"text":{"content":"@fireship"}},'
        '{"text":{"content":"4.33M subscribers"}},'
        '{"text":{"content":"1.8K videos"}}]'
    )
    if subscriber_text(blob) != "4.33M":
        failures += 1
        print(f"FAIL subscriber_text -> {subscriber_text(blob)!r}, want '4.33M'")
    else:
        print("ok   subscriber_text ignores other channels")
    if video_count_text(blob) != "1.8K":
        failures += 1
        print(f"FAIL video_count_text -> {video_count_text(blob)!r}")
    else:
        print("ok   video_count_text")

    # Linked-site domain matching.
    for email, site, expected_keep in SITE_CASES:
        actual_keep = _belongs_to_site(email, site)
        if actual_keep != expected_keep:
            failures += 1
            print(
                f"FAIL site-match {email} on {site} -> {actual_keep}, "
                f"want {expected_keep}"
            )
    else:
        print("ok   linked-site domain matching")

    # Links arrive in several spellings of the same address and must collapse to
    # one. A real MKBHD payload carried vote.mkbhd.com three times.
    from src.extract import _is_infra, external_links

    blob = (
        '"url":"http://MKBHD.com","url":"http://MKBHD.com/",'
        '"url":"https://vote.mkbhd.com","url":"https://vote.MKBHD.com",'
        '"url":"https://vote.mkbhd.com/"'
    )
    links = external_links(blob)
    if len(links) != 2:
        failures += 1
        print(f"FAIL link dedup -> {links}, want 2 distinct")
    else:
        print("ok   duplicate link spellings collapse")

    from src.extract import _is_infra

    for url, expected_infra in [
        ("https://schema.org", True),
        ("http://schema.org/http://schema.org/YoutubeChannelV2", True),
        ("https://m.youtube.com/channel/UC9", True),
        ("https://www.gstatic.com/youtube/img/x.json", True),
        ("https://i.ytimg.com/an_webp/x.webp", True),
        ("https://starlinemgmt.com/contact", False),
        ("https://fireship.dev", False),
    ]:
        if _is_infra(url) != expected_infra:
            failures += 1
            print(f"FAIL _is_infra({url}) -> {_is_infra(url)}, want {expected_infra}")
    else:
        print("ok   infrastructure hosts excluded from links")

    for host, expected_registrable in [
        ("www.creator.co.uk", "creator.co.uk"),
        ("creator.com.br", "creator.com.br"),
        ("x.com", "x.com"),
    ]:
        if _registrable(host) != expected_registrable:
            failures += 1
            print(
                f"FAIL registrable({host}) -> {_registrable(host)}, "
                f"want {expected_registrable}"
            )
    else:
        print("ok   registrable domain")

    print(f"\n{'FAILED' if failures else 'PASSED'}: {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
