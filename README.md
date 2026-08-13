# site/ — the Pruuf website

Plain HTML, one stylesheet, one script. No build step, no framework, no
dependencies, and not one request to another host. To publish it you copy the
files onto a static host — **[DEPLOY.md](DEPLOY.md) walks that through from
buying a domain to reading the messages people send you.**

The design brief, the copy strategy and the reasoning behind both are in
[`../WEBSITE.md`](../WEBSITE.md). Running the forms afterwards — reading and
deleting enquiries, changing where the notification email goes and what it says,
and the release-day switch — is [EMAIL-AND-FORMS.md](EMAIL-AND-FORMS.md).

## The pages

| File | What it is |
|---|---|
| `index.html` | The landing page. Hero contains a live, tappable demo of the app. |
| `enterprise.html` | For care providers. Embeds the real dashboard, live, in a MacBook. |
| `contact.html` | One form, several intents. Posts to a Supabase edge function. |
| `support.html` | Support and FAQ. **Apple requires this URL.** |
| `privacy.html` | Privacy policy. **Apple requires this URL.** |
| `terms.html` | Terms of use, including the pricing promise. |
| `404.html` | Not found. |
| `assets/` | `pruuf.css`, `pruuf.js`, and the images. |
| `dashboard/` | A copy of `../portal/index.html`, so the enterprise page can embed it. |

`privacy.html`, `terms.html`, `support.html` and `404.html` are **generated** —
edit the strings in `_shell.py` and re-run it, or your change is overwritten the
next time anybody does. The two marketing pages are hand-written, because every
section of them is different and a template would only get in the way.

## The tooling

```bash
python3 site/check.py           # every link, anchor, image and promise. Run before publishing.
python3 site/_shell.py          # regenerate privacy / terms / support / 404
python3 site/build_assets.py    # rebuild assets/img from ../marketing
python3 site/shots.py           # full-page screenshots at three widths, into ../build/site-shots
```

`check.py` is the one that matters. It fails on a link to a file or an anchor
that does not exist, on an image with no alt text or no intrinsic size, and on
anything loading from an external host — which is a promise the privacy page
makes on our behalf.

To look at it locally:

```bash
cd site && python3 -m http.server 8000
```

The contact form works from `localhost:8000` — that origin is on the endpoint's
allowlist.

## Two things to know before editing

**The App Store buttons are deliberately not App Store buttons yet.** The app's
product page returns 404 until it is publicly released, so every "get the app"
call to action is authored as a link to the launch-notification form and is
*upgraded* by JavaScript once `CONFIG.appStoreLive` in `assets/pruuf.js` is set
to `true`. That way a visitor with JavaScript off still gets a working button
rather than a dead one, and release day is a one-line change.

**The hero demo is drawn from the real screenshots.** `initHeroDemo` in
`pruuf.js` reproduces the app's own interface in DOM — laid out against
`../AppStore/screenshots/iphone-6.5/`, not from memory. If the app's home screen
changes, that demo has to change with it, or the most prominent thing on the
landing page becomes a picture of an app that no longer exists.

## After the app changes

```bash
AppStore/capture.sh ios              # re-capture from the current app
python3 AppStore/frame_devices.py    # App Store frames (opaque, exact canvas)
python3 AppStore/round_devices.py    # ← what the WEBSITE uses. Do not skip.
python3 marketing/render_devices.py  # transparent framed renders
python3 site/build_assets.py         # web-weight copies for the site
cp portal/index.html site/dashboard/index.html   # if the dashboard changed
python3 site/check.py
```

**`round_devices.py` is the easy one to forget**, and forgetting it is silent:
the framed App Store set updates, the site keeps serving the previous build's
screens, and everything reports success. It happened once already — the site
showed an older version of the app for a full pipeline run before anybody
looked at the picture.

## Commits push themselves

`scripts/install-hooks.sh` in the app repo installs a `post-commit` hook here
that runs `check.py` and, **only if it passes**, pushes — which Cloudflare Pages
turns into a deployment. A commit that would break the live site is committed
locally and simply not sent, with the failures printed.

Run the installer once per clone; `.git/hooks/` is not version-controlled and
does not survive a fresh clone.

```bash
scripts/install-hooks.sh     # from the app repo root
git commit --no-verify       # to skip the hook for one commit
```

## Git

This folder is its own repository — `Wesquire/pruuf-site`, public — because
GitHub Pages will not serve a public site from a private repo, and the main app
repo is private. `git remote -v` in here shows it. It is *also* tracked by the
parent repo, so a commit in either place is a real commit; keep them in step.
