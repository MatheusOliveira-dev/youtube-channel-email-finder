"""Measure whether reading more public sources would raise the hit rate.

    python -m tools.probe_headroom hitrate_measured.json 80

Takes the channels that currently come back empty and retries them with the
public sources widened: more recent videos, link aggregators that the main
extractor skips, and the oldest videos as well as the newest. Prints how many
of the current misses each widening would convert.

This exists so that a claim about the hit rate can be checked before it is made.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from src.enrich import _fetch
from src.extract import clean_emails, video_description
from src.innertube import InnerTubeError, about_tab, player, videos_tab

AGGREGATORS = (
    "linktr.ee",
    "beacons.ai",
    "linkin.bio",
    "komi.io",
    "stan.store",
    "campsite.bio",
    "carrd.co",
    "bio.link",
    "allmylinks.com",
    "milkshake.app",
    "snipfeed.co",
    "withkoji.com",
)
DEEP_VIDEOS = 8


def aggregator_links(blob: str) -> list[str]:
    urls = [
        urllib.parse.unquote(match)
        for match in re.findall(r"q=(https?%3A%2F%2F[^\"&]{8,200})", blob)
    ]
    urls += re.findall(r'"(https?://[^"]{6,160})"', blob)
    return [
        url
        for url in dict.fromkeys(urls)
        if any(host in url.lower() for host in AGGREGATORS)
    ]


def probe(channel_id: str) -> dict:
    result = {"cid": channel_id, "deep_video": None, "aggregator": None}
    try:
        blob = about_tab(channel_id)
    except InnerTubeError:
        return result

    for link in aggregator_links(blob)[:2]:
        html, _ = _fetch(link, 8)
        found = clean_emails(html)
        if found:
            result["aggregator"] = sorted(found)[:2]
            break

    try:
        videos = videos_tab(channel_id)
    except InnerTubeError:
        return result
    ids = list(dict.fromkeys(re.findall(r'"videoId":"([\w\-]{11})"', videos)))
    # Skip the first two: those are what the actor already reads.
    for index, video_id in enumerate(ids[2:DEEP_VIDEOS], start=3):
        try:
            found = clean_emails(video_description(player(video_id)))
        except InnerTubeError:
            continue
        if found:
            result["deep_video"] = {"position": index, "emails": sorted(found)[:2]}
            break
    return result


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else "hitrate_measured.json"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    with open(source, encoding="utf-8") as handle:
        records = json.load(handle)["records"]

    misses = [r["cid"] for r in records if not r.get("emails") and "error" not in r]
    sample = misses[:limit]
    print(f"current misses: {len(misses)}; probing {len(sample)}", flush=True)

    started = time.time()
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for index, result in enumerate(pool.map(probe, sample), 1):
            results.append(result)
            if index % 20 == 0:
                print(f"{index}/{len(sample)} {time.time() - started:.0f}s", flush=True)

    deep = [r for r in results if r["deep_video"]]
    agg = [r for r in results if r["aggregator"]]
    either = [r for r in results if r["deep_video"] or r["aggregator"]]
    n = len(results)
    print(f"\nprobed {n} currently-empty channels in {time.time() - started:.0f}s")
    print(f"  videos 3-{DEEP_VIDEOS} would convert : {len(deep):>3} ({100 * len(deep) / n:.1f}% of misses)")
    print(f"  link aggregators would convert : {len(agg):>3} ({100 * len(agg) / n:.1f}% of misses)")
    print(f"  either                         : {len(either):>3} ({100 * len(either) / n:.1f}% of misses)")
    if deep:
        positions = [r["deep_video"]["position"] for r in deep]
        print(f"  first hit position among those : {sorted(positions)}")
    total_before = len([r for r in records if r.get("emails")])
    scanned = len([r for r in records if "error" not in r])
    rate_before = total_before / scanned
    converted_rate = len(either) / n
    projected = (total_before + converted_rate * len(misses)) / scanned
    print(f"\nhit rate now        : {100 * rate_before:.1f}%")
    print(f"projected with both : {100 * projected:.1f}%  (+{100 * (projected - rate_before):.1f}pp)")
    with open("headroom.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
