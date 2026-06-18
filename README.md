# Lowsec Scout (v3, file-only)

Ranks safe, low-traffic, ore-suitable EVE Online solar systems and keeps a running
record so you can tell "quiet right now" from "actually quiet." No database: the
running record is a CSV, the readable output is an Excel workbook.

Location: `C:\Users\sales\eve-scout`

## What it does each run
1. **Records** the current hour's ESI kill/jump snapshot to `scout_history.csv`
   (append-only). Run hourly to build a real multi-day danger history (ESI only
   exposes the last hour).
2. **Scores** every system: SAFETY (kills + traffic, pod kills weighted as a camp
   signal, blended with recorded history once a system has >= 3 samples) and ORE
   potential (lower truesec = richer ore). Final rank = 70% safety + 30% ore.
3. **Threat-checks** the shortlist against zKillboard (recent kill volume + hours
   since last kill) on interactive runs, extending the 1-hour window to multi-day.

> No public API exposes live ore *anomalies* (only your in-game probe scanner does).
> This finds safe, ore-*suitable* candidate systems. You still warp in and scan.

## Files
| File | What |
|---|---|
| `lowsec_scout.py` | the tool |
| `.venv\` | Python venv (has `openpyxl`) |
| `systems_cache.json` | one-time SDE system map from Fuzzwork (name/sec/truesec/region) |
| `scout_history.csv` | **the running record** (append-only; ts, system_id, ship, pod, npc, jumps) |
| `lowsec_scout.xlsx` | **the running workbook**: one `Shortlist-<space>` sheet per band + a `RunLog` |
| `scout.log` | hourly task output |
| `run.bat` / `run.ps1` | hourly runner (Task Scheduler calls `run.bat`) |
| `scout_server.py` | local page + webhook server (loopback only) |
| `serve.bat` | starts the page server |
| `webhook_state.json` | last payload the page renders (survives restarts) |

## The hourly job (already installed)
A Windows Task Scheduler task **"EVE Lowsec Scout"** runs `run.bat` every hour. It
records a snapshot with `--no-threat` (the unattended run only needs to record;
zKill lookups are for interactive scouting).

```powershell
schtasks /Query  /TN "EVE Lowsec Scout" /V /FO LIST   # inspect
schtasks /Run    /TN "EVE Lowsec Scout"               # run now
schtasks /Change /TN "EVE Lowsec Scout" /DISABLE      # pause
schtasks /Change /TN "EVE Lowsec Scout" /ENABLE       # resume
schtasks /Delete /TN "EVE Lowsec Scout" /F            # remove
```

## Local page (webhook)
A tiny loopback-only web server hosts a live "Top N" page and receives updates from
the scout via a webhook. Start it (leave the window open):

```bat
cd C:\Users\sales\eve-scout
serve.bat                       REM -> http://127.0.0.1:8787/
```

Then any run with `--webhook` pushes its top systems to the page:
```bat
.venv\Scripts\python.exe lowsec_scout.py --space hisec --threat-top 10 --webhook http://127.0.0.1:8787/webhook
```
The hourly task already passes `--webhook http://127.0.0.1:8787/webhook`, so while the
server is running the page refreshes itself every hour (and the post is best-effort:
if the server is down the scout just logs a warning and carries on). The page also
auto-refreshes in the browser every 60s.

Endpoints (all on `127.0.0.1:8787`, not exposed to your network):
`GET /` page &middot; `GET /data` last payload as JSON &middot; `GET /health` &middot;
`POST /webhook` receive a payload. Set `--webhook-top N` to change how many systems are
sent (default 10). An optional shared secret can gate POSTs: start the server with
`--token XYZ` (or env `SCOUT_WEBHOOK_TOKEN`) and pass `--webhook-token XYZ` to the scout.

**Keep it always-on (optional):** to have the page survive reboots, register a logon
task that starts it without a console window:
```powershell
schtasks /Create /SC ONLOGON /TN "EVE Scout Page" /F /TR "C:\Users\sales\eve-scout\.venv\Scripts\pythonw.exe C:\Users\sales\eve-scout\scout_server.py --port 8787"
```

## On-demand scouting
The hourly job builds history quietly. When you actually want a shortlist to go mine:

```bat
cd C:\Users\sales\eve-scout

REM highsec, with zKill threat check, into the workbook
.venv\Scripts\python.exe lowsec_scout.py --space hisec --top 25

REM a specific region, lowsec
.venv\Scripts\python.exe lowsec_scout.py --space lowsec --region Metropolis --top 30

REM fast, skip zKill
.venv\Scripts\python.exe lowsec_scout.py --no-threat
```

Each interactive run also records a snapshot and refreshes its `Shortlist-<space>`
sheet, so a hisec scout does not clobber the hourly lowsec sheet (they are keyed
by space/region). System names in the workbook are clickable DOTLAN map links.

### Running interactively while the hourly job might fire
Both the hourly task and an interactive run write `scout_history.csv` and
`lowsec_scout.xlsx`. They almost never collide (the hourly run is a ~1-2s window at
the top of the hour), and the CSV is append-only and self-healing. If you want to be
certain an interactive run never touches the running files, add `--no-record --no-xlsx`
(it will still print the table and can still write a one-off CSV with `--out`).

## Flags
| Flag | Default | Meaning |
|---|---|---|
| `--space` | `lowsec` | `lowsec` / `hisec` / `null` / `all` |
| `--top` | `25` | how many systems to show |
| `--region` | (all) | limit to one region by name |
| `--min-jumps` | `0` | drop systems below this traffic (e.g. `1` = exclude dead) |
| `--history-days` | `7` | lookback window for the recorded danger average |
| `--retain-days` | `120` | prune `scout_history.csv` older than this (`0` = keep all) |
| `--no-record` | off | do not append this run to the history CSV |
| `--no-threat` | off | skip zKill lookups (faster) |
| `--threat-top` | =`--top` | how many shortlist systems to zKill-check (`0` = none) |
| `--out FILE` | (none) | also write the shown table to a one-off CSV |
| `--history FILE` | `scout_history.csv` | running history CSV path |
| `--xlsx FILE` | `lowsec_scout.xlsx` | running workbook path |
| `--no-xlsx` | off | do not write the workbook |
| `--demo` | off | offline self-test with fake data |

## Columns
`SCORE` = 70% safety + 30% ore. `SAFE` = low kills/traffic (history-blended).
`ORE` = truesec potential (lower sec = richer). `PVP1h` = ship+pod kills this hour.
`~AVG` = recorded avg PVP/hr over the history window. `N` = history samples (once
N >= 3 the score blends recorded danger, else it is live-only). `ZK` = recent zKill
kills, `LASTh` = hours since the last one. Ties (very common at SAFE=100) break by
richer ORE, then by lowest traffic.

## Notes
- Pure Python stdlib **except `openpyxl`** (for the .xlsx; in the venv). Without it
  the tool still runs and keeps `scout_history.csv`, just skipping the workbook.
- Live runs need open internet: `esi.evetech.net`, `fuzzwork.co.uk`, `zkillboard.com`.
  The offline `--demo` works without it.
- History needs time: `~AVG` and history-blended safety only kick in after the hourly
  job has logged >= 3 snapshots per system.
- Data sources can move. As of this build the Fuzzwork SDE lives under
  `/dump/latest/csv/` and ships a UTF-8 BOM (both handled in the code).
