# Video Exclusions

Every video excluded from analysis is recorded as one row in
[`data/exclusions.csv`](../data/exclusions.csv), with a stated reason. This
document explains the two exclusion categories; the CSV is the source of
truth for *which* files, this is the explanation of *why*.

> **Provenance note:** this table was reconstructed from this project's
> analysis history (chat transcripts and prior working sessions) after the
> working environment that originally identified these files was reset and
> the scratchpad scripts that found them were lost. The filenames, days,
> cages, and reasons below are accurate to that record, but **have not yet
> been re-verified by re-running the exclusion logic against the raw
> directory listing**. Before this table is relied on for a final,
> submitted analysis, re-derive it from the raw data (see "How to verify
> this table" below) and confirm it matches.

## Category 1: `fighting_cage`

Cages 11 and 16 (expansion cohort) show persistent fighting/agonistic
contact across most or all of their observation days. Agonistic contact can
be visually similar to allogrooming and risks being miscoded into the
allogrooming or investigation categories, so both cages are excluded
entirely from the cumulative behavior analyses, on every day they appear,
rather than day-by-day.

## Category 2: `duplicate`

Some cage/day combinations have more than one `.mat` annotation file in the
raw data -- typically because a video was re-scored (a "final draft" or
"redo" file superseding an earlier pass) or because a backup copy was saved
under a different filename. Exactly one file is kept per (day, cage); the
other is recorded in `data/exclusions.csv` with the filename that was kept
instead, where that's known.

These are judgment calls, not something a simple automatic rule can fully
reconstruct (e.g. preferring filenames containing "final draft" correctly
resolves most cases, but at least one pilot cohort duplicate -- `Day1Cage5.mat`
vs. `day1cage5_annot_mat_RA.mat` -- was resolved by which file followed the
cohort's standard naming convention, not by an explicit "backup" tag). That is
exactly why this project stores the *resolved decision* as data
(`data/exclusions.csv`), rather than trying to encode the judgment as
automatic logic in `02_resolve_duplicates_and_exclude.py`. The script's job
is only to apply the table and to refuse to run if it finds an unresolved
duplicate the table doesn't cover (see `02_resolve_duplicates_and_exclude.py`'s
defensive check).

## How to verify this table

1. Run `01_parse_annotations.py` on the raw data directory for each cohort.
2. Run `02_resolve_duplicates_and_exclude.py` on the result.
3. If it exits with an "UNRESOLVED DUPLICATES" error, every pair it lists is
   a (day, cage) combination with more than one raw file that
   `data/exclusions.csv` doesn't yet resolve -- add a row for it.
4. If it completes without error, cross-check the printed exclusion counts
   (fighting-cage vs. duplicate) against the counts in this document and in
   `data/exclusions.csv` directly.
