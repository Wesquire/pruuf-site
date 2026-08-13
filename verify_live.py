#!/usr/bin/env python3
"""Prove the DEPLOYED site is right, not just the files on disk.

    python3 site/verify_live.py
    python3 site/verify_live.py --wait      # poll until it is up, then check

`check.py` reads the working tree. This reads what a stranger's browser actually
gets from thepruuf.com: the certificate, the redirects, every page, every asset
the pages reference, and the contact form posting for real from the real origin.

The two failure modes it exists for are the ones that only appear after a
deploy and are invisible locally:

  · The folder was uploaded one level too deep, so every asset 404s while
    index.html still loads and the page merely looks unstyled.
  · The contact form's origin allowlist does not include the live domain, so
    the form fails for every visitor while working perfectly on localhost.

It writes one real message through the form and deletes it again, the same way
`prod_contact.py` does — a form that has never been submitted from the live
domain has not been tested.
"""

import json
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

SITE = "https://thepruuf.com"
APEX = "thepruuf.com"
PAGES = ["/", "/enterprise.html", "/contact.html", "/support.html",
         "/privacy.html", "/terms.html"]
FN = "https://taszjafyqcilujpygtbs.supabase.co/functions/v1/contact"
KEY = "sb_publishable_LvnQvFeV0UNFX82WkbzFFw_c8yKwix4"

passed = failed = 0


def ok(cond, label, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:
        failed += 1
        print(f"FAIL  {label}" + (f"  [{detail}]" if detail else ""))
    return cond


def get(url, method="GET", headers=None, body=None, redirect=True):
    """(status, text, headers). Never raises — the error codes are the point."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):
            return None

    req = urllib.request.Request(url, method=method,
                                 headers=headers or {"User-Agent": "pruuf-verify"},
                                 data=body)
    opener = (urllib.request.build_opener(NoRedirect) if not redirect
              else urllib.request.build_opener())
    try:
        with opener.open(req, timeout=20) as r:
            raw = r.read()
            try:
                return r.status, raw.decode("utf-8", "replace"), r.headers
            except Exception:
                return r.status, "", r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers
    except Exception as e:
        return 0, str(e), {}


def is_up():
    status, _, _ = get(SITE + "/")
    return status == 200


def wait_for_it(minutes=20):
    print(f"\n\033[1mWaiting for {APEX} to come up\033[0m  (up to {minutes} min)\n")
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        status, _, _ = get(SITE + "/")
        stamp = time.strftime("%H:%M:%S")
        if status == 200:
            print(f"  {stamp}  200 — it's live\n")
            return True
        print(f"  {stamp}  {status or 'no DNS'} — still waiting")
        time.sleep(20)
    print("\n  Gave up. Is the custom domain attached in Cloudflare Pages?")
    return False


def main():
    if "--wait" in sys.argv and not is_up():
        if not wait_for_it():
            return 1

    print(f"\n\033[1m── {SITE} ──\033[0m\n")

    # ── It is there at all ────────────────────────────────────────────────
    status, html, headers = get(SITE + "/")
    if not ok(status == 200, "the front page is served", f"HTTP {status}"):
        print("\n  Nothing else can be checked until it resolves.")
        print(f"\n{passed} passed, {failed} failed\n")
        return 1

    # ── HTTPS, and no way around it ───────────────────────────────────────
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(__import__("socket").create_connection((APEX, 443), 10),
                             server_hostname=APEX) as s:
            cert = s.getpeercert()
        names = {v for k, v in cert.get("subjectAltName", ()) if k == "DNS"}
        ok(any(n in (APEX, f"*.{APEX}") for n in names),
           "the certificate is valid for this domain", ", ".join(sorted(names))[:60])
    except Exception as e:
        ok(False, "the certificate is valid for this domain", str(e)[:60])

    status, _, h = get(f"http://{APEX}/", redirect=False)
    loc = (h or {}).get("Location", "") if h else ""
    ok(status in (301, 302, 307, 308) and loc.startswith("https://"),
       "plain HTTP redirects to HTTPS", f"{status} → {loc[:40]}")

    status, _, _ = get(f"https://www.{APEX}/")
    ok(status == 200, "www serves too", f"HTTP {status}")

    # ── Every page ────────────────────────────────────────────────────────
    for path in PAGES:
        status, body, _ = get(SITE + path)
        ok(status == 200 and "<html" in body.lower(), f"{path} is served",
           f"HTTP {status}")

    status, _, _ = get(SITE + "/no-such-page-here")
    ok(status == 404, "a missing page 404s rather than 200s", f"HTTP {status}")

    # ── The canonical the live server actually emits ──────────────────────
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    ok(m and m.group(1) == SITE + "/", "the served canonical is this domain",
       m.group(1) if m else "absent")

    # ── Assets. This is the check that catches a wrong output directory ───
    refs = set(re.findall(r'(?:href|src|srcset)="([^"]+\.(?:css|js|png|webp|ico))"', html))
    broken = []
    for ref in sorted(refs):
        if ref.startswith(("http", "//", "data:")):
            continue
        status, _, _ = get(urljoin(SITE + "/", ref))
        if status != 200:
            broken.append(f"{ref} ({status})")
    ok(not broken, f"every asset the front page references loads ({len(refs)})",
       "; ".join(broken[:3]))

    # ── The embedded dashboard ────────────────────────────────────────────
    status, dash, _ = get(SITE + "/dashboard/index.html")
    ok(status == 200 and "Pruuf" in dash,
       "the provider dashboard is deployed", f"HTTP {status}")

    # ── Crawler files ─────────────────────────────────────────────────────
    status, robots, _ = get(SITE + "/robots.txt")
    ok(status == 200 and f"Sitemap: {SITE}/sitemap.xml" in robots,
       "robots.txt is served and points at the sitemap", f"HTTP {status}")
    status, smap, _ = get(SITE + "/sitemap.xml")
    ok(status == 200 and smap.count("<loc>") == len(PAGES),
       "sitemap.xml lists every page", f"{smap.count('<loc>')} of {len(PAGES)}")

    # ── The contact form, for real, from the real origin ──────────────────
    hdrs = {"Origin": SITE, "Access-Control-Request-Method": "POST"}
    status, _, h = get(FN, method="OPTIONS", headers=hdrs)
    allow = (h or {}).get("access-control-allow-origin", "")
    ok(status == 204 and allow == SITE,
       "the contact endpoint admits this origin", f"{status} {allow}")

    marker = f"liveprobe-{int(time.time())}"
    payload = json.dumps({
        "intent": "support", "name": "Live Probe",
        "email": f"{marker}@example.com",
        "message": "Automated check that the live form works. Safe to delete.",
        "page": "/verify_live.py", "elapsed_ms": 30_000,
    }).encode()
    status, body, _ = get(FN, method="POST", body=payload, headers={
        "Content-Type": "application/json", "apikey": KEY, "Origin": SITE})
    ok(status == 200 and '"ok"' in body.replace(" ", ""),
       "a real message submits from the live domain", f"{status} {body[:40]}")

    # Clean up after ourselves, the same way prod_contact.py does.
    try:
        out = subprocess.run(
            ["npx", "supabase", "projects", "api-keys",
             "--project-ref", "taszjafyqcilujpygtbs", "-o", "json"],
            capture_output=True, text=True, timeout=90, check=True).stdout
        payload = json.loads(out)
        keys = payload["keys"] if isinstance(payload, dict) else payload
        svc = next(k["api_key"] for k in keys if k.get("id") == "service_role")
        req = urllib.request.Request(
            f"https://taszjafyqcilujpygtbs.supabase.co/rest/v1/"
            f"contact_requests?email=like.{marker}*",
            headers={"apikey": svc, "Authorization": f"Bearer {svc}"},
            method="DELETE")
        urllib.request.urlopen(req, timeout=20)
        print("\n\033[2mCleaned up the probe message.\033[0m")
    except Exception:
        print(f"\n\033[33mCould not clean up. Remove by hand:")
        print(f"  delete from public.contact_requests "
              f"where email like '{marker}%';\033[0m")

    print(f"\n{passed} passed, {failed} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
