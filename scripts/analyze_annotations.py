"""
Parse BAnnotator .mat annotation files (Day{N}/{TBI,sham}/*.mat) and compute
per-file behavior metrics: cumulative frames, time spent, and % of video for
every behavior category present in the file (allogrooming, investigation,
offensive_fighting, defensive_fighting, other, ...), plus bout lists for
raster/cumulative plotting.

Usage:
    python analyze_annotations.py <data_root> [--fps 30] [--out metrics.csv]

Outputs three files:
  - <out> (default metrics.csv): long format, one row per file x behavior.
  - <out>_by_file.csv: wide format, one row per file, one column per
    behavior's cumulative frame count -- the file-to-file comparison table.
  - <bouts-out> (default bouts.csv): one row per individual bout, for
    raster/cumulative plotting.

<data_root> is expected to contain subfolders named "Day1".."Day5" (or any
name containing "day" + a digit), each with two subfolders whose names
contain "tbi" and "sham" (case-insensitive), each holding *_annotation.mat
files.
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

# Fallback code->name map used only if a file's own behaviors struct is
# unreadable. Every file we've seen carries its own mapping, which is what
# get_behavior_map() reads.
DEFAULT_BEHAVIOR_MAP = {
    0: "allogrooming",
    1: "investigation",
    2: "offensive_fighting",
    3: "defensive_fighting",
    4: "other",
}


def load_annotation(mat_path):
    d = sio.loadmat(mat_path, struct_as_record=False, squeeze_me=True)
    ann = d["annotation"]
    codes = np.asarray(ann.annotation, dtype=float)
    return ann, codes


def get_behavior_map(ann):
    beh = ann.behaviors
    return {int(getattr(beh, name)): name for name in beh._fieldnames}


def bouts_for_code(codes, code, fps):
    """Return list of (start_sec, end_sec, duration_sec) for contiguous runs of `code`."""
    is_code = codes == code
    bouts = []
    start = None
    for i, flag in enumerate(is_code):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            bouts.append((start / fps, i / fps, (i - start) / fps))
            start = None
    if start is not None:
        bouts.append((start / fps, len(codes) / fps, (len(codes) - start) / fps))
    return bouts


def parse_file(mat_path, fps):
    ann, codes = load_annotation(mat_path)
    beh_map = get_behavior_map(ann)
    name_to_code = {v: k for k, v in beh_map.items()}
    n_frames = len(codes)
    video_seconds = n_frames / fps

    rows = []
    bouts_by_behavior = {}
    for behavior, code in name_to_code.items():
        n_behavior_frames = int(np.sum(codes == code))
        seconds = n_behavior_frames / fps
        pct = 100.0 * n_behavior_frames / n_frames
        rows.append(
            {
                "file": mat_path.name,
                "behavior": behavior,
                "frames": n_behavior_frames,
                "seconds": seconds,
                "pct_of_video": pct,
                "total_frames": n_frames,
                "video_seconds": video_seconds,
            }
        )
        bouts_by_behavior[behavior] = bouts_for_code(codes, code, fps)
    return rows, bouts_by_behavior


DAY_RE = re.compile(r"day\s*(\d+)", re.IGNORECASE)


def find_day_condition(mat_path, data_root):
    parts = mat_path.relative_to(data_root).parts
    day = None
    condition = None
    for p in parts:
        m = DAY_RE.search(p)
        if m:
            day = int(m.group(1))
        low = p.lower()
        if "tbi" in low:
            condition = "TBI"
        elif "sham" in low:
            condition = "sham"
    return day, condition


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_root", type=Path)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--out", type=Path, default=Path("metrics.csv"))
    ap.add_argument("--bouts-out", type=Path, default=Path("bouts.csv"))
    args = ap.parse_args()

    mat_files = sorted(args.data_root.rglob("*.mat"))
    if not mat_files:
        raise SystemExit(f"No .mat files found under {args.data_root}")

    all_rows = []
    all_bout_rows = []
    for mat_path in mat_files:
        day, condition = find_day_condition(mat_path, args.data_root)
        rows, bouts_by_behavior = parse_file(mat_path, args.fps)
        for row in rows:
            row["day"] = day
            row["condition"] = condition
            all_rows.append(row)
        for behavior, bouts in bouts_by_behavior.items():
            for start_s, end_s, dur_s in bouts:
                all_bout_rows.append(
                    {
                        "file": mat_path.name,
                        "day": day,
                        "condition": condition,
                        "behavior": behavior,
                        "start_sec": start_s,
                        "end_sec": end_s,
                        "duration_sec": dur_s,
                    }
                )

    metrics_df = pd.DataFrame(all_rows)
    bouts_df = pd.DataFrame(all_bout_rows)
    metrics_df.to_csv(args.out, index=False)
    bouts_df.to_csv(args.bouts_out, index=False)
    print(f"Wrote {len(metrics_df)} metric rows to {args.out}")
    print(f"Wrote {len(bouts_df)} bout rows to {args.bouts_out}")

    # Wide comparison table: one row per file, one column per behavior's
    # cumulative frame count, so files can be compared side by side.
    id_cols = ["file", "day", "condition", "total_frames", "video_seconds"]
    meta = metrics_df[id_cols].drop_duplicates(subset="file").set_index("file")
    frames_wide = metrics_df.pivot_table(
        index="file", columns="behavior", values="frames", fill_value=0
    )
    by_file = meta.join(frames_wide).reset_index()
    by_file_path = args.out.with_name(args.out.stem + "_by_file.csv")
    by_file.to_csv(by_file_path, index=False)
    print(f"Wrote {len(by_file)} per-file comparison rows to {by_file_path}")


if __name__ == "__main__":
    main()
