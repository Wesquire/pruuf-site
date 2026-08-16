#!/usr/bin/env python3
"""Does the website still tell the truth about the app?

    python3 site/sync_check.py

`check.py` proves the site is internally sound — every link resolves, every
image exists. It cannot catch the failure that actually happens, which is the
site being perfectly valid and *wrong*: a price changed in `Store.swift` and not
in `index.html`, a trial length changed in a migration and not in the FAQ.

That drift is invisible from either side alone. The app and the website are two
separate repositories, the site is nested inside the app's, and nobody diffs a
marketing page against a Swift enum. So the numbers are read from BOTH sides
here and compared.

Deliberately parses the real sources rather than a shared constants file. A
constants file would be the tidier design and it would prove nothing: the site
is hand-written HTML that a person edits, and the whole risk is that the person
edits one place. What has to be checked is the actual rendered claim against the
actual shipped value.

Exit code 1 on any mismatch, so it can gate a release.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREEN, RED, DIM, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[0m"

passed = failed = 0


def check(label, site_value, app_value, note=""):
    global passed, failed
    ok = site_value == app_value
    if ok:
        passed += 1
        print(f"  {GREEN}PASS{OFF}  {label}{DIM}  {site_value}{OFF}")
    else:
        failed += 1
        print(f"  {RED}FAIL{OFF}  {label}")
        print(f"        site says {site_value!r}, the app says {app_value!r}")
        if note:
            print(f"        {note}")


def read(*parts):
    with open(os.path.join(ROOT, *parts)) as fh:
        return fh.read()


# ── the app's side ──────────────────────────────────────────────────────────
store = read("Pruufapp", "Store.swift")

def fallback(term, discount):
    """The price `Store.fallbackPrice` shows with no network."""
    pattern = (rf'case \(\.{term}, {discount}\):\s*return "([^"]+)"' if discount
               else rf'case \(\.{term}, _\):\s*return "([^"]+)"')
    m = re.search(pattern, store)
    return m.group(1) if m else None

storekit = json.loads(read("Pruufapp", "Pruuf.storekit"))

def storekit_price(suffix):
    """What the StoreKit configuration charges. Walks the file rather than
    assuming an order — subscription groups nest differently by Xcode version."""
    want = "com.wesquire.pruufapp.receiver." + suffix
    found = []
    def walk(node):
        if isinstance(node, dict):
            if node.get("productID") == want and "displayPrice" in node:
                found.append(node["displayPrice"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(storekit)
    return f"${found[0]}" if found else None

# The server owns these two; the site quotes them.
sql = "".join(read("supabase", "migrations", f)
              for f in sorted(os.listdir(os.path.join(ROOT, "supabase", "migrations")))
              if f.endswith(".sql"))
def sql_const(fn):
    m = re.search(rf"function public\.{fn}\(\) returns int\s*"
                  r"language sql immutable as \$\$ select (\d+) \$\$", sql)
    return m.group(1) if m else None


# ── the site's side ─────────────────────────────────────────────────────────
index = read("site", "index.html")
pages = "".join(read("site", f) for f in sorted(os.listdir(os.path.join(ROOT, "site")))
                if f.endswith(".html"))

def attr(name):
    m = re.search(rf'data-price [^>]*data-{name}="([^"]+)"', index)
    return m.group(1) if m else None


print(f"\n\033[1m── what the site claims, against what the app does ──{OFF}\n")

monthly, annual = attr("monthly"), attr("annual")
check("monthly price, site vs Store.swift", monthly, fallback("monthly", 0))
check("monthly price, site vs Pruuf.storekit", monthly, storekit_price("monthly"))
check("annual price, site vs Store.swift", annual, fallback("annual", 0))
check("annual price, site vs Pruuf.storekit", annual, storekit_price("annual"))

# The discount tiers never appear on the site, but they must stay cheaper than
# full price or a coupon charges MORE than no coupon — BUG-043, which shipped.
for term in ("monthly", "annual"):
    full = float(fallback(term, 0).lstrip("$"))
    for pct, suffix in ((20, "eighty"), (50, "half")):
        tier = float(fallback(term, pct).lstrip("$"))
        check(f"the {pct}% {term} tier is actually cheaper", True, tier < full,
              f"{tier} is not below {full} — a coupon would charge MORE")
        check(f"the {pct}% {term} tier matches Pruuf.storekit",
              fallback(term, pct), storekit_price(f"{term}.{suffix}"))

# The saving badge. Quoted twice on the page and computed from the two prices,
# so it is the number most likely to be left behind by a price change.
#
# Rounded DOWN, matching `Store.savingPercent` exactly. This is a price claim,
# and understating a saving is defensible where overstating one is not — the app
# made that choice deliberately and the site must not quietly disagree by one
# point in the other direction.
#
# The first draft of this file used round(), computed 17% against the site's 16%,
# and reported the SITE as broken. It was not: 99.99 against 12 x 9.99 is 16.59%,
# the app floors it to 16, and the page is right. A checker that reimplements a
# rule instead of copying it just adds a third opinion — which is the exact trap
# this file's own header warns about, walked straight into.
from decimal import Decimal, ROUND_DOWN
m, a = Decimal(monthly.lstrip("$")), Decimal(annual.lstrip("$"))
yearly = m * 12
real_saving = int(((yearly - a) / yearly * 100).quantize(Decimal("1"), rounding=ROUND_DOWN))
claimed = re.search(r"save (\d+)%", index)
check("the annual saving badge", int(claimed.group(1)) if claimed else None, real_saving,
      f"{annual} against 12 x {monthly} is {real_saving}% rounded down, as the app does")
body = re.search(r"(\d+)% less than\s*\n?\s*paying monthly", index)
check("the saving repeated in the card", int(body.group(1)) if body else None, real_saving)

# "That's $8.33 a month" — an arithmetic claim about a price.
per_month = re.search(r"\$(\d+\.\d\d) a month", index)
check("the monthly equivalent of the annual price",
      per_month.group(1) if per_month else None, f"{a / 12:.2f}")

# The server decides these; the site promises them.
check("the free trial length", 
      (re.search(r"(\d+) days free", pages) or [None, None])[1], sql_const("trial_days"))

# The sender is free. If this ever stops being true on the site, the product
# changed and nobody said so.
check("the sender's price", "$0" in index, True,
      "the site must go on saying the person checking in pays nothing")


# ── Strings the site puts in the app's mouth ────────────────────────────────
#
# The numbers above were never the whole risk. The site also QUOTES the app —
# "the screen says X" — and a quotation is the strongest kind of factual claim a
# marketing page can make, because a reader takes it as something they will see
# with their own eyes.
#
# One of them had already gone false. The FAQ said:
#
#     The screen also counts down to her time — "Check in by 10:00 AM ·
#     1h 56m left" — so she is never guessing how long she has.
#
# The app renders "Check in by 10:00 AM" and nothing else. The live countdown
# was removed on purpose, with a written rationale about not putting a pressure
# clock in front of somebody who may already feel like a burden. Nothing caught
# it: `check.py` proves the page is internally sound, and everything above this
# line compares NUMBERS. A page can be perfectly valid, perfectly priced, and
# describing a screen that does not exist.
#
# So: any text the site presents as something the app says must be marked
#
#     <span data-app-string="Check in by">"Check in by 10:00 AM"</span>
#
# and the marked value must exist as a real string literal in the Swift
# sources. The mark is the honest part — a heuristic that guessed which quotes
# were UI would either miss the next one or cry wolf about ordinary prose — and
# it is enforced in both directions: an unmarked quote is invisible to this
# check, so the FORBIDDEN list below covers the specific claims already known to
# be false, and a marked one cannot rot without the build going red.

swift_sources = []
for folder in ("Pruufapp", "Shared", "PruufWatch"):
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, folder)):
        for fn in files:
            if fn.endswith(".swift"):
                with open(os.path.join(dirpath, fn)) as fh:
                    swift_sources.append(fh.read())
swift = "\n".join(swift_sources)

# Every string literal in the app, interpolation and all. `"Check in by \(due)"`
# is captured as `Check in by \(due)`, so a claim quoting the static half of an
# interpolated string still matches — which is exactly the shape of every claim
# the site actually makes.
literals = re.findall(r'"((?:[^"\\\n]|\\.)*)"', swift)

quoted = re.findall(r'<span data-app-string="([^"]+)"[^>]*>(.*?)</span>', pages, re.S)
check("the site quotes at least one app string", len(quoted) > 0, True,
      "if this drops to zero the check below is asserting nothing")

for claim, shown in quoted:
    check(f"the app really says {claim!r}",
          any(claim in lit for lit in literals), True,
          "no Swift string literal contains it — the site is quoting a screen "
          "that does not exist")
    # And the visible text must actually contain what it claims to be quoting,
    # so the marker cannot drift away from the sentence it is vouching for.
    visible = re.sub(r"<[^>]+>", "", shown)
    check(f"the visible quote around {claim!r} matches its marker",
          claim.lower() in visible.lower().replace("“", "").replace("”", ""),
          True)

# Claims known to be false, kept as a regression guard. This list is a
# blacklist, which is a weaker tool than the marker above and is here for one
# reason: the defect it records shipped, and a check that would not have caught
# it is not much of a check. Each entry names what the app actually does.
FORBIDDEN = [
    ("counts down to your time",
     "the sender's screen shows no countdown BEFORE the deadline — "
     "ParentHomeView renders 'Check in by 10:00 AM' and only counts once overdue"),
    ("counts down to her time",
     "same claim, the FAQ's wording"),
    ("1h 56m left",
     "quotes a countdown string the app has never rendered on the sender's home screen"),
]
for phrase, why in FORBIDDEN:
    check(f"the site does not claim {phrase!r}", phrase.lower() not in pages.lower(), True, why)


# ── The location promises, against the code that has to keep them ──────────
#
# Three sentences now appear on the site that are claims about behaviour rather
# than about prices, and each one is checkable:
#
#   "off in two taps"          → three modes exist, and `never` is one of them
#   "deleted after 30 days"    → the purge really is 30 days
#   "never in the background"  → the app holds WhenInUse and nothing wider
#
# The third is the one worth automating hardest. An `Always` authorisation
# added later would make the site's flagship privacy sentence false, silently,
# in a build that compiled perfectly — and it is exactly the kind of change
# somebody makes at midnight to fix a bug about a missing fix.

migrations = "".join(
    read("supabase", "migrations", f)
    for f in sorted(os.listdir(os.path.join(ROOT, "supabase", "migrations")))
    if f.endswith(".sql"))

check("locations really are purged after 30 days",
      "30 days" in pages.lower() or "30 days" in index.lower(), True,
      "the site should say how long positions are kept")
check("and the purge really is 30 days",
      bool(re.search(r"delete from event_locations\s+where created_at < now\(\) - interval '30 days'",
                     migrations)), True,
      "the site promises 30 days; purge_old_locations() must agree")

check("the sender can genuinely turn it off",
      "'never'" in migrations and "share_location in ('always', 'help_only', 'never')" in migrations,
      True, "the site says it can be switched off entirely")

pbxproj = read("Pruufapp.xcodeproj", "project.pbxproj")
check("the app asks for when-in-use location only",
      "NSLocationWhenInUseUsageDescription" in pbxproj, True)
check("and holds NO always-on location permission",
      "NSLocationAlwaysAndWhenInUseUsageDescription" not in pbxproj
      and "NSLocationAlwaysUsageDescription" not in pbxproj, True,
      "the site says Pruuf never looks in the background — an Always "
      "authorisation would make that false")

# And the app must not have quietly become a tracker: nothing may start
# continuous updates. `requestLocation()` is one fix and then silence.
locator = read("Shared", "Locator.swift")
# Comments stripped first. The check is about what the app DOES, and the file
# explains in prose why it does not call `startUpdatingLocation` — a checker
# that cannot tell code from a comment about code fails on the very file that
# documents the promise it is enforcing. It failed exactly that way when first
# written, which is the reason for this note.
code = re.sub(r"//.*", "", locator)
check("the app takes ONE fix rather than following anybody",
      "requestLocation()" in code and "startUpdatingLocation" not in code, True,
      "startUpdatingLocation would make 'never follows you around' false")

# The claim that there is no AI. Cheap to assert, and it is the one claim on
# the site that a competitor would most enjoy disproving.
for word in ("openai", "anthropic", "gpt-", "llm"):
    check(f"no {word} dependency, as the site says", word not in migrations.lower(), True)

print(f"\n  {GREEN if not failed else RED}{passed} passed, {failed} failed{OFF}\n")
sys.exit(1 if failed else 0)
