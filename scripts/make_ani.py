"""Build a Windows .ani (RIFF ACON) from a list of PNG frames.

ANI layout:
  RIFF 'ACON'
    'anih' (36 bytes)  header
    LIST 'fram'
      'icon' * n       each a full .cur file (32bpp ARGB)
"""
import struct, sys, os
from PIL import Image


def png_to_cur(img: Image.Image, hx: int, hy: int) -> bytes:
    """Pack a PIL RGBA image into a single-image .cur (32bpp BMP + AND mask)."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    # DIB: BITMAPINFOHEADER with doubled height (XOR + AND masks)
    hdr = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, 0, 0, 0, 0, 0)

    # XOR: BGRA, bottom-up
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]
            xor += bytes((b, g, r, a))

    # AND mask: 1bpp, rows padded to 4 bytes. 0 = opaque.
    row_bytes = ((w + 31) // 32) * 4
    andm = bytearray()
    for y in range(h - 1, -1, -1):
        row = bytearray(row_bytes)
        for x in range(w):
            if px[x, y][3] == 0:
                row[x >> 3] |= 0x80 >> (x & 7)
        andm += row

    dib = hdr + bytes(xor) + bytes(andm)

    # ICONDIR + one ICONDIRENTRY; for .cur the "planes/bpp" fields hold the hotspot
    icondir = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, hx, hy, len(dib), 22)
    return icondir + entry + dib


def build_ani(frames, out_path, jif=6, hx=0, hy=0):
    """jif = display rate per frame in 1/60s ticks."""
    icons = []
    for f in frames:
        with Image.open(f) as im:
            icons.append(png_to_cur(im, hx, hy))

    n = len(icons)
    # anih: cbSize, nFrames, nSteps, wx, wy, bpp, nPlanes, rate, flags
    # flags bit0 = icon data (not raw DIB), bit1 = seq chunk present
    anih = struct.pack("<IIIIIIIII", 36, n, n, 0, 0, 0, 0, jif, 0x1)

    fram = b""
    for ic in icons:
        pad = b"\x00" if len(ic) & 1 else b""
        fram += b"icon" + struct.pack("<I", len(ic)) + ic + pad
    fram_chunk = b"LIST" + struct.pack("<I", 4 + len(fram)) + b"fram" + fram

    body = b"ACON" + b"anih" + struct.pack("<I", 36) + anih + fram_chunk
    riff = b"RIFF" + struct.pack("<I", len(body)) + body

    with open(out_path, "wb") as fh:
        fh.write(riff)
    return out_path, n


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    jif = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    frames = [os.path.join(src, f"MC_loading_frame{i}.png") for i in range(1, 15)]
    missing = [f for f in frames if not os.path.exists(f)]
    if missing:
        sys.exit(f"missing frames: {missing}")
    p, n = build_ani(frames, out, jif=jif)
    print(f"wrote {p} ({n} frames, {os.path.getsize(p)} bytes, {jif}/60s per frame)")
