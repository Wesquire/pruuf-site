# Pruuf — public site

Three pages Apple requires to be publicly reachable before it will accept the
app submission. Plain HTML, no build step, no dependencies.

- `index.html` — landing
- `privacy.html` — **Privacy Policy URL** (mandatory)
- `support.html` — **Support URL** (mandatory)

Regenerate `privacy.html` after editing `../AppStore/copy/privacy-policy.md`;
the markdown is the source of truth.

## Publishing (see the step-by-step in the chat, or below)

The app repo is PRIVATE, and GitHub Pages cannot serve public pages from a
private repo on a free plan — so these live in their own public repo.

1. Create a new PUBLIC repo named `pruuf-site`.
2. Copy the contents of this folder into it (not the folder itself).
3. Push to `main`.
4. Repo → Settings → Pages → Source: "Deploy from a branch" → `main` / `/ (root)` → Save.
5. Wait ~1 minute. The URLs become:
   - https://wesquire.github.io/pruuf-site/privacy.html
   - https://wesquire.github.io/pruuf-site/support.html
