"""
Monte Carlo coverage check: regenerate the synthetic dataset under many
random seeds (same generative model/ground truth as generate_synthetic_data.py,
same cage/day structure as the real study: 6 TBI cages, 4 sham cages, 5 days),
refit the real fit_models.py pipeline each time, and check how often the
planted true value falls inside the reported 95% CI.

This answers: "is the discrepancy we saw in the single run a code bug, or
expected sampling variability given this many clusters?"
"""
import numpy as np
import pandas as pd
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import NegativeBinomial
from statsmodels.genmod.generalized_estimating_equations import GEE
import statsmodels.formula.api as smf

N_SIMS = 200
CAGES = {"TBI": [101, 102, 103, 104, 105, 106], "sham": [201, 202, 203, 204]}  # matches real study: 6 TBI / 4 sham
DAYS = [1, 2, 3, 4, 5]
BASE_ALLO = 60.0
TBI_RATIO = 10.0
DAY_DECAY = 0.80
CAGE_ALPHA = 0.3


def simulate_one(seed):
    rng = np.random.default_rng(seed)
    rows = []
    for condition, cage_list in CAGES.items():
        for cage in cage_list:
            k = 1.0 / CAGE_ALPHA
            cage_mult = rng.gamma(shape=k, scale=1.0 / k)
            for day in DAYS:
                rate = BASE_ALLO * (TBI_RATIO if condition == "TBI" else 1.0) * (DAY_DECAY ** (day - 1)) * cage_mult
                n_allo = rng.poisson(rate)
                rows.append({"cage": cage, "day": day, "condition": condition, "allogrooming": n_allo})
    return pd.DataFrame(rows)


def fit_one(df):
    nb_mle = smf.negativebinomial('allogrooming ~ C(condition, Treatment("sham")) + day', df).fit(disp=False)
    alpha_hat = nb_mle.params["alpha"]
    fam = NegativeBinomial(alpha=alpha_hat)
    gee = GEE.from_formula('allogrooming ~ C(condition, Treatment("sham")) + day', groups="cage",
                            data=df, cov_struct=Exchangeable(), family=fam)
    return gee.fit()


condition_term = 'C(condition, Treatment("sham"))[T.TBI]'
covered_condition = 0
covered_day = 0
irrs = []
for seed in range(N_SIMS):
    df = simulate_one(seed)
    try:
        result = fit_one(df)
    except Exception:
        continue
    irr = np.exp(result.params)
    ci = np.exp(result.conf_int())
    lo_c, hi_c = ci.loc[condition_term, 0], ci.loc[condition_term, 1]
    lo_d, hi_d = ci.loc["day", 0], ci.loc["day", 1]
    covered_condition += int(lo_c <= TBI_RATIO <= hi_c)
    covered_day += int(lo_d <= DAY_DECAY <= hi_d)
    irrs.append({"seed": seed, "irr_condition": irr[condition_term], "irr_day": irr["day"]})

irr_df = pd.DataFrame(irrs)
n = len(irr_df)
print(f"Completed {n}/{N_SIMS} simulated datasets (6 TBI cages / 4 sham cages / 5 days each, matching the real study's cluster count)")
print()
print(f"True condition IRR = {TBI_RATIO}, true day IRR = {DAY_DECAY}")
print()
print(f"95% CI coverage for condition effect: {covered_condition}/{n} = {100*covered_condition/n:.1f}%  (nominal target: 95%)")
print(f"95% CI coverage for day effect:       {covered_day}/{n} = {100*covered_day/n:.1f}%  (nominal target: 95%)")
print()
print("Distribution of recovered condition IRR across simulations:")
print(irr_df["irr_condition"].describe())
print()
print("Distribution of recovered day IRR across simulations:")
print(irr_df["irr_day"].describe())
irr_df.to_csv("./tests/synthetic_data/coverage_check.csv", index=False)
