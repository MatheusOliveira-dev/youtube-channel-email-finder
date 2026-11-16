# Per-niche sample data

The full 25-niche breakdown from the development sample. It sits here rather than
in the README because **the per-niche numbers are not reliable enough
to make decisions on**. They are shown here, with the reasoning, rather than
quietly left out.

Each niche was sampled with 14 channels. The same 350 channels were measured
twice during development: once with an earlier version of the extraction code,
once with the final version. The overall hit rate barely moved, from 35.1% to
35.4%. The individual niches did not hold nearly as still.

| Niche | Run 1 | Run 2 | Run 2, 95% confidence |
|---|---|---|---|
| personal finance investing | 8/14 = 57% | 9/14 = 64% | 39–84% |
| travel vlog | 8/14 = 57% | 9/14 = 64% | 39–84% |
| beauty makeup tutorial | 7/14 = 50% | 8/14 = 57% | 33–79% |
| pet care dogs | 8/14 = 57% | 8/14 = 57% | 33–79% |
| skincare routine | 9/14 = 64% | 8/14 = 57% | 33–79% |
| tech review gadgets | 6/14 = 43% | 7/14 = 50% | 27–73% |
| van life | 9/14 = 64% | 7/14 = 50% | 27–73% |
| fitness workout | 4/14 = 29% | 6/14 = 43% | 21–67% |
| language learning | 6/14 = 43% | 6/14 = 43% | 21–67% |
| woodworking projects | 4/14 = 29% | 6/14 = 43% | 21–67% |
| real estate investing | 7/14 = 50% | 6/14 = 43% | 21–67% |
| chess strategy | 5/14 = 36% | 6/14 = 43% | 21–67% |
| gaming walkthrough | 1/14 = 7% | 4/14 = 29% | 12–55% |
| gardening tips | 6/14 = 43% | 4/14 = 29% | 12–55% |
| coffee brewing | 4/14 = 29% | 4/14 = 29% | 12–55% |
| podcast interview | 5/14 = 36% | 4/14 = 29% | 12–55% |
| home cooking recipes | 5/14 = 36% | 3/14 = 21% | 8–48% |
| photography tutorial | 3/14 = 21% | 3/14 = 21% | 8–48% |
| car review | 3/14 = 21% | 3/14 = 21% | 8–48% |
| guitar lessons | 4/14 = 29% | 3/14 = 21% | 8–48% |
| drone footage | 3/14 = 21% | 3/14 = 21% | 8–48% |
| knitting crochet | 0/14 = 0% | 2/14 = 14% | 4–40% |
| 3d printing | 4/14 = 29% | 2/14 = 14% | 4–40% |
| productivity tips | 3/14 = 21% | 2/14 = 14% | 4–40% |
| meditation mindfulness | 1/14 = 7% | 1/14 = 7% | 1–31% |

## What this table shows

The same channels, measured twice, moved by up to 21 percentage points on a single
niche (gaming walkthrough). Several swung 14 to 22 points in either direction,
some up and some down. That pattern — movement in both directions, with a stable total —
is sampling noise, not a change in the underlying thing being measured.

With n = 14, a result near 50% carries a confidence interval roughly 45 points
wide. Pinning a single niche down to plus or minus 10 points would take about 96
channels in that niche, which across 25 niches is 2,400 channels — and most
target niches would still fall outside the list.

The README therefore groups these into three families, where the samples are
large enough to be stable:

| Family | Run 1 | Run 2 |
|---|---|---|
| Products, money, travel | 57% (56/98) | 56% (55/98) |
| Instructional and professional | 39% (33/84) | 36% (30/84) |
| Hobby, craft and gaming | 20% (34/168) | 23% (39/168) |

Those moved 1 to 3 points between runs, which is what a usable measurement looks
like.

## Measuring a specific niche instead

A pilot of 50 channels from the niche in question, with
`includeChannelsWithoutEmail: true`, reports the real rate in the final line of
the run log. Only the addresses found are billed, so the empty channels in that
pilot carry no charge. That figure describes the niche better than this entire
table.
