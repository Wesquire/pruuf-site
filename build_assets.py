#!/usr/bin/env python3
"""Turn the marketing renders into web-weight assets.

Sources are `AppStore/screenshots/framed-web/` — the real device, drawn to
Apple's own geometry, on transparency and cropped to the hardware. Produced by
`python3 AppStore/frame_devices.py --web`.

This pointed at the bodiless `rounded/` screens for a while, on the reasoning
that at web sizes the black slab is most of the picture. That reasoning was
sound and the result was still wrong: without the hardware, each image is a
coloured rectangle that could be anything, and a page whose whole argument is
"this product was considered" cannot afford to look unfinished. The frame is
what makes it read as a real thing on a real phone.

What it must NOT be is the App Store framing, which draws the device on an
opaque cream canvas at an exact required size. On a web page that canvas is a
pale box fighting whatever section it sits in. The `--web` mode is the same
geometry with the backdrop removed and the shadow kept.

They are still 1242–2752px and ~1MB each, so shipping them untouched would make
the landing page several megabytes, which on the 4G connection of somebody's
mother is thirty seconds of white screen — and this site's entire argument is
that we are the calm, considered option.

Each source produces two files:

  name.webp   what almost everybody gets. Alpha, ~8x smaller than the PNG.
  name.png    the fallback, quantised to a 255-colour palette + alpha.

They are wired up with <picture><source type="image/webp">, so a browser that
cannot do WebP still gets a correct, transparent image rather than a broken one.

Idempotent: run it as often as you like. Re-run it after regenerating anything
in ../marketing.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "assets", "img")

# (source, output stem, target width)
#
# Widths are 2x the largest CSS size the asset is ever displayed at, which is
# the point past which a retina screen cannot tell the difference. Nothing here
# is displayed above ~600px CSS, so nothing needs to be above ~1200px.
SHOTS = "AppStore/screenshots/framed-web"

JOBS = [
    # The iPad, running THE APP.
    #
    # This started out pointing at marketing/hero/hero-ipad-portrait.png, which
    # is a render of the provider DASHBOARD on an iPad. It went into the
    # consumer "whichever one is nearest" row, so a section about one family
    # showed a care agency's client roster.
    (f"{SHOTS}/ipad-13/03-one-tap-check-in.png", "ipad-app", 700),

    # The phone. Four of the eight screens tell the whole story.
    (f"{SHOTS}/iphone-6.5/03-one-tap-check-in.png",   "iphone-checkin",  620),
    (f"{SHOTS}/iphone-6.5/04-done-for-the-day.png",   "iphone-done",     620),
    (f"{SHOTS}/iphone-6.5/06-family-sees-status.png", "iphone-family",   620),
    (f"{SHOTS}/iphone-6.5/07-your-people.png",        "iphone-people",   620),

    # The watch. Ultra 3 is the largest and the best looking. Wider than the
    # screen it wraps, because the case and crown are now part of the picture.
    (f"{SHOTS}/watch/ultra-3-422x514/02-one-tap-check-in.png", "watch-checkin", 470),

    # Brand marks.
    ("AppStore/icon/logo-transparent-1024.png", "logo",     512),
    ("AppStore/icon/AppIcon-1024.png",          "appicon",  512),
]


def emit(src_rel, stem, width):
    src = os.path.join(ROOT, src_rel)
    if not os.path.exists(src):
        print(f"  MISSING  {src_rel}")
        return False

    im = Image.open(src)
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    if im.width > width:
        height = round(im.height * width / im.width)
        im = im.resize((width, height), Image.LANCZOS)

    webp = os.path.join(OUT, stem + ".webp")
    png = os.path.join(OUT, stem + ".png")

    # method=6 is the slowest and smallest setting. This script runs once.
    im.save(webp, "WEBP", quality=88, method=6)

    # PNG fallback. `quantize` with an alpha channel needs the RGBA-capable
    # median-cut path, and 255 colours leaves index 255 for full transparency.
    im.quantize(colors=255, method=Image.FASTOCTREE).save(png, "PNG", optimize=True)

    print(f"  {stem:<20} {im.width:>5}x{im.height:<5} "
          f"webp {os.path.getsize(webp)//1024:>4}KB   png {os.path.getsize(png)//1024:>4}KB")
    return True


def _font(path, size, weight):
    """A system face at a named weight, or None on a machine that lacks it.

    New York and SF Pro Rounded are variable fonts, so the weight is selected by
    axis name rather than by loading a separate file. Returning None rather than
    raising keeps this script usable on Linux CI, where the card simply comes
    out as the logo on a warm ground — the images that matter are the device
    renders above, and those are platform-independent.
    """
    try:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass          # static build of the face; the default weight will do
        return f
    except OSError:
        return None


def brand_furniture():
    """Favicons and the link-preview card.

    Both are opaque. A transparent favicon disappears against a dark browser
    theme, and every social platform composites an alpha OG image onto a
    background of its own choosing — usually black, usually badly.
    """
    icon = Image.open(os.path.join(ROOT, "AppStore/icon/AppIcon-1024.png")).convert("RGB")

    icon.resize((180, 180), Image.LANCZOS).save(
        os.path.join(OUT, "apple-touch-icon.png"), "PNG", optimize=True)

    # One .ico carrying the three sizes Windows and older browsers ask for.
    icon.resize((64, 64), Image.LANCZOS).save(
        os.path.join(ROOT, "site", "favicon.ico"), "ICO",
        sizes=[(16, 16), (32, 32), (48, 48)])

    # Open Graph card: 1200x630 is the size Facebook, LinkedIn, Slack, iMessage
    # and X all crop toward. Set in the same two faces as the site — New York
    # for the line, SF Pro Rounded for the mark — so a link preview looks like
    # the page it opens.
    card = Image.new("RGB", (1200, 630), (251, 250, 247))
    logo = Image.open(os.path.join(ROOT, "AppStore/icon/logo-transparent-1024.png"))
    logo = logo.convert("RGBA").resize((132, 132), Image.LANCZOS)
    card.paste(logo, (96, 96), logo)

    d = ImageDraw.Draw(card)
    serif = _font("/System/Library/Fonts/NewYork.ttf", 72, "Semibold")
    round_ = _font("/System/Library/Fonts/SFNSRounded.ttf", 30, "Bold")
    small = _font("/System/Library/Fonts/SFNSRounded.ttf", 25, "Medium")

    if round_:
        d.text((248, 140), "Pruuf", font=round_, fill=(22, 21, 15))
    if serif:
        d.text((96, 300), "One tap. And everyone", font=serif, fill=(22, 21, 15))
        d.text((96, 384), "stops worrying.", font=serif, fill=(22, 21, 15))
    if small:
        d.text((96, 524), "A daily check-in for the people you love.",
               font=small, fill=(110, 106, 98))

    # The brand hairline, clear of the descenders on the line above — at 470 it
    # ran straight through the tail of the "y" in "worrying".
    d.rectangle([96, 492, 200, 494], fill=(176, 141, 87))
    card.save(os.path.join(OUT, "og-card.png"), "PNG", optimize=True)

    print(f"  {'brand furniture':<20} favicon.ico, apple-touch-icon.png, og-card.png")


def prune():
    """Delete anything in the output folder this script no longer produces.

    Without this the folder only ever grows: three dashboard renders and a
    second watch shot stayed behind after the site stopped using them, and
    would have been published — a quarter of a megabyte of images nothing links
    to, kept because deleting them was somebody's separate job.
    """
    keep = {f"{stem}.{ext}" for _, stem, _ in JOBS for ext in ("webp", "png")}
    keep |= {"apple-touch-icon.png", "og-card.png"}
    for name in sorted(os.listdir(OUT)):
        if name not in keep and name.endswith((".png", ".webp")):
            os.remove(os.path.join(OUT, name))
            print(f"  {'removed':<20} {name}")


def resize_html():
    """Rewrite the width/height attributes in the pages to what was emitted.

    These are not decoration. A browser uses them to reserve the right box
    before the image arrives, so a wrong pair either shifts the whole page as it
    loads or — when a stylesheet sets `max-width` without `height: auto` —
    stretches the picture to a shape it never had. Both have happened here: the
    device shots once rendered 4.6x too tall for exactly that reason.

    Kept in the build rather than in a checklist because the numbers change
    every time the source geometry does, and a number a human has to remember to
    update is a number that is wrong by the third time.
    """
    import re
    pages = [os.path.join(ROOT, "site", f)
             for f in os.listdir(os.path.join(ROOT, "site")) if f.endswith(".html")]
    fixed = 0
    for page in pages:
        with open(page) as fh:
            text = fh.read()
        before = text
        for _, stem, _ in JOBS:
            out = os.path.join(OUT, f"{stem}.png")
            if not os.path.exists(out):
                continue
            w, h = Image.open(out).size
            text = re.sub(
                rf'(src="assets/img/{re.escape(stem)}\.png"\s+width=")\d+("\s+height=")\d+"',
                rf'\g<1>{w}\g<2>{h}"', text)
        if text != before:
            with open(page, "w") as fh:
                fh.write(text)
            fixed += 1
            print(f"  {'sized':<20} {os.path.basename(page)}")
    return fixed


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"→ {os.path.relpath(OUT, ROOT)}")
    ok = all([emit(*j) for j in JOBS])
    brand_furniture()
    prune()
    resize_html()

    total = sum(os.path.getsize(os.path.join(OUT, f))
                for f in os.listdir(OUT) if f.endswith(".webp"))
    print(f"\n  WebP total (what a modern browser downloads): {total//1024}KB")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
