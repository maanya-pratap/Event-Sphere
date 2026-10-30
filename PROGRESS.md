# Progress plan — mentor reviews every 10–12 days

This maps the build to five review checkpoints. Since a lot of the
scaffold is already working, checkpoints 1–2 are close to "done" already —
use the time you save there to polish UI and write more tests, since
that's what tends to impress a guide most in a working-prototype demo.

## Review 1 (Day 1–10) — Foundations
**Show:** app boots, DB models, register/login for all 3 roles, role-based
redirects, an organiser signup that lands in "pending approval".
**Demo script:** register as a participant → log in → register as an
organiser → show it's blocked from logging in → log in as admin → approve it.
**Status:** ✅ done — `app/models.py`, `app/routes/auth.py`, `admin.py`
(approve/reject organisers).

## Review 2 (Day 11–22) — Events & registration
**Show:** organiser creates an event, participant browses/searches events,
registers, gets a QR pass rendered on screen.
**Demo script:** log in as organiser → create event → log in as participant
→ search for it → register → show the QR ticket page.
**Status:** ✅ done — `organiser.create_event`, `participant.register_for_event`,
`services/qr_service.py`, `templates/participant/qr_ticket.html`.

## Review 3 (Day 23–34) — Attendance & certificates
**Show:** the camera-based scanner marking a real participant present, and
a certificate PDF appearing automatically.
**Demo script:** on your phone or laptop camera, open the organiser scanner
page, scan the QR from Review 2's ticket (or `seed.py`'s demo pass), watch
the "Welcome, {name}!" toast, then log back in as that participant and
download the certificate from `/participant/certificates`.
**Status:** ✅ done — `organiser.check_in`, `services/certificate_services.py`.
**Talking point for your guide:** the check-in endpoint rejects a QR from
the wrong event and rejects a second scan of the same person — mention this
explicitly, it shows you thought about edge cases, not just the happy path.

## Review 4 (Day 35–46) — Feedback, analytics, admin oversight
**Show:** feedback form after attending, organiser + admin analytics
dashboards with real charts (registrations vs. check-ins, turnout %).
**Demo script:** submit feedback as a participant → show the organiser's
analytics page update → show the admin's platform-wide analytics.
**Status:** ✅ done — `participant.feedback`, `organiser/analytics.html`,
`admin/analytics.html`, `services/analytics_service.py`.
**If you have spare time this cycle:** add a rating breakdown chart
(1–5 stars histogram) using `event.feedback` — the model already stores
individual ratings, it just isn't charted yet.

## Review 5 (Day 47–58) — Polish, testing, deployment story
**Show:** the test suite passing (`pytest`), the responsive mobile layout,
error pages, and a one-page deployment plan (even if you don't actually
deploy — guides usually just want to see you know what production would
involve: env vars, a real Postgres DB, HTTPS for camera access since
browsers block camera on non-HTTPS origins except localhost).
**Status:** ✅ tests written (`tests/`), responsive CSS in place.
**Still worth doing before this review:** run `pytest` yourself once you
have the packages installed locally and fix anything that fails in your
environment (dates/timezones are the most likely source of a flaky test).

---

### General tips for every review
- Always demo with `python seed.py` first — an empty database with no
  events looks unfinished even when the code isn't.
- Keep a 1-slide "what changed since last time" summary; guides remember
  progress, not just the end state.
- If something is half-built, say so plainly rather than demoing around
  it — "attendance works, certificates are next" reads better than a
  demo that visibly avoids a button.
