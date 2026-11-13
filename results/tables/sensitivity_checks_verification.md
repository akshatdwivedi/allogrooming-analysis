# Sensitivity Checks Verification Against Real Raw Data

`05_sensitivity_checks.py` was built to formalize the truncation and
nonparametric analyses that previously existed only as this-session
scratch code, then run against the real raw data from both cohorts.

## A design bug this verification caught

The first version of `truncate` dropped any video below 90% of the target
window entirely. Re-running it against real data gave IRR=2.304 for the
"pilot only, truncated" check -- close to, but not matching, the
previously reported 2.69. The discrepancy traced to one video
(`day1cage5_annot_mat_RA.mat`, 11,082 frames, 6.16 min): the original
18.93-minute check kept it at its own full length (its purpose was capping
videos that ran *long*, not excluding short ones), while the first version
of this script excluded it outright, changing the pilot-only sample from
25 to 24 videos.

Fixed with an explicit `--on-short-video {keep,exclude}` flag -- `keep`
(now the default) for the 18.93-min check, `exclude` for the 20-min
common-window check (where every video genuinely needs to reach the same
length for the comparison to be fair). Both policies are named and
explained in the script, not left as an undocumented default.

## Verified results (all exact matches after the fix)

| Check | Outcome | Result | Matches prior report? |
|---|---|---|---|
| Pilot only, truncated 18.93 min | Allogrooming | IRR=2.688, CI=[0.541,13.358], p=0.2266 | Yes, exactly |
| Pilot only, truncated 18.93 min | Investigation | IRR=1.411, CI=[0.969,2.056], p=0.0727 | Yes, exactly |
| Combined, pilot truncated 18.93 min | Allogrooming | IRR=3.719, CI=[0.937,14.767], p=0.0619 | Yes, exactly |
| Combined, pilot truncated 18.93 min | Investigation | IRR=1.446, CI=[1.190,1.757], p=0.0002 | Yes, exactly |
| Combined, truncated + Winsorized | Allogrooming | IRR=7.429, CI=[2.796,19.739], p=0.0001 | Yes, exactly |
| Combined, truncated + Winsorized | Investigation | IRR=1.444, CI=[1.191,1.752], p=0.0002 | Yes, exactly |
| Mann-Whitney U, 20-min window | Allogrooming | U=988.0, p<0.0001 (TBI n=42 med=644.0, sham n=29 med=50.0) | Yes, exactly |
| Mann-Whitney U, 20-min window | Investigation | U=942.0, p=0.0001 (TBI med=8266.5, sham med=6468.0) | Yes, exactly |
| Kruskal-Wallis H, 2-group | Allogrooming | H=19.728, p<0.0001 | Yes, exactly |
| Kruskal-Wallis H, 2-group | Investigation | H=15.174, p<0.0001 | Yes, exactly |
| Kruskal-Wallis H, across days (TBI/sham x 2 outcomes) | both | All 4 H/p values and all day medians | Yes, exactly |

## Status

Every number from the truncation and nonparametric sensitivity analyses is
now verified against real raw data through committed, re-runnable code.
Combined with `expansion_only_verification.md` and `combined_verification.md`,
every headline and sensitivity result in this project's analysis record is
now backed by code in this repository rather than a chat session.
