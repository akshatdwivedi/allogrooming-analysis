"""
Generate a small synthetic BAnnotator-format dataset with a KNOWN planted
effect, so we can run the real pipeline (analyze_annotations.py + fit_models.py)
on data whose ground truth we already know, and check the recovered estimates
against it.

Generative model (frame-level, per cage/day):
  - Each cage has its own random multiplicative "baseline" (Gamma-distributed,
    mean 1) -- mixing a Poisson rate with a Gamma multiplier produces genuine
    Negative-Binomial-distributed counts, i.e. real cage-level overdispersion,
    not just frame-level noise. This matches the generative assumption behind
    the negative binomial GEE model we are validating.
  - allogrooming rate = BASE_ALLO * (TBI_RATIO if TBI else 1) * (DAY_DECAY ** (day-1)) * cage_multiplier
  - investigation rate = BASE_INV * (TBI_INV_RATIO if TBI else 1) * cage_multiplier  (no day effect)
  - remaining frames are "other"
  - no fighting/defensive behavior in this synthetic set (kept simple)

Ground truth planted:
  TBI_RATIO (allogrooming IRR, condition)  = 10.0
  DAY_DECAY (allogrooming IRR, per day)    = 0.80
  TBI_INV_RATIO (investigation IRR, condition) = 1.5
"""
import json
from pathlib import Path

import numpy as np
import scipy.io as sio

rng = np.random.default_rng(42)

OUT_ROOT = Path("./tests/synthetic_data/data")
FPS = 30.0
VIDEO_SECONDS = 1200.0
N_FRAMES = int(FPS * VIDEO_SECONDS)

CAGES = {
    "TBI": [101, 102, 103, 104],
    "sham": [201, 202, 203, 204],
}
DAYS = [1, 2, 3, 4, 5]

# --- Ground truth parameters (what we expect fit_models.py to recover) ---
BASE_ALLO = 60.0     # sham, day 1, mean allogrooming frames (before cage multiplier)
TBI_RATIO = 10.0      # true condition IRR for allogrooming
DAY_DECAY = 0.80      # true per-day IRR for allogrooming (applies to both groups)
BASE_INV = 7000.0     # sham, mean investigation frames
TBI_INV_RATIO = 1.5   # true condition IRR for investigation

CAGE_OVERDISPERSION_ALPHA = 0.3  # Gamma shape parameter controlling cage-to-cage spread

BEHAVIOR_MAP = {
    "allogrooming": 0,
    "investigation": 1,
    "offensive_fighting": 2,
    "defensive_fighting": 3,
    "other": 4,
}


def gamma_multiplier():
    # mean-1 Gamma multiplier: shape k, scale 1/k  ->  mean = 1, var = 1/k
    k = 1.0 / CAGE_OVERDISPERSION_ALPHA
    return rng.gamma(shape=k, scale=1.0 / k)


def make_codes(n_allo, n_inv, n_frames):
    n_allo = min(n_allo, n_frames)
    n_inv = min(n_inv, n_frames - n_allo)
    n_other = n_frames - n_allo - n_inv
    codes = np.array(
        [BEHAVIOR_MAP["allogrooming"]] * n_allo
        + [BEHAVIOR_MAP["investigation"]] * n_inv
        + [BEHAVIOR_MAP["other"]] * n_other,
        dtype=float,
    )
    rng.shuffle(codes)  # frame order doesn't matter for cumulative-frame metrics
    return codes


def write_mat(path, codes):
    behaviors_dtype = np.dtype([(name, "O") for name in BEHAVIOR_MAP])
    behaviors_struct = np.zeros((1, 1), dtype=behaviors_dtype)
    for name, code in BEHAVIOR_MAP.items():
        behaviors_struct[name][0, 0] = np.array([[code]], dtype=np.uint8)

    annotation_dtype = np.dtype([("stream_ID", "O"), ("annotation", "O"), ("behaviors", "O")])
    ann_struct = np.zeros((1, 1), dtype=annotation_dtype)
    ann_struct["stream_ID"][0, 0] = np.array([[1]], dtype=np.uint8)
    ann_struct["annotation"][0, 0] = codes.reshape(-1, 1)
    ann_struct["behaviors"][0, 0] = behaviors_struct

    sio.savemat(str(path), {"annotation": ann_struct})


ground_truth_rows = []
for condition, cage_list in CAGES.items():
    for cage in cage_list:
        cage_mult = gamma_multiplier()
        for day in DAYS:
            allo_rate = BASE_ALLO * (TBI_RATIO if condition == "TBI" else 1.0) * (DAY_DECAY ** (day - 1)) * cage_mult
            inv_rate = BASE_INV * (TBI_INV_RATIO if condition == "TBI" else 1.0) * cage_mult

            n_allo = rng.poisson(allo_rate)
            n_inv = rng.poisson(inv_rate)

            codes = make_codes(n_allo, n_inv, N_FRAMES)

            day_dir = OUT_ROOT / f"day {day}"
            day_dir.mkdir(parents=True, exist_ok=True)
            fname = day_dir / f"day{day}cage{cage}_annot.mat"
            write_mat(fname, codes)

            ground_truth_rows.append({
                "file": fname.name, "day": day, "cage": cage, "condition": condition,
                "true_allo_rate": allo_rate, "true_inv_rate": inv_rate,
                "actual_allo_frames": int(n_allo), "actual_inv_frames": int(n_inv),
                "cage_multiplier": cage_mult,
            })

meta_path = OUT_ROOT.parent / "ground_truth.json"
with open(meta_path, "w") as f:
    json.dump({
        "params": {
            "BASE_ALLO": BASE_ALLO, "TBI_RATIO": TBI_RATIO, "DAY_DECAY": DAY_DECAY,
            "BASE_INV": BASE_INV, "TBI_INV_RATIO": TBI_INV_RATIO,
            "CAGE_OVERDISPERSION_ALPHA": CAGE_OVERDISPERSION_ALPHA,
        },
        "rows": ground_truth_rows,
    }, f, indent=2)

print(f"Wrote {len(ground_truth_rows)} synthetic video files under {OUT_ROOT}")
print(f"Ground truth saved to {meta_path}")
