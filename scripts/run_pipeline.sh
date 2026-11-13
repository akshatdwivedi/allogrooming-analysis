#!/usr/bin/env bash
# End-to-end pipeline: raw .mat files -> parsed metrics -> cleaned/excluded
# -> Winsorized -> modeled. This is the single source of truth for how the
# reported numbers are produced; if a step here doesn't match a step
# described in the paper's Methods section, one of the two is wrong.
#
# Usage:
#   EXPANSION_RAW=/path/to/expansion/mat/files \
#   PILOT_RAW=/path/to/pilot/mat/files \
#   scripts/run_pipeline.sh
set -euo pipefail

: "${EXPANSION_RAW:?Set EXPANSION_RAW to the expansion cohort's raw .mat directory}"
: "${PILOT_RAW:?Set PILOT_RAW to the pilot cohort's raw .mat directory}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DATA="$REPO_ROOT/data"
mkdir -p "$DATA/interim" "$DATA/processed" "$REPO_ROOT/results/tables"

echo "=== 1. Parse raw annotations ==="
python3 "$SCRIPT_DIR/01_parse_annotations.py" "$EXPANSION_RAW" \
    --out "$DATA/interim/expansion_metrics.csv" --bouts-out "$DATA/interim/expansion_bouts.csv"
python3 "$SCRIPT_DIR/01_parse_annotations.py" "$PILOT_RAW" \
    --out "$DATA/interim/pilot_metrics.csv" --bouts-out "$DATA/interim/pilot_bouts.csv"

echo "=== 2. Resolve duplicates and apply exclusions ==="
# Neither cohort's raw data has TBI/sham subfolders, so 01_parse_annotations.py
# cannot infer `condition` for either one -- both need --condition-map
# (verified against the expansion cohort's real raw data; an earlier version
# of this pipeline incorrectly assumed only the pilot cohort needed this).
python3 "$SCRIPT_DIR/02_resolve_duplicates_and_exclude.py" "$DATA/interim/expansion_metrics_by_file.csv" \
    --cohort expansion --exclusions "$DATA/exclusions.csv" --condition-map "$DATA/expansion_condition_map.json" \
    --out "$DATA/processed/expansion_clean.csv"
python3 "$SCRIPT_DIR/02_resolve_duplicates_and_exclude.py" "$DATA/interim/pilot_metrics_by_file.csv" \
    --cohort pilot --exclusions "$DATA/exclusions.csv" --condition-map "$DATA/pilot_condition_map.json" \
    --out "$DATA/processed/pilot_clean.csv"

echo "=== 3. Combine cohorts and Winsorize ==="
python3 - "$DATA/processed/expansion_clean.csv" "$DATA/processed/pilot_clean.csv" "$DATA/processed/combined_clean.csv" <<'PYEOF'
import sys
import pandas as pd
exp, pilot, out = sys.argv[1:4]
pd.concat([pd.read_csv(exp), pd.read_csv(pilot)], ignore_index=True).to_csv(out, index=False)
PYEOF
python3 "$SCRIPT_DIR/03_winsorize.py" "$DATA/processed/combined_clean.csv" \
    --columns allogrooming,investigation --out "$DATA/processed/combined_winsorized.csv"

echo "=== 4. Fit models ==="
for outcome in allogrooming investigation; do
    echo "--- expansion only, $outcome ---"
    python3 "$SCRIPT_DIR/04_fit_models.py" "$DATA/processed/expansion_clean.csv" --outcome "$outcome" \
        | tee "$REPO_ROOT/results/tables/expansion_${outcome}.txt"
    echo "--- combined, Winsorized, $outcome ---"
    python3 "$SCRIPT_DIR/04_fit_models.py" "$DATA/processed/combined_winsorized.csv" --outcome "$outcome" \
        | tee "$REPO_ROOT/results/tables/combined_winsorized_${outcome}.txt"
done

echo "=== Done. See $REPO_ROOT/results/tables/ ==="
