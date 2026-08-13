# Publishing the Pruuf website

Everything in this folder is a plain file. There is no build step, no framework,
no server: to publish it, you copy it somewhere that serves static files over
HTTPS. That is the whole architecture, and it is the reason this will still be
editable in five years.

Follow this once and you have a live site on your own domain. It takes about
half an hour, most of which is waiting for DNS.

**The domain is `thepruuf.com`.** It is written down in exactly one place —
`SITE` at the top of `check.py` — and `check.py` fails on any page, sitemap
entry or robots line that disagrees with it. To move domains, change that
constant and let the failures list every file that still needs editing.

---

## What you are publishing

```
site/
  index.html          the landing page
  enterprise.html     for care providers
  contact.html        the contact form
  support.html        support / FAQ          ← Apple requires this URL
  privacy.html        privacy policy         ← Apple requires this URL
  terms.html          terms of use
  404.html            not-found page
  favicon.ico
  assets/             one CSS file, one JS file, the images
  dashboard/          the provider dashboard, embedded on the enterprise page
```

Everything else in this folder (`build_assets.py`, `_shell.py`, `check.py`,
`shots.py`, this file, `README.md`) is **tooling**. Uploading it is harmless —
`.py` and `.md` files are served as plain text and nothing links to them — but
if your host lets you exclude files, exclude those.

---

## Step 1 — Check it before it goes anywhere

```bash
python3 site/check.py
```

This walks every page and fails if any link points at a file or an anchor that
does not exist, if an image is missing alt text, or if anything tries to load
from an external host. It takes a second and it is the difference between
publishing a site and publishing a site with a broken privacy link on it.

To look at it locally first:

```bash
cd site && python3 -m http.server 8000
```

then open <http://localhost:8000>. The contact form works from localhost — that
origin is already on the allowlist.

---

## Step 2 — Buy the domain

Any registrar. **Cloudflare Registrar** and **Namecheap** are both fine;
Cloudflare sells at cost and does not raise the price in year two, which most
registrars do.

Buy the apex — `thepruuf.com`, not `www.thepruuf.com`. You will point both at the
site in Step 4.

> `.app` is a Google-operated TLD on the HSTS preload list, which means browsers
> refuse to load it over plain HTTP at all. That is a good thing — it makes
> HTTPS non-optional — but it does mean a misconfigured certificate shows as a
> hard failure rather than a warning. Get Step 3 right and it is a non-issue.

---

## Step 3 — Choose a host

Any of these serve this folder correctly. Pick one; do not do two.

| | Best for | Cost | Custom domain |
|---|---|---|---|
| **Cloudflare Pages** | **What thepruuf.com uses.** Fastest, free TLS, instant rollbacks, per-branch preview URLs | Free | Yes |
| **Netlify** | Drag-and-drop with no git at all | Free tier | Yes |
| **GitHub Pages** | You already have `Wesquire/pruuf-site` | Free | Yes |

### 3A — Cloudflare Pages (recommended)

1. Sign in at <https://dash.cloudflare.com> → **Workers & Pages** → **Create** →
   **Pages** → **Upload assets**.
2. Name the project `pruuf`.
3. Drag the **contents** of the `site` folder in — the files themselves, not the
   folder. `index.html` must end up at the top level.
4. **Deploy.** You get `pruuf.pages.dev` immediately. Check it works.
5. **Custom domains** → **Set up a domain** → `thepruuf.com`. If the domain is
   registered at Cloudflare, DNS is written for you and there is nothing to do
   in Step 4. Repeat for `www.thepruuf.com`.

To update later: same screen, **Create new deployment**, drag the folder again.
Every deployment is kept and any of them can be made live again with one click,
which is the cheapest insurance there is.

### 3B — Netlify

1. <https://app.netlify.com/drop> — drag the `site` folder onto the page. It is
   live in seconds at a random `*.netlify.app` address.
2. **Site configuration → Domain management → Add a custom domain** →
   `thepruuf.com`, and follow Step 4.
3. Later updates: the same drop page, signed in, on the same site.

### 3C — GitHub Pages

> **An alternative, not an addition.** thepruuf.com is served by Cloudflare
> Pages (3A). If GitHub Pages is *also* switched on for this repo, the same
> site is live at two addresses — which splits search ranking between them and
> means the contact form silently fails on one, because the origin allowlist
> only admits thepruuf.com. Every page's canonical tag already points at
> thepruuf.com, so search engines are told which one is real; but if Pages is
> on and you are not using it, turn it off.

You already have a public repo for this: `Wesquire/pruuf-site` (this folder is
itself a checkout of it — `git remote -v` inside `site/` shows it).

```bash
cd site
git add -A
git commit -m "The full site: landing, enterprise, contact, legal"
git push origin main
```

Then in that repo on github.com: **Settings → Pages → Source: Deploy from a
branch → `main` / `/ (root)` → Save.** A minute later it is at
`https://wesquire.github.io/pruuf-site/`.

For the custom domain: **Settings → Pages → Custom domain** → `thepruuf.com` →
Save, tick **Enforce HTTPS** once it becomes available (a few minutes), then
follow Step 4. GitHub writes a `CNAME` file into the repo when you do this;
leave it there.

> The main Pruuf repo is private, and GitHub Pages will not serve a public site
> from a private repo on the free plan. That is why the site is a separate
> public repo rather than a folder of the app repo.

---

## Step 4 — Point the domain at the host

Skip this entirely if your domain is registered at Cloudflare *and* you used
Cloudflare Pages — it was done for you.

At your registrar's DNS panel:

**Cloudflare Pages or Netlify** — they will show you the exact values. It is
normally:

| Type | Name | Value |
|---|---|---|
| CNAME | `www` | `pruuf.pages.dev` (or `<site>.netlify.app`) |
| CNAME or ALIAS | `@` | the same target |

If your registrar will not allow a CNAME on the apex `@` (many will not), use
the A records the host gives you, or move DNS to Cloudflare, which supports it.

**GitHub Pages** — these four A records and one CNAME, exactly:

| Type | Name | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `wesquire.github.io` |

DNS usually propagates in minutes and is allowed up to 48 hours. Check with:

```bash
dig +short thepruuf.com
```

Then load `https://thepruuf.com` and confirm the padlock. **Do not skip the
padlock check** — an unencrypted contact form on a page about somebody's elderly
mother is not acceptable, and the browser will refuse `.app` over HTTP anyway.

---

## Step 5 — Tell the backend about the new domain

The contact form posts to a Supabase Edge Function, which only accepts requests
from origins it recognises. Until you do this, the form on your live domain will
fail — gracefully, offering the visitor a pre-written email instead, but it will
fail.

**Already done** for thepruuf.com — this section is the record of what was set
and how to change it.

**5A. The origin allowlist:**

```bash
npx supabase secrets set \
  CONTACT_ALLOWED_ORIGINS="https://thepruuf.com,https://www.thepruuf.com"
npx supabase functions deploy contact --no-verify-jwt
```

Setting this secret **replaces** the built-in list rather than adding to it, so
include every origin you want, and keep `http://localhost:8000` if you want the
form to work while developing.

**No `*.pages.dev` entry, and no wildcard.** A Cloudflare Pages project name is
claimed first-come, so listing one before creating it would let whoever claims
it post into the table from a page we do not control. The consequence is that
branch-preview URLs cannot submit the form — they fall back to the pre-composed
email. If you want the form working on the `.pages.dev` address, create the
project first and then add its real hostname here.

**5B. Set a pepper for the IP hashing**, so the rate-limit hashes are not
derived from the service key:

```bash
npx supabase secrets set CONTACT_IP_PEPPER="$(openssl rand -hex 32)"
npx supabase functions deploy contact --no-verify-jwt
```

**5C. Update the canonical URLs** if your domain is not `thepruuf.com`. They are
declarations of where each page lives, used by search engines and by link
previews:

```bash
cd site
grep -rl "thepruuf.com" *.html _shell.py | xargs sed -i '' 's|pruuf\.app|yourdomain.com|g'
python3 check.py
```

**5D. Prove it works from the real domain.** Open `https://thepruuf.com/contact.html`,
send yourself a message, and confirm you get the "Thank you — we have it."
panel rather than the fallback. Then read it back:

Supabase dashboard → **Table Editor** → `contact_requests`. Your message is
there.

---

## Step 6 — Read the messages people send you

There is no inbox integration; the messages land in a table. Two ways to see
them:

**The dashboard.** <https://supabase.com/dashboard/project/taszjafyqcilujpygtbs>
→ Table Editor → `contact_requests`. Sort by `created_at` descending. Mark one
`handled` when you have replied, so the next look is short.

**SQL, for the ones you have not answered:**

```sql
select created_at, intent, name, org, email, message
  from public.contact_requests
 where not handled
 order by created_at desc;
```

The table holds personal data. Delete a row once the conversation it belongs to
is over — the privacy page promises exactly that:

```sql
delete from public.contact_requests where id = '…';
```

> **Worth setting up when you have ten minutes:** Supabase can send a webhook on
> insert (Database → Webhooks) to anything that emails you. Until then, look at
> the table a couple of times a week. A contact form nobody reads is worse than
> no contact form.

---

## Step 7 — Release day, when the app goes live

One line, in `site/assets/pruuf.js`:

```js
appStoreLive: true,
```

Every "Get the launch link" button on every page turns into a real **Download on
the App Store** link pointing at the product page. Nothing else needs editing.

Leave it `false` until the app is *publicly released* — the App Store product
page returns 404 while the record exists only in App Store Connect, and a dead
download button on every page is a bad first impression at the worst possible
moment.

Then email the people who signed up:

```sql
select email, created_at from public.contact_requests
 where intent = 'launch' order by created_at;
```

You promised them exactly one email. Send exactly one.

---

## Step 8 — Give Apple the URLs

App Store Connect → your app → **App Information**:

- **Privacy Policy URL:** `https://thepruuf.com/privacy.html`
- **Support URL:** `https://thepruuf.com/support.html`
- **Marketing URL:** `https://thepruuf.com` *(optional, but now worth having)*

Both required URLs must be publicly reachable before Apple will accept the
submission. Load them in a private browsing window to be sure you are not
seeing a cached or authenticated version.

---

## Updating the site later

| What changed | What to do |
|---|---|
| Copy on the landing or enterprise page | Edit the HTML, re-upload |
| Privacy, terms, support, 404 | Edit the strings in `_shell.py`, run `python3 site/_shell.py`, re-upload |
| Anything at all | `python3 site/check.py` before you upload |
| The app's screenshots | Re-run `AppStore/capture.sh`, then `marketing/render_devices.py`, then `python3 site/build_assets.py` |
| The provider dashboard | `cp portal/index.html site/dashboard/index.html` |

To see the whole site as an image at three widths — which is the only way to
judge spacing over a page this long:

```bash
cd site && python3 -m http.server 8000 &
python3 site/shots.py
```

---

## If something is wrong

**The contact form says the connection failed.** The origin is not on the
allowlist — redo Step 5A with your exact domain, including `https://` and
without a trailing slash. Confirm with:

```bash
curl -i -X OPTIONS https://taszjafyqcilujpygtbs.supabase.co/functions/v1/contact -H "Origin: https://thepruuf.com"
```

You want `access-control-allow-origin: https://thepruuf.com` in the response. If it
says `null`, the secret has not taken effect — redeploy the function.

**The dashboard on the enterprise page is blank.** The `dashboard/` folder did
not get uploaded. It must sit next to `enterprise.html`.

**Styling is missing everywhere.** `assets/` did not get uploaded, or the folder
itself was dragged instead of its contents, putting everything one level too
deep.

**The favicon is the old one.** Browsers cache favicons aggressively and ignore
normal refreshes. Load `https://thepruuf.com/favicon.ico` directly once.

**Changes are not showing up.** Hard-reload (⌘⇧R). If you are on Cloudflare,
**Caching → Purge Everything** once.
