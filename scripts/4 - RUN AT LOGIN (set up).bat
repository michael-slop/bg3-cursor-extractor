@echo off
REM ============================================================
REM  Makes the click animation start automatically at login.
REM
REM  Puts a shortcut in your Startup folder pointing at the
REM  click-animation script, then starts it now so you don't
REM  have to reboot to see it working.
REM
REM  REQUIRES PYTHON - same as file 2. The cursors themselves
REM  work without it; this is only for the click animation.
REM
REM  Undo with "5 - RUN AT LOGIN (remove).bat".
REM ============================================================
setlocal
cd /d "%~dp0"

REM Resolve pythonw to an ABSOLUTE path. A bare "pythonw" depends on the user
REM PATH, which is not reliably present for every login-launched process.
set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"

if not defined PYW goto nopython
if not exist "%PYW%" goto nopython

set "SCRIPT=%~dp0Click-Animation\bg3_cursor_click.py"
set "FRAMES=%~dp0Click-Animation\frames"

if not exist "%SCRIPT%" goto noscript
if not exist "%FRAMES%" goto noframes

REM Create the Startup shortcut. Uses WScript.Shell's own SpecialFolders rather
REM than [Environment]::GetFolderPath - the latter proved unreliable once nested
REM inside this quoting, silently producing no shortcut at all.
powershell -NoProfile -Command ^
  "$sh=New-Object -ComObject WScript.Shell;" ^
  "$p=Join-Path $sh.SpecialFolders('Startup') 'BG3 Cursor Click.lnk';" ^
  "$s=$sh.CreateShortcut($p);" ^
  "$s.TargetPath='%PYW%';" ^
  "$s.Arguments='\"%SCRIPT%\" --raw \"%FRAMES%\"';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.Description='BG3 cursor click animation';" ^
  "$s.WindowStyle=7;" ^
  "$s.Save();" ^
  "if(-not (Test-Path $p)){ exit 1 }"

if errorlevel 1 goto failed

REM Start it now too (the script refuses to run twice, so this is safe).
REM /b keeps cmd from waiting on the hook, which would hang this window.
start "" /b "%PYW%" "%SCRIPT%" --raw "%FRAMES%"

echo.
echo   Done. The click animation will now start automatically
echo   every time you log in.
echo.
echo   It is also running right now - hold a mouse button and
echo   the pointer's finger curls in.
echo.
echo   Interpreter: %PYW%
echo.
echo   To undo, run "5 - RUN AT LOGIN (remove).bat".
echo.
pause
goto :eof

:nopython
echo.
echo   PYTHON NOT FOUND.
echo.
echo   The click animation needs Python installed. Everything
echo   else - all 100 cursors and the animated loading
echo   hourglass - already works without it, so this is
echo   entirely optional.
echo.
echo   Install Python from https://python.org  (tick "Add
echo   python.exe to PATH" in the installer), then run this
echo   file again.
echo.
pause
goto :eof

:noscript
echo.
echo   ERROR: cannot find Click-Animation\bg3_cursor_click.py
echo   next to this file. Keep the pack folder together.
echo.
pause
goto :eof

:noframes
echo.
echo   ERROR: cannot find Click-Animation\frames
echo   next to this file. Keep the pack folder together.
echo.
pause
goto :eof

:failed
echo.
echo   ERROR: could not create the Startup shortcut.
echo.
pause
