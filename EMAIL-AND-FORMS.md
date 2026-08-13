# The forms, the email, and what you control

Everything a visitor can send you, where it lands, how to read it, how to change
what it says, and how to delete it.

`DEPLOY.md` covers first-time setup. This is the file to open afterwards, when
somebody asks "did that walkthrough request come through?" or "can we change the
wording?".

---

## What can be submitted

There are **two** forms and they are the **same endpoint** — the launch signup is
the contact form with everything except the email address left blank.

| | Where | Fields | `intent` |
|---|---|---|---|
| **Contact form** | `contact.html` | name, org, email, roster size, message, intent | whatever the visitor picks |
| **Launch signup** | `index.html#launch`, and the same block on `enterprise.html` | email only | `launch` |

Both post to the `contact` Edge Function, both write to the **`contact_requests`**
table, and both trigger the same notification email.

**"Book a walkthrough"** is not a third thing. Every one of those buttons links
to `contact.html?intent=enterprise`, and the page reads that parameter and
pre-selects the intent — so a walkthrough request arrives as an enterprise
enquiry with 🔔 on the subject line. If you want it to be its own category, add
an `<option value="walkthrough">` to the select in `contact.html` and point the
buttons at `?intent=walkthrough`; nothing else needs to change, because the
intent is stored as free text.

---

## Where it lands

**Table:** `public.contact_requests`, in Supabase.

<https://supabase.com/dashboard/project/taszjafyqcilujpygtbs> → **Table Editor**
→ `contact_requests`.

**The table is the record. The email is only a nudge.** The row is committed
*before* the email is attempted, and a failed send is logged rather than raised
— so a Resend outage costs you a notification, never an enquiry. If you ever
doubt whether something arrived, look at the table, not the inbox.

### Reading it

```sql
select created_at, intent, name, org, email, size, message
  from public.contact_requests
 where not handled
 order by created_at desc;
```

Mark one done when you have replied, so the next look is short:

```sql
update public.contact_requests set handled = true where id = '…';
```

### Just the launch list

```sql
select created_at, email
  from public.contact_requests
 where intent = 'launch'
 order by created_at;
```

### Exporting it

Table Editor → the table → **⋯ → Export as CSV**, or run the query above and use
the **Download CSV** button under the SQL editor results. That CSV is the mailing
list to import into whatever you send the launch announcement with.

### Deleting it

The table holds personal data and the privacy page promises it does not sit
there forever. Delete a row once the conversation it belongs to is over:

```sql
delete from public.contact_requests where id = '…';
```

Everything handled and older than a year:

```sql
delete from public.contact_requests
 where handled and created_at < now() - interval '1 year';
```

The launch list is the exception — those people asked to be told about a thing
that has not happened yet. Keep them until you have told them, then delete.

---

## The email you get

Off by default. It needs two secrets, because Supabase cannot send mail itself:

```bash
npx supabase secrets set RESEND_API_KEY="re_xxxxxxxx" CONTACT_NOTIFY_EMAIL="wesleymwilliams@gmail.com"
```

```bash
npx supabase functions deploy contact --no-verify-jwt
```

With them unset **nothing is broken** — the row is still saved and still
readable. You are simply not told about it.

### What arrives

```
Subject: 🔔 Pruuf enterprise — Jane Doe · Sunrise Home Care
Reply-To: jane@sunrisehomecare.com

Intent:  enterprise
Name:    Jane Doe
Org:     Sunrise Home Care
Email:   jane@sunrisehomecare.com
Size:    40-100
Page:    /enterprise.html

We have about sixty clients across two offices and…
```

- The **🔔** appears on `enterprise` and `partnership` only. Those are the ones
  with a clock on them; everything else can wait for the next tidy-up.
- **Reply-To is the sender**, so hitting reply in your mail client goes to them
  and not to Resend.
- A launch signup arrives with the body
  `(no message — this was the launch-notification signup)`, so it is obvious at a
  glance that there is nothing to read.

### Changing the destination

```bash
npx supabase secrets set CONTACT_NOTIFY_EMAIL="someone.else@example.com"
npx supabase functions deploy contact --no-verify-jwt
```

One address only. For several people, forward it, or use a group address.

### Sending from your own domain

`onboarding@resend.dev` works and looks like what it is. To send from
`hello@thepruuf.com`:

1. Resend → **Domains** → add `thepruuf.com`.
2. Add the DNS records it gives you. Two clicks — the domain is already on
   Cloudflare, and Resend's instructions name the exact record types.
3. Wait for Resend to show the domain **verified**. This is usually minutes.

```bash
npx supabase secrets set CONTACT_FROM_EMAIL="Pruuf <hello@thepruuf.com>"
npx supabase functions deploy contact --no-verify-jwt
```

Do not set `CONTACT_FROM_EMAIL` to an address at a domain Resend has not
verified. The send fails, silently as designed, and you stop getting
notifications while the form goes on working perfectly.

### Changing the wording

`supabase/functions/contact/index.ts`, the `notify()` function. The subject line
is one template string and the body is a list of lines. Redeploy after editing:

```bash
npx supabase functions deploy contact --no-verify-jwt
```

---

## What the sender sees

**Nothing is emailed to them.** There is no auto-reply, deliberately: an
automatic "we have received your message" from a product that is not launched
yet reads as a machine, and this site's whole argument is that a person is
behind it. The confirmation is on the page — the form is replaced in place by
"Thank you — we have it. You'll hear back within one business day, from a
person, at the address you gave us." — and the reply they get is one you wrote.

That sentence is a promise you have to keep. It lives in `contact.html` under
`data-form-done`; change it there if a business day is not realistic.

If you ever do want an auto-reply, it belongs in `notify()` as a **second**
`fetch` to Resend with `to: [sender]`, and it must be as fail-soft as the first
one. Do not make the visitor's success depend on it.

---

## Controlling the launch-signup screen

**Before launch** — the section at `index.html#launch` collects email addresses
and every "Get Pruuf" button on every page scrolls to it.

**On release day**, one line in `site/assets/pruuf.js`:

```js
appStoreLive: true,
```

Every "Get the launch link" button turns into a real **Download on the App
Store** link pointing at the product page. Nothing else needs editing, and the
signup section can stay where it is or be deleted.

Leave it `false` until the app is **publicly released**. The App Store product
page returns 404 while the record exists only in App Store Connect, and a dead
download button on every page is a bad first impression at the worst possible
moment.

To change what the signup section *says*, edit the block under
`<section id="launch">` in `site/index.html`. It also appears on
`enterprise.html`; `python3 site/check.py` will tell you if you break a link
while you are in there.

---

## When the form does not work

**Nothing arrives at all, from anywhere.** The origin allowlist. The function
only accepts requests from origins it knows, and Cloudflare serves both
`thepruuf.com` and a `*.pages.dev` preview address:

```bash
npx supabase secrets set CONTACT_ALLOWED_ORIGINS="https://thepruuf.com,https://www.thepruuf.com,https://pruuf.pages.dev"
npx supabase functions deploy contact --no-verify-jwt
```

**A visitor says it rejected them.** The three quiet defences, in the order they
are likeliest to fire:

- **Too fast.** A form completed in under a couple of seconds is a script. A
  real person pasting one email address can trip this — they see an error and
  succeed on the second try.
- **Rate limit.** A handful an hour from one source, counted in SQL so two
  simultaneous requests cannot both slip through.
- **Honeypot.** A hidden field a human never sees. Some password managers fill
  in every field on a page, including that one.

None of them is silent to the visitor: each returns a message and the page
offers a pre-written email as a fallback, so nobody is ever left with a form
that simply does nothing.

**Checking it end to end:**

```bash
python3 supabase/tests/prod_contact.py
```

Submits through the real endpoint, asserts the row lands, checks the CORS
headers, and cleans up after itself so it can be run as often as you like.
