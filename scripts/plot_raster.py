"""
Raster plots of allogrooming/investigation bouts (Figure 1 style): one
horizontal row per animal/video, colored segments for each bout, split into
one panel per condition (sham / TBI), one figure per day.

Usage:
    python plot_raster.py bouts.csv --out-dir figures/raster
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

COLORS = {"allogrooming": "tab:blue", "investigation": "tab:red"}


def plot_day(day_df, day, out_dir):
    conditions = [c for c in ("sham", "TBI") if c in day_df["condition"].unique()]
    if not conditions:
        return
    fig, axes = plt.subplots(1, len(conditions), figsize=(6 * len(conditions), 3), squeeze=False)
    axes = axes[0]
    for ax, condition in zip(axes, conditions):
        cond_df = day_df[day_df["condition"] == condition]
        files = sorted(cond_df["file"].unique())
        for row_idx, file in enumerate(files):
            file_df = cond_df[cond_df["file"] == file]
            for _, bout in file_df.iterrows():
                ax.barh(
                    row_idx,
                    bout["duration_sec"] / 60,
                    left=bout["start_sec"] / 60,
                    height=0.6,
                    color=COLORS.get(bout["behavior"], "gray"),
                )
        ax.set_yticks(range(len(files)))
        ax.set_yticklabels(files, fontsize=6)
        ax.set_xlabel("time (min)")
        ax.set_title(f"Day {day} - {condition}")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLORS.values()]
    fig.legend(handles, COLORS.keys(), loc="upper right")
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"day{day}_raster.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bouts_csv", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("figures/raster"))
    args = ap.parse_args()

    bouts_df = pd.read_csv(args.bouts_csv)
    for day, day_df in bouts_df.groupby("day"):
        plot_day(day_df, day, args.out_dir)
    print(f"Wrote raster plots to {args.out_dir}")


if __name__ == "__main__":
    main()
