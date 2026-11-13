# Combined Cohort Verification Against Real Raw Data

Run against the actual re-uploaded pilot cohort raw `.mat` files (29 files)
alongside the previously-verified expansion cohort data (56 files), through
the full committed pipeline end to end. This closes out the code audit:
every headline number in this project's prior reports is now confirmed
against real data and committed, re-runnable code, not reconstructed from
memory.

## Pilot cohort exclusions

`02_resolve_duplicates_and_exclude.py` ran against the real pilot data with
**zero unresolved-duplicate errors**: 29 raw rows -> 4 excluded (0
fighting-cage, 4 duplicate) -> 25 remaining, matching the documented counts
exactly. `data/exclusions.csv`'s pilot-cohort rows are confirmed correct.

Pilot Cage 2's full five-day trajectory (the video central to the whole
pilot-integration question) also matches exactly: Day 1-5 allogrooming =
176, 117, 2000, **5712**, 2836 frames.

## Combined dataset (15 cages: 9 TBI, 6 sham; 72 videos: 47 expansion + 25 pilot)

Winsorizing ran across every row (not just previously-flagged ones, per the
lesson from the expansion-only check) and found exactly the previously
reported 9 capped rows -- 5 TBI (fence 3402.9), 4 sham (fence 553.8) for
allogrooming; 1 TBI, 1 sham for investigation. No discrepancy here; this
one had already been applied correctly before.

| Scenario | Outcome | IRR | 95% CI | p | Matches prior report? |
|---|---|---|---|---|---|
| Pre-Winsorization | Allogrooming | 3.084 | [0.690, 13.782] | 0.1403 | Yes, exactly |
| Post-Winsorization | Allogrooming | 7.592 | [2.856, 20.179] | 4.82e-05 | Yes, exactly |
| Pre-Winsorization | Investigation | 1.456 | [1.197, 1.770] | 1.65e-04 | Yes, exactly |
| Post-Winsorization | Investigation | 1.456 | [1.200, 1.767] | 1.38e-04 | Yes, exactly |

## Status

Both cohorts' exclusion tables, the expansion-only model, and the combined
(pre- and post-Winsorization) model are now verified against real raw data
through the committed pipeline. The one correction from this audit is
recorded separately in `expansion_only_verification.md` (the expansion-only
Winsorized figure: 18.894, not the earlier 15.60).

Not yet re-verified against real data: the truncation-based sensitivity
analyses (18.93-min pilot window, 20-min common window) and the
Mann-Whitney U / Kruskal-Wallis checks, none of which are committed as
scripts yet (see docs/METHODS.md).
