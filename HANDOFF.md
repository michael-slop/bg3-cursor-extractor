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

**2. The `_1`/`_2` pairs are hover states, NOT animation frames.**
`_1` = active/highlighted, `_2` = dimmed. The padlock is closed in `_1` and open in
`_2`; the speech bubble is bright vs grey. The game swaps them on hover, which reads
as "animation" in play. Only the loading hourglass is genuinely frame-animated.
`build_set.py` uses the `_1` variants. Verify visually before assuming otherwise.

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

## Possible next steps (none started)

- Larger cursors for 4K: the game has no higher-res source, so this means upscaling.
  Prefer raising the Windows cursor-size slider first.
- A `-Slot` flag on the installer to swap one cursor without redoing the whole scheme.
