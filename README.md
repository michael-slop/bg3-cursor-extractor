# BG3 Cursor Extractor

Turn Baldur's Gate 3's **actual in-game cursors** into a Windows cursor scheme —
including a real animated `.ani` built from the game's loading hourglass.

> ### ⚠️ You must own and have installed Baldur's Gate 3
>
> **This repository contains no game assets and never will.** It is tooling only.
> The scripts read the cursors out of *your own local copy* of the game
> (`Data\Game.pak`). Nothing is downloaded from Larian, and there is no bundled
> artwork, mirror, or fallback — **without the game installed there is literally
> nothing to extract.** `extract.py` checks for the install first and stops with a
> plain explanation if it can't find one.
>
> The cursor artwork is © Larian Studios. Keep what you extract for personal use.

---

## Why this exists

Every "BG3 cursor set" floating around is redrawn or traced from screenshots. The
most popular one says so in its own readme: *"I mainly used screenshots to create
them."* You can tell — the detail is gone.

It turns out that isn't necessary. Larian ships the cursors as **native Windows
`.cur` files** inside `Game.pak`. They can be pulled out and used directly, with
zero conversion and zero quality loss.

| | Traced from screenshots | This tool |
|---|---|---|
| Source | Screenshots, redrawn by hand | The game's own `.cur` files |
| Fidelity | Approximate | Byte-identical to the game's |
| Coverage | ~14 generic Windows cursors | All 100 game cursors |
| Animation | A generic spinner | The game's real 14-frame hourglass |

---

## What you need

| Requirement | Notes |
|---|---|
| **Baldur's Gate 3, installed** | Steam or GOG. The whole point — see the warning above. |
| **Windows** | The output is Windows `.cur` / `.ani`. |
| **Python 3.8+** with Pillow | `pip install pillow` |
| **[LSLib](https://github.com/Norbyte/lslib/releases)** | Norbyte's `ExportTool` zip. Provides `Divine.exe`. |
| **.NET 8 Desktop Runtime** | For LSLib. If you have a newer .NET, the scripts set `DOTNET_ROLL_FORWARD=Major` so it works anyway. |

Unzip LSLib next to the scripts as `lslib/`, or pass `--divine` with its path.

---

## Usage

```bash
# 1. Pull the cursors out of your installed game
python scripts/extract.py
#    ...or point it at an unusual install location:
python scripts/extract.py --game-dir "D:\Games\Baldurs Gate 3"

# 2. Build the Windows cursor set (17 slots + the animated .ani)
python scripts/build_set.py

# 3. Apply it
powershell -ExecutionPolicy Bypass -File scripts/Install-BG3Cursors.ps1
```

### Click animation (optional)

To get the pressed frame on real clicks — the finger curling in as you hold the
button, exactly like the game:

```bash
pythonw scripts/bg3_cursor_click.py --raw scripts/raw/Cursors
```

It installs a `WH_MOUSE_LL` hook, calls `SetSystemCursor` on button-down and
button-up, and restores your cursors on every exit path. Standard library only —
no extra packages.

The frames folder is found automatically (`./frames`, then `./raw/Cursors`), so
`--raw` is optional. A named mutex (`Local\bg3_cursor_click`) keeps it to one
instance — a second launch exits quietly rather than fighting the first over
`SetSystemCursor`, which matters once an autostart entry and a manual launch both
exist.

**It is a process, so it stops at shutdown.** To start it at login, create a
Startup-folder shortcut whose target is an absolute `pythonw.exe` path:

```
target    C:\...\pythonw.exe
arguments "<pack>\Click-Animation\bg3_cursor_click.py" --raw "<pack>\Click-Animation\frames"
```

Use the absolute interpreter path, not a bare `pythonw` — Python is often a
user-scope install resolved through the *user* `PATH`, which is not dependable for
every login-launched process. The cursor pack ships
`4 - RUN AT LOGIN (set up).bat` / `5 - RUN AT LOGIN (remove).bat` to do this.

Skip the hook entirely and everything still works — you just get the mouse-up frame
all the time, which looks entirely normal.

Undo at any time:

```powershell
.\scripts\Install-BG3Cursors.ps1 -Uninstall
```

The installer **backs up your current cursors to a `.reg` first**, and verifies
every file loads via `LoadCursorFromFile` before touching the registry — if any
cursor is malformed it aborts and changes nothing.

---

## What comes out

- **100 cursors** — every one the game uses: gauntlets, crossed swords, bows,
  padlocks, treasure chests, the anvil, the shovel, speech bubbles, the ear.
- **A real animated cursor** — the 14-frame loading hourglass, rebuilt as a
  proper RIFF/ACON `.ani`.
- **17 mapped to Windows slots** — sensible defaults you can override freely.

### Slot mapping

| Windows slot | BG3 cursor | | Windows slot | BG3 cursor |
|---|---|---|---|---|
| Arrow | Arrow | | Hand | ItemPickUp |
| Help | Identify | | Person | Talk |
| IBeam | InputText | | Pin | Listen |
| No | Cross | | NWPen | Repair |
| Crosshair | GroundCast | | UpArrow | Bow |
| SizeAll | ItemMove | | SizeNS | scalerArrowV |
| SizeNESW | scalerArrow | | SizeNWSE | *rotated 90°* |
| SizeWE | *rotated 90°* | | Wait / AppStarting | loading animation |

---

## Things worth knowing

**The `_1` / `_2` pairs are input states, not a timed loop.** `_1` is the mouse-up
frame and `_2` is the mouse-down frame — the pointing finger curls in, the glove
closes to a fist, the bow looses its arrow, the padlock's shackle swings open. BG3
swaps them the instant you press a button.

This matters because **Windows cursor files cannot reproduce that.** The `.ani`
format plays its frames on a fixed timer and has no click trigger, so building a
pair into an `.ani` gives you a cursor that twitches constantly whether you're
clicking or not. `build_set.py` therefore installs the mouse-up frame statically,
and `bg3_cursor_click.py` delivers the pressed frame via a low-level mouse hook —
see [Click animation](#click-animation-optional).

The loading hourglass is the exception: that one *is* a real 14-frame timed
animation in the game, so it ships as a true `.ani` and needs no helper.

**Cursors are 32×32** (the hourglass is 40×40). That's the game's native size — not
a limitation of this tool. There is no higher-resolution version in the game files.
On a 4K display, raise the Windows cursor-size slider rather than upscaling these.

**Hotspots are mostly (0,0)** in the game files, which is correct for pointer-shaped
art. For slots where that feels wrong on a desktop (resize, move, text caret) the
hotspot is re-centred to (16,16). The artwork itself is never modified.

**BG3 has no diagonal-resize or horizontal-resize cursor,** so `SizeNWSE` and
`SizeWE` are the game's own scaler arrows rotated 90°. Everything else is
the unmodified game file.

---

## Files

| Path | What it does |
|---|---|
| `scripts/extract.py` | Finds your BG3 install, pulls `Cursors/*` out of `Game.pak` |
| `scripts/build_set.py` | Maps cursors to Windows slots, fixes hotspots, builds the `.ani` |
| `scripts/make_ani.py` | A from-scratch RIFF/ACON encoder — PNG frames → Windows `.ani` |
| `scripts/bg3_cursor_click.py` | Mouse hook that swaps to the pressed frame on click |
| `scripts/Install-BG3Cursors.ps1` | Registers the scheme, with backup and clean uninstall |
| `scripts/verify_ani.ps1` | Asks Win32 to load each cursor — catches malformed files |

`make_ani.py` is standalone and has nothing to do with BG3 — if you just want to
build a Windows animated cursor from a folder of PNGs, it does that.

---

## Licence

The **code** here is MIT (see `LICENSE`).

The **cursor artwork it extracts is not mine to license** — it's Larian Studios'
copyrighted property. Extracting it from a copy you own for personal use is
ordinary private use. Redistributing the extracted `.cur` files is not, regardless
of it being free or credited. That's exactly why this repo ships tooling instead of
art: run it against your own copy and you get the same result in a minute.

Not affiliated with or endorsed by Larian Studios.
