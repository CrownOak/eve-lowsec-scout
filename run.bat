@echo off
REM CROWN & OAK - Lowsec Scout hourly recorder (Windows Task Scheduler entry point)
REM Records one ESI snapshot to scout_history.csv and refreshes lowsec_scout.xlsx.
REM --no-threat: the unattended hourly run only needs to RECORD; zKill lookups are
REM for interactive shortlisting and would needlessly hammer zKill every hour.
cd /d "%~dp0"
REM Writes index.html (the page) each run, then commits + pushes it to git.
".venv\Scripts\python.exe" lowsec_scout.py --no-threat >> scout.log 2>&1
call "%~dp0publish.bat" >> scout.log 2>&1
