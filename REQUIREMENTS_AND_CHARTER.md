# EventSphere — Requirements & Project Charter

**BCA V · CN312 Project (MO 2026) · Guide: Dr. Amrita Priyam**
**Team:** Maanya Pratap (Lead) · Nistha · Astha Kumari · Shreya S. Xaxa

This is the document a team writes *before* coding starts, formalising what
you're building and why. Presenting this at your first mentor review (or
even retroactively, framed as "here's what we scoped in week one") is
standard practice and shows process maturity, not just a finished app.

---

## 1. Problem statement

College event organisers currently manage registration on paper or
spreadsheets, take attendance manually (error-prone, slow, easy to proxy),
collect feedback informally if at all, and issue certificates manually
per attendee. There is no single system that ties registration →
attendance → feedback → certification together, and no easy way for a
society to see how their events actually performed.

## 2. Project scope

### In scope
- Three-role web application: Admin, Organiser (society account), Participant
- Event creation, discovery, and search
- Online registration with QR-code ticketing
- Camera-based QR scanning for attendance at the venue
- Automatic PDF certificate generation for verified attendees
- Post-event feedback collection (rating + comment)
- Analytics dashboards for organisers (per event) and admin (platform-wide)
- Organiser account approval workflow (admin gatekeeping)

### Out of scope (explicitly, for this version)
- Payment processing / paid events
- Email or SMS notifications (in-app flash messages only)
- Multi-language support
- Native mobile app (mobile web only, responsive)
- Waitlists for full events
- Real-time chat/Q&A during events

Stating what's *out* of scope is as important as what's in — it stops
"scope creep" questions from a mentor turning into last-minute feature
demands, and shows you made deliberate calls rather than running out of time.

## 3. Functional requirements

Grouped by module, written as testable statements (this is the format
your `tests/` folder should map back to).

### 3.1 Authentication & roles
- FR1: A user can register as a Participant or an Organiser (society), providing name, email, mobile, and password.
- FR2: Organiser accounts require Admin approval before they can log in.
- FR3: A user can log in and log out; sessions persist via Flask-Login.
- FR4: Each role is restricted to its own set of routes — a Participant hitting an Organiser/Admin route receives a 403, not data.
- FR5: Passwords are stored hashed, never in plaintext.

### 3.2 Event management
- FR6: An approved Organiser can create an event with title, description, category, venue, date/time, and capacity.
- FR7: An Organiser can edit or cancel only their own events.
- FR8: A Participant can browse and search/filter published events.
- FR9: An Admin can view all events across all organisers, read-only.

### 3.3 Registration & QR ticketing
- FR10: A Participant can register for a published event if it is not full and they haven't already registered.
- FR11: On registration, a unique QR token is generated and bound to that specific registration (not just the user).
- FR12: A Participant can view their QR ticket for any event they've registered for.
- FR13: A Participant can view a list of their upcoming and past registrations ("My events").

### 3.4 Attendance
- FR14: An Organiser can scan a participant's QR code using an in-browser camera scanner at their event.
- FR15: The system verifies the token belongs to that specific event before marking attendance.
- FR16: A token can only be used once — a second scan is rejected with a clear message.
- FR17: An Organiser can view a live list of who has checked in to their event.

### 3.5 Certificates
- FR18: A certificate PDF is generated automatically the moment a registration is marked present.
- FR19: A Participant can download their certificate at any time after issuance.
- FR20: Certificates are not generated for registrations without attendance.

### 3.6 Feedback
- FR21: A Participant can submit a 1–5 rating and optional comment for an event they attended.
- FR22: Feedback is restricted to participants who actually attended (checked-in registrations only).

### 3.7 Analytics
- FR23: An Organiser can view registrations vs. check-ins and turnout % per event.
- FR24: An Admin can view the same metrics aggregated across the whole platform.

## 4. Non-functional requirements

| Category | Requirement |
|---|---|
| **Usability** | A first-time participant should be able to find and register for an event within 3 clicks of landing on the homepage |
| **Performance** | Pages should load in under 2 seconds on campus Wi-Fi with the demo dataset (~50 events, ~500 registrations) |
| **Security** | Passwords hashed (never plaintext); QR tokens are opaque random UUIDs, not guessable IDs; role checks enforced server-side, never trusted from the client |
| **Reliability** | Duplicate registration, double check-in, and over-capacity registration must be impossible, not just discouraged |
| **Compatibility** | Must work on Chrome and Firefox (desktop) and Chrome (Android) at minimum; camera scanning requires HTTPS or localhost |
| **Maintainability** | Code split by role (routes) and by concern (services) so any one member can work on their module without merge conflicts with another's |
| **Testability** | Every functional requirement above has at least one corresponding automated test in `tests/` |

## 5. Assumptions & constraints

- Assumes each participant has one account and one device to show their QR ticket (no shared-device edge case handling)
- Assumes organiser accounts represent one society each (not multiple societies sharing one login)
- Assumes campus Wi-Fi/internet is available during the event for real-time check-in (no offline scanning mode)
- Constraint: built with SQLite for the academic submission; a real deployment (e.g. for the Aurora event) would need PostgreSQL — documented in `PROGRESS.md`, not implemented in this version
- Constraint: single-server deployment assumed; no load balancing in this version

## 6. Technology choices & why

| Choice | Reason |
|---|---|
| Flask (not Django) | Lightweight, easier for 4 people to reason about the whole codebase; Django's batteries would be overkill for this scope |
| SQLAlchemy ORM | DB-agnostic — makes a future SQLite → Postgres migration (for Aurora) a config change, not a rewrite |
| Flask-Login | Standard, well-documented session handling; no need to hand-roll auth |
| `qrcode` + `html5-qrcode` | `qrcode` (server-side generation) and `html5-qrcode` (client-side camera scanning) are the two most-used libraries for this exact pairing, both free and well-maintained |
| ReportLab | Programmatic PDF generation without needing a headless browser or external service |
| Chart.js | Simple, CDN-loadable, no build step — fits a project with no frontend bundler |
| No frontend framework (React/Vue) | Server-rendered Jinja templates are enough for this scope and easier for all 4 members to edit without a build pipeline |

## 7. Deliverables checklist

- [x] Working web application (all 3 roles)
- [x] ER diagram
- [x] System flowcharts
- [x] Roles/permissions map
- [x] Functional & non-functional requirements (this document)
- [x] Automated test suite
- [x] README with setup instructions
- [x] Phase-wise development log (`DEV_LOG_PHASES.md`)
- [ ] Final report / synopsis writeup (submit per department format)
- [ ] Viva/demo rehearsal

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Camera scanning fails on mentor's device during demo | Medium | High | Always test the exact demo device beforehand; carry a backup phone; know the HTTPS/localhost requirement cold so you can explain a failure instead of being caught off guard |
| SQLite locks under concurrent writes if demoed with many simultaneous registrations | Low (fine for demo scale) | Medium | Documented as a known limitation with a stated Postgres migration path, not hidden |
| One member's module blocks another's (e.g. QR service not ready when attendance UI needs it) | Medium | Medium | Services layer (`app/services/`) defines function signatures early, even as stubs, so dependent modules can be built against the interface before the implementation lands |
| Scope creep after mentor sees it and suggests "add X" | High | Medium | Keep the out-of-scope list visible; log new suggestions as "Phase 6 / future work" rather than derailing the current phase |

## 9. Definition of done (per feature)

A feature is "done", not just "working on my machine", when:
1. It has at least one automated test in `tests/`
2. It handles the obvious failure case (full event, wrong role, invalid input) — not just the happy path
3. It's been tested by a team member other than whoever built it
4. The relevant row in `DEV_LOG_PHASES.md` is filled in honestly

## 10. Team communication norms

- Daily 10-minute standup (async on WhatsApp is fine): what I did, what I'm doing next, any blockers
- All merges to `main` reviewed by at least one other member
- Anyone blocked for more than a day flags it immediately rather than sitting on it — this is what your mentor actually wants to hear about at reviews, not just green checkmarks
