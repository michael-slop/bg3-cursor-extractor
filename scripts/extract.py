"""Extract the cursor assets from your own installed copy of Baldur's Gate 3.

REQUIRES A LEGALLY OWNED, INSTALLED COPY OF THE GAME. This script reads the
cursors out of your local Game.pak. It does not download game assets, and it
cannot work without the game installed - there is nothing to extract from.

Usage:
    python extract.py                          # auto-detect the install
    python extract.py --game-dir "D:\\...\\Baldurs Gate 3"
    python extract.py --divine "C:\\lslib\\Tools\\Divine.exe"
"""
import argparse
import os
import shutil
import subprocess
import sys

# Common Steam / GOG install locations, checked in order.
CANDIDATE_DIRS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3",
    r"C:\Program Files\Steam\steamapps\common\Baldurs Gate 3",
    r"C:\GOG Games\Baldurs Gate 3",
    r"C:\Program Files (x86)\GOG Galaxy\Games\Baldurs Gate 3",
]

PAK = "Game.pak"
INTERNAL_GLOB = "Cursors/*"


def find_game_dir(explicit=None):
    """Locate the BG3 install, or explain clearly why we can't."""
    if explicit:
        pak = os.path.join(explicit, "Data", PAK)
        if not os.path.isfile(pak):
            sys.exit(
                f"\nERROR: no {PAK} under {explicit}\n"
                f"       Expected: {pak}\n\n"
                "       Point --game-dir at the folder that contains the\n"
                "       'Data' directory (the one with Game.pak inside).\n"
            )
        return explicit

    for d in CANDIDATE_DIRS:
        if os.path.isfile(os.path.join(d, "Data", PAK)):
            return d

    # Try to read extra Steam library folders.
    vdf = r"C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf"
    if os.path.isfile(vdf):
        try:
            with open(vdf, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if '"path"' in line:
                        base = line.split('"')[3].replace("\\\\", "\\")
                        cand = os.path.join(
                            base, "steamapps", "common", "Baldurs Gate 3")
                        if os.path.isfile(os.path.join(cand, "Data", PAK)):
                            return cand
        except OSError:
            pass

    sys.exit(
        "\n"
        "=====================================================================\n"
        " Baldur's Gate 3 was not found on this machine.\n"
        "=====================================================================\n"
        "\n"
        " This tool extracts cursors from YOUR OWN installed copy of the game.\n"
        " It does not download anything from Larian and it cannot produce the\n"
        " cursors without the game files present - there is nothing to read.\n"
        "\n"
        " If you do own BG3 but it lives somewhere unusual, point at it:\n"
        "     python extract.py --game-dir \"D:\\Games\\Baldurs Gate 3\"\n"
        "\n"
        " That folder should contain a 'Data' directory with Game.pak in it.\n"
    )


def find_divine(explicit=None):
    """Locate Divine.exe from LSLib."""
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit(f"ERROR: no Divine.exe at {explicit}")
        return explicit

    for c in ("Divine.exe",
              os.path.join("lslib", "Tools", "Divine.exe"),
              os.path.join("lslib", "Packed", "Tools", "Divine.exe")):
        if os.path.isfile(c):
            return os.path.abspath(c)

    found = shutil.which("Divine.exe")
    if found:
        return found

    sys.exit(
        "\nERROR: Divine.exe (from LSLib) not found.\n\n"
        "  Download the ExportTool zip from:\n"
        "    https://github.com/Norbyte/lslib/releases\n\n"
        "  Unzip it next to this script as 'lslib/', or pass the path:\n"
        "    python extract.py --divine \"C:\\path\\to\\Divine.exe\"\n"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", help="BG3 install folder (contains Data\\)")
    ap.add_argument("--divine", help="path to Divine.exe from LSLib")
    ap.add_argument("--out", default="raw", help="output folder (default: raw)")
    args = ap.parse_args()

    game = find_game_dir(args.game_dir)
    divine = find_divine(args.divine)
    pak = os.path.join(game, "Data", PAK)

    print(f"game:   {game}")
    print(f"divine: {divine}")
    print(f"pak:    {pak}\n")

    env = dict(os.environ)
    # LSLib targets .NET 8; allow it to run on a newer runtime if that's what's here.
    env.setdefault("DOTNET_ROLL_FORWARD", "Major")

    # Divine rejects relative destinations: "Cannot proceed without absolute path"
    out_abs = os.path.abspath(args.out)
    os.makedirs(out_abs, exist_ok=True)

    cmd = [divine, "-g", "bg3", "-a", "extract-package",
           "-s", os.path.abspath(pak), "-d", out_abs,
           "-x", INTERNAL_GLOB, "-l", "off"]
    print("running:", " ".join(cmd), "\n")
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        sys.exit(f"\nDivine failed with exit code {r.returncode}.")

    cur_dir = os.path.join(out_abs, "Cursors")
    n_cur = len([f for f in os.listdir(cur_dir)
                 if f.lower().endswith(".cur")]) if os.path.isdir(cur_dir) else 0
    frames = os.path.join(cur_dir, "MC_loader_anim")
    n_png = len(os.listdir(frames)) if os.path.isdir(frames) else 0

    print(f"\nExtracted {n_cur} cursors and {n_png} animation frames to {cur_dir}")
    if n_cur == 0:
        sys.exit("No .cur files found - the pak layout may have changed in a patch.")
    print("\nNext:  python build_set.py     (build the Windows cursor set)")


if __name__ == "__main__":
    main()
