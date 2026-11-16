"""Actor entry point.

All scraping logic lives in scrape.py, which is SDK-free. This module adds only
the platform concerns: reading input, charging, and pushing dataset items.

Pricing stance: the only paid event is `email-found`, charged once per channel
that actually yields an address. Channels that come back empty are free. Every
competitor measured on 2026-11-08 charges per channel processed instead, which
at the measured 11.7% hit rate means their buyers pay about $0.43 per usable
address while believing they pay $0.05.
"""
from __future__ import annotations

import asyncio

from apify import Actor

from .innertube import InnerTubeError
from .scrape import (
    Settings,
    collect_targets,
    scrape_channel,
    warn_about_mode_mismatch,
)

CHARGE_EVENT = "email-found"


async def main() -> None:
    async with Actor:
        settings = Settings.from_input(await Actor.get_input())
        for warning in warn_about_mode_mismatch(settings):
            Actor.log.warning(warning)
        targets = await asyncio.to_thread(collect_targets, settings)
        Actor.log.info(f"{len(targets)} channels queued (mode={settings.mode})")

        semaphore = asyncio.Semaphore(settings.concurrency)
        stats = {"scanned": 0, "with_email": 0, "filtered": 0, "failed": 0}

        async def handle(target: dict) -> None:
            async with semaphore:
                try:
                    record = await asyncio.to_thread(scrape_channel, target, settings)
                except InnerTubeError as exc:
                    stats["failed"] += 1
                    Actor.log.warning(f"{target['channelId']}: {exc}")
                    return

            if record is None:
                stats["filtered"] += 1
                return

            stats["scanned"] += 1
            if record["hasEmail"]:
                stats["with_email"] += 1
                # Charged per channel that yielded an address, never per channel
                # merely looked at.
                await Actor.charge(CHARGE_EVENT)
                await Actor.push_data(record)
            elif settings.include_channels_without_email:
                await Actor.push_data(record)

        await asyncio.gather(*(handle(target) for target in targets))

        hit_rate = stats["with_email"] / stats["scanned"] if stats["scanned"] else 0.0
        Actor.log.info(
            f"scanned={stats['scanned']} with_email={stats['with_email']} "
            f"hit_rate={hit_rate:.1%} filtered={stats['filtered']} "
            f"failed={stats['failed']}"
        )
