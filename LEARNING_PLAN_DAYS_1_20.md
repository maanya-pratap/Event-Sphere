# EventSphere — Days 1–20 rebuild plan (learn-then-implement)

**Team:** Maanya (lead) · Nistha · Astha · Shreya

## The method, every single day

1. **Read** the reference file for today's task (from the zip) — don't copy it yet.
2. **Close it.** Try to write the feature yourself, from what you understood + docs.
3. **Compare** your version to the reference. Where you differ, ask *why* — sometimes yours is fine, sometimes the reference handles an edge case you missed.
4. **Test it** — manually click through it, and where a test exists in `tests/`, run it.
5. **Commit** with a real message describing what you built, not "day 3 commit."

If a day's task takes 3 hours instead of the planned time, that's fine —
adjust the next day rather than rushing. A slower, real pace beats a fast,
fake one.

## Setup (Day 0, before Day 1 — do this together, one sitting)

- Everyone installs Python 3.11+, VS Code, Git
- Create the GitHub repo, everyone clones it
- `python -m venv venv`, activate, `pip install -r requirements.txt` — if
  anything fails to install, debug it now as a group, don't let one
  person silently fix it
- Agree on branch naming (`feature/auth`, `feature/events`, etc.) and that
  every merge to `main` needs one other person's review

---

## Days 1–5 — Flask fundamentals + project skeleton
**Owner: whole team together** (everyone needs this foundation before splitting off)

| Day | Task |
|---|---|
| 1 | Learn Flask basics: routes, `render_template`, the app factory pattern. Build a throwaway 2-page Flask app from scratch (not EventSphere) — a route that says hello, a route with a form. This is where "what even is a route" gets settled before touching the real project. |
| 2 | Read `app/__init__.py` and `config.py` from the reference. Understand *why* it's a factory function (`create_app()`) instead of a global `app = Flask(__name__)` — hint: testing needs a fresh app instance each time. Then, from scratch, build your own `create_app()` skeleton with just a landing route. |
| 3 | Learn SQLAlchemy models: columns, relationships (`db.relationship`, `ForeignKey`). Read `app/models.py`'s `User` model only. Then write the `User` model yourself from memory + docs, migrate, and manually insert a row via Python shell (`flask shell`) to see it land in `eventsphere.db`. |
| 4 | Add the rest of the models one at a time (`Event`, `Registration`, `Attendance`, `Feedback`, `Certificate`) — write each yourself, then diff against the reference. Pay attention to the foreign keys; draw the ER diagram from earlier next to your screen while doing this. |
| 5 | Set up `flask db init` / migrations with Flask-Migrate. Get everyone's local `eventsphere.db` created from the same models. Commit: "Database schema — all 6 tables". |

**Checkpoint:** everyone can run `flask shell`, import `User`, and query
an empty table. If someone can't, don't move on — pair up and fix it.

---

## Days 6–10 — Authentication & roles
**Owner: Maanya leads, whole team implements alongside**

| Day | Task |
|---|---|
| 6 | Learn password hashing (`werkzeug.security`) and why plaintext passwords are unacceptable. Read `auth.py`'s register route. Write your own register route from scratch — form handling, hashing, saving to DB. Test it by registering a user and checking the DB has a hash, not plaintext. |
| 7 | Learn Flask-Login: `UserMixin`, `login_user`, `current_user`, `@login_required`. Implement login/logout yourself, then compare to reference `auth.py`. |
| 8 | Implement the organiser-approval gate: an organiser who registers gets `is_approved=False` and is blocked from logging in until an admin flips it. Write this yourself — it's a good exercise in a conditional check inside the login route. |
| 9 | Build the `@role_required` decorator from scratch (this is the trickiest part — a decorator that wraps a view function and checks `current_user.role`). If you get stuck, look at Flask-Login's `login_required` source for the pattern, then adapt it. |
| 10 | Wire up the 403 error page, base template, navbar with role-aware links. Whole-team review: everyone tries registering as all 3 roles and confirms the approval gate + role redirects work. Commit + this is your **Phase 1 mentor demo**, done for real. |

**Checkpoint / mentor-ready:** register as participant, register as
organiser (blocked), approve as admin, log in as organiser. If this
doesn't work end-to-end, don't move to Days 11+ yet.

---

## Days 11–15 — Event creation & browsing
**Split starts here — each person owns a piece, but everyone still writes their own code first**

| Day | Nistha (events) | Shreya (browse/search UI) | Astha (prep for QR) | Maanya (integration) |
|---|---|---|---|---|
| 11 | Learn WTForms or plain `request.form` validation. Write the "create event" form + route from scratch, compare to reference `organiser.py`. | Study the existing `main.css`/`dashboard.css` theme — pick 3 rules you don't understand and figure out why they're there before reusing them. | Read up on the `qrcode` Python library — generate a throwaway QR from a string in a standalone script, decode it back. | Review Nistha's and Shreya's branches once they open a PR; give real feedback. |
| 12 | Add edit/cancel event, with the "only the owner organiser can edit" check — write this check yourself, it's the same `current_user.id == event.organiser_id` pattern used elsewhere; understand it, don't just paste it. | Build the event listing page with search/filter from scratch, then compare layout to reference `participant/events.html`. | Read `services/qr_service.py` fully — understand why it stores a random token per *registration*, not per user (security reasoning from the requirements doc). | Merge Nistha + Shreya's work, resolve any conflicts together as a team so everyone sees how merging works. |
| 13 | Add capacity field + "event full" check. | Style the event cards (banner gradient, category tag) matching the Gen-Z aesthetic. | Start the registration route: link a `User` to an `Event` via `Registration`, no QR yet. | Test the full organiser → create → participant → browse loop manually. |
| 14 | Admin's read-only "all events" view. | Empty states (no events yet) + responsive check on a phone. | Wire QR generation into the registration route (Day 12's reading pays off here). | Write your first pytest test together, based on `tests/test_events.py`, understanding each assertion before running it. |
| 15 | Team review day: everyone walks through everyone else's code out loud, one file at a time. This is the single most useful exercise for actually being able to answer mentor questions on any part of the app. | | | |

**Checkpoint:** organiser creates an event, participant finds and
registers, gets a QR rendered on screen. This is your **Phase 2 mentor
demo**.

---

## Days 16–20 — QR check-in (start of Phase 3, get ahead)

| Day | Task | Owner |
|---|---|---|
| 16 | Learn `html5-qrcode` (JS library) basics — get a bare camera preview working in a standalone HTML file before touching `scanner.js`. | Astha, with Shreya on the HTML/CSS side |
| 17 | Build the check-in API endpoint yourself: receive a token, look up the `Registration`, validate it belongs to *this* event, check it's not already used. Compare against reference `organiser.py`'s check-in route line by line — this is the most important validation logic in the whole app. | Astha + Maanya |
| 18 | Wire the scanner JS to call the check-in endpoint and show a live "Welcome, {name}" toast. | Astha + Shreya |
| 19 | Test on an actual phone camera over the same Wi-Fi as the laptop. Hit the HTTPS wall on purpose — you should discover this yourselves rather than being told, then read up on why (browser camera permissions require a secure origin), and set up ngrok as the fix. | Whole team |
| 20 | Write the attendance tests (`test_attendance.py`) together, understanding each rejected-case test (wrong event, duplicate scan) before running it. Do a full dry run of the mentor demo: register → QR → scan → live check-in list. | Whole team |

**Checkpoint / mentor-ready:** live camera scan working on a phone,
demoed over ngrok. This the natural point to circle back to
`DEV_LOG_PHASES.md` and `PROGRESS.md` for what comes next (certificates,
feedback, analytics — Days 21–40).

---

## A few honest notes

- Some days will run long, some short — that's real development, keep the
  order but flex the pace.
- When you genuinely get stuck (not "don't feel like reading docs" stuck,
  actually stuck), that's a legitimate moment to ask me — but ask about
  the *concept* first ("how does Flask-Login know who's logged in
  between requests?") rather than "give me the code," so the
  understanding actually lands.
- Keep committing in small pieces as you go, not one giant commit at the
  end of each phase — a real git history has this shape naturally when
  the work is real.
