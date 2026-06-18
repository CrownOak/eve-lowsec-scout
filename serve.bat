@echo off
REM CROWN & OAK - Lowsec Scout : start the local page + webhook server.
REM Serves http://127.0.0.1:8787/  (loopback only). Leave this window open.
title Lowsec Scout - local page (127.0.0.1:8787)
cd /d "%~dp0"
".venv\Scripts\python.exe" scout_server.py --port 8787
