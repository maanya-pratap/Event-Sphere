# What changed in this version (read these files, then rebuild each change yourselves)

## 1. Admin can permanently delete participants and organisers
- `app/models.py` — `cascade="all, delete-orphan"` on `User.events`, `User.registrations`, new `User.feedback_given`
- `app/services/cleanup_service.py` (NEW) — collects QR/certificate/gallery file paths and deletes them from disk
- `app/routes/admin.py` — new `delete_user` route; `reject_organiser` now reuses it; admins can't be deleted
- `app/templates/admin/users.html`, `app/templates/admin/organisers.html` — Delete buttons with confirm()

## 2. Profile editing (participant + organiser)
- `app/services/profile_service.py` (NEW) — validation + save; password change needs the correct current password
- `app/routes/participant.py`, `app/routes/organiser.py` — `/profile` now accepts POST
- `app/templates/participant/profile.html` (rewritten), `app/templates/organiser/profile.html` (NEW), `app/templates/organiser/_sidebar.html` (link)

## 3. Shared-QR gap
- `app/routes/organiser.py` — check-in returns `name`; only the event's own organiser may scan (403 otherwise)
- `app/static/js/scanner.js` — registrant name shown large; organiser compares it to the person at the door

## 4. Gallery upload (camera + library)
- `app/routes/organiser.py` — `gallery` (upload, extension whitelist, `secure_filename`, uuid prefix), `delete_photo`
- `app/templates/organiser/gallery.html` — event picker, upload form, photo grid
- `config.py` — upload limit raised 5 MB -> 25 MB

## 5. Sentiment analysis
- `ml/generate_synthetic_data.py` (NEW), `data/synthetic_feedback.csv`, `data/holdout/hard_cases.csv` — SYNTHETIC data (labelled as such)
- `train_sentiment.py` (NEW) — trains TF-IDF + Logistic Regression and Naive Bayes, reports accuracy/precision/recall/F1/confusion matrix, compares with VADER, saves `app/ml_models/sentiment_model.joblib` and `reports/sentiment_report.md`
- `app/services/ml_service.py` (NEW) — trained model -> VADER -> star rating fallback; keyword extraction
- `app/models.py` — `Feedback.sentiment_label`, `Feedback.sentiment_score`
- `app/routes/participant.py` — labels feedback on submit; `app/routes/organiser.py` + `app/templates/organiser/analytics.html` — sentiment doughnut + praised/complaint keywords
- `requirements.txt` — scikit-learn, pandas, joblib, vaderSentiment, gunicorn, psycopg2-binary, pytest

## Tests added
`tests/test_admin_delete.py`, `tests/test_profile.py`, `tests/test_gallery_and_scan.py`, `tests/test_sentiment.py`

## After unzipping
1. `pip install -r requirements.txt`
2. The Feedback table gained two columns: delete `instance/eventsphere.db` and run `python seed.py` (or use `flask db migrate` / `flask db upgrade`).
3. `pytest`
4. `python train_sentiment.py` (re-run after you add real labelled comments to `data/`; VADER numbers appear once vaderSentiment is installed)

## v3 patch
- config.py: converts Render's `postgres://` DATABASE_URL to `postgresql://` so the app connects to Render Postgres.
- Email verification at sign-up and a working forgot-password flow (signed, expiring links):
  new `app/services/email_service.py`, `User.email_verified`, routes `/auth/verify/<token>`,
  `/auth/resend-verification`, `/auth/forgot-password`, `/auth/reset-password/<token>`,
  template `auth/reset_password.html`, ProxyFix so links are https on Render, tests in `tests/test_email_flow.py`.
  Existing databases need the new column: delete `instance/eventsphere.db` and run `python seed.py`.
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` environment variables create the first admin on a fresh online database (no shell needed).
