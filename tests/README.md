# Synthetic validation

These scripts check the analysis pipeline against data whose ground truth is
known, rather than real annotations.

- `generate_synthetic_data.py` -- writes a small set of BAnnotator-format
  `.mat` files (8 cages, 5 days) with a planted allogrooming/investigation
  effect, using the real `.mat` struct layout so `scripts/analyze_annotations.py`
  parses them completely unmodified. Ground truth (the true rates/ratios used
  to generate the data) is saved to `synthetic_data/ground_truth.json`.

- `coverage_check.py` -- Monte Carlo check (200 simulated datasets, same
  cluster count as the real study: 6 TBI cages / 4 sham cages / 5 days) of
  whether `scripts/fit_models.py`'s 95% CIs actually contain the true planted
  value at the advertised rate. Answers: are point estimates unbiased, and are
  the reported confidence intervals trustworthy at this sample size?

Run:

```
python tests/generate_synthetic_data.py
python scripts/analyze_annotations.py tests/synthetic_data/data --out tests/synthetic_data/metrics.csv
# merge in tests/synthetic_data/ground_truth.json's condition labels by file, then:
python scripts/fit_models.py <merged_csv> --outcome allogrooming

python tests/coverage_check.py
```

## Findings (as of the last run)

- Both the `.mat` parsing and the negative binomial GEE model correctly
  recover planted effects on average: across 200 simulated datasets, the mean
  recovered condition IRR was 10.54 against a true value of 10.0, and the day
  IRR was 0.801 against a true 0.80 -- no evidence of a bug or systematic bias
  in either the parsing code or the modeling code.
- However, with only 10 cage clusters (matching the real study), the
  **condition (between-cage) effect is highly variable from sample to
  sample** -- individual simulated datasets recovered IRRs ranging from 3.8 to
  30.2 for a true value of 10. A single real dataset this size can easily land
  far from the population truth by chance, even with correct code.
- **95% CI coverage was 87% for the condition effect and 89% for the day
  effect** (both below the nominal 95%), meaning the GEE sandwich-estimator
  confidence intervals are somewhat anti-conservative (too narrow) at this
  cluster count. The real study's reported condition effect (IRR=17.75, 95%
  CI [7.48, 42.14]) should be read as "a real, large, correctly-signed effect"
  but with the true population magnitude less tightly pinned down than the
  interval implies.
- By contrast, the **day (within-cage) effect is recovered with high
  precision** even at this cluster count, because it draws on repeated
  within-cage contrasts rather than a handful of between-cage comparisons.
