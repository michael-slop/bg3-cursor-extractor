@echo off
REM ============================================================
REM  BG3 CURSORS - ONE CLICK SETUP
REM
REM  Does everything in one go:
REM    * installs all the cursors
REM    * turns on the click animation (if Python is installed)
REM    * makes the animation come back automatically at login
REM
REM  Just double-click this file. Nothing else to do.
REM
REM  Works from wherever you unzipped the folder - Downloads,
REM  Desktop, anywhere - as long as you keep the folder.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title BG3 Cursors - one click setup

echo.
echo   ============================================
echo     BALDUR'S GATE 3 CURSORS - SETUP
echo   ============================================
echo.

REM --- Find the pack, even if it unzipped one folder deeper -----------
set "PACK=%~dp0"
if not exist "%PACK%Cursors" (
  if exist "%PACK%BG3-Cursors\Cursors" (
    set "PACK=%PACK%BG3-Cursors\"
  )
)
if not exist "%PACK%Cursors" goto nopack

REM --- Warn if run from a temp/zip location ---------------------------
echo %PACK% | findstr /i "\Temp\ \AppData\Local\Temp" >nul
if not errorlevel 1 goto intemp

REM --- 1. Install the cursors -----------------------------------------
echo   [1/3] Installing cursors...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PACK%Install-BG3Cursors.ps1" -CursorDir "%PACK%Cursors" >nul 2>&1
if errorlevel 1 goto installfail
echo         done - 17 cursors applied.
echo.

REM --- 2. Is Python here? ---------------------------------------------
echo   [2/3] Checking for Python...
set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW goto nopython_done
if not exist "!PYW!" goto nopython_done
echo         found - !PYW!
echo.

set "SCRIPT=%PACK%Click-Animation\bg3_cursor_click.py"
set "FRAMES=%PACK%Click-Animation\frames"
if not exist "!SCRIPT!" goto nopython_done
if not exist "!FRAMES!" goto nopython_done

REM --- 3. Autostart + start now ---------------------------------------
echo   [3/3] Setting up the click animation...
powershell -NoProfile -Command ^
  "$sh=New-Object -ComObject WScript.Shell;" ^
  "$p=Join-Path $sh.SpecialFolders('Startup') 'BG3 Cursor Click.lnk';" ^
  "$s=$sh.CreateShortcut($p);" ^
  "$s.TargetPath='!PYW!';" ^
  "$s.Arguments='\"!SCRIPT!\" --raw \"!FRAMES!\"';" ^
  "$s.WorkingDirectory='!PACK!';" ^
  "$s.Description='BG3 cursor click animation';" ^
  "$s.WindowStyle=7;" ^
  "$s.Save();" ^
  "if(-not (Test-Path $p)){ exit 1 }"
if errorlevel 1 goto shortcutfail

start "" /b "!PYW!" "!SCRIPT!" --raw "!FRAMES!"

echo         done - it will start itself every login.
echo.
echo   ============================================
echo     ALL SET
echo   ============================================
echo.
echo   Your cursors are the real Baldur's Gate 3 ones.
echo.
echo   Hold down a mouse button - the pointer's finger
echo   curls in, just like in the game.
echo.
echo   IMPORTANT: keep this folder where it is. Windows
echo   reads the cursor files off disk every time you
echo   log in. If you move it, run this file again.
echo.
echo   To undo everything later, run
echo   "UNINSTALL (restore old cursors).bat".
echo.
pause
goto end

:nopython_done
echo         Python not found - skipping the click animation.
echo.
echo   ============================================
echo     CURSORS INSTALLED
echo   ============================================
echo.
echo   All your BG3 cursors are in and working, including
echo   the animated loading hourglass.
echo.
echo   The only thing missing is the CLICK animation (the
echo   pointer's finger curling in when you press a button).
echo   That part needs Python, because Windows cursor files
echo   cannot react to a click on their own.
echo.
echo   If you want it:
echo     1. Install Python from https://python.org
echo        (tick "Add python.exe to PATH" in the installer)
echo     2. Run this file again.
echo.
echo   Everything else already works without it.
echo.
pause
goto end

:nopack
echo   ERROR: this file is not next to the cursor pack.
echo.
echo   Keep it in the same folder as "Cursors" and
echo   "Install-BG3Cursors.ps1", then run it again.
echo.
pause
goto end

:intemp
echo   STOP - you are running this from inside the ZIP
echo   or a temporary folder:
echo.
echo   %PACK%
echo.
echo   Windows loads cursors off the disk every session, so
echo   this folder has to stay put. Please:
echo.
echo     1. Extract the ZIP to somewhere permanent
echo        (Documents, or your Desktop)
echo     2. Run this file from there.
echo.
pause
goto end

:installfail
echo   ERROR: the cursors could not be installed.
echo   Try running "1 - INSTALL CURSORS (no extras needed).bat"
echo   on its own to see the reason.
echo.
pause
goto end

:shortcutfail
echo   The cursors installed fine, but the login shortcut
echo   could not be created. You can still turn the click
echo   animation on each time with
echo   "2 - ADD CLICK ANIMATION (needs Python).bat".
echo.
pause
goto end

:end
endlocal
