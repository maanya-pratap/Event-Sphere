# EventSphere: fact sheet taken from the code (v4)

Use this to check every claim in your report against what the app really does.

## Tables and columns

### users

- `id`: db.Integer
- `name`: db.String(120)
- `email`: db.String(150)
- `mobile`: db.String(20)
- `password_hash`: db.String(255)
- `role`: db.String(20)
- `society_name`: db.String(150)
- `is_approved`: db.Boolean
- `email_verified`: db.Boolean
- `avatar`: db.String(255)
- `created_at`: db.DateTime

### events

- `id`: db.Integer
- `title`: db.String(150)
- `description`: db.Text
- `category`: db.String(60)
- `venue`: db.String(150)
- `start_time`: db.DateTime
- `end_time`: db.DateTime
- `banner_image`: db.String(255)
- `capacity`: db.Integer
- `organiser_id`: db.Integer
- `status`: db.String(20)
- `created_at`: db.DateTime

### registrations

- `id`: db.Integer
- `user_id`: db.Integer
- `event_id`: db.Integer
- `qr_token`: db.String(64)
- `qr_code_path`: db.String(255)
- `registered_at`: db.DateTime

### attendance

- `id`: db.Integer
- `registration_id`: db.Integer
- `present`: db.Boolean
- `checked_in_at`: db.DateTime
- `checked_in_by`: db.Integer

### feedback

- `id`: db.Integer
- `event_id`: db.Integer
- `user_id`: db.Integer
- `rating`: db.Integer
- `comments`: db.Text
- `sentiment_label`: db.String(10)
- `sentiment_score`: db.Float
- `submitted_at`: db.DateTime

### certificates

- `id`: db.Integer
- `registration_id`: db.Integer
- `certificate_code`: db.String(64)
- `file_path`: db.String(255)
- `issued_at`: db.DateTime

## Routes (URL prefix, path, methods, function)

- `/admin/dashboard` [GET] `dashboard` (admin.py)
- `/admin/organisers` [GET] `organisers` (admin.py)
- `/admin/organisers/<int:user_id>/approve` [POST] `approve_organiser` (admin.py)
- `/admin/organisers/<int:user_id>/reject` [POST] `reject_organiser` (admin.py)
- `/admin/users/<int:user_id>/delete` [POST] `delete_user` (admin.py)
- `/admin/events` [GET] `events` (admin.py)
- `/admin/users` [GET] `users` (admin.py)
- `/admin/analytics` [GET] `analytics` (admin.py)
- `/auth/register` [GET, POST] `register` (auth.py)
- `/auth/login` [GET, POST] `login` (auth.py)
- `/auth/verify/<token>` [GET] `verify_email` (auth.py)
- `/auth/resend-verification` [POST] `resend_verification` (auth.py)
- `/auth/forgot-password` [GET, POST] `forgot_password` (auth.py)
- `/auth/reset-password/<token>` [GET, POST] `reset_password` (auth.py)
- `/auth/logout` [GET] `logout` (auth.py)
- `/` [GET] `landing` (main.py)
- `/organiser/dashboard` [GET] `dashboard` (organiser.py)
- `/organiser/events/new` [GET, POST] `create_event` (organiser.py)
- `/organiser/events/<int:event_id>/edit` [GET, POST] `edit_event` (organiser.py)
- `/organiser/events/<int:event_id>/participants` [GET] `participants` (organiser.py)
- `/organiser/events/<int:event_id>/scanner` [GET] `scanner` (organiser.py)
- `/organiser/events/<int:event_id>/check-in` [POST] `check_in` (organiser.py)
- `/organiser/events/<int:event_id>/attendance` [GET] `attendance` (organiser.py)
- `/organiser/gallery` [GET, POST] `gallery` (organiser.py)
- `/organiser/events/<int:event_id>/gallery/<filename>/delete` [POST] `delete_photo` (organiser.py)
- `/organiser/profile` [GET, POST] `profile` (organiser.py)
- `/organiser/analytics` [GET] `analytics` (organiser.py)
- `/participant/dashboard` [GET] `dashboard` (participant.py)
- `/participant/events` [GET] `events` (participant.py)
- `/participant/events/<int:event_id>` [GET] `event_details` (participant.py)
- `/participant/events/<int:event_id>/register` [POST] `register_for_event` (participant.py)
- `/participant/tickets/<int:reg_id>` [GET] `qr_ticket` (participant.py)
- `/participant/my-events` [GET] `my_events` (participant.py)
- `/participant/certificates` [GET] `certificates` (participant.py)
- `/participant/events/<int:event_id>/feedback` [GET, POST] `feedback` (participant.py)
- `/participant/profile` [GET, POST] `profile` (participant.py)

## Services

- `analytics_service.py`: 
- `certificate_services.py`: 
- `cleanup_service.py`: Removing a user's files from disk.
- `email_service.py`: Email sending and signed links for verification and password reset.
- `ml_service.py`: Sentiment analysis for event feedback comments.
- `profile_service.py`: Shared profile-update logic for participants and organisers.
- `qr_service.py`: 

## Tests

### test_admin_delete.py
- test_admin_deletes_participant_and_all_their_data
- test_admin_deletes_organiser_with_events_and_checkins
- test_admin_cannot_delete_admin
- test_participant_cannot_delete_users
### test_attendance.py
- test_organiser_can_check_in_valid_token
- test_checkin_rejects_unknown_token
- test_checkin_rejects_second_scan
- test_checkin_rejects_token_from_other_event
### test_auth.py
- test_register_participant
- test_register_organiser_requires_approval
- test_register_password_mismatch
- test_login_success_and_logout
- test_login_wrong_password
- test_duplicate_email_registration_rejected
### test_certifications.py
- test_certificate_pdf_is_written_to_disk
- test_certificate_code_is_unique_per_registration
- test_no_certificate_without_attendance
- test_participant_sees_certificate_after_checkin
### test_email_flow.py
- test_register_sends_link_and_blocks_login_until_verified
- test_bad_verification_link_is_rejected
- test_organiser_needs_verification_and_approval
- test_resend_verification
- test_forgot_password_full_flow
- test_reset_link_works_only_once
- test_forgot_password_unknown_email_gives_same_message
- test_reset_rejects_mismatched_passwords
### test_events.py
- test_organiser_can_create_event
- test_participant_cannot_create_event
- test_anonymous_redirected_from_event_creation
- test_organiser_cannot_edit_others_event
- test_published_event_visible_to_participants
### test_gallery_and_scan.py
- test_organiser_uploads_photo_and_bad_type_is_skipped
- test_checkin_returns_registrant_name
- test_other_organiser_cannot_scan_for_this_event
### test_profile.py
- test_participant_can_edit_name_mobile_email
- test_email_must_be_unique
- test_password_change_requires_correct_current_password
- test_organiser_can_edit_society_but_not_email
- test_participant_cannot_open_organiser_profile
### test_registration.py
- test_participant_can_register_for_event
- test_cannot_register_twice
- test_registration_blocked_when_event_full
- test_qr_ticket_only_visible_to_owner
### test_sentiment.py
- test_empty_comment_falls_back_to_rating
- test_clear_comments_are_classified
- test_top_keywords_ignores_stopwords
- test_feedback_stores_sentiment_label

## Known gaps to state honestly
- Test results: run `pytest` and record real output.
- Uploaded photos, QR images and certificates are stored on the server disk (lost on a free Render redeploy).
- Reset/verification emails need a configured provider; without one they print in the terminal.
- No rate limiting on email requests; no CSRF tokens on forms.
- The sentiment model is trained on synthetic data and scored 0.25 accuracy on 12 hard sentences.
