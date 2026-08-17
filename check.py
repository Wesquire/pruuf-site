#!/usr/bin/env python3
"""Prove that every link on the site goes somewhere.

    python3 site/check.py

A brochure site fails quietly. A mistyped href does not throw, does not show up
in a screenshot, and is found weeks later by a stranger who wanted the privacy
policy. So this walks every page, resolves every href and src, and fails if any
of them points at a file or an anchor that does not exist.

It also asserts the handful of properties that are easy to lose in an edit:
that no page ships a bare `#` button, that every image has alt text and
dimensions, that every page carries the shared stylesheet and script, and that
nothing loads from an external host — which is a promise the privacy page
makes on our behalf.

And it pins the DOMAIN. Canonical and Open Graph URLs are the one kind of
mistake that is invisible on the page and expensive off it: a canonical tag
pointing at a domain you do not own tells search engines the real page lives
somewhere else, and nothing about the site looks wrong while it does that. The
site carried `pruuf.app` — a placeholder — on all seven pages until somebody
thought to look.
"""

import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urldefrag, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))

# The one place the live domain is written down. Everything else is checked
# against it, so moving domains is a one-line edit plus a failing test telling
# you every file that still disagrees.
SITE = "https://thepruuf.com"

# Pages that must NOT be in the sitemap, and why.
NOINDEX = {"404.html"}

problems = []
checks = 0


def check(cond, label):
    global checks
    checks += 1
    if not cond:
        problems.append(label)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []      # (attr value, tag)
        self.ids = set()
        self.imgs = []
        self.buttons = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if "name" in a and tag == "a":
            self.ids.add(a["name"])
        for key in ("href", "src"):
            if key in a:
                self.links.append((a[key], tag, a.get("rel", "")))
        if tag == "img":
            self.imgs.append(a)
        if tag == "button":
            self.buttons += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


parsed = {}
for name in PAGES:
    with open(os.path.join(HERE, name)) as f:
        raw = f.read()
    p = Page()
    p.feed(raw)
    parsed[name] = (p, raw)

print(f"\n\033[1m── {len(PAGES)} pages ──\033[0m\n")

for name in PAGES:
    p, raw = parsed[name]
    page_problems_before = len(problems)

    check(bool(p.title.strip()), f"{name}: no <title>")
    check('rel="stylesheet" href="assets/pruuf.css"' in raw,
          f"{name}: does not load the shared stylesheet")
    check('src="assets/pruuf.js"' in raw, f"{name}: does not load the shared script")
    check('name="viewport"' in raw, f"{name}: no viewport meta")
    check('class="skip"' in raw, f"{name}: no skip link")
    check(raw.count("<h1") == 1, f"{name}: {raw.count('<h1')} <h1> elements, want exactly 1")

    # ── The domain, per page ────────────────────────────────────────────
    # The canonical URL is what search engines treat as this page's real
    # address, and og:url is what a link preview shows. Both are absolute, so
    # both hard-code the domain, so both rot silently when it changes.
    slug = "" if name == "index.html" else name
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', raw)
    check(canonical is not None, f"{name}: no canonical URL")
    if canonical:
        want = f"{SITE}/{slug}"
        check(canonical.group(1) == want,
              f"{name}: canonical is {canonical.group(1)}, want {want}")

    og_url = re.search(r'<meta property="og:url" content="([^"]+)"', raw)
    check(og_url is not None, f"{name}: no og:url")
    if og_url and canonical:
        check(og_url.group(1) == canonical.group(1),
              f"{name}: og:url and canonical disagree — "
              f"{og_url.group(1)} vs {canonical.group(1)}")

    og_img = re.search(r'<meta property="og:image" content="([^"]+)"', raw)
    check(og_img is not None, f"{name}: no og:image")
    if og_img:
        # Must be absolute AND on our host: every platform fetches this
        # server-side, where a relative path resolves against nothing.
        check(og_img.group(1).startswith(SITE + "/"),
              f"{name}: og:image is not an absolute {SITE} URL "
              f"({og_img.group(1)})")

    # No other domain may appear as one of ours anywhere in the markup.
    for stray in re.findall(r'https?://[a-z0-9.-]*pruuf[a-z0-9.-]*', raw, re.I):
        host = urlparse(stray).netloc
        check(host in ("thepruuf.com", "www.thepruuf.com"),
              f"{name}: refers to {host}, which is not this site")

    for href, tag, rel in p.links:
        if href.startswith(("mailto:", "tel:", "data:")):
            continue

        # Nothing may be FETCHED from another host: the privacy page says this
        # site sets no cookies and loads nothing from anybody else, and one
        # stray font link would make that false.
        #
        # `<link rel="canonical">` and the Open Graph URLs are absolute by
        # requirement — they are declarations about where this page lives, not
        # requests — so they are not subresources and must not be flagged. An
        # earlier version of this check did flag them, which would have pushed
        # somebody toward "fixing" correct SEO markup.
        if href.startswith(("http://", "https://", "//")):
            host = urlparse(href).netloc
            fetches = (tag in ("script", "img", "iframe", "source", "video", "audio")
                       or (tag == "link" and rel not in ("canonical", "alternate")))
            check(not fetches, f"{name}: loads a subresource from {host} ({href})")
            continue

        check(href != "#", f"{name}: a bare '#' {tag} that goes nowhere")
        if href.startswith("#"):
            check(href[1:] in p.ids, f"{name}: #{href[1:]} does not exist on this page")
            continue

        path, frag = urldefrag(href)
        path = path.split("?")[0]
        target = os.path.normpath(os.path.join(HERE, path))
        check(os.path.exists(target), f"{name}: {path} does not exist")

        # The dashboard is a single-page app whose fragment is a ROUTE, not an
        # element id — `#today` is handled by its own router. Checking it as an
        # anchor would fail on a link that works perfectly.
        if path.startswith("dashboard/"):
            continue

        # A cross-page anchor is the one most likely to rot, because nothing
        # visible breaks when the section it pointed at is renamed.
        if frag and path in parsed:
            check(frag in parsed[path][0].ids,
                  f"{name}: {path}#{frag} — that anchor is not on that page")
        elif frag and os.path.exists(target) and path.endswith(".html"):
            with open(target) as f:
                other = Page()
                other.feed(f.read())
            check(frag in other.ids, f"{name}: {path}#{frag} does not exist")

    for img in p.imgs:
        src = img.get("src", "?")
        check("alt" in img, f"{name}: <img {src}> has no alt text")
        # Width and height stop the page reflowing as images arrive, which on a
        # slow connection is what makes a site feel cheap.
        check("width" in img and "height" in img,
              f"{name}: <img {src}> has no intrinsic size")

    new = len(problems) - page_problems_before
    links = len(p.links)
    status = "\033[32mok\033[0m" if new == 0 else f"\033[31m{new} problems\033[0m"
    print(f"  {name:<18} {links:>3} links  {len(p.imgs):>2} images   {status}")

# ── Properties of the site as a whole ────────────────────────────────────
for required in ("index.html", "enterprise.html", "contact.html",
                 "privacy.html", "terms.html", "support.html", "404.html"):
    check(required in PAGES, f"missing page: {required}")

check(os.path.exists(os.path.join(HERE, "dashboard", "index.html")),
      "the enterprise page embeds dashboard/index.html, which is not here")
check(os.path.exists(os.path.join(HERE, "favicon.ico")), "no favicon.ico")

# ── Pruuf never tells anybody to seek emergency help ─────────────────────
#
# A product boundary, enforced here because prose is where it erodes.
#
# Pruuf notifies the people a family chose. It does not know what a situation
# is, cannot escalate and cannot follow up — so it is in no position to advise
# anybody on whether to involve anyone else. That judgement belongs to the
# person who is actually there.
#
# The failure mode is subtle and worth naming, because the sentences that break
# this rule are always written with good intentions. Once a page tells you to
# call for help in ONE place, every page that stays quiet starts to read as
# "this one is not serious" — so the silence becomes advice too, and it is
# advice nobody wrote or reviewed. Naming a particular service compounds it by
# positioning Pruuf beside that service, which is a characterisation neither an
# app reviewer nor a court would read the way the sentence intended.
#
# What IS allowed, and is deliberately not caught below: the bare factual
# disclaimer "Pruuf is not an emergency service". That is the opposite of
# encouragement — it is the sentence that stops somebody assuming Pruuf
# dispatches help — and removing it would create the very misunderstanding this
# whole rule exists to prevent.
DIRECTIVES = [
    "call your local emergency", "ring your local emergency",
    "call emergency services", "contact emergency services",
    "call 911", "dial 911", "call 999", "dial 999",
    "needs help right now, call", "needs help now, call",
    "in place of calling emergency",
]
NAMED_SERVICES = ["911", "ambulance", "paramedic"]

for name in PAGES:
    raw = parsed[name][1]
    low = raw.lower()
    for phrase in DIRECTIVES:
        check(phrase not in low,
              f"{name}: tells the reader to seek emergency help — \"{phrase}\"")
    for word in NAMED_SERVICES:
        check(word not in low,
              f"{name}: names an emergency service — \"{word}\" — which "
              f"positions Pruuf beside it")

# ── robots.txt and sitemap.xml ───────────────────────────────────────────
# Both name the domain, and the sitemap has to stay level with the pages —
# a sitemap that lists a page which no longer exists, or misses one that does,
# is a slow leak nobody ever notices.
robots_path = os.path.join(HERE, "robots.txt")
sitemap_path = os.path.join(HERE, "sitemap.xml")
check(os.path.exists(robots_path), "no robots.txt")
check(os.path.exists(sitemap_path), "no sitemap.xml")

if os.path.exists(robots_path) and os.path.exists(sitemap_path):
    robots = open(robots_path).read()
    sitemap = open(sitemap_path).read()

    check(f"Sitemap: {SITE}/sitemap.xml" in robots,
          f"robots.txt does not point at {SITE}/sitemap.xml")
    check("Disallow: /dashboard/" in robots,
          "robots.txt lets the demo dashboard be indexed — its fabricated "
          "roster would surface in search as a real client list")

    listed = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
    for u in listed:
        check(u.startswith(SITE + "/"),
              f"sitemap.xml lists {u}, which is not on {SITE}")

    for name in PAGES:
        want = f"{SITE}/" + ("" if name == "index.html" else name)
        if name in NOINDEX:
            check(want not in listed,
                  f"sitemap.xml lists {name}, which is marked noindex")
        else:
            check(want in listed, f"sitemap.xml is missing {name}")

# Every marketing page must offer a way to act. A page with no call to action
# is a page that cannot convert, and it is easy to leave one behind in an edit.
for name in ("index.html", "enterprise.html"):
    raw = parsed[name][1]
    check("btn--ok" in raw, f"{name}: no primary call to action")

# The App Store link must not ship live while the product page still 404s.
with open(os.path.join(HERE, "assets", "pruuf.js")) as f:
    js = f.read()
live = re.search(r"appStoreLive:\s*(true|false)", js)
check(live is not None, "CONFIG.appStoreLive is missing from pruuf.js")
if live and live.group(1) == "true":
    print("\n\033[33m  NOTE: appStoreLive is true — every CTA now points at the App "
          "Store.\n  That is only correct once the app is publicly released.\033[0m")

print()
if problems:
    print(f"\033[31m{len(problems)} of {checks} checks FAILED\033[0m\n")
    for pr in problems:
        print(f"  FAIL  {pr}")
    print()
    sys.exit(1)

print(f"\033[32m  all {checks} checks passed\033[0m\n")
