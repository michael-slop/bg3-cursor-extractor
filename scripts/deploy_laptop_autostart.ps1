# Deploy the login-autostart update to SloppyLaptopy.
# Expects bg3autostart.tgz already copied to C:\Users\micha\.
$ErrorActionPreference = 'Stop'
$d = "C:\Users\micha\Desktop\BG3-Cursors"

# Stop the old hook before replacing its script.
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*bg3_cursor_click*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 1

tar -xzf C:\Users\micha\bg3autostart.tgz -C $d
if (Test-Path C:\Users\micha\BG3-Cursors.zip) {
    Move-Item C:\Users\micha\BG3-Cursors.zip "$env:USERPROFILE\Desktop\BG3-Cursors.zip" -Force
}

# Create the Startup shortcut with an absolute interpreter path.
$pyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pyw) { throw "pythonw not found on PATH" }

$sh   = New-Object -ComObject WScript.Shell
$lnkP = Join-Path $sh.SpecialFolders('Startup') 'BG3 Cursor Click.lnk'
$lnk  = $sh.CreateShortcut($lnkP)
$lnk.TargetPath       = $pyw
$lnk.Arguments        = '"' + $d + '\Click-Animation\bg3_cursor_click.py" --raw "' + $d + '\Click-Animation\frames"'
$lnk.WorkingDirectory = $d
$lnk.Description      = 'BG3 cursor click animation'
$lnk.WindowStyle      = 7
$lnk.Save()
if (-not (Test-Path $lnkP)) { throw "shortcut was not created" }

# Re-apply cursors and start the hook now.
& "$d\Install-BG3Cursors.ps1" -CursorDir "$d\Cursors" | Select-Object -Last 2
Start-Process $pyw -ArgumentList "$d\Click-Animation\bg3_cursor_click.py","--raw","$d\Click-Animation\frames" -WorkingDirectory $d
Start-Sleep -Seconds 3

# Report what actually happened.
$chk = $sh.CreateShortcut($lnkP)
"interpreter : $($chk.TargetPath)"
"target OK   : $(Test-Path $chk.TargetPath)"
"frames OK   : $(Test-Path "$d\Click-Animation\frames")"
$h = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
     Where-Object { $_.CommandLine -like '*bg3_cursor_click*' }
"hook        : $(@($h).Count) running"
"zip on desk : $(Test-Path "$env:USERPROFILE\Desktop\BG3-Cursors.zip")"
