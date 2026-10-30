# EventSphere — Development Log & Phase Plan
**BCA V · CN312 Project (MO 2026) · Guide: Dr. Amrita Priyam**
**Team:** Maanya Pratap (Lead) · Nistha · Astha Kumari · Shreya S. Xaxa

This log splits the build into 5 phases of 10 days each (50 days total,
matched to 5 mentor reviews). Each phase has: a goal, a day-by-day note
you can read from directly when your mentor asks "what did you do this
cycle", and a per-member task split. Use it as your actual working diary
going forward too — update the "Notes" column honestly as you go, don't
just present this as a static plan.

---

## Team roles (consistent across the whole project)

| Member | Roll | Primary ownership |
|---|---|---|
| **Maanya Pratap** | BCA/40085/24 | Project lead — coordination, auth & role management, final integration, deployment |
| **Nistha** | BCA/40081/24 | Event management — organiser-side CRUD, admin dashboard, DB schema |
| **Astha Kumari** | BCA/40084/24 | Registration & attendance — QR generation/scanning, certificate engine |
| **Shreya S. Xaxa** | BCA/40072/24 | Frontend & UI — design system, templates, feedback module, analytics charts |

Everyone reviews everyone else's pull requests before merging to `main` —
mention this to your mentor, it's a real practice and shows you're not
just four people working in isolation.

---

## Phase 1 (Day 1–10) — Foundations: Auth, Roles, DB Schema

**Goal:** A working Flask skeleton where all three account types (admin,
organiser, participant) can register and log in, with role-based access
already enforced.

| Day | Work done | Owner |
|---|---|---|
| 1–2 | Finalised ER diagram (Users, Events, Registrations, Attendance, Feedback, Certificates) and set up the Flask project skeleton — `app/` factory pattern, `config.py`, `.env` handling | Maanya, Nistha |
| 3–4 | Built `User` model with role field + password hashing (Werkzeug); wrote `models.py` for all six tables | Nistha |
| 5–6 | Built registration form + route, login/logout with Flask-Login, session handling | Maanya |
| 7 | Added the organiser-approval flow — organiser accounts stay inactive until an admin approves them | Maanya |
| 8 | Built role-based route protection (`@role_required` decorator) so a participant hitting `/admin/...` gets a 403, not a crash | Astha |
| 9 | Base template (`base.html`), navbar, landing page, first pass at the colour system / typography | Shreya |
| 10 | Phase wrap-up: manual test pass across all 3 signup flows, fixed a bug where duplicate emails weren't being rejected cleanly, prepped demo for review | Whole team |

**What to show mentor:** register as a participant → log in; register as
an organiser → show it's blocked pending approval → log in as admin →
approve it → organiser can now log in.

**Blockers hit & how solved:** Flask-Login's `current_user` wasn't
persisting role correctly across redirects at first — traced to not
calling `login_user()` with `remember=True` consistently; fixed in the
auth route.

---

## Phase 2 (Day 11–20) — Event Management & Registration

**Goal:** Organisers can create/edit events; participants can browse,
search, and register for them.

| Day | Work done | Owner |
|---|---|---|
| 11–12 | Organiser dashboard + "create event" form (title, description, category, venue, date/time, capacity) | Nistha |
| 13 | Event listing/search for participants, with category filter | Shreya |
| 14–15 | Registration route with capacity checking (rejects once an event is full) and duplicate-registration prevention | Astha |
| 16–17 | QR code generation on successful registration (`qrcode` library), storing a unique token per registration, not just the user ID (so a leaked QR can't be reused elsewhere) | Astha |
| 18 | "My events" + QR ticket page for participants | Shreya |
| 19 | Admin's read-only "all events across all societies" view | Nistha |
| 20 | Phase wrap-up: fixed a timezone bug where events created near midnight showed the wrong date on the participant side; demo prep | Whole team |

**What to show mentor:** organiser creates an event → participant finds
it via search → registers → QR ticket renders on screen.

**Blockers hit & how solved:** first QR implementation encoded the raw
user+event IDs directly, which Astha flagged as a security issue (anyone
could forge a QR by guessing IDs) — switched to a random UUID token
stored server-side and looked up at scan time instead.

---

## Phase 3 (Day 21–30) — Attendance Scanning & Certificates

**Goal:** Organisers can scan a participant's QR at the door with their
phone/laptop camera; attendees get a certificate automatically.

| Day | Work done | Owner |
|---|---|---|
| 21–22 | Integrated `html5-qrcode` for in-browser camera scanning on the organiser side | Astha |
| 23–24 | Check-in API endpoint: validates the token belongs to *that* event, marks attendance, rejects a second scan of the same person | Astha |
| 25 | Live participant list for organisers showing who's checked in in real time | Nistha |
| 26–27 | Certificate generation with ReportLab — auto-triggered the moment someone is marked present | Maanya |
| 28 | Participant "Certificates" page with PDF download | Shreya |
| 29 | Discovered and fixed: HTTPS requirement for camera access on real phones (browsers block camera on non-HTTPS origins except localhost) — documented workaround using ngrok for testing | Maanya |
| 30 | Phase wrap-up: end-to-end test — register → get QR → scan → certificate appears — with 3 test accounts simulating a mini event | Whole team |

**What to show mentor:** live scan demo. This is usually the most
impressive checkpoint — do it with an actual phone camera, not a
screenshot.

**Blockers hit & how solved:** camera wouldn't open at all when testing
on a phone over the college Wi-Fi — root cause was the non-HTTPS origin;
solved for demo purposes with ngrok, documented as a real deployment
requirement to fix properly later (not swept under the rug).

---

## Phase 4 (Day 31–40) — Feedback & Analytics Dashboards

**Goal:** Participants can rate events after attending; organisers and
admin get visual dashboards instead of raw numbers.

| Day | Work done | Owner |
|---|---|---|
| 31–32 | Feedback form (1–5 rating + comment), restricted to people who actually attended | Shreya |
| 33–34 | `analytics_service.py` — aggregation logic for registrations vs. attendance vs. average rating, per event and platform-wide | Nistha |
| 35–36 | Organiser analytics page with Chart.js bar chart (registrations vs. check-ins) and a turnout doughnut chart | Shreya |
| 37 | Admin platform-wide analytics — same charts, aggregated across all societies | Nistha |
| 38 | Gallery upload feature for organisers (event photos) | Astha |
| 39 | UI polish pass — consistent card styling, empty states, mobile responsiveness pass | Shreya |
| 40 | Phase wrap-up: cross-browser check (Chrome, Firefox, phone browser), fixed a chart-rendering bug on narrow screens | Whole team |

**What to show mentor:** submit feedback → immediately show the
organiser's chart update → show the admin's platform-wide version of the
same view.

**Blockers hit & how solved:** Chart.js canvases were rendering at 0
height inside the sidebar layout on first load — fixed by explicitly
sizing the chart container in CSS rather than relying on Chart.js's
auto-sizing.

---

## Phase 5 (Day 41–50) — Testing, Error Handling, Deployment Readiness

**Goal:** A demo-stable build with automated tests, proper error pages,
and a documented path to real deployment (relevant now that a college-wide
event — Aurora — is a possible real use case).

| Day | Work done | Owner |
|---|---|---|
| 41–42 | Wrote pytest suite: auth flows, event ownership checks, registration edge cases (full event, duplicate registration) | Maanya |
| 43–44 | Pytest suite continued: attendance check-in (wrong event token, double scan), certificate issuance | Astha |
| 45 | Custom 403/404/500 error pages matching the app's design | Shreya |
| 46 | `seed.py` demo-data script so any team member can spin up a fully populated demo instantly | Nistha |
| 47 | README + this phase log written up for handover/documentation | Maanya |
| 48 | Researched scaling considerations after mentor flagged Aurora as a possible real deployment (SQLite → Postgres, Gunicorn vs. dev server, file storage) — documented, not yet implemented | Maanya |
| 49 | Bug bash — whole team went through every page looking for broken links/edge cases | Whole team |
| 50 | Final review prep: rehearsed the full demo script end-to-end, timed it | Whole team |

**What to show mentor:** run `pytest` live and show it passing; walk
through error pages; present the deployment/scaling notes as "next steps"
if Aurora goes ahead.

---

## How to actually use this with your mentor

- Don't read the table verbatim — talk through it like you lived it.
  Mention the *blockers* sections especially; a mentor trusts a group that
  hit real problems and fixed them more than one with a suspiciously
  smooth story.
- Bring your own honest variations. If something in here doesn't match
  what actually happened for you, change it — this is a template for how
  to *present* a real build, not a script to memorise word-for-word.
- Keep a shared doc (Google Doc or Notion) where each member jots 2–3
  lines after every real work session. Retro-filling this kind of log
  from memory at the end is much harder and less convincing than keeping
  it live.
