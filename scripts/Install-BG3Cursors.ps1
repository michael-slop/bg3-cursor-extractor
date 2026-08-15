<#
.SYNOPSIS
    Installs the Baldur's Gate 3 cursor scheme (ripped from the game's own Game.pak).

.DESCRIPTION
    Registers the cursors as a named Windows scheme, points HKCU\Control Panel\Cursors
    at them, and broadcasts the change so it applies without a logoff.

    Backs up the current cursor registry to a .reg file first.

.PARAMETER Uninstall
    Restore the previous cursors from the most recent backup.

.EXAMPLE
    .\Install-BG3Cursors.ps1
    .\Install-BG3Cursors.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$CursorDir,
    [string]$SchemeName = 'Baldurs Gate 3'
)

$ErrorActionPreference = 'Stop'

# $PSScriptRoot is empty under Windows PowerShell 5.1 in some invocation modes,
# so fall back to the invocation path before using it.
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }
if (-not $CursorDir) { $CursorDir = Join-Path $ScriptDir 'Cursors' }
$RegPath    = 'HKCU:\Control Panel\Cursors'
$BackupDir  = Join-Path $ScriptDir 'backup'

# Windows cursor slots, in the exact order the Scheme registry value expects.
$SlotOrder = @(
    'Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No',
    'SizeNS','SizeWE','SizeNWSE','SizeNESW','SizeAll','UpArrow','Hand',
    'Person','Pin'
)

function Broadcast-CursorChange {
    # SPI_SETCURSORS = 0x0057. Applies the new cursors immediately.
    if (-not ('W32.Cur' -as [type])) {
        Add-Type -Namespace W32 -Name Cur -MemberDefinition @'
[DllImport("user32.dll", SetLastError=true)]
public static extern bool SystemParametersInfo(uint a, uint b, IntPtr c, uint d);
'@
    }
    [void][W32.Cur]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 0x03)
}

function Backup-Cursors {
    if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $file  = Join-Path $BackupDir "cursors-$stamp.reg"
    & reg.exe export 'HKCU\Control Panel\Cursors' $file /y | Out-Null
    Write-Host "Backed up current cursors -> $file" -ForegroundColor DarkGray
    return $file
}

if ($Uninstall) {
    $latest = Get-ChildItem (Join-Path $BackupDir '*.reg') -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw "No backup found in $BackupDir" }
    & reg.exe import $latest.FullName | Out-Null
    Broadcast-CursorChange
    Write-Host "Restored cursors from $($latest.Name)" -ForegroundColor Green
    return
}

if (-not (Test-Path $CursorDir)) { throw "Cursor folder not found: $CursorDir" }

# --- Resolve the file for each slot (.ani wins over .cur) --------------------
$files = @{}
foreach ($slot in $SlotOrder) {
    $ani = Join-Path $CursorDir "BG3_$slot.ani"
    $cur = Join-Path $CursorDir "BG3_$slot.cur"
    if     (Test-Path $ani) { $files[$slot] = $ani }
    elseif (Test-Path $cur) { $files[$slot] = $cur }
    else   { Write-Warning "no file for slot '$slot' - leaving it unchanged" }
}
if ($files.Count -eq 0) { throw "No cursor files found in $CursorDir" }

# --- Sanity-check every file actually loads before touching the registry -----
if (-not ('W32.Load' -as [type])) {
    Add-Type -Namespace W32 -Name Load -MemberDefinition @'
[DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
public static extern IntPtr LoadCursorFromFile(string p);
[DllImport("user32.dll")] public static extern bool DestroyCursor(IntPtr h);
'@
}
foreach ($kv in $files.GetEnumerator()) {
    $h = [W32.Load]::LoadCursorFromFile($kv.Value)
    if ($h -eq [IntPtr]::Zero) { throw "Windows cannot load $($kv.Value) - aborting, registry untouched." }
    [void][W32.Load]::DestroyCursor($h)
}
Write-Host "All $($files.Count) cursor files verified loadable." -ForegroundColor DarkGray

Backup-Cursors | Out-Null

# --- Apply -------------------------------------------------------------------
foreach ($kv in $files.GetEnumerator()) {
    Set-ItemProperty -Path $RegPath -Name $kv.Key -Value $kv.Value -Type ExpandString
}

# Register as a reusable named scheme (shows up in Mouse Properties)
$schemeValue = ($SlotOrder | ForEach-Object { if ($files.ContainsKey($_)) { $files[$_] } else { '' } }) -join ','
$schemesKey  = 'HKCU:\Control Panel\Cursors\Schemes'
if (-not (Test-Path $schemesKey)) { New-Item -Path $schemesKey -Force | Out-Null }
Set-ItemProperty -Path $schemesKey -Name $SchemeName -Value $schemeValue -Type ExpandString

Set-ItemProperty -Path $RegPath -Name '(default)' -Value $SchemeName -Type String
Set-ItemProperty -Path $RegPath -Name 'Scheme Source' -Value 1 -Type DWord

Broadcast-CursorChange

Write-Host ""
Write-Host "Baldur's Gate 3 cursors applied ($($files.Count) slots)." -ForegroundColor Green
Write-Host "Saved as scheme '$SchemeName' in Mouse Properties." -ForegroundColor Green
Write-Host "Undo with:  .\Install-BG3Cursors.ps1 -Uninstall" -ForegroundColor DarkGray
