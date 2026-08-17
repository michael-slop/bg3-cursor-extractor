"""bg3-cursor-click - swap BG3 cursors to their pressed frame on mouse-down.

Baldur's Gate 3 ships each cursor as a PAIR: Cursor_X_1.cur (mouse-up) and
Cursor_X_2.cur (mouse-down). The game swaps them on input. Windows cursor files
cannot do that on their own - .ani plays on a fixed timer with no click trigger -
so this installs a low-level mouse hook and calls SetSystemCursor at press/release.

Run it:
    pythonw bg3_cursor_click.py            # background, no console
    python  bg3_cursor_click.py --verbose  # with logging

The frame folder is found automatically (./frames, then ./raw/Cursors); pass
--raw to override. Only one copy runs at a time - a second launch exits rather
than fighting the first over SetSystemCursor.

Stop it with Ctrl+C, or by killing the process. Cursors are ALWAYS restored on
exit - including on Ctrl+C, logoff, and taskkill - via SystemParametersInfo.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import os
import signal
import sys
import atexit

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# --- Win32 constants ---------------------------------------------------------
WH_MOUSE_LL      = 14
WM_LBUTTONDOWN   = 0x0201
WM_LBUTTONUP     = 0x0202
WM_RBUTTONDOWN   = 0x0204
WM_RBUTTONUP     = 0x0205
LR_LOADFROMFILE  = 0x0010
LR_DEFAULTSIZE   = 0x0040
SPI_SETCURSORS   = 0x0057
SPIF_SENDCHANGE  = 0x02

# The system cursor slots we swap. OCR_NORMAL is the plain arrow; OCR_HAND is
# the link-select hand. These are the two you actually click with.
OCR_NORMAL = 32512
OCR_IBEAM  = 32513
OCR_HAND   = 32649

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype = wt.HHOOK
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = wt.LPARAM
user32.LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT, ctypes.c_int,
                              ctypes.c_int, wt.UINT]
user32.LoadImageW.restype = wt.HANDLE
user32.SetSystemCursor.argtypes = [wt.HANDLE, wt.DWORD]
user32.SetSystemCursor.restype = wt.BOOL
user32.CopyIcon.argtypes = [wt.HANDLE]
user32.CopyIcon.restype = wt.HANDLE

HOOKPROC = ctypes.CFUNCTYPE(wt.LPARAM, ctypes.c_int, wt.WPARAM, wt.LPARAM)


def load_cursor(path):
    """Load a .cur/.ani from disk as an HCURSOR."""
    h = user32.LoadImageW(None, str(path), 2, 0, 0,
                          LR_LOADFROMFILE | LR_DEFAULTSIZE)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def restore_system_cursors():
    """Put Windows' own cursor scheme back. Safe to call more than once."""
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_SENDCHANGE)


ERROR_ALREADY_EXISTS = 183
_mutex = None  # module-level so the handle outlives claim_single_instance()


def claim_single_instance(name=r"Local\bg3_cursor_click"):
    """True if we got the lock; False if another copy already holds it.

    An autostart entry and a hand-run .bat can otherwise both start a hook, and
    two hooks fight over SetSystemCursor - the pressed frame sticks or flickers.
    """
    global _mutex
    _mutex = kernel32.CreateMutexW(None, True, name)
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS


def resolve_raw_dir(explicit, here):
    """Find the folder holding the Cursor_*_1/_2.cur frames.

    The distributed pack keeps them in Click-Animation\\frames; a working repo
    keeps them in raw\\Cursors. Try both rather than making --raw mandatory,
    because an autostart shortcut that omits the flag would fail silently.
    """
    candidates = [explicit] if explicit else [
        os.path.join(here, "frames"),
        os.path.join(here, "raw", "Cursors"),
        os.path.join(os.path.dirname(here), "frames"),
    ]
    for c in candidates:
        if c and os.path.isdir(c):
            return c, candidates
    return None, candidates


class ClickSwapper:
    """Holds the up/down cursor pairs and swaps them on button events."""

    def __init__(self, pairs, verbose=False):
        # pairs: {ocr_id: (up_path, down_path)}
        self.verbose = verbose
        self.up = {}
        self.down = {}
        for ocr, (u, d) in pairs.items():
            self.up[ocr] = load_cursor(u)
            self.down[ocr] = load_cursor(d)
        self.pressed = False

    def log(self, *a):
        if self.verbose:
            print(*a, flush=True)

    def _apply(self, table):
        # SetSystemCursor DESTROYS the handle it is given, so always hand it a
        # copy or the second click has nothing to set.
        for ocr, h in table.items():
            user32.SetSystemCursor(user32.CopyIcon(h), ocr)

    def press(self):
        if self.pressed:
            return
        self.pressed = True
        self._apply(self.down)
        self.log("down")

    def release(self):
        if not self.pressed:
            return
        self.pressed = False
        self._apply(self.up)
        self.log("up")

    def restore(self):
        """Back to the installed BG3 (mouse-up) cursors, then the real scheme."""
        try:
            self._apply(self.up)
        except Exception:
            pass
        restore_system_cursors()


def build_pairs(cursor_dir, raw_dir):
    """Map system cursor slots to their (mouse-up, mouse-down) BG3 files."""
    def pair(name):
        u = os.path.join(raw_dir, f"Cursor_{name}_1.cur")
        d = os.path.join(raw_dir, f"Cursor_{name}_2.cur")
        return (u, d) if os.path.exists(u) and os.path.exists(d) else None

    wanted = {
        OCR_NORMAL: pair("Arrow"),        # pointing hand -> finger flexes in
        OCR_HAND:   pair("ItemPickUp"),   # open glove -> closed fist
    }
    return {k: v for k, v in wanted.items() if v}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--raw", default=None,
                    help="folder of Cursor_*_1/_2.cur frames "
                         "(default: ./frames, then ./raw/Cursors)")
    ap.add_argument("--cursors", default=os.path.join(here, "out"),
                    help="folder of built BG3_*.cur slot files")
    ap.add_argument("--verbose", action="store_true", help="log each press")
    args = ap.parse_args()

    raw, tried = resolve_raw_dir(args.raw, here)
    if not raw:
        sys.exit("ERROR: could not find the cursor frames.\n\n"
                 "       Looked in:\n"
                 + "".join(f"         {p}\n" for p in tried)
                 + "\n       Pass the folder explicitly:\n"
                   "         --raw \"<path to the frames folder>\"\n\n"
                   "       In the cursor pack that folder is\n"
                   "       Click-Animation\\frames, and the easiest way to start\n"
                   "       this is \"2 - ADD CLICK ANIMATION (needs Python).bat\".")

    # One hook only - see claim_single_instance().
    if not claim_single_instance():
        print("bg3-cursor-click is already running; leaving the existing one alone.")
        return

    pairs = build_pairs(args.cursors, raw)
    if not pairs:
        sys.exit(f"ERROR: no _1/_2 cursor pairs found in {raw}")

    sw = ClickSwapper(pairs, verbose=args.verbose)

    # Restore on every plausible exit path, so we never strand a pressed cursor.
    atexit.register(sw.restore)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGBREAK):
        try:
            signal.signal(sig, lambda *_: sys.exit(0))
        except (ValueError, AttributeError, OSError):
            pass

    @HOOKPROC
    def hook(code, wparam, lparam):
        if code >= 0:
            if wparam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                sw.press()
            elif wparam in (WM_LBUTTONUP, WM_RBUTTONUP):
                sw.release()
        return user32.CallNextHookEx(None, code, wparam, lparam)

    h = user32.SetWindowsHookExW(WH_MOUSE_LL, ctypes.cast(hook, ctypes.c_void_p),
                                 None, 0)
    if not h:
        sys.exit(f"failed to install mouse hook: {ctypes.WinError(ctypes.get_last_error())}")

    print(f"bg3-cursor-click running - {len(pairs)} cursor pair(s) swap on click.")
    print("Ctrl+C to stop (cursors are restored automatically).")

    # Standard message pump; the hook fires on this thread.
    msg = wt.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(h)
        sw.restore()
        print("stopped, cursors restored.")


if __name__ == "__main__":
    main()
