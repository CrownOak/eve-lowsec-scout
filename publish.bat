@echo off
REM Publish the lowsec page into the wdeve site (wdeve/lowsec/). FAIL-CLOSED: refuses
REM to publish an unlocked page and exits non-zero so a missing password surfaces.
cd /d "%~dp0"
findstr /C:"const B =" index.html >nul
if errorlevel 1 (
  echo publish: index.html is NOT locked -- refusing to push. Is EVE_PAGE_PASSWORD set?
  exit /b 1
)
set "DEST=C:\Users\sales\wdeve\lowsec"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y index.html "%DEST%\index.html" >nul
pushd "C:\Users\sales\wdeve"
git add lowsec/index.html
git diff --cached --quiet
if %ERRORLEVEL%==0 ( echo publish: no page change ) else ( git commit -m "lowsec: update page" & git push )
popd
