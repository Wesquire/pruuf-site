#!/usr/bin/env python3
"""Full-page screenshots of every page, at three widths.

    (cd site && python3 -m http.server 8000 &)
    python3 site/shots.py

For looking at the site all at once rather than a viewport at a time. Spacing
that reads well in a 900px window can be badly out of rhythm over 6,000px of
page, and the only way to see that is to look at the whole page.

Two details that both cost a wasted round of "verified" screenshots elsewhere in
this project:

· Headless Chrome's --screenshot captures the WINDOW, not the document. Asking
  for 1440x1200 gives you the first 1200px of a 16,000px page and nothing tells
  you the rest was dropped. So the window is opened absurdly tall and the blank
  tail is trimmed off afterwards.

· The reveal-on-scroll animation would leave everything below the fold blank in
  a capture that never scrolls. `?motion=off` takes the same code path as
  prefers-reduced-motion and shows everything at once.

The output directory is emptied first. A screenshot harness that serves a stale
image is worse than no harness: it is evidence for a change that did not happen.
"""

import os
import shutil
import subprocess
import sys
import urllib.request
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "build", "site-shots")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8000

# Derived from what is actually on disk, never typed.
#
# This was a hand-maintained list, and it did what hand-maintained lists do:
# `security.html` was added, the harness reported success, and the one new page
# was the only page nobody had looked at. A screenshot run that silently skips a
# page is worse than one that fails, because it produces a clean bill of health.
PAGES = sorted(
    f[:-5] for f in os.listdir(HERE) if f.endswith(".html")
)
# 500 is the NARROWEST capture Chrome will actually produce.
#
# `--window-size=390` yields a 390-pixel-wide IMAGE but a 500-CSS-pixel layout
# viewport — headless Chrome clamps the window and then crops. The result looks
# exactly like a site overflowing its container: text clipped mid-word down the
# right edge of every "mobile" capture. Half an hour went into hunting a layout
# bug that did not exist, in a harness that reported it confidently.
#
# Verified by loading a probe page that printed `documentElement.clientWidth`
# into the capture: 390 in, 500 out, in both --headless=old and --headless=new.
#
# So the narrow capture is honestly labelled 500. A true 375/390 viewport needs
# a real browser or CDP device emulation; the site is checked at 390 that way
# instead.
MIN_HEADLESS_WIDTH = 500
WIDTHS = [("narrow", 500), ("tablet", 820), ("desktop", 1440)]
TALL = 26000          # taller than any page here; trimmed back afterwards


def trim(path):
    """Cut the uniform tail left by the over-tall window.

    Below the end of the document Chrome paints the body background, so the
    real page height is the last row that is NOT that flat colour.

    Scanned linearly from the bottom rather than by bisection. Bisection needs
    the property "everything below row X is uniform" to be monotonic, and it
    is not — any full-width band of flat colour part-way up the page satisfies
    the test, so the search converged on it and cropped whole pages down to a
    few hundred pixels. Three of the twenty-one captures came out truncated
    that way, and two of those looked plausible enough to accept.
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    stride = w * 3
    data = im.tobytes()
    tail = data[(h - 1) * stride:h * stride]

    row = h - 1
    while row > 0 and data[row * stride:(row + 1) * stride] == tail:
        row -= 1

    bottom = min(h, row + 2)
    im.crop((0, 0, w, bottom)).save(path, optimize=True)
    return (w, bottom)


def main():
    if not os.path.exists(CHROME):
        print(f"No Chrome at {CHROME}")
        return 1
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/", timeout=5)
    except Exception:
        print(f"Nothing serving on :{PORT}. Start one:")
        print(f"  (cd site && python3 -m http.server {PORT})")
        return 1

    # A note for whoever reads these images: the window is 26,000px tall, so
    # any `vh` unit resolves against THAT rather than against a real screen.
    # Nothing on the site sizes itself in vh for exactly this reason — if
    # something starts to, its capture will look absurdly stretched and the
    # capture will be the thing that is wrong, not the page.
    too_narrow = [w for _, w in WIDTHS if w < MIN_HEADLESS_WIDTH]
    if too_narrow:
        print(f"Widths below {MIN_HEADLESS_WIDTH} are cropped, not rendered: {too_narrow}")
        print("See the note on MIN_HEADLESS_WIDTH. Refusing to produce a "
              "screenshot that shows a layout the browser never laid out.")
        return 1

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    for page in PAGES:
        for label, width in WIDTHS:
            path = os.path.join(OUT, f"{page}-{label}.png")
            subprocess.run([
                CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                f"--window-size={width},{TALL}",
                f"--screenshot={path}",
                "--virtual-time-budget=6000",
                f"http://localhost:{PORT}/{page}.html?motion=off",
            ], capture_output=True, timeout=120)
            if not os.path.exists(path):
                print(f"  {page:<12} {label:<8} FAILED")
                continue
            size = trim(path)
            print(f"  {page:<12} {label:<8} {size[0]}x{size[1]}"
                  f"   {os.path.getsize(path) // 1024}KB")

    print(f"\n→ {os.path.relpath(OUT, os.path.dirname(HERE))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
