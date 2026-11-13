"""
Winsorize one or more outcome columns using Tukey's fence (Q3 + 1.5*IQR),
computed separately within each group (by default, condition), and cap any
value exceeding its group's fence at that fence value.

This is the single, consistently-applied rule behind every "corrected"
number reported for the combined pilot+expansion dataset: no observation is
ever dropped, and the same formula is applied to every video in a group, not
selectively to whichever one happens to be inconvenient.

Usage:
    python 03_winsorize.py clean_combined.csv --columns allogrooming,investigation \
        --out ../data/processed/combined_winsorized.csv
"""
import argparse
from pathlib import Path

import pandas as pd


def tukey_fence(series):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q3 + 1.5 * iqr


def winsorize(df, column, group_col):
    df = df.copy()
    # The Tukey fence is generally fractional (e.g. 16.125), so the outcome
    # column must be float before any value gets capped at it -- otherwise
    # assigning a fractional cap into an integer frame-count column either
    # crashes (recent pandas) or silently truncates it (older pandas), the
    # latter being the more dangerous failure mode.
    df[column] = df[column].astype(float)
    capped_col = f"{column}_capped"
    fence_col = f"{column}_fence"
    df[capped_col] = False
    df[fence_col] = float("nan")
    for group_value, idx in df.groupby(group_col).groups.items():
        fence = tukey_fence(df.loc[idx, column])
        over = idx[df.loc[idx, column] > fence]
        df.loc[idx, fence_col] = fence
        df.loc[over, capped_col] = True
        df.loc[over, column] = fence
        print(f"  {column} / {group_col}={group_value}: fence={fence:.1f}, "
              f"capped {len(over)} of {len(idx)}")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clean_csv", type=Path)
    ap.add_argument("--columns", required=True, help="Comma-separated outcome columns to Winsorize")
    ap.add_argument("--group-by", default="condition", help="Column defining the fence group (default: condition)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.clean_csv)
    columns = [c.strip() for c in args.columns.split(",")]

    print(f"Winsorizing {len(df)} rows, fences computed within each '{args.group_by}' group:")
    for col in columns:
        df = winsorize(df, col, args.group_by)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    n_capped_any = df[[f"{c}_capped" for c in columns]].any(axis=1).sum()
    print(f"\nWrote {len(df)} rows to {args.out} ({n_capped_any} row(s) capped on at least one column)")


if __name__ == "__main__":
    main()
