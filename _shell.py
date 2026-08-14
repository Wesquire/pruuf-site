#!/usr/bin/env python3
"""Generate the document pages — privacy, terms, support, 404.

The marketing pages are hand-written because every section of them is
different. These four are the same page four times with different prose, and
keeping the header and footer identical across them by hand is exactly the sort
of thing that drifts: a link gets added to one footer and not the others, and
six months later two pages disagree about where "Support" lives.

So the shell lives here, once, and the four pages are generated from it.

    python3 site/_shell.py

Edit the BODY strings below, re-run, and the four HTML files are rewritten. The
marketing pages are not touched.
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

MARK = ('<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        '<path d="M12 21s-7.5-4.7-7.5-10A4.5 4.5 0 0 1 12 8.5 4.5 4.5 0 0 1 19.5 11'
        'c0 5.3-7.5 10-7.5 10Z" fill="#fff"/>'
        '<path d="M8.8 12.4l2.3 2.3 4.3-4.6" stroke="#0B7A45" stroke-width="2.1" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{robots}<link rel="canonical" href="https://thepruuf.com/{slug}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="https://thepruuf.com/assets/img/og-card.png">
<meta property="og:url" content="https://thepruuf.com/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FBFAF7">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="stylesheet" href="assets/pruuf.css">
<script src="assets/pruuf.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html"><span class="brand-mark">{mark}</span>Pruuf</a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav" aria-label="Menu">
      <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
    <nav class="site-nav" id="nav" aria-label="Main">
      <a href="index.html"{home}>Home</a>
      <a href="index.html#how">How it works</a>
      <a href="index.html#pricing">Pricing</a>
      <a href="enterprise.html">For care providers</a>
      <a href="contact.html"{contact}>Contact</a>
      <a class="btn btn--ok btn--sm js-cta-app" href="index.html#launch"
         data-live-label="Download on the App Store"><span class="js-cta-label">Get Pruuf</span></a>
    </nav>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-cols">
      <div>
        <a class="brand" href="index.html" style="margin-bottom:1rem">
          <span class="brand-mark">{mark}</span>Pruuf
        </a>
        <p class="small" style="max-width:19rem">
          A daily check-in for the people you love. Made by The ScoutsOn Watch
          Company.
        </p>
      </div>
      <div>
        <h4>Pruuf</h4>
        <ul>
          <li><a href="index.html#how">How it works</a></li>
          <li><a href="index.html#pricing">Pricing</a></li>
          <li><a href="index.html#faq">Questions</a></li>
          <li><a href="enterprise.html">For care providers</a></li>
        </ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="contact.html">Contact us</a></li>
          <li><a href="support.html">Support</a></li>
          <li><a href="contact.html?intent=enterprise">Talk to sales</a></li>
        </ul>
      </div>
      <div>
        <h4>Legal</h4>
        <ul>
          <li><a href="privacy.html">Privacy policy</a></li>
          <li><a href="terms.html">Terms of use</a></li>
          <li><a href="security.html">Security</a></li>
          <li><a href="terms.html#pricing">Pricing promise</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-base">
      <span>&copy; <span data-year>2026</span> The ScoutsOn Watch Company. All rights reserved.</span>
      <span>Pruuf notifies the people you add. It is not an emergency service.</span>
    </div>
  </div>
</footer>
</body>
</html>
"""


def page(slug, title, description, body, noindex=False, nav=""):
    html = SHELL.format(
        slug=slug, title=title, description=description, body=body.strip(),
        mark=MARK,
        robots='<meta name="robots" content="noindex">\n' if noindex else "",
        home=' aria-current="page"' if nav == "home" else "",
        contact=' aria-current="page"' if nav == "contact" else "",
    )
    with open(os.path.join(HERE, slug), "w") as f:
        f.write(html)
    print(f"  {slug:<16} {len(html) // 1024}KB")


# ═══════════════════════════════════════════════════════════════════════════
# Privacy. The legal text is the source of truth in
# AppStore/copy/privacy-policy.md — keep the two in step when either changes.
# ═══════════════════════════════════════════════════════════════════════════
PRIVACY = """
<section class="section section--tight">
  <div class="wrap doc">
    <p class="eyebrow">Legal</p>
    <h1 class="h1">Privacy Policy</h1>
    <p class="updated" style="margin-top:1.25rem">
      Pruuf &middot; The ScoutsOn Watch Company &middot; Last updated 12 August 2026
    </p>

    <h2 id="who">Who we are</h2>
    <p>Pruuf is published by <strong>The ScoutsOn Watch Company</strong>. &ldquo;We&rdquo;
      and &ldquo;us&rdquo; below mean that company.</p>

    <h2 id="short">The short version</h2>
    <p>Pruuf stores your first name, the time of day you&rsquo;ve chosen to check
      in, and a list of who is connected to you. It does not track your location,
      read your messages, or show you advertising. There are no accounts and no
      passwords.</p>

    <h2 id="collect">What we collect</h2>
    <p><strong>A first name.</strong> Whatever you type when you set up. It can be
      a nickname. It is shown to the family members connected to you so they know
      whose check-in they&rsquo;re seeing.</p>
    <p><strong>Your check-in time and time zone.</strong> So we know when a missed
      check-in should trigger an alert.</p>
    <p><strong>A record of your check-ins.</strong> The date and time you tapped
      the button.</p>
    <p><strong>A record of help requests.</strong> If you tap &ldquo;I need
      help&rdquo;, we store the time you tapped it and whether it was sent or
      cancelled, so the app knows whether your loved ones still need to be
      alerted.</p>
    <p><strong>An anonymous account identifier.</strong> Created automatically
      when you first open the app. It is a random identifier. It is not linked to
      your email, phone number, Apple ID, or any advertising identifier.</p>
    <p><strong>A push notification token</strong>, if you allow notifications.
      This is what lets Apple deliver a notification to your device. We store it
      so we know where to send alerts. One token is stored per device, so an alert
      reaches your iPhone, your iPad and your Apple Watch rather than only the
      last one you set up.</p>
    <p><strong>A record of each device you use Pruuf on.</strong> When you add a
      second device we store, for that device: a random identifier, whether it is
      an iPhone, iPad, Apple Watch or Mac, the device name iOS reports for it, and
      the date it was added. This is what the &ldquo;My devices&rdquo; screen shows
      you, and it is what lets you sign a device out.</p>
    <p>The device name comes from Apple and, for apps like ours, is the model name
      &mdash; &ldquo;iPad Pro 13-inch&rdquo;, not &ldquo;Margaret&rsquo;s
      iPad&rdquo;. We do not request the entitlement that would reveal your
      personal device name, and we collect no hardware identifier, serial number,
      IMEI, or advertising identifier.</p>
    <p><strong>A pairing secret, stored in your own iCloud.</strong> So a new
      iPhone or iPad signed in to the same Apple ID can join your existing account
      without you typing anything, Pruuf saves one random string to Apple&rsquo;s
      iCloud key-value storage. That storage belongs to you and your Apple ID; we
      cannot read it, and nothing else is ever put there. If you have iCloud turned
      off, nothing is stored and you add devices with a six-character code
      instead.</p>
    <p><strong>Who is connected to whom.</strong> The link between a person
      checking in and the people receiving their check-ins.</p>
    <p><strong>If you write to us through this website:</strong> the name, email
      address and message you type into the contact form, so that we can reply. We
      also store a one-way hash of your IP address &mdash; not the address itself
      &mdash; purely so that one source cannot flood the form. The form posts to
      our own servers; it is not a third-party form service, and nothing you write
      is passed to anyone else. We delete these messages once the conversation
      they belong to is finished, and you can ask us to delete yours sooner.</p>

    <h2 id="not-collected">What we do not collect</h2>
    <ul>
      <li><strong>Your location.</strong> Never, in any form.</li>
      <li><strong>Your contacts.</strong> When you add a family member, the app
        opens Apple&rsquo;s contact picker and uses the name and number you select
        to pre-fill a text message and to offer a call button. <strong>That
        information is never sent to us.</strong> It is stored on your device and
        synced through your own iCloud account &mdash; so if you use Pruuf on an
        iPhone and an iPad you only add it once &mdash; which means it is covered
        by Apple&rsquo;s encryption and your Apple ID, and never by us. We have no
        way to read it.</li>
      <li><strong>Your email address or phone number</strong> &mdash; unless you
        give us an email address by writing to us.</li>
      <li><strong>Any health, fitness, or medical data.</strong></li>
      <li><strong>Analytics, advertising identifiers, or behavioural data.</strong>
        There are no third-party advertising or analytics SDKs in this app, and
        none on this website either &mdash; no cookies are set by it, no fonts or
        scripts are loaded from anybody else&rsquo;s servers, and there is nothing
        here that would need a cookie banner.</li>
    </ul>

    <h2 id="use">How we use it</h2>
    <p>Only to make the app work:</p>
    <ol>
      <li>To send a notification to your loved ones when you check in.</li>
      <li>To send an alert to them if you have not checked in by your chosen time.</li>
      <li>To send an alert if you tap the help button.</li>
      <li>To show you and them the current status.</li>
    </ol>
    <p>We do not sell your data. We do not share it with advertisers, data
      brokers, or any third party for their own purposes.</p>

    <h2 id="where">Where it&rsquo;s stored</h2>
    <p>Data is stored on servers operated by Supabase, which hosts our database in
      the United States. Push notifications are delivered through Apple&rsquo;s
      Push Notification service. Both process this data on our behalf in order to
      provide the service.</p>

    <h2 id="retention">How long we keep it</h2>
    <p>We keep your information for as long as you use the app. Check-in records
      are kept so the app can show whether you&rsquo;ve checked in today.</p>

    <h2 id="delete">Deleting your data</h2>
    <p><strong>In the app:</strong> open Settings (the gear in the top corner) and
      choose <strong>Delete my account</strong>. This immediately and permanently
      removes your profile, your check-in history, your help requests, every
      connection between you and your loved ones, and the record of every device
      you had signed in. It cannot be undone, and it takes effect for all your
      devices at once, not just the one you did it on.</p>
    <p><strong>Removing a single device:</strong> Settings &rarr;
      <strong>My devices</strong> &rarr; the &#8854; next to it. That device stops
      receiving alerts and is forgotten; your account and everyone connected to you
      are unaffected.</p>
    <p>You can also email
      <a href="mailto:wesleymwilliams@gmail.com">wesleymwilliams@gmail.com</a> and
      we&rsquo;ll do it for you within 30 days.</p>
    <p>Note that deleting the app from your phone does <strong>not</strong> by
      itself remove your data from our servers, because the account is anonymous
      and tied to the app installation. Use Delete my account first if you want it
      gone.</p>

    <h2 id="children">Children</h2>
    <p>Pruuf is not directed at children and we do not knowingly collect
      information from anyone under 13.</p>

    <h2 id="security">Security</h2>
    <p><strong>There are no passwords.</strong> Pruuf has no accounts, usernames
      or password resets, so there is no credential of yours to leak, phish, or
      reuse against you on another site. Two people are connected by a
      six-character code that grants nothing else.</p>
    <p><strong>Check-ins are signed on the device that makes them.</strong> Each
      install holds a private key created inside Apple&rsquo;s Secure Enclave,
      which cannot be exported, copied to another device or recovered from a
      backup. We verify the signature before recording a check-in as verified &mdash;
      so a verified check-in could not have been produced by anybody not holding
      that unlocked device, ourselves included. Where signing is unavailable the
      check-in is still recorded, unsigned; being told about a missed day matters
      more than being able to prove one.</p>
    <p><strong>Access is restricted by row-level security</strong> inside the
      database itself, keyed to the account making the request, so one
      person&rsquo;s data is not returned to another &mdash; a rule the database
      enforces rather than one our application code has to remember.</p>
    <p>Traffic between the app and our servers is encrypted with TLS, and stored
      data is encrypted at rest.</p>
    <p><strong>We do not offer end-to-end encryption, and we will say why.</strong>
      Our servers must be able to see that a check-in did not arrive, or they
      could not alert anyone &mdash; which is the entire purpose of Pruuf. Anybody
      offering both server-side alerting and end-to-end encryption is describing
      something that cannot work.</p>
    <p>No system is perfectly secure, and we cannot guarantee absolute security.
      A fuller description of how this works is at
      <a href="security.html">thepruuf.com/security</a>.</p>

    <h2 id="limitation">An important limitation</h2>
    <div class="callout">
      <p>Pruuf is not an emergency service and is not a medical alert device. The
        help button notifies the people you have added &mdash; it does not contact
        emergency services, ambulances, or any monitoring centre.</p>
      <p>Notification delivery depends on Apple&rsquo;s service, on internet
        connectivity, and on the recipient&rsquo;s phone and notification settings
        &mdash; none of which we control. Do not rely on Pruuf as the only way of
        knowing whether someone is safe, and never use it in place of calling
        emergency services.</p>
    </div>

    <h2 id="changes">Changes</h2>
    <p>If this policy changes we&rsquo;ll update the date at the top of this
      page.</p>

    <h2 id="contact">Contact</h2>
    <p>The ScoutsOn Watch Company &middot;
      <a href="mailto:wesleymwilliams@gmail.com">wesleymwilliams@gmail.com</a>
      &middot; <a href="contact.html?intent=privacy">write to us</a></p>
  </div>
</section>
"""

# ═══════════════════════════════════════════════════════════════════════════
# Terms. Written to be read, and to say the two things that actually matter:
# what Pruuf is not, and what happens to your price.
# ═══════════════════════════════════════════════════════════════════════════
TERMS = """
<section class="section section--tight">
  <div class="wrap doc">
    <p class="eyebrow">Legal</p>
    <h1 class="h1">Terms of Use</h1>
    <p class="updated" style="margin-top:1.25rem">
      Pruuf &middot; The ScoutsOn Watch Company &middot; Last updated 12 August 2026
    </p>

    <p class="lead">These terms are the agreement between you and The ScoutsOn
      Watch Company for the use of Pruuf. We have written them to be read rather
      than to be impressive. Using the app means you accept them.</p>

    <h2 id="what">1. What Pruuf is</h2>
    <p>Pruuf is a notification tool between family members and the people they
      care about. One person taps a button once a day; the people connected to
      them are told. If the tap does not happen by the time that person chose,
      those people are told that instead.</p>

    <h2 id="not">2. What Pruuf is not</h2>
    <div class="callout">
      <p><strong>Pruuf is not an emergency service, a medical device, a medical
        alert system, or a monitoring service.</strong> It does not contact
        emergency services, ambulances, fire, police, or any monitoring centre,
        and it never will without saying so explicitly.</p>
      <p>It notifies the people you have added and nobody else. If someone needs
        help now, call your local emergency number. Do not use Pruuf as the only
        means of knowing whether a person is safe.</p>
    </div>
    <p>Delivery of a notification depends on Apple&rsquo;s Push Notification
      service, on internet connectivity, on the recipient&rsquo;s device being
      switched on, and on their notification settings &mdash; none of which are
      under our control. A notification may be delayed or may not arrive.</p>

    <h2 id="accounts">3. Accounts and who may use it</h2>
    <p>Pruuf creates an anonymous account for you automatically. There is no
      password to protect, and equally no way for us to recover an account from a
      device you no longer have &mdash; which is why the app offers device pairing
      and a six-character code.</p>
    <p>You must be 13 or older to use Pruuf. You are responsible for who you
      connect to your account: anyone holding your six-character code can receive
      your check-ins until you remove them.</p>

    <h2 id="pricing">4. Subscriptions, and our pricing promise</h2>
    <p><strong>The person who checks in is never charged.</strong> That is not an
      introductory offer; it is how the product works.</p>
    <p>Family members who want alerts subscribe. Subscriptions are billed by Apple
      through your App Store account, renew automatically, and can be cancelled at
      any time in your Apple ID settings &mdash; cancelling takes effect at the end
      of the period you have paid for. The free trial period is stated in the app
      before you buy.</p>
    <p>Our promise about price changes, which we intend to keep permanently:</p>
    <ul>
      <li><strong>The price you sign up at is the price you keep paying</strong>
        &mdash; for as long as you keep your subscription. If we put the price up
        for new subscribers, you are not moved.</li>
      <li><strong>This holds even if you cancel and come back later.</strong>
        Apple&rsquo;s own price preservation only lasts while a subscription runs
        continuously; ours does not depend on that, because your rate is recorded
        against your account rather than against a billing streak.</li>
    </ul>
    <p>We are deliberately not promising to move you <em>down</em> if we ever
      launch at a lower price. We would rather say what we will actually do: a
      price we advertise is a price we keep, and a new price is a new offer to new
      subscribers. If we ever ran a lower launch price you would be free to
      cancel and take it &mdash; and we would tell you so.</p>
    <p>One subscription covers everyone you look after. Refunds are handled by
      Apple under the App Store&rsquo;s terms, not by us &mdash; we cannot issue
      them, though we will happily help you ask.</p>

    <h2 id="acceptable">5. Using it properly</h2>
    <p>Do not use Pruuf to monitor somebody who has not agreed to it, to harass
      anyone, to attempt to break into other people&rsquo;s accounts, or to
      interfere with the service. Connections in Pruuf are consensual by design:
      the person checking in shares their own code, and can remove anybody at any
      time.</p>

    <h2 id="availability">6. Availability</h2>
    <p>We work to keep Pruuf running continuously, and the alerting runs on our
      servers precisely so that it does not depend on any one phone. Even so, we
      do not guarantee uninterrupted service, and we may change or discontinue
      features. If we ever discontinue the service entirely, we will give notice
      in the app before it stops.</p>

    <h2 id="liability">7. Liability</h2>
    <p>Pruuf is provided &ldquo;as is&rdquo;. To the fullest extent permitted by
      law, we are not liable for indirect or consequential loss, or for any harm
      arising from a notification that was delayed, undelivered, or not acted upon.
      Our total liability is limited to the amount you paid us in the twelve months
      before the claim.</p>
    <p>Nothing in these terms limits liability that cannot lawfully be limited,
      and some jurisdictions do not allow certain exclusions &mdash; in which case
      the rest still applies and only the unlawful part does not.</p>

    <h2 id="changes">8. Changes to these terms</h2>
    <p>If we change these terms we will update the date at the top of this page,
      and we will tell you in the app if the change is material.</p>

    <h2 id="law">9. Governing law</h2>
    <p>These terms are governed by the laws of the State of Delaware, United
      States, without regard to its conflict-of-law rules.</p>

    <h2 id="contact">10. Contact</h2>
    <p>The ScoutsOn Watch Company &middot;
      <a href="mailto:wesleymwilliams@gmail.com">wesleymwilliams@gmail.com</a>
      &middot; <a href="contact.html">write to us</a></p>

    <p class="note" style="margin-top:2.5rem">These terms are written in plain
      language on purpose and have not been reviewed by a lawyer. If you are
      buying Pruuf on behalf of an organisation, ask us for the provider agreement
      instead &mdash; it is the document your procurement team will want.</p>
  </div>
</section>
"""

# ═══════════════════════════════════════════════════════════════════════════
# Support. Apple requires a reachable support URL; this is written for the
# person with the actual problem rather than for the requirement.
# ═══════════════════════════════════════════════════════════════════════════
SUPPORT = """
<section class="section section--tight">
  <div class="wrap doc">
    <p class="eyebrow">Support</p>
    <h1 class="h1">Something not working?</h1>
    <p class="lead" style="margin-top:1.25rem">
      Start here &mdash; the things that go wrong go wrong in a handful of
      predictable ways, and the fix is usually thirty seconds. If none of this
      helps, <a href="contact.html?intent=support">write to us</a> and a person
      will reply within one business day.
    </p>

    <div class="callout" style="margin-top:2.5rem">
      <p><strong>If someone needs help right now, call your local emergency
        number.</strong> Pruuf notifies the family members you have added. It does
        not contact emergency services, and nobody is watching this inbox
        overnight.</p>
    </div>

    <h2 id="not-arriving">Alerts aren&rsquo;t arriving</h2>
    <p>In order of how often each one is the cause:</p>
    <ol>
      <li><strong>Notifications are switched off for Pruuf.</strong> On the phone
        that should be receiving them: Settings &rarr; Notifications &rarr; Pruuf
        &rarr; Allow Notifications on. Check <em>Time Sensitive</em> is allowed
        too, or a Focus mode will silently hold alerts back.</li>
      <li><strong>A Focus or Do Not Disturb schedule</strong> is running at the
        time the alert fires &mdash; often overnight, which is exactly when it
        matters.</li>
      <li><strong>The subscription has lapsed.</strong> Alerts stop when it does.
        Open Settings inside the app; it says so plainly at the top.</li>
      <li><strong>The connection was never completed.</strong> On the checking-in
        person&rsquo;s phone, open <em>My Loved Ones</em> &mdash; if the name is not
        listed there, the code was never entered successfully.</li>
    </ol>

    <h2 id="code">The six-character code doesn&rsquo;t work</h2>
    <p>Codes are not case-sensitive and never contain the letter O or the digit 0
      &mdash; if you are looking at something that appears to, it is the other one.
      Codes do not expire. If it still refuses, have the person checking in open
      <em>My Loved Ones</em> and read the code straight off that screen rather than
      from a text message that may be out of date.</p>

    <h2 id="missed">She checked in, but I got a missed alert</h2>
    <p>Alerts fire against the check-in time in <em>her</em> time zone, not yours.
      If she has travelled, or if the two of you are in different zones, open
      Settings on her phone and confirm the time zone shown is where she actually
      is. Tell us if this happens when the time zone is right &mdash; that would be
      a fault on our side and we want to know today, not next month.</p>

    <h2 id="watch">The watch app is empty or won&rsquo;t open</h2>
    <p>The watch gets its account from the iPhone. Open Pruuf on the iPhone once,
      with the watch on your wrist and nearby, and give it a few seconds. If the
      watch still shows nothing, restart it &mdash; watchOS caches aggressively and
      this clears it.</p>

    <h2 id="new-phone">Moving to a new phone</h2>
    <p>If the new phone is signed in to the same Apple ID and you have iCloud on,
      install Pruuf and it joins your existing account by itself. If not, open
      Settings &rarr; <em>My devices</em> on the old phone, and use the code shown
      there on the new one.</p>

    <h2 id="cancel">Cancelling, and getting a refund</h2>
    <p>Cancel any time: on your iPhone, Settings &rarr; your name &rarr;
      Subscriptions &rarr; Pruuf &rarr; Cancel. It keeps working until the end of
      the period you have paid for. Refunds are issued by Apple rather than by us
      &mdash; <a href="https://reportaproblem.apple.com" rel="noopener">Apple&rsquo;s
      refund page</a> is the place to ask, and we will help if it gets stuck.</p>

    <h2 id="delete">Deleting an account</h2>
    <p>In the app: Settings (the gear, top right) &rarr; <strong>Delete my
      account</strong>. It is immediate, permanent, and applies to every device at
      once. Deleting the app on its own does not remove anything from our servers.
      Full detail is in the <a href="privacy.html#delete">privacy policy</a>.</p>

    <h2 id="human">Talk to a person</h2>
    <p><a class="arrow" href="contact.html?intent=support">Write to us</a> &mdash;
      or email
      <a href="mailto:wesleymwilliams@gmail.com">wesleymwilliams@gmail.com</a>
      directly. Tell us which phone, which screen, and what you expected to happen;
      it saves a round trip.</p>
    <p class="muted">We answer within one business day. If you are a care provider
      with clients affected, say so and we will treat it accordingly.</p>
  </div>
</section>
"""

NOT_FOUND = """
<section class="section" style="display:grid;place-items:center;padding-block:clamp(5rem,14vw,10rem)">
  <div class="wrap center" style="max-width:34rem">
    <p class="eyebrow" style="justify-content:center">404</p>
    <h1 class="display" style="font-size:var(--fs-h1)">That page isn&rsquo;t here.</h1>
    <p class="lead" style="margin-top:1rem">
      It may have moved, or the link may have been mistyped. Nothing is broken on
      your end.
    </p>
    <div class="btn-row btn-row--center" style="margin-top:2rem">
      <a class="btn btn--ok" href="index.html">Back to the start</a>
      <a class="btn btn--ghost" href="contact.html">Tell us the link was wrong</a>
    </div>
  </div>
</section>
"""

# ═══════════════════════════════════════════════════════════════════════════
# Security. Every claim on this page is a claim the code can be held to —
# nothing here is aspirational and nothing is adjectival. "Bank-level" and
# "military-grade" mean nothing, and "end-to-end encrypted" would be a lie:
# the server reads check-ins, and it MUST, or the alert cannot fire when one
# does not arrive. That trade-off is stated rather than hidden, because it is
# the trade-off that makes the product work.
# ═══════════════════════════════════════════════════════════════════════════
SECURITY = """
<section class="section section--tight">
  <div class="wrap" style="max-width:52rem">
    <p class="eyebrow">Security</p>
    <h1 class="h1">What actually protects<br>your mother&rsquo;s data.</h1>
    <p class="lead" style="margin-top:1.25rem">
      Specifics, not adjectives. Every claim below is one you could check, and
      one we would have to answer for.
    </p>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap doc">

    <h2>There is no password to steal</h2>
    <p class="prose">
      Most breaches you read about are password breaches. Somebody gets a
      database of email addresses and password hashes, cracks the weak ones, and
      tries them everywhere else &mdash; because people reuse passwords.
    </p>
    <p class="prose">
      <strong>Pruuf never created that database.</strong> There are no accounts,
      no usernames, no passwords and no password reset emails, so there is
      nothing of that kind to leak, phish, guess, or stuff into another site.
      Two people are connected by a six-character code that does one job and
      grants nothing else.
    </p>
    <p class="prose muted">
      We built it that way so an 82-year-old would never be locked out at eleven
      at night. That it removes the most commonly breached thing in software is
      a genuine consequence, not a marketing claim.
    </p>

    <h2 class="h2" style="margin-top:3rem">A check-in can&rsquo;t be forged</h2>
    <p class="prose">
      When your mother taps I&rsquo;M OK, her device signs that check-in with a
      private key created inside the <strong>Secure Enclave</strong> &mdash; the
      separate security chip in her iPhone, iPad or Apple Watch. That key cannot
      be exported, copied to another device, or recovered from a backup. It
      never leaves the chip; the signing happens there.
    </p>
    <p class="prose">
      Our server checks that signature before recording the check-in as
      verified. Which means a check-in could not have been produced by anybody
      not physically holding her unlocked device &mdash; <strong>including
      us</strong>. We could write a row in our own database; we could not
      produce a signature for it, and the gap would stay visible in the record.
    </p>
    <p class="prose">
      The signature covers the day as well as the moment, so yesterday&rsquo;s
      check-in cannot be replayed as today&rsquo;s.
    </p>
    <div class="callout">
      <p><strong>And if the signing fails, the check-in still goes.</strong> On
        an older device, or after a restore, a check-in is recorded without a
        signature rather than not recorded at all. A family told their mother
        missed a day she did not miss &mdash; because of a cryptographic detail
        &mdash; would be a far worse product than one with no signatures.</p>
    </div>

    <h2 class="h2" style="margin-top:3rem">The database refuses, not the app</h2>
    <p class="prose">
      Every request is filtered by <strong>row-level security</strong> inside
      PostgreSQL itself, keyed to the account making it. One family&rsquo;s data
      is not kept separate because our application code remembers to check &mdash;
      it is kept separate because the database declines to return it.
    </p>
    <p class="prose muted">
      The difference matters. Application checks are the ones that get forgotten
      in the new feature written at midnight. This one cannot be forgotten,
      because it is not written per feature.
    </p>

    <h2 class="h2" style="margin-top:3rem">Encrypted in transit and at rest</h2>
    <p class="prose">
      Everything between the app and our servers travels over TLS. Everything
      stored is encrypted on disk. This is the ordinary, expected standard
      rather than anything clever, and we mention it because its absence would
      matter.
    </p>

    <h2 class="h2" style="margin-top:3rem">Yes, it runs on a server. That&rsquo;s the point.</h2>
    <p class="prose">
      Almost everything calling itself a check-in app is a reminder running on
      the phone of the person being checked on. If that phone is flat, off, or
      at the bottom of a handbag, the app has nothing to say &mdash; and silence
      is indistinguishable from a good day.
    </p>
    <p class="prose">
      <strong>Pruuf&rsquo;s alerts run on our servers.</strong> At her check-in
      time the server looks for a tap, and tells her family if there isn&rsquo;t
      one, whatever state her phone is in. That is the entire product, and it is
      only possible because a system that is not her phone is watching.
    </p>
    <p class="prose">
      It is also why we do <em>not</em> claim end-to-end encryption. End-to-end
      would mean our servers cannot read her check-ins &mdash; and a server that
      cannot read them cannot notice one is missing. Anybody offering you both
      is describing something that does not work. We would rather tell you which
      one we chose, and why.
    </p>

    <h2 class="h2" style="margin-top:3rem">What we never collect</h2>
    <ul class="tick-list">
      <li><strong>No location.</strong> Not optional, not buried in a setting.
        Pruuf never asks for it and could not show it if it wanted to.</li>
      <li><strong>No camera, microphone or health data.</strong></li>
      <li><strong>No advertising or analytics trackers</strong> &mdash; in the
        app, or on this website.</li>
      <li><strong>Nothing sold or shared.</strong> There is no data business
        here; the subscription is the business.</li>
    </ul>

    <h2 class="h2" style="margin-top:3rem">For care providers</h2>
    <p class="prose">
      Signed check-ins are the reason the audit trail is worth something. A
      verified record answers &ldquo;how do you know that was really the
      client?&rdquo; with cryptography rather than with a policy. The integrity
      report shows verified and unverified counts side by side &mdash; a report
      that hid its own gaps would not be an audit trail.
    </p>
    <div class="btn-row" style="margin-top:1.5rem">
      <a class="btn btn--ok" href="contact.html?intent=enterprise">Talk to us about a deployment</a>
      <a class="btn btn--ghost" href="privacy.html">Read the privacy policy</a>
    </div>

    <h2 class="h2" style="margin-top:3rem">Found something?</h2>
    <p class="prose">
      If you believe you have found a security problem, please
      <a href="contact.html?intent=security">tell us</a> before telling anyone
      else, and we will reply within one business day. We will not threaten you,
      and we will credit you if you would like us to.
    </p>
    <p class="prose muted small">
      No system is perfectly secure and we will not pretend otherwise. What we
      will do is describe what we actually built, accurately, and fix what we
      get wrong.
    </p>
  </div>
</section>
"""

if __name__ == "__main__":
    print("→ site/")
    page("privacy.html", "Pruuf — Privacy Policy",
         "How Pruuf handles your data. No location tracking, no advertising, no "
         "analytics, and no third-party trackers on this website either.",
         PRIVACY)
    page("terms.html", "Pruuf — Terms of Use",
         "The agreement for using Pruuf, including what it deliberately is not, "
         "and our promise that a price cut reaches existing subscribers.",
         TERMS)
    page("support.html", "Pruuf — Support",
         "Fixes for the things that go wrong most often, and a way to reach a "
         "person who will reply within one business day.",
         SUPPORT)
    page("security.html", "Pruuf — Security",
         "No passwords to steal, check-ins signed in the Secure Enclave so they "
         "cannot be forged, and row-level security in the database itself.",
         SECURITY)
    page("404.html", "Pruuf — Page not found",
         "That page isn't here.", NOT_FOUND, noindex=True)
