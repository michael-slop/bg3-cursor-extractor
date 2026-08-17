# HANDOFF — bg3-cursor-extractor

Status as of **2026-08-14**. Read this before touching the repo.

## What it is

Extracts Baldur's Gate 3's real in-game cursors and installs them as a Windows
cursor scheme. Public at https://github.com/michael-slop/bg3-cursor-extractor.

Built because every existing "BG3 cursor set" is traced from screenshots — the
popular RW-Designer one says so in its own readme — and looks it. The real assets
are extractable and dramatically better.

## State: done and deployed

- Applied and verified live on **pHub** and **SloppyLaptopy**.
- `Desktop\BG3-Cursors.zip` (400 KB) is the portable copy — all 100 cursors plus a
  double-click installer. Also sitting on SloppyLaptopy's desktop.
- Pipeline re-verified end to end from a clean state after the last fix.

Nothing is in progress. No known bugs.

## The two things everyone gets wrong

**1. The cursors are native Windows `.cur`, not DDS.**
They live at `Cursors/` — *top level* inside `Data\Game.pak`, not under
`Public/Game/GUI/Assets/` where every other GUI asset lives. 100 `.cur` files plus
`MC_loader_anim/` (14 PNG frames). BG3's UI is NoesisGUI, which speaks `.cur`/`.ani`
natively, so **no conversion is needed**. Don't build a DDS pipeline; it's wasted work.

**2. The `_1`/`_2` pairs are mouse-up / mouse-down frames.**
`_1` = released, `_2` = pressed. The pointing finger curls in, the glove closes to a
fist, the bow looses its arrow, the padlock's shackle swings open. BG3 swaps them the
instant you press a button.

**Windows `.ani` cannot do this.** The format plays frames on a fixed timer and has no
click trigger, so building a pair into an `.ani` produces a cursor that twitches
constantly whether you're clicking or not. Don't try it — it was tried, installed, and
reverted. `build_set.py` installs the `_1` frame statically; `bg3_cursor_click.py`
supplies the pressed frame via a `WH_MOUSE_LL` hook calling `SetSystemCursor`.

The loading hourglass is the exception — a genuine 14-frame timed animation, so it
ships as a real `.ani`.

## The click hook needs an autostart (fixed 2026-08-17)

The static cursors persist because they are registry entries. The click animation is
a **process**, so it dies at shutdown and the cursors go static until it is started
again. Reported as "doesn't animate until I relaunch that py script" — it was never
running at login, because nothing started it. Verified at the time: no entry in
HKCU/HKLM `Run`/`RunOnce`, neither Startup folder, none of 216 scheduled tasks.

Fixed with a Startup-folder shortcut, created by `4 - RUN AT LOGIN (set up).bat` in
the pack (`5 - ...(remove).bat` undoes it). Two details that matter:

- The shortcut's target must be an **absolute** `pythonw.exe` path. Every Python on
  pHub is a user-scope install resolved via *user* `PATH`; a bare `pythonw` is not
  dependable for a login-launched process.
- `bg3_cursor_click.py` now takes a named mutex (`Local\bg3_cursor_click`). Without
  it, the autostart plus a hand-run `2 - ADD CLICK ANIMATION.bat` gives two hooks
  fighting over `SetSystemCursor`, and the pressed frame sticks or flickers.

**GlazeWM `startup_commands` was considered and deliberately rejected** — don't
"fix" it that way later. It only helps machines running GlazeWM (the pack now has
third-party users who don't), and that config was being edited by a concurrent
session at the time, which is a known hazard here.

Also fixed alongside: `--raw` used to default to `<script dir>\raw\Cursors`, which
does not exist in the shipped pack (frames live in `frames\`), and the error message
pointed at `extract.py`, which the pack does not contain. A no-argument launch
therefore failed with dead-end advice. It now falls back `./frames` →
`./raw/Cursors` → `../frames` and names the paths it tried.

## Traps

- **`Divine.exe` rejects relative `-d` paths** — fails with
  `Cannot proceed without absolute path [E2]`. Easy to miss because it works when run
  from inside the tool's own directory. `extract.py` calls `os.path.abspath` now.
- **LSLib targets .NET 8**; pHub has 6/9/10. `DOTNET_ROLL_FORWARD=Major` runs it on 9
  with no extra install — the scripts set this automatically.
- **`granny2.dll` is missing from `Tools\`** in ExportTool v1.20.4 (a known bg3.wiki
  issue). Irrelevant for cursors, only matters for model conversion.
- **`$PSScriptRoot` is empty under Windows PowerShell 5.1** in some invocation modes;
  `Install-BG3Cursors.ps1` falls back to `$MyInvocation.MyCommand.Path`.
- **Don't delete `Desktop\BG3-Cursors\`** — Windows reads cursor files from disk every
  session. Deleting it leaves the registry pointing at nothing. Move it and re-run the
  installer instead.

## Never commit the artwork

The repo is tooling only, deliberately. `.gitignore` blocks `*.cur`, `*.ani`, `*.dds`,
the contact sheet, and every output directory. The extracted art is Larian's copyright:
personal use is fine, public redistribution is not.

Before any commit that might touch output, check:

```bash
git add -A -n | grep -iE "\.(cur|ani|dds)'?$"   # must be empty
```

And after pushing, confirm the remote tree is clean:

```bash
gh api repos/michael-slop/bg3-cursor-extractor/git/trees/main?recursive=1 \
  --jq '[.tree[].path | select(test("cur$|ani$|dds$|png$"; "i"))] | length'   # must be 0
```

## Rebuilding from scratch

```bash
python scripts/extract.py                                   # needs BG3 installed
python scripts/build_set.py                                 # -> out/ (17 files)
powershell -File scripts/Install-BG3Cursors.ps1             # apply
powershell -File scripts/Install-BG3Cursors.ps1 -Uninstall  # revert
```

`scripts/verify_ani.ps1` asks Win32 `LoadCursorFromFile` to parse each file — use it
rather than trusting that a file was written. The installer runs this check itself and
aborts before touching the registry if anything fails.

## Process note

The `_1`/`_2` meaning was got wrong **twice** — first "hover states", then "continuous
animation" — before simply asking Michael, who plays the game and knew it was click.
Both wrong answers were written into the docs as settled fact, and the second one put a
twitching pointer on two live machines before being reverted.

For anything about how software *behaves in use* — when something triggers, what it
looks like, whether it loops — ask him rather than inferring from the files. The files
say what the bytes are; they don't say when the game decides to show them. Full account
in `Desktop\BG3-Cursors\WHAT-WENT-WRONG.txt`.

## Possible next steps (none started)

- Larger cursors for 4K: the game has no higher-res source, so this means upscaling.
  Prefer raising the Windows cursor-size slider first.
- A `-Slot` flag on the installer to swap one cursor without redoing the whole scheme.
- Extend `bg3_cursor_click.py` beyond Arrow/Hand — the pairs exist for ~45 cursors, but
  Windows only exposes a handful of system slots worth swapping.
- Optional: a tray icon / autostart shortcut for the click hook, so it survives reboot
  without a manual Startup-folder step.
