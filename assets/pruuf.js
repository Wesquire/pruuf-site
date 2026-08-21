/* ═══════════════════════════════════════════════════════════════════════════
   Pruuf — site behaviour
   ═══════════════════════════════════════════════════════════════════════════

   Every page loads this one file. Nothing here is required for the site to be
   readable, navigable or purchasable-from: the HTML stands on its own and this
   adds the demo, the reveals, the pricing toggle and the form submission. If
   this file fails to load, the site degrades to a perfectly good static
   brochure rather than to a blank page.

   No dependencies, no analytics, no external requests. See ../../WEBSITE.md.
   ══════════════════════════════════════════════════════════════════════════ */

const CONFIG = {
  /* ── The one switch to flip on release day ───────────────────────────────
     The App Store record exists (id 6798915583) but its public product page
     returns 404 until the app is actually released. Shipping that link now
     would break trust at the exact moment the site is trying to establish it,
     and would do it on every page at once.

     While this is false, every "get the app" button asks for an email instead.
     Set it to true the day the app goes live — nothing else needs editing. */
  appStoreLive: false,
  appStoreURL: 'https://apps.apple.com/app/id6798915583?mt=8',

  /* Where the contact form posts. The same Supabase project the app uses. */
  supabaseURL: 'https://taszjafyqcilujpygtbs.supabase.co',
  supabaseKey: 'sb_publishable_LvnQvFeV0UNFX82WkbzFFw_c8yKwix4',

  contactEmail: 'wesleymwilliams@gmail.com',
};

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
/** True when animation should be skipped entirely.
 *
 *  `?motion=off` exists for the screenshot harness: a full-page capture never
 *  scrolls, so every reveal below the fold would photograph as blank space and
 *  the picture would be worthless as evidence. It takes the same code path the
 *  accessibility setting does, so it cannot drift from it. */
const reducedMotion = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
  new URLSearchParams(location.search).get('motion') === 'off';

/* ═══════════════════════════════════════════════════════════════
   Header — mobile menu and the hairline that appears on scroll
   ═══════════════════════════════════════════════════════════════ */
function initHeader() {
  const header = $('.site-header');
  const nav = $('.site-nav');
  const toggle = $('.nav-toggle');
  if (!header) return;

  const onScroll = () => header.classList.toggle('stuck', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    // Close after following an in-page link, or the menu covers the target.
    nav.addEventListener('click', e => {
      if (e.target.closest('a')) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
}

/* ═══════════════════════════════════════════════════════════════
   Reveal on scroll
   ═══════════════════════════════════════════════════════════════ */
function initReveals() {
  const items = $$('.reveal');
  if (!items.length) return;

  // Reduced motion, or a browser without IntersectionObserver: show everything
  // immediately. Content must never be hidden behind an effect that did not run.
  if (reducedMotion() || !('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('in'));
    return;
  }

  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      // Stagger by position within the parent, so a grid cascades rather than
      // landing all at once.
      const siblings = Array.from(entry.target.parentElement.children)
        .filter(el => el.classList.contains('reveal'));
      const i = Math.max(0, siblings.indexOf(entry.target));
      setTimeout(() => entry.target.classList.add('in'), Math.min(i, 6) * 60);
      obs.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

  items.forEach(el => io.observe(el));
}

/* ═══════════════════════════════════════════════════════════════
   The app-store call to action
   ═══════════════════════════════════════════════════════════════
   The HTML is authored in the HONEST state — every one of these buttons is
   already a working link to the launch-notification form. This function only
   ever upgrades them, so a visitor with JavaScript off still gets a live
   button rather than a dead one.                                          */
function initAppCTAs() {
  if (!CONFIG.appStoreLive) return;
  $$('.js-cta-app').forEach(el => {
    el.href = CONFIG.appStoreURL;
    el.removeAttribute('data-fallback');
    const label = el.querySelector('.js-cta-label') || el;
    label.textContent = el.dataset.liveLabel || 'Download on the App Store';
  });
}

/* ═══════════════════════════════════════════════════════════════
   Hero demo — the whole product in six seconds
   ═══════════════════════════════════════════════════════════════
   A real iPhone drawn in DOM, running the real interface. Tap the button and
   the daughter's notification arrives beside it; play the second scene and the
   day is missed instead.

   Laid out against AppStore/screenshots/iphone-6.5/ rather than from memory.
   The first version invented a green pill button and a screen that has never
   existed, which made the most prominent thing on the landing page a picture
   of a different app — the exact opposite of what a demo is for.          */
function initHeroDemo() {
  const stage = $('#demo');
  if (!stage) return;

  const screen  = $('#demo-screen', stage);
  const feed    = $('#demo-feed', stage);
  const clock   = $('#demo-clock', stage);
  const replay  = $('#demo-replay', stage);
  const missBtn = $('#demo-miss', stage);
  const caption = $('#demo-caption', stage);

  let timers = [];
  const after = (ms, fn) => timers.push(setTimeout(fn, reducedMotion() ? 0 : ms));
  const clear = () => { timers.forEach(clearTimeout); timers = []; };

  const notif = (title, time, body, alarm) => `
    <div class="notif slide-in">
      <div class="notif-icon ${alarm ? 'notif-icon--alarm' : ''}">
        ${alarm ? ICON.bell : ICON.heart}
      </div>
      <div style="min-width:0">
        <div class="notif-title"><span>Pruuf</span><span class="notif-time">${time}</span></div>
        <div class="notif-body"><strong>${title}</strong><br>${body}</div>
      </div>
    </div>`;

  /** The parts of the screen that never change, so the scenes below only
   *  describe what actually differs between them. */
  const chrome = (due, chip) => `
    <div class="app-bar">
      <span class="app-wordmark">PRUUF</span>
      <span class="app-gear">${ICON.gear}</span>
    </div>
    <div class="app-greeting">Good morning, Margaret</div>
    <div class="app-due">${ICON.clock}<span>${due}</span>${
      chip ? `<span class="app-done-chip">${chip}</span>` : ''}</div>`;

  const footer = (dim) => `
    <button class="app-help" type="button" id="demo-help" ${dim ? 'disabled' : ''}
            ${dim ? 'style="opacity:.4"' : ''}>
      ${ICON.exclaim}
      <span>
        <span class="app-help-title">I NEED HELP</span><br>
        <span class="app-help-sub">Tells your loved ones right away</span>
      </span>
    </button>
    <button class="app-loved" type="button" id="demo-loved">MY LOVED ONES</button>`;

  /* ── Scene 1: there is a check-in to do ────────────────────────────── */
  function sceneReady() {
    clear();
    clock.textContent = '8:04';
    caption.textContent = 'Tap I’M OK — and watch this phone.';
    feed.innerHTML = `<p class="small muted mb-0" style="padding:.5rem 0">
        Margaret’s daughter, two states away. Her phone is quiet.</p>`;
    screen.innerHTML = chrome('Check in by 10:00 AM') + `
      <button class="app-big is-inviting" type="button" id="demo-imok">
        <span class="app-big-title">I'M OK</span>
        <span class="app-big-sub">Tap to tell your loved ones</span>
      </button>` + footer();
    wire();
  }

  /* ── Scene 2: she taps it ──────────────────────────────────────────── */
  function sceneCheckedIn() {
    clear();
    caption.textContent = 'That’s the whole app. Every day, one tap.';
    // Still a button, and still tappable — checking in again is the point.
    screen.innerHTML = chrome('Next check-in tomorrow at 10:00 AM', 'DONE TODAY') + `
      <button class="app-big app-big--done fade-swap" type="button" id="demo-imok">
        <span class="app-tick">${ICON.check}</span>
        <span class="app-big-title app-big-title--small">Thanks for<br>checking in</span>
        <span class="app-big-sub app-big-sub--strong">
          Your next check-in is tomorrow at 10:00 AM.</span>
        <span class="app-big-sub" style="opacity:.8;font-size:calc(var(--w) * .042)">
          Checked in at 8:04 AM · I'M OK AGAIN</span>
      </button>` + footer();
    wire();

    after(320, () => {
      feed.innerHTML = notif('Margaret checked in ✓', 'now', 'Checked in at 8:04 AM');
    });
    after(1500, () => {
      feed.insertAdjacentHTML('beforeend', `
        <p class="small muted" style="padding:.9rem 0 0;margin:0">
          No call to make. Nobody wondering.</p>`);
    });
  }

  /* ── Scene 3: the day she doesn't ──────────────────────────────────── */
  function sceneMissed() {
    clear();
    caption.textContent = 'This part runs on our servers — not on her phone.';
    feed.innerHTML = `<p class="small muted mb-0" style="padding:.5rem 0">
        10:00 AM. Nothing has been tapped.</p>`;
    screen.innerHTML = chrome('Overdue · 15m late') + `
      <div class="app-big" style="opacity:.4">
        <span class="app-big-title">I'M OK</span>
        <span class="app-big-sub">Tap to tell your loved ones</span>
      </div>` + footer(true);

    ['9:20', '9:45', '10:00'].forEach((v, i) =>
      after(420 * (i + 1), () => { clock.textContent = v; }));

    after(1500, () => {
      feed.innerHTML = notif('⚠️ Margaret has NOT checked in', '10:00 AM',
        'No check-in today. You may want to reach out.', true);
    });
    after(2300, () => {
      feed.insertAdjacentHTML('beforeend', `
        <div class="card card--flat slide-in" style="margin-top:.85rem;padding:1rem 1.1rem">
          <div style="font-weight:800;margin-bottom:.7rem">What her family can do, right there:</div>
          <div class="btn-row">
            <button class="btn btn--sm btn--ok" type="button" data-demo-act="Calling Margaret…">CALL</button>
            <button class="btn btn--sm btn--ghost" type="button" data-demo-act="Texting Margaret…">TEXT</button>
            <button class="btn btn--sm btn--ghost" type="button" data-demo-act="Told the others you’re handling it.">I’VE GOT THIS</button>
          </div>
          <p class="small muted" style="margin:.9rem 0 0">
            “I’ve got this” tells her brother and sister to stand down, so all
            three of them don’t ring her at once.</p>
        </div>`);

      $$('[data-demo-act]', feed).forEach(b => b.addEventListener('click', () => {
        caption.textContent = b.dataset.demoAct;
        b.closest('.card').querySelectorAll('button').forEach(x => { x.disabled = true; });
        b.style.opacity = '1';
      }));
    });
  }

  /* ── Scene 4: the help button ──────────────────────────────────────── */
  function sceneHelp() {
    clear();
    caption.textContent = 'Tapped by mistake? Stand it down and everyone is told it’s over.';
    screen.innerHTML = chrome('Check in by 10:00 AM') + `
      <div class="app-big app-big--help fade-swap">
        <span class="app-tick">${ICON.bellBig}</span>
        <span class="app-big-title app-big-title--small">HELP IS<br>ON THE WAY</span>
        <span class="app-big-sub app-big-sub--strong">
          Tap to cancel if you're OK</span>
      </div>
      <button class="app-loved" type="button" id="demo-cancel">CANCEL — I'M FINE</button>`;
    $('#demo-cancel', screen).addEventListener('click', () => {
      caption.textContent = 'Stood down — and everyone who was told gets the all-clear.';
      feed.innerHTML = notif('Margaret has cancelled their help request', 'now',
        'Margaret says they’re OK and stood the alert down themselves.');
      after(1400, sceneReady);
    });

    after(300, () => {
      feed.innerHTML = notif('🚨 Margaret NEEDS HELP', 'now',
        'They tapped the help button in Pruuf. Please check on them now.', true);
    });
  }

  /** Re-attach handlers after a scene rewrites the screen. Kept in one place
   *  so a new scene cannot forget one and leave a dead button in the demo. */
  function wire() {
    const ok = $('#demo-imok', screen);
    if (ok) ok.addEventListener('click', () => {
      caption.textContent = 'Checked in again — they’ll be told each time.';
      sceneCheckedIn();
    });
    const help = $('#demo-help', screen);
    if (help && !help.disabled) help.addEventListener('click', sceneHelp);
    const loved = $('#demo-loved', screen);
    if (loved) loved.addEventListener('click', () => {
      caption.textContent = 'That screen holds her six-character code and who is connected.';
    });
  }

  replay.addEventListener('click', sceneReady);
  missBtn.addEventListener('click', sceneMissed);
  sceneReady();
}

/* ═══════════════════════════════════════════════════════════════
   The dashboard modal
   ═══════════════════════════════════════════════════════════════
   Keeps people on the page. A new tab is the one thing a page trying to hold
   somebody should not do — they leave, explore, and come back to a tab whose
   context they have lost, or do not come back at all.

   The iframe's src is set on FIRST open rather than in the markup, so the
   106KB dashboard is not fetched by the majority of visitors who never ask
   for it.                                                                  */
function initDashboardModal() {
  const modal = $('#dashboard-modal');
  if (!modal) return;

  const frame = $('iframe', modal);
  let lastFocused = null;

  const open = trigger => {
    lastFocused = trigger || document.activeElement;
    if (!frame.src) frame.src = frame.dataset.src;
    modal.hidden = false;
    // The page behind must not scroll under the overlay.
    document.body.style.overflow = 'hidden';
    $('[data-close-modal]', modal).focus();
  };

  const close = () => {
    modal.hidden = true;
    document.body.style.overflow = '';
    // Put focus back where it came from, or a keyboard user is dropped at the
    // top of the document with no idea what just happened.
    if (lastFocused) lastFocused.focus();
  };

  $$('[data-open-dashboard]').forEach(b =>
    b.addEventListener('click', () => open(b)));
  $$('[data-close-modal]', modal).forEach(b => b.addEventListener('click', close));

  // Click the backdrop, but not the panel itself.
  modal.addEventListener('click', e => { if (e.target === modal) close(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !modal.hidden) close();
  });
}

/* ═══════════════════════════════════════════════════════════════
   Role switcher — mirrors the app's own "choose your side" screen
   ═══════════════════════════════════════════════════════════════ */
function initRoleSwitch() {
  const tabs = $$('[data-role-tab]');
  if (!tabs.length) return;

  const show = role => {
    tabs.forEach(t => {
      const on = t.dataset.roleTab === role;
      t.setAttribute('aria-selected', String(on));
      t.classList.toggle('card--link', !on);
    });
    $$('[data-role-panel]').forEach(p => {
      const on = p.dataset.rolePanel === role;
      p.hidden = !on;
      if (on) p.classList.add('fade-swap');
    });
  };

  tabs.forEach(t => t.addEventListener('click', () => show(t.dataset.roleTab)));
  show(tabs[0].dataset.roleTab);
}

/* ═══════════════════════════════════════════════════════════════
   Pricing toggle
   ═══════════════════════════════════════════════════════════════ */
function initPricing() {
  const toggle = $('#term-toggle');
  if (!toggle) return;

  const set = term => {
    $$('button', toggle).forEach(b =>
      b.setAttribute('aria-pressed', String(b.dataset.term === term)));
    $$('[data-price]').forEach(el => { el.textContent = el.dataset[term]; });
    $$('[data-price-note]').forEach(el => { el.textContent = el.dataset[term]; });
    $$('[data-annual-only]').forEach(el => { el.hidden = term !== 'annual'; });
  };

  $$('button', toggle).forEach(b => b.addEventListener('click', () => set(b.dataset.term)));
  set('annual');   // the better deal for them, and the honest default to show
}

/* ═══════════════════════════════════════════════════════════════
   Contact form
   ═══════════════════════════════════════════════════════════════ */
function initForms() {
  $$('form[data-contact-form]').forEach(form => {
    const status = $('[data-form-status]', form);
    const submit = $('[type="submit"]', form);
    const done   = $('[data-form-done]', form.parentElement);
    const opened = Date.now();

    // Preselect an intent from the URL, so "Book a walkthrough" arrives on the
    // contact page already knowing why.
    const intent = new URLSearchParams(location.search).get('intent')
                || (location.hash || '').replace('#', '');
    const select = $('[name="intent"]', form);
    if (select && intent && $$('option', select).some(o => o.value === intent)) {
      select.value = intent;
    }
    if (select) {
      const sync = () => $$('[data-show-for]').forEach(el => {
        el.hidden = !el.dataset.showFor.split(' ').includes(select.value);
      });
      select.addEventListener('change', sync);
      sync();
    }

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(form).entries());

      // Client-side validation, so a mistyped email is caught before a round
      // trip. The function validates again — this is courtesy, not security.
      //
      // Driven by which fields the form actually has, because the same handler
      // serves both the full contact form and the one-field launch signup. A
      // fixed list would have made "name" and "message" required on a form
      // that has neither, and the signup could never have been submitted.
      const has = n => !!$(`[name="${n}"]`, form);
      const bad = [];
      if (has('name') && !String(data.name || '').trim()) bad.push('name');
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(String(data.email || ''))) bad.push('email');
      if (has('message') && String(data.message || '').trim().length < 10) bad.push('message');
      $$('[name]', form).forEach(el =>
        el.setAttribute('aria-invalid', String(bad.includes(el.name))));
      if (bad.length) {
        status.hidden = false;
        status.className = 'form-status form-status--err';
        status.textContent = 'Please check the highlighted fields.';
        $(`[name="${bad[0]}"]`, form).focus();
        return;
      }

      submit.disabled = true;
      const original = submit.textContent;
      submit.textContent = 'Sending…';
      status.hidden = true;

      try {
        const res = await fetch(`${CONFIG.supabaseURL}/functions/v1/contact`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': CONFIG.supabaseKey,
            'Authorization': `Bearer ${CONFIG.supabaseKey}`,
          },
          body: JSON.stringify({
            ...data,
            page: location.pathname,
            elapsed_ms: Date.now() - opened,   // a bot fills a form in ~0ms
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        form.hidden = true;
        done.hidden = false;
        done.focus();
      } catch (err) {
        // Never a dead end. Hand them a pre-written email containing every word
        // they just typed, so the effort is not lost.
        const subject = encodeURIComponent(`Pruuf — ${data.intent || 'enquiry'}`);
        const body = encodeURIComponent(
          `${data.message}\n\n— ${data.name}${data.org ? `, ${data.org}` : ''}\n${data.email}`);
        status.hidden = false;
        status.className = 'form-status form-status--err';
        status.innerHTML =
          `That didn’t send — the connection failed. ` +
          `<a href="mailto:${CONFIG.contactEmail}?subject=${subject}&body=${body}">` +
          `Send it as an email instead</a>, with everything you wrote already in it.`;
        submit.disabled = false;
        submit.textContent = original;
      }
    });
  });
}

/* ═══════════════════════════════════════════════════════════════
   Year stamp, so the footer never goes stale
   ═══════════════════════════════════════════════════════════════ */
function initYear() {
  $$('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });
}

/* ── Inline SVG, defined once ──────────────────────────────────────── */
const ICON = {
  heart: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 21s-7.5-4.7-7.5-10A4.5 4.5 0 0 1 12 8.5 4.5 4.5 0 0 1 19.5 11c0 5.3-7.5 10-7.5 10Z" fill="#fff"/>
      <path d="M8.8 12.4l2.3 2.3 4.3-4.6" stroke="#0B7A45" stroke-width="2.1"
            stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3a5.5 5.5 0 0 0-5.5 5.5c0 4-1.5 5.5-1.5 5.5h14s-1.5-1.5-1.5-5.5A5.5 5.5 0 0 0 12 3Z"
            fill="#fff"/><path d="M10.2 17.5a2 2 0 0 0 3.6 0" stroke="#fff" stroke-width="1.8"
            stroke-linecap="round"/></svg>`,
  bellBig: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3a5.5 5.5 0 0 0-5.5 5.5c0 4-1.5 5.5-1.5 5.5h14s-1.5-1.5-1.5-5.5A5.5 5.5 0 0 0 12 3Z"
            fill="#fff"/><path d="M10.2 17.5a2 2 0 0 0 3.6 0" stroke="#fff" stroke-width="1.8"
            stroke-linecap="round"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12.5 10 17.5 19 7" stroke="#fff" stroke-width="3"
            stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  gear: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" stroke="#16150F" stroke-width="2"/>
      <path d="M19.4 13a7.6 7.6 0 0 0 0-2l2-1.5-2-3.4-2.3 1a7.6 7.6 0 0 0-1.8-1L14.9 3h-3.8l-.4 2.5a7.6 7.6 0 0 0-1.8 1l-2.3-1-2 3.4L6.6 11a7.6 7.6 0 0 0 0 2l-2 1.5 2 3.4 2.3-1c.55.42 1.16.76 1.8 1l.4 2.6h3.8l.4-2.6c.64-.24 1.25-.58 1.8-1l2.3 1 2-3.4-2-1.5Z"
            stroke="#16150F" stroke-width="2" stroke-linejoin="round"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="#3A3833"/>
      <path d="M12 7.5V12l3 1.8" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>`,
  exclaim: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="4" width="18" height="14" rx="4" fill="#fff"/>
      <path d="M12 8v4" stroke="#C1121F" stroke-width="2.4" stroke-linecap="round"/>
      <circle cx="12" cy="14.6" r="1.2" fill="#C1121F"/></svg>`,
};

/* ── Go ────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initReveals();
  initAppCTAs();
  initHeroDemo();
  initDashboardModal();
  initRoleSwitch();
  initPricing();
  initForms();
  initYear();
});
