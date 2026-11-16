"""Measure the real hit rate by running the actor's own code over a channel list.

    python -m tools.measure_hitrate channels.json out.json

`channels.json` is a list of objects with at least a "cid" key, and optionally
"niche" and "subs" for the breakdown. Output is one record per channel plus the
aggregate, so the README numbers can always be regenerated from code rather than
from a one-off script.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from src.innertube import InnerTubeError
from src.scrape import Settings, scrape_channel

SETTINGS = Settings.from_input(
    {
        "mode": "channels",
        "scanVideoDescriptions": True,
        "enrichFromLinkedSite": True,
        "includeChannelsWithoutEmail": True,
    }
)
BANDS = [
    (0, 1e3, "under 1K"),
    (1e3, 1e4, "1K-10K"),
    (1e4, 1e5, "10K-100K"),
    (1e5, 1e6, "100K-1M"),
    (1e6, 1e13, "over 1M"),
]


def parse_subs(text: str | None) -> float | None:
    if not text:
        return None
    match = re.match(r"([\d.,]+)\s*([KMB]?)", text.strip().replace(",", "."))
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[match.group(2)]


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else "channels.json"
    destination = sys.argv[2] if len(sys.argv) > 2 else "hitrate_measured.json"
    with open(source, encoding="utf-8") as handle:
        channels = json.load(handle)

    def run(entry: dict) -> dict:
        target = {"channelId": entry["cid"], "subscriberText": None, "queryMatched": None}
        try:
            record = scrape_channel(target, SETTINGS) or {}
        except InnerTubeError as exc:
            return {"cid": entry["cid"], "niche": entry.get("niche"), "error": str(exc)}
        return {
            "cid": entry["cid"],
            "niche": entry.get("niche"),
            "subs": record.get("subscribersText"),
            "emails": record.get("emails") or [],
            "source": record.get("emailSource"),
            "sourceUrl": record.get("sourceUrl"),
        }

    started = time.time()
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for index, record in enumerate(pool.map(run, channels), 1):
            results.append(record)
            if index % 50 == 0:
                print(f"{index}/{len(channels)} {time.time() - started:.0f}s", flush=True)

    valid = [r for r in results if "error" not in r]
    hits = [r for r in valid if r["emails"]]
    by_source: dict[str, int] = defaultdict(int)
    for record in hits:
        by_source[record["source"] or "?"] += 1

    per_niche: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    per_band: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for record in valid:
        niche = record.get("niche") or "?"
        per_niche[niche][0] += 1
        value = parse_subs(record.get("subs"))
        band = (
            "unknown"
            if value is None
            else next(label for low, high, label in BANDS if low <= value < high)
        )
        per_band[band][0] += 1
        if record["emails"]:
            per_niche[niche][1] += 1
            per_band[band][1] += 1

    rate = len(hits) / max(len(valid), 1)
    print(f"\nHIT RATE: {len(hits)}/{len(valid)} = {rate:.1%}")
    print(f"errors: {len(results) - len(valid)}  elapsed: {time.time() - started:.0f}s")
    print(f"by source: {dict(by_source)}")
    print("\nby niche:")
    for label, (total, hit) in sorted(
        per_niche.items(), key=lambda kv: -(kv[1][1] / max(kv[1][0], 1))
    ):
        print(f"| {label} | {hit}/{total} | {100 * hit / max(total, 1):.0f}% |")
    print("\nby subscriber band:")
    for _, _, label in sorted(BANDS, key=lambda b: -b[0]):
        total, hit = per_band[label]
        if total:
            print(f"| {label} | {hit}/{total} | {100 * hit / total:.0f}% |")

    with open(destination, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "hit_rate": rate,
                "hits": len(hits),
                "scanned": len(valid),
                "by_source": dict(by_source),
                "records": results,
            },
            handle,
            indent=1,
            ensure_ascii=False,
        )
    print(f"\nwrote {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
