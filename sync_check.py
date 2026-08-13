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

print(f"\n  {GREEN if not failed else RED}{passed} passed, {failed} failed{OFF}\n")
sys.exit(1 if failed else 0)
