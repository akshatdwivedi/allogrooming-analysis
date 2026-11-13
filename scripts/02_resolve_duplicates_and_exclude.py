"""
Apply the project's documented data-quality exclusions to a parsed
metrics_by_file.csv (the output of 01_parse_annotations.py), and resolve
duplicate videos down to exactly one authoritative file per cage/day.

This replaces what used to be ad hoc, unversioned cleanup code: every
exclusion applied here is a row in data/exclusions.csv, with a stated
reason, so the full raw-to-clean transformation is inspectable and
re-runnable rather than something that only ever existed in a chat session.

The pilot cohort's raw files are not organized into TBI/sham subfolders the
way the expansion cohort's are, so 01_parse_annotations.py cannot infer
`condition` for pilot rows from the folder path. Supply --condition-map for
any cohort where that's the case (a JSON file: {"<cage>": "TBI"|"sham"}).

Usage:
    python 02_resolve_duplicates_and_exclude.py metrics_by_file.csv \
        --cohort expansion --exclusions ../data/exclusions.csv \
        --out ../data/processed/expansion_clean.csv

    python 02_resolve_duplicates_and_exclude.py pilot_metrics_by_file.csv \
        --cohort pilot --exclusions ../data/exclusions.csv \
        --condition-map pilot_condition_map.json \
        --out ../data/processed/pilot_clean.csv
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def apply_condition_map(df, condition_map_path):
    mapping = json.loads(Path(condition_map_path).read_text())
    mapping = {int(k): v for k, v in mapping.items()}
    missing = set(df["cage"].unique()) - set(mapping)
    if missing:
        raise SystemExit(
            f"--condition-map is missing cages {sorted(missing)}; every cage "
            "must have a condition before exclusions/modeling can proceed."
        )
    df = df.copy()
    df["condition"] = df["cage"].map(mapping)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics_by_file_csv", type=Path)
    ap.add_argument("--cohort", required=True, help="Label matching the 'cohort' column in exclusions.csv")
    ap.add_argument("--exclusions", type=Path, required=True)
    ap.add_argument("--condition-map", type=Path, default=None,
                    help="JSON {cage: condition}, required for cohorts without TBI/sham subfolders (e.g. pilot)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.metrics_by_file_csv)

    if args.condition_map:
        df = apply_condition_map(df, args.condition_map)

    if df["condition"].isna().any():
        bad = df.loc[df["condition"].isna(), "file"].tolist()
        raise SystemExit(
            f"{len(bad)} row(s) have no condition and no --condition-map was given "
            f"to fill them in (e.g. {bad[:3]}). Refusing to silently drop or guess."
        )

    exclusions = pd.read_csv(args.exclusions)
    cohort_exclusions = exclusions[exclusions["cohort"] == args.cohort]
    excluded_files = set(cohort_exclusions["file"])

    before = len(df)
    df = df[~df["file"].isin(excluded_files)].copy()
    after = len(df)
    print(f"[{args.cohort}] {before} raw video rows -> {before - after} excluded "
          f"({(cohort_exclusions['category'] == 'fighting_cage').sum()} fighting-cage, "
          f"{(cohort_exclusions['category'] == 'duplicate').sum()} duplicate) -> {after} remaining")

    # Defensive check: after exclusion, every remaining (day, cage) pair must
    # map to exactly one file. If it doesn't, there's an unresolved duplicate
    # that data/exclusions.csv doesn't yet know about -- fail loudly rather
    # than silently averaging or picking one at random.
    dupe_groups = df.groupby(["day", "cage"]).filter(lambda g: len(g) > 1)
    if len(dupe_groups):
        print("UNRESOLVED DUPLICATES (not covered by data/exclusions.csv):", file=sys.stderr)
        print(dupe_groups[["file", "day", "cage", "condition"]].to_string(index=False), file=sys.stderr)
        raise SystemExit(
            "Refusing to proceed with unresolved duplicate (day, cage) pairs. "
            "Add a row to data/exclusions.csv for each one and re-run."
        )

    df.insert(0, "cohort", args.cohort)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} clean rows to {args.out}")


if __name__ == "__main__":
    main()
