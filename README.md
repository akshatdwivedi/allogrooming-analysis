# Allogrooming & Social Investigation After Repetitive TBI

Analysis pipeline for a behavioral study of allogrooming and social
investigation in mice following repetitive traumatic brain injury (TBI),
combining a 10-cage expansion cohort and a 5-cage pilot cohort scored from
BAnnotator video annotations.

## Start here

- **What each file/column means:** [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md)
- **Why the statistics are built this way:** [`docs/METHODS.md`](docs/METHODS.md)
- **Which videos were excluded and why:** [`docs/EXCLUSIONS.md`](docs/EXCLUSIONS.md)

## Getting the data

Raw `.mat` annotation files are not stored in this repository -- they're
hosted on a public data archive (Zenodo/Dryad; link added once the archive
entry is created, see the paper's data-availability statement). Download
them and point the pipeline at the resulting directories as described
below. `data/exclusions.csv`, `data/DATA_DICTIONARY.md`, and
`data/expansion_condition_map.json` and `data/pilot_condition_map.json` *are*
tracked here, since they're small and document the pipeline itself rather
than being the raw data. Both cohorts need their condition map -- neither
cohort's raw files are organized into TBI/sham subfolders, so
`01_parse_annotations.py` cannot infer `condition` from the folder
structure for either one (verified against the expansion cohort's real raw
data; this repo's docs briefly, incorrectly, assumed otherwise).

## Reproducing the analysis end-to-end

```bash
pip install -r requirements.txt

EXPANSION_RAW=/path/to/expansion/mat/files \
PILOT_RAW=/path/to/pilot/mat/files \
scripts/run_pipeline.sh
```

This runs every stage in order and writes results to `results/tables/`:

| Stage | Script | What it does |
|---|---|---|
| 1 | `scripts/01_parse_annotations.py` | Raw `.mat` -> per-video frame counts and bout lists |
| 2 | `scripts/02_resolve_duplicates_and_exclude.py` | Applies `data/exclusions.csv`; refuses to run if it finds an unresolved duplicate video the table doesn't cover |
| 3 | `scripts/03_winsorize.py` | Caps outlier values at Tukey's fence, per condition, consistently -- never deletes a row |
| 4 | `scripts/04_fit_models.py` | Fits the negative binomial GEE model (cage-clustered, bias-corrected SEs) and reports incidence rate ratios |

Each script can also be run on its own (see its `--help` / module
docstring) -- `run_pipeline.sh` is just the documented, re-runnable chain
connecting them, so "how was this number produced" always has a literal
answer.

## Visualization

`scripts/plot_raster.py` and `scripts/plot_cumulative.py` produce the
frame-by-frame raster plots and cumulative behavior-time figures from the
bout-level and metrics CSVs produced in stage 1.

## Validation

- `tests/test_parsing_ground_truth.py` -- builds synthetic `.mat` files with
  hand-computed, exactly-known answers (including edge cases: a bout
  running to the last frame, two separate bouts of the same behavior, a
  zero-count behavior, single-frame bouts) and checks stage 1's output
  against them exactly. No code from `scripts/` is used to compute the
  expected answer.
- `tests/generate_synthetic_data.py` + `tests/coverage_check.py` -- Monte
  Carlo validation of the statistical model itself: simulates data with a
  planted, known true effect and checks how often the model's 95%
  confidence intervals actually contain it (this is what motivated the
  `bias_reduced` correction in stage 4).

Run either with `python tests/<name>.py`.
