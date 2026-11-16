"""Run the scraper against live YouTube without Apify, a container or an account.

    python -I -m tools.local_check --handles @mkbhd @LinusTechTips
    python -I -m tools.local_check --search "skincare routine" --per-query 10

Exercises exactly the code the actor runs, minus Actor.charge/push_data.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from src.innertube import InnerTubeError
from src.scrape import Settings, collect_targets, scrape_channel

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")


def build_settings(args: argparse.Namespace) -> Settings:
    payload: dict = {
        "maxChannels": args.max_channels,
        "maxChannelsPerQuery": args.per_query,
        "scanVideoDescriptions": not args.no_videos,
        "enrichFromLinkedSite": not args.no_site,
        "includeChannelsWithoutEmail": True,
        "concurrency": args.concurrency,
    }
    if args.min_subs:
        payload["minSubscribers"] = args.min_subs
    if args.search:
        payload["mode"] = "search"
        payload["searchQueries"] = args.search
    else:
        payload["mode"] = "channels"
        payload["channels"] = args.handles
    return Settings.from_input(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handles", nargs="*", default=["@mkbhd"])
    parser.add_argument("--search", nargs="*")
    parser.add_argument("--per-query", type=int, default=10)
    parser.add_argument("--max-channels", type=int, default=12)
    parser.add_argument("--min-subs", type=int)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--no-videos", action="store_true")
    parser.add_argument("--no-site", action="store_true")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    settings = build_settings(args)
    targets = collect_targets(settings)
    print(f"{len(targets)} channels queued (mode={settings.mode})")
    if not targets:
        print("nothing to scan - check the handles or query")
        return 1

    records: list[dict] = []

    def run(target: dict) -> dict | None:
        try:
            return scrape_channel(target, settings)
        except InnerTubeError as exc:
            print(f"  FAIL {target['channelId']}: {exc}")
            return None

    with ThreadPoolExecutor(max_workers=settings.concurrency) as pool:
        for record in pool.map(run, targets):
            if record is None:
                continue
            records.append(record)
            flag = "HIT " if record["hasEmail"] else "miss"
            title = (record["title"] or "?")[:34]
            print(
                f"  {flag} {title:<34} subs={record['subscribersText'] or '?':<8}"
                f" src={record['emailSource'] or '-':<18}"
                f" {record['primaryEmail'] or ''}"
            )

    scanned = len(records)
    hits = sum(1 for record in records if record["hasEmail"])
    by_source: dict[str, int] = {}
    for record in records:
        if record["emailSource"]:
            by_source[record["emailSource"]] = by_source.get(record["emailSource"], 0) + 1
    print(f"\nscanned={scanned} hits={hits} hit_rate={hits / max(scanned, 1):.1%}")
    print(f"by source: {by_source}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=1, ensure_ascii=False)
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
