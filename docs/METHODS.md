# Statistical Methods, Plain-Language Version

This explains *why* the pipeline is built the way it is, for anyone
(including a future version of ourselves) who needs the reasoning without
re-deriving it from the code. A more formal version of this belongs in the
paper's Methods section; this document is the "show your work" companion.

## Why not a t-test or ANOVA

Each cage is observed repeatedly (once per day across the week). Those
repeated measurements from the same cage are not independent of each
other -- a cage that grooms a lot tends to do so consistently across its
days. A t-test, or ANOVA of any kind (including repeated-measures ANOVA),
assumes either full independence between observations or a normally
distributed, evenly-spread-out outcome. Our outcome (frames of a behavior
per video) is a skewed count that can be exactly zero, which breaks the
normality assumption outright -- a plain linear mixed model fit to this
data predicts a mathematically impossible negative amount of behavior for
one group, which is the model directly telling us it doesn't fit.

## What we use instead: negative binomial regression with cage-level clustering (GEE)

Negative binomial regression is built for over-dispersed, zero-inflated
count data like ours. Fitting it with GEE (Generalized Estimating
Equations), with cage as the clustering variable, means the model is
explicitly told which measurements belong together, rather than treating
every video as an independent animal. The sample size that actually drives
how confident we can be is the number of cages, not the number of videos.
The reported effect size is an incidence rate ratio (IRR): an IRR of 7.6
means TBI cages show the behavior at 7.6x the rate of sham cages, holding
day constant.

`04_fit_models.py` estimates the negative binomial dispersion parameter
(alpha) first, via an ordinary (non-clustered) maximum-likelihood fit, then
plugs that fixed value into the clustered GEE model. This two-step approach
is standard practice for NB-GEE (joint estimation of dispersion and
correlation parameters isn't well established) and was cross-checked
against an independent R implementation (`glm.nb`) during the code audit --
both gave the identical dispersion estimate to four decimal places.

## The bias_reduced correction

With few clusters (as few as 5 cages in the pilot-only scenarios), GEE's
default uncertainty estimate tends to be overconfident. This was confirmed
directly by simulation (`tests/coverage_check.py`): at cluster counts
matching this study, nominal 95% confidence intervals only achieved 87-89%
actual coverage under the default estimator. `04_fit_models.py` therefore
fits with `cov_type="bias_reduced"` (the Mancl-DeRouen/Fay-Graubard
small-sample correction) everywhere -- this widens confidence intervals to
their honest width without changing the point estimate (the IRR) at all.

## Outlier handling: Winsorizing, not deletion

When one video's value is extreme, deleting it outright is hard to defend
-- it looks like (and can become) cherry-picking, especially if the
decision to exclude is made after seeing that it changes the result. The
defensible alternative is Winsorizing (`03_winsorize.py`): cap any value
beyond a pre-specified, fixed rule (Tukey's fence: Q3 + 1.5*IQR) at that
fence, applied to every video in the relevant group, not selectively to the
inconvenient one. No data point is ever deleted under this rule -- extreme
values are capped, and exactly which rows were capped is recorded
(`<column>_capped`) rather than hidden.

## Sensitivity and robustness checks

Beyond the primary model, this project ran several independent checks, all
converging on the same conclusion for the behaviors they tested:

- **Video-length truncation**: cutting every video to a common duration
  before modeling, to rule out video-length differences (the pilot cohort
  ranges 6-24 minutes; the expansion cohort is uniform) as a confound.
- **Mann-Whitney U / Kruskal-Wallis H**: rank-based tests with no
  distributional assumptions, as a sanity check against the parametric GEE
  model (though these treat each video as independent, which the repeated-
  measures design violates -- they're corroborating evidence, not a
  replacement for the clustered model).
- **Cross-language cross-check**: the NB dispersion estimate and the
  mean-model/clustering mechanics were independently re-implemented in R
  (`glm.nb`, `geepack`) during the code audit and matched the Python
  pipeline's results.

## Known limitation

R's two most common GEE packages (`gee`, `geepack`) do not support an
arbitrary negative-binomial variance family out of the box -- both are
restricted to a short hardcoded list of standard families. A true NB-vs-NB
cross-language comparison was not possible for that reason; the Poisson-GEE
comparison used instead still validates the mean-model specification and
clustering mechanics, which is where a genuine coding error would most
likely show up.
