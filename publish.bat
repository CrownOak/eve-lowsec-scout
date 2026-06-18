@echo off
REM CROWN & OAK - publish the generated page to git. Safe to run anytime:
REM it is a no-op if the page has not changed, and only ever commits index.html.
cd /d "%~dp0"
git add index.html
git diff --cached --quiet
if %ERRORLEVEL%==0 (
  echo publish: no page change
) else (
  git commit -m "scout: update top 10"
  git push
)
