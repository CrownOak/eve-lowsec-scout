# Lowsec Scout (v3, file-only)

Ranks safe, low-traffic, ore-suitable EVE Online solar systems and keeps a running
record so you can tell "quiet right now" from "actually quiet." No database. Each run
saves a Top-10 page and auto-publishes it to GitHub Pages.

- Working dir: `C:\Users\sales\eve-scout`
- Repo: https://github.com/CrownOak/eve-lowsec-scout
- **Live page: https://crownoak.github.io/eve-lowsec-scout/**

## What it does each run
1. **Records** the current hour's ESI kill/jump snapshot to `scout_history.csv`
   (append-only). Run hourly to build a real multi-day danger history.
2. **Scores** every system: SAFETY (kills + traffic, pod kills weighted, blended with
   recorded history once a system has >= 3 samples) and ORE (lower truesec = richer).
   Final rank = 70% safety + 30% ore.
3. **Saves the page** `index.html` (top 10) and **pushes it to git**, so the live URL
   updates automatically.
4. **Threat-checks** the shortlist against zKillboard on interactive runs.

> No public API exposes live ore *anomalies*. This finds safe, ore-*suitable* candidate
> systems. You still warp in and scan.

## Files
| File | What |
|---|---|
| `lowsec_scout.py` | the tool |
| `scout_page.py` | shared HTML page renderer |
| `index.html` | the generated Top-10 page (committed + served by Pages) |
| `run.bat` / `run.ps1` | hourly runner: scout, then `publish.bat` |
| `publish.bat` | commit + push `index.html` (no-op if unchanged) |
| `scout_server.py` / `serve.bat` | OPTIONAL local http server (only if you want a localhost URL) |
| `.venv\` | Python venv (has `openpyxl`) |
| `systems_cache.json` | one-time SDE system map (gitignored) |
| `scout_history.csv` | running history record (gitignored, append-only) |
| `lowsec_scout.xlsx` | running workbook: `Shortlist-<space>` sheets + `RunLog` (gitignored) |
| `scout.log` | hourly task output (gitignored) |

Only the page + source are committed; the venv, history CSV, workbook, cache, and logs
are gitignored.

## The hourly job (installed)
A Windows Task Scheduler task **"EVE Lowsec Scout"** runs `run.bat` every hour: it
records a snapshot (`--no-threat`), writes `index.html`, and pushes it. While you are
logged in this keeps the live page current with zero babysitting.

```powershell
schtasks /Query  /TN "EVE Lowsec Scout" /V /FO LIST   # inspect
schtasks /Run    /TN "EVE Lowsec Scout"               # run now
schtasks /Change /TN "EVE Lowsec Scout" /DISABLE      # pause
schtasks /Change /TN "EVE Lowsec Scout" /ENABLE       # resume
```

The push uses your existing `gh`/git credentials (account CrownOak). The hourly run is
`--no-threat`, so the page's ZK/LASTh columns are blank between interactive runs (the
page notes this so blanks are not misread as "zero kills").

## On-demand scouting
```bat
cd C:\Users\sales\eve-scout

REM highsec, with zKill threat check, open the page locally
.venv\Scripts\python.exe lowsec_scout.py --space hisec --threat-top 10 --open

REM a specific region, lowsec
.venv\Scripts\python.exe lowsec_scout.py --space lowsec --region Metropolis --top 30
```
Interactive runs update `index.html` locally (and `--open` opens it). They do not push
by default; run `publish.bat` to push, or just let the next hourly run publish.

## Optional: local http server
If you ever want a localhost URL instead of the file/Pages, run `serve.bat`
(http://127.0.0.1:8787) and add `--webhook http://127.0.0.1:8787/webhook` to a run.
Not needed for the Pages workflow.

## Flags
| Flag | Default | Meaning |
|---|---|---|
| `--space` | `lowsec` | `lowsec` / `hisec` / `null` / `all` |
| `--top` | `25` | how many systems in the console/workbook |
| `--page-top` | `10` | how many systems on the page / webhook |
| `--region` | (all) | limit to one region by name |
| `--min-jumps` | `0` | drop systems below this traffic |
| `--history-days` | `7` | lookback window for the recorded danger average |
| `--retain-days` | `120` | prune `scout_history.csv` older than this (`0` = keep all) |
| `--no-record` | off | do not append this run to the history CSV |
| `--no-threat` | off | skip zKill lookups (faster) |
| `--threat-top` | =`--top` | how many shortlist systems to zKill-check (`0` = none) |
| `--html FILE` | `index.html` | the page to write |
| `--no-html` | off | do not write the page |
| `--open` | off | open the page in your browser after writing |
| `--out FILE` | (none) | also write the shown table to a one-off CSV |
| `--demo` | off | offline self-test with fake data |

## Columns
`SCORE` = 70% safety + 30% ore. `SAFE` = low kills/traffic (history-blended).
`ORE` = truesec potential (lower sec = richer). `PVP1h` = ship+pod kills this hour.
`~AVG` = recorded avg PVP/hr over the window. `N` = history samples (>= 3 means the
score is history-blended). `ZK`/`LASTh` = recent zKill kills / hours since the last.
Ties (common at SAFE=100) break by richer ORE, then lowest traffic.

## Notes
- Pure stdlib **except `openpyxl`** (for the .xlsx; in the venv).
- Live runs need internet: `esi.evetech.net`, `fuzzwork.co.uk`, `zkillboard.com`.
- History needs time: `~AVG` and history-blended safety kick in after >= 3 snapshots.
- Fuzzwork SDE lives under `/dump/latest/csv/` and ships a UTF-8 BOM (both handled).
