# Development notes

## Layout

```
src/innertube.py   client for YouTube's internal API (resolve, search, browse, player)
src/extract.py     pulling addresses, counts, links and search results out of payloads
src/enrich.py      following the creator's linked site, with the domain-match rule
src/scrape.py      the scraping logic, with no Apify dependency
src/main.py        the Apify layer only: input, charging, dataset writes
src/__main__.py    entry point, so `python -m src` works for both CLI and container
tools/             local runners and checks, not shipped behaviour
```

The split between `scrape.py` and `main.py` is deliberate. Because the scraping
logic imports nothing from the Apify SDK, it can be exercised against live
YouTube from a terminal with no account, no container and no platform run. Three
of the bugs listed below were found that way within minutes of writing the code.

## Running without Apify

```bash
python -m tools.local_check --handles @mkbhd @LinusTechTips
python -m tools.local_check --search "skincare routine" --per-query 10 --min-subs 10000
```

Prints one line per channel with the source and the address found, then the hit
rate and a breakdown by source.

## Checks

```bash
python -m tools.test_extract
```

Offline, no network, runs in about a second. Every case in it is a bug that was
once real against live channels, so it doubles as a regression record:

- JSON escapes glued to the local part, turning `>merch@x.com` into
  `u003emerch@x.com`
- a prefix-stripping heuristic added to fix the above, which turned
  `real@creator.com` into `eal@creator.com` and would have damaged any address
  starting with n, r or t
- platform addresses billed as finds: `no-reply@patreon.com`, `plus@shopify.com`,
  `public-schemaorg@w3.org`, `hello@tally.so`
- subscriber counts read from a recommended channel instead of the requested one,
  and a directional mark (`⁨`) whose escape ends in digits gluing onto the
  figure to produce `206821.4M`
- `subscriberCountText` in search results now carrying the `@handle` rather than
  a number

## Reproducing the figures in the README

```bash
python -m tools.measure_hitrate sample_channels.public.json out.json
```

Runs the actor's own `scrape_channel` over the 350-channel sample and prints the
hit rate, the breakdown by source, and the tables by niche and subscriber band.
The README numbers come from this command rather than from a one-off script, so
they can always be checked.

`sample_channels.public.json` holds the 350 channels with their niche labels
and subscriber counts. It deliberately carries no addresses: the addresses
found in the measurement belong to the creators, so they are not republished
here, and re-running the command finds them again from the public pages. Any file
with the same shape works: a list of objects carrying a `cid`, and optionally
`niche` and `subs`.

## Running as the actor

```bash
apify run --input '{"mode":"channels","channels":["@mkbhd"]}'
```

Needs the Apify CLI and a `.venv` with `requirements.txt` installed. In a local
run the SDK logs `Ignored attempt to charge for an event — the Actor does not
use the pay-per-event pricing`, which is expected: the charge call is made at the
right point, and the platform ignores it until pay-per-event is configured on the
published actor.

## Notes on the payloads

Extraction works by regex over the whole JSON text rather than by walking parsed
structures. YouTube reshapes its response objects often, while the string
literals being matched stay put. `innertube.call` re-serialises every response
with compact separators so patterns never have to tolerate stray whitespace —
forgetting that was the cause of two early failures where nothing matched at all.

Subscriber and video counts are read from the page header's `metadataParts`. The
About payload mentions "subscribers" dozens of times, once for every recommended
channel, so an unanchored search returns a different channel's figure.

## Dependency note

`requirements.txt` pins `apify~=4.2`. An earlier pin of `apify<3.0.0` resolved to
SDK 2.7.3, which fails at import against pydantic 2.14 with
`cannot specify both default and default_factory`.
