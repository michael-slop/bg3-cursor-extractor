# Verify a cursor file by asking Win32 LoadCursorFromFile to parse it.
# A malformed .ani/.cur returns NULL -> this is a real check, not a file-exists check.
param([Parameter(Mandatory=$true)][string[]]$Path)

Add-Type -Namespace W -Name U -MemberDefinition @'
[DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
public static extern IntPtr LoadCursorFromFile(string lpFileName);
[DllImport("user32.dll")]
public static extern bool DestroyCursor(IntPtr h);
[DllImport("user32.dll")]
public static extern bool GetIconInfo(IntPtr hIcon, out ICONINFO i);
[StructLayout(LayoutKind.Sequential)]
public struct ICONINFO { public bool fIcon; public int xHotspot; public int yHotspot; public IntPtr hbmMask; public IntPtr hbmColor; }
'@

$fail = 0
foreach ($p in $Path) {
    $full = (Resolve-Path $p -ErrorAction SilentlyContinue).Path
    if (-not $full) { Write-Host "MISSING  $p" -ForegroundColor Red; $fail++; continue }
    $h = [W.U]::LoadCursorFromFile($full)
    if ($h -eq [IntPtr]::Zero) {
        $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        Write-Host ("FAIL     {0}  (Win32 error {1})" -f (Split-Path $full -Leaf), $err) -ForegroundColor Red
        $fail++
    } else {
        $ii = New-Object W.U+ICONINFO
        $null = [W.U]::GetIconInfo($h, [ref]$ii)
        Write-Host ("OK       {0}  hotspot=({1},{2})" -f (Split-Path $full -Leaf), $ii.xHotspot, $ii.yHotspot) -ForegroundColor Green
        [void][W.U]::DestroyCursor($h)
    }
}
Write-Host ""
if ($fail) { Write-Host "$fail file(s) FAILED to load" -ForegroundColor Red; exit 1 }
else { Write-Host "All $($Path.Count) cursor file(s) loaded successfully by Windows" -ForegroundColor Green }
