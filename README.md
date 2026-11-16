*A Portuguese version of this page (`README.pt.md`) ships with the source.*

# YouTube Channel Email Finder

Finds the business contact email published by YouTube channels, from a list of
channels or from a niche keyword. Billing applies only to channels where an
address is found.

Measured rate: **35.4% of channels yield an address** (124 of 350 sampled across
25 niches). That figure is published here, with its confidence intervals and the
method behind it, because the usual promise of "verified emails in bulk" tells a
buyer nothing about what a run will actually return.

## What it is for

- Building an outreach list for influencer or creator marketing, by niche
- Enriching an existing list of channels with contact details
- Sponsorship prospecting, filtered to a subscriber range
- Competitive research into which creators a category is reaching out to
- Feeding a CRM or a sheet through the API on a schedule

## What a run costs

$0.03 per channel that yields an address. Channels that come back empty are not
billed.

At the measured rate, 1,000 channels scanned return around 354 addresses and
cost about **$10.60**, which is $0.03 per usable address.

Several actors in this category bill per channel scanned instead. At $0.075 per
channel, 1,000 channels cost $75 and return around 117 addresses if only the
About tab is read — about $0.64 per usable address. The headline figure and the
real one diverge, and the gap is invisible until the run finishes.

Cheaper options do exist, and the comparison table further down names them.

## Where the addresses come from

Three sources, checked in order of cost, stopping at the first hit. A channel
that publishes its address in the About tab therefore costs a single request.

| Source | Channels with an address, cumulative |
|---|---|
| 1. The channel's About tab | 21.1% |
| 2. Descriptions of recent videos | 27.1% |
| 3. The creator's own website and its contact page | **35.4%** |

Source 2 exists because many creators put "business inquiries" in a video
description rather than in the About tab; it found addresses on 21 channels where
source 1 came up empty. Source 3 follows the link the channel itself publishes,
resolving shortened links, and checks the usual contact pages. It accounted for
another 29.

Both can be switched off with `scanVideoDescriptions` and
`enrichFromLinkedSite`, for a faster pass that reads only the About tab.

### Why 35% is the ceiling, not a starting point

Widening the public sources was tested on 80 channels that currently come back
empty: reading videos 3 through 8 instead of just the first two converted 1 of
them, and following link aggregators converted none. Projected over the whole
sample that is +0.8 points, for several times the requests.

Roughly two thirds of YouTube channels publish no reachable contact address
anywhere. That is a property of YouTube, and it is the reason billing is tied to
results rather than to channels scanned.

## How addresses belonging to someone else are excluded

A creator's website carries addresses that are not the creator's: the form
builder behind the contact page, the shop platform, a Patreon no-reply address,
occasionally a standards body quoted in the page markup. Under per-result
billing, each of those would appear as a billable find.

An address found on a linked site is kept only when its domain matches the site
it was found on, or when it belongs to a mailbox provider such as Gmail or
Outlook. `hello@tally.so` sitting on a dermatologist's website is a form builder,
not a contact, so it is dropped. The rule removes the category rather than
maintaining a list of names.

## What the measurements show

The type of niche matters more than anything else. Niches built around
sponsorship publish contact details, because they receive offers and want to be
reachable. Hobby and craft niches mostly do not.

| Type of niche | Channels with an address | 95% confidence |
|---|---|---|
| **Products, money, travel** — skincare, beauty, personal finance, real estate, travel, van life, pet care | 55/98 = **56%** | 46–66% |
| **Instructional and professional** — tech reviews, language learning, gardening, podcasts, cooking, chess | 30/84 = **36%** | 26–46% |
| **Hobby, craft and gaming** — woodworking, guitar, fitness, coffee, 3D printing, photography, drones, cars, meditation, gaming, knitting | 39/168 = **23%** | 17–30% |

Channel size separates less than might be expected, and really only at the
bottom of the range:

| Subscribers | Channels with an address | 95% confidence |
|---|---|---|
| 100K or more | 81/194 = 42% | 35–49% |
| 10K to 100K | 24/59 = 41% | 29–53% |
| under 10K | 18/84 = 21% | 14–31% |

The `minSubscribers` filter exists for this reason: a floor around 10,000 keeps a
run away from the part of the range where addresses are scarce.

### Why no per-niche figures appear here

The same 350 channels were measured twice during development, with two versions
of the extraction code. The overall rate barely moved, 35.1% to 35.4%. Individual
niches moved a great deal: van life 64% to 50%, gaming 7% to 29%, knitting 0% to
14%.

Each niche in that sample holds 14 channels, and at that size a result near 50%
carries a confidence interval about 45 points wide. "Van life: 64%" would mean
"somewhere between 39% and 84%", which is not precise enough to publish as
guidance. Grouped into the three families above the samples hold still: 56%, 36%
and 23% in the second run against 57%, 39% and 20% in the first.

The full 25-niche breakdown, both runs side by side with intervals, is in
[SAMPLE.md](https://github.com/MatheusOliveira-dev/youtube-channel-email-finder/blob/main/SAMPLE.md).

### Measuring a specific niche

Most niches are not in that sample, and a measurement of the real target is worth
more than any average published here. Since only found addresses are billed, a
pilot costs very little:

```json
{
  "mode": "search",
  "searchQueries": ["the niche in question"],
  "maxChannelsPerQuery": 50,
  "minSubscribers": 10000,
  "includeChannelsWithoutEmail": true
}
```

The run log closes with a line in the form
`scanned=50 with_email=19 hit_rate=38.0%`. That is the real rate for that niche,
and the empty channels listed in the dataset carry no charge.

## How long a run takes

Measured at concurrency 10, with all three sources enabled:

| Channels | Approximate time |
|---|---|
| 30 | under a minute |
| 100 | 1 to 2 minutes |
| 500 | 6 to 10 minutes |
| 1,000 | 12 to 20 minutes |

Channels that yield an address in the About tab finish in well under a second.
The time is spent on the ones that do not, since those trigger the video and
website lookups. A run with `scanVideoDescriptions` and `enrichFromLinkedSite`
switched off is roughly three times faster and finds roughly 40% fewer addresses.

The API endpoint `run-sync-get-dataset-items` has a 300-second limit, so runs
above about 300 channels suit the asynchronous endpoint or a schedule better.

## Input

Searching a niche:

```json
{
  "mode": "search",
  "searchQueries": ["skincare routine", "van life"],
  "maxChannelsPerQuery": 25,
  "maxChannels": 200,
  "minSubscribers": 10000
}
```

Working from an existing list. Channel URLs, `@handles` and raw `UC...` ids are
all accepted, and can be mixed:

```json
{
  "mode": "channels",
  "channels": [
    "@mkbhd",
    "https://www.youtube.com/@LinusTechTips",
    "UCBJycsmduvYEL83R_U4JriQ"
  ]
}
```

### Settings

| Field | Default | Effect |
|---|---|---|
| `mode` | `channels` | `channels` for an existing list, `search` to find them by keyword |
| `channels` | — | URLs, handles or ids |
| `searchQueries` | — | niche keywords, used in `search` mode |
| `maxChannelsPerQuery` | 20 | channels taken from each query |
| `maxChannels` | 100 | hard ceiling for the run, so a broad query cannot run away |
| `minSubscribers` | — | skips channels below this size |
| `maxSubscribers` | — | skips channels above it, for smaller creators |
| `scanVideoDescriptions` | `true` | source 2; runs only when the About tab came up empty |
| `enrichFromLinkedSite` | `true` | source 3; runs only when sources 1 and 2 came up empty |
| `includeChannelsWithoutEmail` | `false` | lists the empty channels too, showing everything checked. Never billed |
| `language` / `country` | `en` / `US` | affects which channels `search` returns |
| `concurrency` | 5 | parallel scans, 1 to 10 |

## Output

One row per channel. A real row from a search run:

```json
{
  "channelId": "UC9YAqNOtA38qIymbvf3o_aQ",
  "channelUrl": "https://www.youtube.com/channel/UC9YAqNOtA38qIymbvf3o_aQ",
  "title": "sasa",
  "subscribers": 696000,
  "subscribersText": "696K",
  "videoCountText": "149",
  "emails": ["sasa@starlinemgmt.com", "sasastudio25@gmail.com"],
  "primaryEmail": "sasa@starlinemgmt.com",
  "emailCount": 2,
  "emailSource": "about",
  "sourceUrl": null,
  "externalLinks": ["https://us.selflessbyhyram.com/"],
  "queryMatched": "skincare routine",
  "hasEmail": true
}
```

| Field | Contents |
|---|---|
| `channelId`, `channelUrl` | stable identifier and direct link |
| `title` | channel name |
| `subscribers` | integer, for sorting and filtering |
| `subscribersText` | the same figure as YouTube displays it |
| `videoCountText` | publishing volume, an indicator of an active channel |
| `emails` | every address found, business-style inboxes first |
| `primaryEmail` | the best candidate, for a single-column export |
| `emailCount` | how many were found |
| `emailSource` | `about`, `video_description` or `linked_site` |
| `sourceUrl` | for `linked_site`, the exact page it was read from |
| `externalLinks` | the creator's own links, affiliate and shortened links last |
| `queryMatched` | which query surfaced the channel |
| `hasEmail` | boolean, for quick filtering |

`emailSource` together with `sourceUrl` makes every result checkable against its
origin. In a product billed per result, that matters: it is possible to verify
what was charged.

## When something goes wrong

| Situation | Behaviour | Billed |
|---|---|---|
| No address found | Omitted from the dataset, or included with `hasEmail: false` when `includeChannelsWithoutEmail` is on | No |
| Outside the subscriber filter | Omitted, counted as `filtered` in the log | No |
| Network or parsing failure on one channel | Omitted, counted as `failed`, logged as a warning | No |
| Handle cannot be resolved | Logged as a warning, the run continues | No |
| `maxChannels` reached | Run stops at the ceiling | Only for addresses found |

The final log line always reports `scanned`, `with_email`, `hit_rate`,
`filtered` and `failed`, so a run that returns little can be told apart from a
run that went wrong.

## How this compares

Prices as listed on the Apify Store in November 2026, with each actor's own
charging event:

| Actor | Price | Charges for | Store rating |
|---|---|---|---|
| **This actor** | **$0.03** | channel with an address found | new |
| `haketa/youtube-contact-scraper` | $0.003 | dataset item | 5.0 (1 review) |
| `exporter24/youtube-email-bulk-scraper` | $0.03 | dataset item | 5.0 (3 reviews) |
| `automation-lab/…-email-scraper` | $0.023 + $0.0023 | address found, plus every channel processed | no reviews |
| `khadinakbar/…-email-extractor` | $0.05 + $0.12 | address found, plus a paid unlock | 3.0 (1 review) |
| `endspec/youtube-instant-email-scraper` | $0.075 | every channel parsed | 1.0 (2 reviews) |
| `creatorlens/social-media-email-scraper-2026` | $0.10 | address found | 1.41 (5 reviews) |
| `dataovercoffee/…-Business-Email-Scraper` | $0.12 | each email returned | 4.4 (30 reviews) |

Charging only for results is not unusual here, and this actor does not claim it
as an invention. `haketa` is ten times cheaper per item, and the category leader
has thirty reviews and a 4.4 rating.

What is specific to this one: the hit rate is measured and published with its
confidence intervals, the sources are documented and switchable, every address
carries the source it came from, and the niches where it performs badly are named
rather than omitted. Nothing here depends on taking a claim on trust.

## Questions

**Why do some channels come back empty?**
Around two thirds of channels publish no reachable address. Widening the search
was tested and converted 1 of 80 empty channels, so this is a ceiling rather than
something a setting can fix. Empty channels are not billed.

**Can it get the address behind the "View email address" button?**
No. That field is absent from anonymous responses: it requires a logged-in Google
session and solving a captcha. Supporting it would mean handling the session
credentials of whoever runs the actor, and working around a protection put in
place specifically to stop automated collection. Everything read here is
published openly by the channel.

**Are the addresses verified?**
No. They are returned exactly as published. A verification pass before a large
send is a sensible precaution.

**Does it need a proxy, a login or cookies?**
None of the three. 350 channels were scanned back to back without a block, which
is what keeps the cost per run low.

**How current is the data?**
Every run reads YouTube live. Nothing is cached or resold between runs.

**Can it run on a schedule?**
Yes, through Apify schedules, and results can be sent onward by webhook or to
Google Sheets, Slack, S3 and similar.

**How do the results get exported?**
The dataset exports as JSON, JSONL, CSV, XLSX, XML, HTML or RSS, from the Console
or the API, with `fields` to pick columns.

**Is this legal?**
The addresses are published by the creators themselves for business contact, and
only public channel data is read. Responsibility for use lies with whoever uses
them: bulk outreach falls under GDPR, CAN-SPAM and comparable rules depending on
jurisdiction.

**What happens if YouTube changes something?**
It reads YouTube's internal interface, so a change there can break it until it is
updated. The final log line makes a breakage obvious: the hit rate collapses
while `scanned` stays normal.

## Support

Issues go to the Issues tab on this actor's page, which is monitored. A report
that includes the run id and the input used is the fastest to act on. Breakage
after a YouTube change is treated as a priority.

---

Notes on the code, the local test tools and how to reproduce every figure above
are in [DEVELOPMENT.md](https://github.com/MatheusOliveira-dev/youtube-channel-email-finder/blob/main/DEVELOPMENT.md).
