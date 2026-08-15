"""Assemble the BG3 cursor set: copy the chosen .cur files into Windows-slot names,
fix hotspots where BG3's (0,0) is wrong for a desktop role, and emit the .ani.
"""
import os, shutil, struct, sys
from make_ani import build_ani

RAW = "raw/Cursors"
OUT = "out"

# Windows slot -> (BG3 source file, hotspot override or None to keep original)
# The _1 variants are the bright/active art; _2 are the dimmed state.
MAPPING = {
    # slot name          source                          hotspot
    "Arrow":            ("Cursor_Arrow_1.cur",            None),
    "Help":             ("Cursor_Identify_1.cur",         None),
    "AppStarting":      (None,                            None),   # -> .ani below
    "Wait":             (None,                            None),   # -> .ani below
    "Crosshair":        ("Cursor_GroundCast_1.cur",       None),
    "IBeam":            ("Cursor_InputText.cur",          (16, 16)),
    "NWPen":            ("Cursor_Repair_1.cur",           None),
    "No":               ("Cursor_Cross_1.cur",            (16, 16)),
    "SizeNS":           ("Cursor_scalerArrowV.cur",       (16, 16)),
    "SizeNESW":         ("Cursor_scalerArrow.cur",        (16, 16)),
    "SizeAll":          ("Cursor_ItemMove_1.cur",         (16, 16)),
    "UpArrow":          ("Cursor_Bow_1.cur",              None),
    "Hand":             ("Cursor_ItemPickUp_1.cur",       None),
    "Person":           ("Cursor_Talk_1.cur",             None),
    "Pin":              ("Cursor_Listen_1.cur",           None),
}

# BG3 ships only two scaler arrows: scalerArrow is diagonal (NE-SW) and
# scalerArrowV is vertical. Rotate each 90 deg to get the missing pair.
DERIVED = {
    "SizeNWSE": ("Cursor_scalerArrow.cur", 90),   # NE-SW -> NW-SE
    "SizeWE":   ("Cursor_scalerArrowV.cur", 90),  # vertical -> horizontal
}


def set_hotspot(path, hx, hy):
    """Rewrite the hotspot fields in a single-image .cur in place."""
    with open(path, "r+b") as f:
        d = bytearray(f.read())
        struct.pack_into("<HH", d, 10, hx, hy)   # xHotspot, yHotspot in ICONDIRENTRY
        f.seek(0)
        f.write(d)


def make_rotated(src, angle, dst):
    """Rotate a cursor's art to derive a missing direction, via PIL."""
    from PIL import Image
    from make_ani import png_to_cur
    with Image.open(src) as im:
        im = im.convert("RGBA")
        rot = im.rotate(angle, resample=Image.BICUBIC, expand=False)
    with open(dst, "wb") as f:
        f.write(png_to_cur(rot, 16, 16))


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []

    for slot, (src, hs) in MAPPING.items():
        if src is None:
            continue
        s = os.path.join(RAW, src)
        if not os.path.exists(s):
            print(f"  !! missing source {src} for {slot}")
            continue
        d = os.path.join(OUT, f"BG3_{slot}.cur")
        shutil.copy2(s, d)
        if hs:
            set_hotspot(d, *hs)
        made.append((slot, d, src))

    for slot, (src, ang) in DERIVED.items():
        s = os.path.join(RAW, src)
        d = os.path.join(OUT, f"BG3_{slot}.cur")
        make_rotated(s, ang, d)
        made.append((slot, d, f"{src} rotated {ang}deg"))

    # Animated: the 14-frame loading hourglass
    frames = [os.path.join(RAW, "MC_loader_anim", f"MC_loading_frame{i}.png")
              for i in range(1, 15)]
    # frames are 40x40, so centre the hotspot at 20,20
    for slot, jif in (("Wait", 5), ("AppStarting", 5)):
        d = os.path.join(OUT, f"BG3_{slot}.ani")
        build_ani(frames, d, jif=jif, hx=20, hy=20)
        made.append((slot, d, "MC_loader_anim (14 frames)"))

    print(f"\nBuilt {len(made)} cursor files:\n")
    for slot, path, src in sorted(made):
        print(f"  {slot:14s} <- {src}")
    return made


if __name__ == "__main__":
    main()
