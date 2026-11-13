# Manuscript Outline

Working skeleton for the paper. Each section below names what it needs to
say and, where applicable, which script or result file in this repo
supplies the evidence for it -- the goal is that nothing in the Results or
Methods section should ever need "trust me," only "see `scripts/X.py`" or
"see `results/tables/Y.md`."

Status markers: `[ ]` not started, `[~]` drafted from this repo's existing
analysis record, `[x]` written and checked against the cited source.

---

## Title (working)

*Repetitive mild TBI increases allogrooming and social investigation in
mice: a multi-cohort video-based behavioral analysis*

(Placeholder -- revisit once the Day 1 effect and the biological
interpretation in Discussion are settled.)

## Abstract

`[ ]` ~250 words. Write last, after Results and Discussion are stable.
Should state: the question, the two-cohort design, the primary model
(negative binomial GEE, cage-clustered), the headline effect sizes for
both behaviors, and the one-sentence caveat about the pilot cohort's
annotation scheme.

## 1. Introduction

`[ ]`
- TBI's effects on social behavior in rodent models; why allogrooming and
  social investigation are meaningful, measurable readouts.
- The repetitive-injury model used here, and why repeated measurement
  (same cage, multiple days) is both a strength (power, within-subject
  trajectory) and a statistical complication (Methods 2.2).
- Gap this study addresses / what's novel about combining a pilot and an
  expansion cohort rather than treating them separately.
- Explicit aims/hypotheses.

## 2. Methods

### 2.1 Animals and injury model
`[ ]` TBI induction protocol, repeated-injury schedule, sham controls
(anesthetized but not injured), cage composition.

### 2.2 Behavioral testing and video acquisition
`[ ]` Testing paradigm, recording duration/frame rate (30 fps), what "one
observation" means (one cage, one day).

### 2.3 Behavioral annotation
`[ ]`
- BAnnotator, the five behavior categories (allogrooming, investigation,
  offensive/defensive fighting, other).
- Inter-rater reliability procedure and results -- cite the Cage 14/Day 5
  overlap-video kappa analysis (Fleiss' kappa = 0.614 across 4 raters,
  0.584 with the excluded rater included) as the model for how IRR is
  assessed; note whether more overlap videos get scored before submission
  (currently n=1 video checked this way).
- Note the pilot cohort predates the fighting categories, which is the
  root cause behind 3.3 below -- state this as a methods limitation, not
  just in Discussion.

### 2.4 Data quality control
`[x]` drafted directly from committed code:
- Duplicate-scoring resolution and the persistent-fighting cage exclusion
  (cages 11, 16): `data/exclusions.csv`, applied by
  `scripts/02_resolve_duplicates_and_exclude.py`. State the exact counts:
  expansion 56->47 (8 fighting-cage, 1 duplicate), pilot 29->25 (4
  duplicate, 0 fighting-cage) -- verified against real raw data, see
  `results/tables/combined_verification.md`.
- Outlier handling (Winsorizing): `scripts/03_winsorize.py`, Tukey's
  fence, applied per condition. State which analyses use it and which
  don't (expansion-only headline currently reported raw; recommend
  Winsorized, see 3.1 below).

### 2.5 Statistical analysis
`[x]` drafted from `docs/METHODS.md` -- turn that document's prose into
Methods-section register (less "we found," more "was used"):
- Why not t-test/ANOVA (non-independence + non-normal, zero-inflated
  counts).
- Negative binomial GEE, cage as clustering unit, exchangeable
  correlation, IRR as the effect-size metric.
- Two-step dispersion estimation (non-clustered MLE, then fixed in the
  GEE fit) -- cross-validated against an independent R implementation
  (`glm.nb`), matching to 4 decimal places.
- bias_reduced small-sample correction, motivated by the coverage
  simulation (`tests/coverage_check.py`: 87-89% actual vs. 95% nominal
  coverage under the default estimator at this study's cluster counts).
- Sensitivity analyses: video-length truncation and Winsorizing combined
  (`scripts/05_sensitivity_checks.py`), nonparametric corroboration
  (Mann-Whitney U, Kruskal-Wallis H).

### 2.6 Code and data availability
`[ ]` Link to the GitHub repo and the data archive (Zenodo/Dryad --
pending archive creation). State the reproducibility claim precisely:
"every exclusion, correction, and model fit reported here can be
reproduced by running `scripts/run_pipeline.sh` against the archived raw
data" -- only true once the pilot/expansion raw data is actually uploaded
to that archive, so don't write this section until that's done.

## 3. Results

### 3.1 Primary finding: expansion cohort
`[x]` IRR=17.755 (raw) or IRR=18.894 (Winsorized, recommended -- see
`results/tables/expansion_only_verification.md`) for allogrooming,
IRR=1.484 for investigation, both p<0.001. **Open decision before
writing this section**: report raw or Winsorized as the headline number?
Winsorized is more consistent with how every other cohort/scenario in
this project is handled, but changes the historical "17.75x" figure
you've shown your PI -- worth a conscious decision, not a silent swap.

### 3.2 Pilot cohort integration
`[x]`
- Investigation replicates cleanly (no cohort x condition interaction;
  pooling preserves significance).
- Allogrooming attenuates under naive pooling (p=0.1403) due to pilot
  Cage 2's Day 4 video; formal interaction test confirms a real
  cohort difference, not just noise.
- Three independent corrections (Winsorizing, 18.93-min truncation, both
  together) each restore significance at a consistent effect size
  (IRR 7.4-7.6x) -- state this convergence explicitly, it's the strongest
  evidence in the paper that the corrected number is right.
- Full table: `results/tables/combined_verification.md` and
  `results/tables/sensitivity_checks_verification.md`.

### 3.3 Robustness checks
`[x]` Mann-Whitney U / Kruskal-Wallis H corroborate the GEE model's
direction and significance for both behaviors (20-min common window,
n=71 videos). No significant day-to-day trend detected within either
condition, though both show a Day 1 peak worth noting as a candidate
novelty effect (see 3.4).

### 3.4 Exploratory: Day 1 effect and additional outlier screening
`[~]` New finding from the expansion-only Winsorizing re-check: three
sham-cohort videos, all Day 1, were independently flagged as outliers by
the same Tukey-fence rule (separate from the two filename-flagged
videos). Consider whether this belongs in Results (if treated as a
substantive finding) or stays a Methods/Discussion caveat (if treated as
a data-quality note). Decide before drafting.

## 4. Discussion

`[ ]`
- Biological interpretation: what does increased allogrooming/
  investigation after repetitive TBI suggest, in the context of existing
  literature on TBI and social behavior.
- Methodological contribution: the paper can reasonably claim a secondary
  contribution in *how* it validated its own pipeline (code audit,
  synthetic ground-truth tests, cross-language cross-check) -- worth a
  paragraph, especially for a methods-adjacent journal, but don't oversell
  it if targeting a pure behavioral-neuroscience venue.
- Limitations: pilot cohort's missing fighting category (the likely root
  cause of its one anomalous video); cage 10's incomplete day coverage in
  the expansion cohort (2 of 5 days only -- confirm this is a real data
  gap, not a parsing issue, before writing this); small cluster counts in
  the pilot-only analyses; the Day 1 effect noted in 3.4 being
  underpowered to confirm.
- Future directions: direct video re-review of the flagged videos
  (pilot Cage 2 Days 3-5, expansion Day4/Cage9, Day1/Cage13); expanding
  the cohort; formal IRR across more overlap videos.

## 5. Conclusion

`[ ]` Two or three sentences. Write last.

## Supplementary Material

`[~]`
- Full IRR/CI/p table across every scenario (already exists in
  `results/tables/`, needs reformatting for a supplement).
- Raster plots (per-day, per-condition, pilot/expansion divided) --
  regenerate from real data via `scripts/plot_raster.py` once the full
  cleaned+Winsorized combined dataset is rebuilt from the real raw files
  end to end (not yet done in this environment).
- Inter-rater reliability detail (Cage 14/Day 5 kappa breakdown).
- Code audit summary (synthetic parsing test, cross-language GEE
  cross-check) -- optional; depends on whether the target journal/reviewers
  would value this or see it as out of scope.

---

## Open decisions (yours, not mine)

1. **Raw vs. Winsorized as the expansion-only headline number** (3.1).
2. **Target journal** -- still "not yet decided" per our repo-structure
   conversation; revisit once Results/Discussion are drafted enough to
   judge fit (methods-heavy vs. straightforward behavioral-neuroscience
   venue).
3. **How much of the code-audit process to surface** in the paper itself
   vs. keeping it as repo documentation only (Supplementary Material, last
   bullet above).
4. **Cage 10's incomplete day coverage** -- confirm with the raw data
   whether this is a true data gap before deciding how (or whether) to
   footnote it.
