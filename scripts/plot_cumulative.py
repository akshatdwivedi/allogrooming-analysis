"""
Daily cumulative plots (Figure 2 style): cumulative time spent per behavior
over the 20-min session, mean +/- SEM across animals, sham vs TBI, one
figure per day with two panels (investigation on top, allogrooming below).

Usage:
    python plot_cumulative.py bouts.csv --out-dir figures/cumulative
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

COLORS = {"sham": "black", "TBI": "tab:red"}
GROOM_COLORS = {"sham": "black", "TBI": "tab:blue"}
N_TIMEPOINTS = 200


def cumulative_curve(file_bouts, session_end_sec, n_points=N_TIMEPOINTS):
    t = np.linspace(0, session_end_sec, n_points)
    cum = np.zeros(n_points)
    for _, bout in file_bouts.iterrows():
        cum += np.clip(t - bout["start_sec"], 0, bout["duration_sec"])
    return t, cum


def plot_behavior_panel(ax, day_df, behavior, colors):
    beh_df = day_df[day_df["behavior"] == behavior]
    session_end = beh_df["end_sec"].max() if len(beh_df) else 1200.0
    for condition, color in colors.items():
        cond_df = beh_df[beh_df["condition"] == condition]
        files = cond_df["file"].unique()
        if len(files) == 0:
            continue
        curves = []
        for file in files:
            t, cum = cumulative_curve(cond_df[cond_df["file"] == file], session_end)
            curves.append(cum)
        curves = np.array(curves)
        mean = curves.mean(axis=0)
        sem = curves.std(axis=0, ddof=1) / np.sqrt(len(curves)) if len(curves) > 1 else np.zeros_like(mean)
        t_min = t / 60
        ax.plot(t_min, mean, color=color, label=condition)
        ax.fill_between(t_min, mean - sem, mean + sem, color=color, alpha=0.2)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("Time spent (sec)")
    ax.set_title(behavior)
    ax.legend()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bouts_csv", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("figures/cumulative"))
    args = ap.parse_args()

    bouts_df = pd.read_csv(args.bouts_csv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for day, day_df in bouts_df.groupby("day"):
        fig, (ax_inv, ax_groom) = plt.subplots(2, 1, figsize=(5, 7))
        plot_behavior_panel(ax_inv, day_df, "investigation", COLORS)
        plot_behavior_panel(ax_groom, day_df, "allogrooming", GROOM_COLORS)
        fig.suptitle(f"Day {day}")
        fig.tight_layout()
        fig.savefig(args.out_dir / f"day{day}_cumulative.png", dpi=150)
        plt.close(fig)
    print(f"Wrote cumulative plots to {args.out_dir}")


if __name__ == "__main__":
    main()
