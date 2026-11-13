# Data Dictionary

This describes every file and column produced by the pipeline in `scripts/`,
in the order they're created. Raw `.mat` files themselves are not stored in
this repository (see the top-level README for where to get them); everything
here is either a small, trackable metadata file or a description of data
that lives in `data/raw/`, `data/interim/`, or `data/processed/` on disk once
you've downloaded it.

## Raw annotation files (`data/raw/`, not committed)

One `.mat` file per video (one cage, one day). Produced by BAnnotator. Each
file contains a MATLAB struct `annotation` with:

| Field | Meaning |
|---|---|
| `stream_ID` | Identifier string for the video/recording |
| `annotation` | One integer code per video frame (30 fps), the scored behavior at that instant |
| `behaviors` | A struct mapping behavior name -> integer code **for this specific file**. This mapping is not guaranteed to be the same across files/raters -- always read it from the file itself, never assume a fixed order. |

Behavior names used throughout this project: `allogrooming`, `investigation`,
`offensive_fighting`, `defensive_fighting`, `other`.

## `metrics.csv` / `metrics_by_file.csv` (`data/interim/`, output of `01_parse_annotations.py`)

Long format (`metrics.csv`, one row per file x behavior) and wide format
(`metrics_by_file.csv`, one row per file):

| Column | Meaning |
|---|---|
| `file` | Source `.mat` filename |
| `day` | Observation day (1-5), parsed from the containing folder name |
| `condition` | `TBI` or `sham`, parsed from the containing folder name. **Not populated for cohorts without TBI/sham subfolders** (e.g. the pilot cohort) -- see `02_resolve_duplicates_and_exclude.py --condition-map`. |
| `cage` | Cage number, parsed from the filename |
| `behavior` (long format only) | Which behavior this row's counts are for |
| `frames` | Total frames scored as this behavior in this video |
| `seconds` | `frames / 30` |
| `pct_of_video` | `100 * frames / total_frames` |
| `total_frames`, `video_seconds` | Length of the full video |

## `data/exclusions.csv`

The complete, versioned record of which raw videos were excluded from
analysis and why. See `docs/EXCLUSIONS.md` for the full explanation;
columns are:

| Column | Meaning |
|---|---|
| `file` | Excluded filename (matches `metrics_by_file.csv`) |
| `day`, `cage`, `condition`, `cohort` | Identifying metadata |
| `category` | `fighting_cage` (persistent agonistic behavior contaminating the readout) or `duplicate` (a second annotation of the same cage/day, superseded by another file) |
| `kept_counterpart` | For duplicates, the filename that was kept instead (where known) |
| `rationale` | Plain-language reason for this specific exclusion |

## `*_clean.csv` (`data/processed/`, output of `02_resolve_duplicates_and_exclude.py`)

One row per video that survived exclusion, plus a `cohort` column
(`expansion` or `pilot`). Exactly one row per (`day`, `cage`) pair -- the
script refuses to produce output otherwise.

## `*_winsorized.csv` (`data/processed/`, output of `03_winsorize.py`)

Same as the clean data, with two additional columns per Winsorized outcome
column `<col>`:

| Column | Meaning |
|---|---|
| `<col>_fence` | The Tukey fence (Q3 + 1.5*IQR) computed for this row's group (default: its condition) |
| `<col>_capped` | `True` if this row's original value exceeded the fence and was capped down to it |

## Behavior counts as model inputs

`04_fit_models.py` treats a behavior count column (e.g. `allogrooming`) as
the outcome, `condition` and `day` (and any `--covariates`) as predictors,
and `cage` as the clustering variable. See `docs/METHODS.md` for why.
