"""
Sensitivity/robustness checks that sit alongside the primary negative
binomial GEE model (04_fit_models.py), formalized here as committed,
re-runnable code rather than one-off analysis that only ever existed in a
chat session.

Two subcommands:

  truncate      Re-derive per-video behavior counts from the raw .mat files,
                capping every video at a common frame-count window (to rule
                out video-length differences as a confound), and write a
                metrics_by_file-style CSV comparable to 01_parse_annotations
                .py's output -- feed this into 02_resolve_duplicates_and_
                exclude.py / 03_winsorize.py / 04_fit_models.py exactly like
                the untruncated pipeline.

  nonparametric Run Mann-Whitney U and Kruskal-Wallis H on a cleaned CSV
                (the output of 02/03), as an assumption-light corroboration
                of the GEE model. Also runs Kruskal-Wallis across days
                within each condition, a genuine 3+ group use of the test.

Usage:
    python 05_sensitivity_checks.py truncate <raw_dir> --cutoff-frames 34078 \
        --out ../data/interim/pilot_truncated_metrics_by_file.csv

    python 05_sensitivity_checks.py nonparametric clean_combined.csv \
        --outcome allogrooming
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu

FPS = 30.0
DAY_RE = re.compile(r"day\s*(\d+)", re.IGNORECASE)
CAGE_RE = re.compile(r"cage\s*0*(\d+)", re.IGNORECASE)


def load_raw_codes(mat_path):
    """Minimal, self-contained .mat loader (can't `import 01_parse_annotations`
    -- a leading digit makes it an invalid Python module name)."""
    import scipy.io as sio
    d = sio.loadmat(mat_path, struct_as_record=False, squeeze_me=True)
    ann = d["annotation"]
    beh = ann.behaviors
    name_to_code = {name: int(getattr(beh, name)) for name in beh._fieldnames}
    codes = np.asarray(ann.annotation, dtype=float)
    return codes, name_to_code


def cmd_truncate(args):
    # Two distinct, previously-used truncation policies for videos SHORTER
    # than --cutoff-frames -- you can't pad missing data, so something has
    # to give, and which one is correct depends on what the check is for:
    #   "keep"    (default): leave the short video at its own full length.
    #              Used for the 18.93-min pilot-only sensitivity check,
    #              whose purpose is capping videos that ran LONG (notably
    #              pilot Cage 2/Day 4), not equalizing every video's length.
    #   "exclude": drop any video below --min-frames-ratio of the cutoff
    #              entirely. Used for the 20-min common-window check (the
    #              Mann-Whitney/Kruskal-Wallis and raster-plot analyses),
    #              where every video needs to genuinely reach the same
    #              length for the comparison to be fair.
    # Re-deriving this script against real data (not just memory) is what
    # surfaced that these two prior analyses actually used different
    # policies here -- hardcoding one silently would have reproduced only
    # one of the two previously reported truncation results.
    raw_dir = Path(args.raw_dir)
    rows = []
    too_short = []
    for mat_path in sorted(raw_dir.rglob("*.mat")):
        if "__MACOSX" in str(mat_path) or mat_path.name.startswith("._"):
            continue
        codes, name_to_code = load_raw_codes(mat_path)
        day_m = DAY_RE.search(mat_path.parent.name) or DAY_RE.search(mat_path.name)
        cage_m = CAGE_RE.search(mat_path.name)
        if day_m is None or cage_m is None:
            raise SystemExit(f"Could not parse day/cage from {mat_path}")
        day, cage = int(day_m.group(1)), int(cage_m.group(1))

        total_frames = len(codes)
        if args.on_short_video == "exclude" and total_frames < args.min_frames_ratio * args.cutoff_frames:
            too_short.append((mat_path.name, total_frames))
            continue
        used_frames = min(total_frames, args.cutoff_frames)
        truncated = codes[:used_frames]

        row = {"file": mat_path.name, "day": day, "cage": cage,
               "total_frames": total_frames, "used_frames": used_frames}
        for behavior, code in name_to_code.items():
            row[behavior] = int(np.sum(truncated == code))
        rows.append(row)

    if too_short:
        print(f"Excluded {len(too_short)} video(s) too short to fill the "
              f"{args.cutoff_frames}-frame window (below "
              f"{args.min_frames_ratio:.0%} of it): {too_short}")

    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} truncated rows (window = {args.cutoff_frames} frames, "
          f"{args.cutoff_frames / FPS / 60:.2f} min) to {args.out}")


def cmd_nonparametric(args):
    df = pd.read_csv(args.csv)
    outcome = args.outcome

    print(f"=== Mann-Whitney U / Kruskal-Wallis H: TBI vs. sham, {outcome} ===")
    tbi = df.loc[df.condition == "TBI", outcome]
    sham = df.loc[df.condition == "sham", outcome]
    u, p_mwu = mannwhitneyu(tbi, sham, alternative="two-sided")
    h, p_kw = kruskal(tbi, sham)
    print(f"TBI n={len(tbi)} median={tbi.median():.1f}   sham n={len(sham)} median={sham.median():.1f}")
    print(f"Mann-Whitney U={u:.1f}  p={p_mwu:.4g}")
    print(f"Kruskal-Wallis H={h:.3f}  p={p_kw:.4g}  (2 groups -- same question as Mann-Whitney, as a check)")

    if "day" in df.columns:
        print(f"\n=== Kruskal-Wallis across days, within each condition, {outcome} ===")
        for cond in sorted(df.condition.unique()):
            sub = df[df.condition == cond]
            groups = [sub.loc[sub.day == d, outcome] for d in sorted(sub.day.unique())]
            if len(groups) < 2:
                continue
            h, p = kruskal(*groups)
            medians = [round(g.median(), 1) for g in groups]
            print(f"{cond:5s}  H={h:.3f}  p={p:.4g}  day medians: {medians}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    t = sub.add_parser("truncate")
    t.add_argument("raw_dir", type=Path)
    t.add_argument("--cutoff-frames", type=int, required=True)
    t.add_argument("--on-short-video", choices=["keep", "exclude"], default="keep",
                   help="'keep' (default): leave videos shorter than --cutoff-frames at their own full "
                        "length. 'exclude': drop them entirely if below --min-frames-ratio of the cutoff.")
    t.add_argument("--min-frames-ratio", type=float, default=0.9,
                   help="Only used with --on-short-video=exclude (default 0.9)")
    t.add_argument("--out", type=Path, required=True)
    t.set_defaults(func=cmd_truncate)

    n = sub.add_parser("nonparametric")
    n.add_argument("csv", type=Path)
    n.add_argument("--outcome", required=True)
    n.set_defaults(func=cmd_nonparametric)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
