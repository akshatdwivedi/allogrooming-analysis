"""
Fit the models used for the allogrooming/investigation results summary:
a Gaussian linear mixed model (for comparison) and a negative binomial GEE
(the model actually reported), both with cage as the clustering/random-effect
variable.

Input CSV must have columns: cage, day, condition ("TBI"/"sham"), and the
outcome columns to model (e.g. allogrooming, investigation), one row per
video/cage/day.

Usage:
    python fit_models.py clean_data.csv --outcome allogrooming
    python fit_models.py clean_data.csv --outcome investigation --interaction
"""
import argparse

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import NegativeBinomial
from statsmodels.genmod.generalized_estimating_equations import GEE


def fit_gaussian_lmm(df, outcome, interaction):
    formula = f'{outcome} ~ C(condition, Treatment("sham")) * day' if interaction \
        else f'{outcome} ~ C(condition, Treatment("sham")) + day'
    model = smf.mixedlm(formula, df, groups=df["cage"])
    return model.fit(reml=True)


def fit_negative_binomial_gee(df, outcome, interaction):
    formula = f'{outcome} ~ C(condition, Treatment("sham")) * day' if interaction \
        else f'{outcome} ~ C(condition, Treatment("sham")) + day'

    # Estimate the dispersion parameter (alpha) via MLE rather than assuming a
    # value -- this is what confirms real over-dispersion vs. a Poisson model.
    nb_mle = smf.negativebinomial(formula, df).fit(disp=False)
    alpha_hat = nb_mle.params["alpha"]

    family = NegativeBinomial(alpha=alpha_hat)
    gee = GEE.from_formula(formula, groups="cage", data=df,
                            cov_struct=Exchangeable(), family=family)
    result = gee.fit()
    return result, alpha_hat


def summarize_irr(result):
    irr = np.exp(result.params)
    ci = np.exp(result.conf_int())
    rows = []
    for term in result.params.index:
        rows.append({
            "term": term,
            "IRR": round(irr[term], 3),
            "ci_low": round(ci.loc[term, 0], 3),
            "ci_high": round(ci.loc[term, 1], 3),
            "p_value": result.pvalues[term],
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_csv")
    ap.add_argument("--outcome", required=True, help="Column name to model, e.g. allogrooming")
    ap.add_argument("--interaction", action="store_true",
                     help="Include day x condition interaction (fading/temporal question)")
    args = ap.parse_args()

    df = pd.read_csv(args.data_csv)
    df[args.outcome] = df[args.outcome].astype(int)
    print(f"n rows: {len(df)}, n cages: {df.cage.nunique()}")
    print(df.groupby("condition").cage.nunique())
    print()

    print("=== Gaussian linear mixed model ===")
    gauss = fit_gaussian_lmm(df, args.outcome, args.interaction)
    print(gauss.summary())
    print()

    print("=== Negative binomial (GEE, cage-clustered) ===")
    nb_result, alpha_hat = fit_negative_binomial_gee(df, args.outcome, args.interaction)
    print(f"MLE-estimated dispersion (alpha): {alpha_hat:.3f}")
    print(nb_result.summary())
    print()
    print("Incidence rate ratios:")
    print(summarize_irr(nb_result).to_string(index=False))


if __name__ == "__main__":
    main()
