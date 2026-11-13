# Expansion-Only Verification Against Real Raw Data

Run against the actual re-uploaded expansion cohort raw `.mat` files
(56 files), through the committed pipeline (`01_parse_annotations.py` ->
`02_resolve_duplicates_and_exclude.py` -> `03_winsorize.py` ->
`04_fit_models.py`), not reconstructed from memory.

## Exclusion table verification

`02_resolve_duplicates_and_exclude.py` ran against the real data with
**zero unresolved-duplicate errors**: 56 raw rows -> 9 excluded (8
fighting-cage, 1 duplicate) -> 47 remaining. `data/exclusions.csv`'s
expansion-cohort rows are confirmed correct against the real raw file
listing.

## Raw (uncorrected) model result

Matches the previously reported headline number exactly:

| | |
|---|---|
| IRR | 17.755 |
| 95% CI | [5.829, 54.085] |
| p | 4.155e-07 |

## Correction: the Winsorized expansion-only number was wrong

A prior chat response recommended reporting the expansion-only allogrooming
effect as **15.60x (Winsorized)**, based on manually checking only the two
videos with suspicious filenames (Day4/Cage9 "aggressive allogrooming",
Day1/Cage13 "aggression mounting") against the TBI Tukey fence by hand.

Running `03_winsorize.py` -- which applies the fence to *every* row, not
just those two -- against the real data found **6 outlier rows**, not 1:

| File | Day/Cage | Condition | Capped on |
|---|---|---|---|
| Day1cage6_annotation.mat | 1/6 | sham | allogrooming |
| day1cage12_annotation_editedMAT.mat | 1/12 | sham | allogrooming |
| day1cage15 (1)_annotMAT.mat | 1/15 | sham | allogrooming |
| day1cage14 (1)_annotMAT.mat | 1/14 | TBI | allogrooming, investigation |
| day2cage7_annot_editedMAT.mat | 2/7 | TBI | allogrooming |
| Day4cage9_annotation_aggressive allogrooming.mat | 4/9 | TBI | allogrooming |

The correctly, consistently Winsorized result:

| | |
|---|---|
| IRR | **18.894** (supersedes the earlier 15.60 figure) |
| 95% CI | [7.156, 49.884] |
| p | 2.975e-09 |

Note the direction: Winsorizing here *increases* the point estimate rather
than decreasing it, because three sham-side outliers were also capped
downward, not just the TBI-side ones. The three sham outliers are all Day 1
and capped to nearly the same value -- plausibly a genuine Day 1 novelty
effect shared by both conditions, consistent with the day-decline pattern
noted elsewhere, rather than a scoring artifact. Worth a biological look,
not necessarily a data-quality concern the way Cage 9's video is.

## Still unverified

The pilot cohort's raw data has not yet been re-supplied to this
environment, so the pilot-side exclusions and the combined (pilot +
expansion) IRR/CI/p figures remain unverified against real data as of this
check -- they still rest on the reconstructed record only.
