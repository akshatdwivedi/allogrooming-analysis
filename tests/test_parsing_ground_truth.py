"""
Ground-truth test for 01_parse_annotations.py: builds synthetic .mat files
with hand-designed, exactly-known frame sequences, records the correct
frame counts/percentages/bout lists independently (by plain arithmetic,
never by calling any function from 01_parse_annotations.py), runs the real
script on them, and diffs every value exactly.

Exercises: a single bout that runs to the last frame (the trailing-bout
edge case), two separate bouts of the same behavior, a behavior with zero
frames, and several single-frame bouts back to back.

Usage:
    python tests/test_parsing_ground_truth.py
Exits non-zero (and prints every mismatch) if anything disagrees.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

FPS = 30.0
BEHAVIORS = {"allogrooming": 0, "investigation": 1, "offensive_fighting": 2,
             "defensive_fighting": 3, "other": 4}
REPO_ROOT = Path(__file__).resolve().parent.parent
PARSE_SCRIPT = REPO_ROOT / "scripts" / "01_parse_annotations.py"


def block(behavior, n):
    return np.full(n, BEHAVIORS[behavior], dtype=float)


def build_file(out_root, ground_truth, day, condition, cage, blocks, fname):
    codes = np.concatenate([block(b, n) for b, n in blocks])
    n_total = len(codes)

    frame_counts = {}
    for b, n in blocks:
        frame_counts[b] = frame_counts.get(b, 0) + n

    merged = []
    for b, n in blocks:
        if merged and merged[-1][0] == b:
            merged[-1] = (b, merged[-1][1] + n)
        else:
            merged.append((b, n))
    bouts_by_behavior, offset = {}, 0
    for b, n in merged:
        bouts_by_behavior.setdefault(b, []).append(
            {"start_sec": offset / FPS, "end_sec": (offset + n) / FPS, "duration_sec": n / FPS})
        offset += n
    assert offset == n_total

    for b in BEHAVIORS:
        n_b = frame_counts.get(b, 0)
        ground_truth.append({
            "file": fname, "day": day, "condition": condition, "cage": cage, "behavior": b,
            "frames": n_b, "pct_of_video": 100.0 * n_b / n_total,
            "bouts": bouts_by_behavior.get(b, []),
        })

    out_dir = out_root / f"Day{day}" / condition
    out_dir.mkdir(parents=True, exist_ok=True)
    sio.savemat(out_dir / fname,
                {"annotation": {"stream_ID": fname, "annotation": codes, "behaviors": dict(BEHAVIORS)}})


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        mat_root = tmp / "synthetic_mat_data"
        ground_truth = []

        build_file(mat_root, ground_truth, 1, "TBI", 1,
            [("allogrooming", 100), ("investigation", 250), ("offensive_fighting", 10),
             ("defensive_fighting", 10), ("other", 630)], "day1cage1_annot.mat")
        build_file(mat_root, ground_truth, 1, "TBI", 2,
            [("allogrooming", 50), ("other", 50), ("allogrooming", 40), ("investigation", 460)],
            "day1cage2_annot.mat")
        build_file(mat_root, ground_truth, 1, "sham", 3,
            [("other", 700), ("investigation", 100)], "day1cage3_annot.mat")
        build_file(mat_root, ground_truth, 1, "sham", 4,
            [("allogrooming", 1), ("other", 1), ("allogrooming", 1), ("other", 1),
             ("allogrooming", 1), ("investigation", 495)], "day1cage4_annot.mat")

        metrics_out, bouts_out = tmp / "metrics.csv", tmp / "bouts.csv"
        subprocess.run(
            [sys.executable, "-I", str(PARSE_SCRIPT), str(mat_root), "--out", str(metrics_out),
             "--bouts-out", str(bouts_out)],
            check=True, cwd=tmp,
        )
        metrics, bouts = pd.read_csv(metrics_out), pd.read_csv(bouts_out)

        mismatches = 0
        for row in ground_truth:
            got = metrics[(metrics.file == row["file"]) & (metrics.behavior == row["behavior"])]
            if len(got) != 1 or int(got.iloc[0]["frames"]) != row["frames"]:
                print(f"MISMATCH (frames): {row['file']}/{row['behavior']} expected {row['frames']}, "
                      f"got {got.iloc[0]['frames'] if len(got) == 1 else 'missing/duplicate row'}")
                mismatches += 1

            expected_bouts = sorted(row["bouts"], key=lambda b: b["start_sec"])
            got_bouts = bouts[(bouts.file == row["file"]) & (bouts.behavior == row["behavior"])] \
                .sort_values("start_sec")
            if len(expected_bouts) != len(got_bouts):
                print(f"MISMATCH (bout count): {row['file']}/{row['behavior']} "
                      f"expected {len(expected_bouts)}, got {len(got_bouts)}")
                mismatches += 1
                continue
            for exp_b, (_, got_b) in zip(expected_bouts, got_bouts.iterrows()):
                if (abs(exp_b["start_sec"] - got_b["start_sec"]) > 1e-9 or
                        abs(exp_b["end_sec"] - got_b["end_sec"]) > 1e-9):
                    print(f"MISMATCH (bout timing): {row['file']}/{row['behavior']} "
                          f"expected {exp_b}, got start={got_b['start_sec']} end={got_b['end_sec']}")
                    mismatches += 1

        if mismatches:
            print(f"\nFAILED: {mismatches} mismatch(es)")
            sys.exit(1)
        print(f"PASSED: {len(ground_truth)} frame-count rows and all bouts matched exactly")


if __name__ == "__main__":
    main()
