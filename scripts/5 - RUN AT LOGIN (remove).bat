@echo off
REM ============================================================
REM  Stops the click animation starting at login, and stops it
REM  now. Your cursors stay installed - only the animation goes.
REM ============================================================
cd /d "%~dp0"

REM Remove the Startup shortcut.
powershell -NoProfile -Command ^
  "$sh=New-Object -ComObject WScript.Shell;" ^
  "$p=Join-Path $sh.SpecialFolders('Startup') 'BG3 Cursor Click.lnk';" ^
  "if(Test-Path $p){Remove-Item $p -Force; 'removed startup shortcut'}else{'no startup shortcut was set'}"

REM Stop any running hook. Filter on the COMMAND LINE - never kill every
REM pythonw, which would take unrelated Python programs with it.
powershell -NoProfile -Command ^
  "$h=Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' OR Name='python.exe'\" | Where-Object { $_.CommandLine -like '*bg3_cursor_click*' };" ^
  "if($h){$h | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; 'stopped ' + @($h).Count + ' running hook(s)'}else{'nothing was running'}"

REM Put the static BG3 cursors back.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-BG3Cursors.ps1" -CursorDir "%~dp0Cursors" >nul 2>&1

echo.
echo   Click animation removed from startup and stopped.
echo   Your BG3 cursors are still installed.
echo.
pause
