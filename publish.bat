@echo off
REM CROWN & OAK - publish the generated page to git. Safe to run anytime:
REM it is a no-op if the page has not changed, and only ever commits index.html.
cd /d "%~dp0"
REM Safety: never publish an unlocked page. The locked page contains the "const B =" blob.
findstr /C:"const B =" index.html >nul
if errorlevel 1 (
  echo publish: index.html is NOT locked -- refusing to push. Is EVE_PAGE_PASSWORD set?
  exit /b 0
)
git add index.html
git diff --cached --quiet
if %ERRORLEVEL%==0 (
  echo publish: no page change
) else (
  git commit -m "scout: update top 10"
  git push
)
