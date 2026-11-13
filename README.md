# SwimMatch

SwimMatch is a two-sided college swimming recruiting platform. **Coaches** post what their
program is recruiting for (events, target times, course and graduation year), and **swimmers
and visitors** browse those posts.

The original swimmer-side matching scaffold is still here: program search, school detail and
the swimmer profile. It models each athlete as a **set of event times** (50 Free, 100 Free,
200 Free, 500 Free, 100 Back, 100 Breast, 100 Fly, 200 IM) and compares them against each
program's **per-event recruiting standards**.

> **Status:** Accounts and coach recruiting posts are working. The matching scaffold still uses
> placeholder logic: match scoring is hardcoded (`# TODO: implement multi-event match scoring`
> in `backend/routes/schools.py`), and the swimmer profile form doesn't save yet.

## Running locally

Requires Python 3.10+.

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:5000>.

On first start the app creates `swim.db` (SQLite) in the project root. New tables are created
automatically by `db.create_all()`; there are no migrations. On an empty database it seeds
8 sample programs, 1 sample swimmer profile, a demo coach account and 3 sample recruiting
posts. Delete `swim.db` and restart to reset the data.

Optional config lives in `.env`. Copy `.env.example` to see the available settings. No API
keys or external services are needed.

### Demo coach login (local development only)

| Email                  | Password         | Role  |
|------------------------|------------------|-------|
| `coach@swimmatch.test` | `SwimCoach2026!` | coach |

The demo account and its posts are created only when `SWIMMATCH_SEED_DEMO=1` (the default).
Set `SWIMMATCH_SEED_DEMO=0` for any shared or deployed environment. Create a swimmer account
(or a second coach) yourself at `/register`.

## Routes

### Accounts

| Method   | Path        | Access         | Purpose                                     |
|----------|-------------|----------------|---------------------------------------------|
| GET/POST | `/register` | logged out     | Create an account and choose coach or swimmer |
| GET/POST | `/login`    | logged out     | Log in (supports a same-site `?next=`)      |
| POST     | `/logout`   | logged in      | Log out                                     |

### Coach recruiting posts

| Method   | Path                    | Access              | Purpose                    |
|----------|-------------------------|---------------------|----------------------------|
| GET      | `/posts/`               | anyone              | Browse all posts, newest first |
| GET      | `/posts/<id>`           | anyone              | View a post's full details |
| GET/POST | `/posts/new`            | coach               | Create a post              |
| GET/POST | `/posts/<id>/edit`      | the coach who owns the post | Edit a post        |
| POST     | `/posts/<id>/delete`    | the coach who owns the post | Delete a post      |

Visitors who hit a coach-only route are sent to the login page. A logged-in swimmer, or a coach
who doesn't own the post, gets **403 Forbidden**.

### Existing scaffold (unchanged)

`/` (landing), `/profile`, `/schools`, `/schools/<id>`, `/athlete/api/<id>`,
`/athlete/<id>/update` (stub), `/api/schools/`, `/api/schools/<id>`, `/api/schools/match/<swimmer_id>`.

## Security notes

- Passwords are hashed with `werkzeug.security` and stored only as hashes. There is no plaintext column.
- Sessions are handled by Flask-Login. Session cookies are `HttpOnly` and `SameSite=Lax`.
- All create/edit/delete routes require login and the coach role (`coach_required`).
  Every edit and delete also re-checks server-side that the post's `coach_id` matches the
  current user (`_get_owned_post_or_403` in `backend/routes/posts.py`).
- All form input is validated on the server (`backend/validation.py`): required fields, allowed
  divisions/courses/grad years, length limits, and target-time format (`46.50` / `1:41.80`)
  checked against realistic per-event ranges.
- Every POST carries a per-session CSRF token (`backend/security.py`, rendered with `{{ csrf_field() }}`).
- Login uses a generic error message, and `?next=` only accepts same-site paths.

## Project structure

```
run.py                  # entry point — calls create_app()
requirements.txt
.env.example            # documents optional config
backend/
  app.py                # create_app(): config, SQLite, security, blueprints, filters, db.create_all()
  security.py           # Flask-Login setup, coach_required, CSRF check, safe-redirect helper
  validation.py         # server-side validation for registration + post forms, time parsing
  seed.py               # fictional sample schools, swimmer, demo coach + posts
  models/
    __init__.py         # db instance + canonical EVENTS list
    user.py             # User (coach | swimmer), password hashing
    post.py             # Post: coach recruiting post (events/target times as JSON)
    swimmer.py          # Swimmer + SwimmerEventTime (one row per event)
    school.py           # School + SchoolEventStandard (recruit / walk-on per event)
  routes/
    auth.py             # /register, /login, /logout
    posts.py            # /posts/... browse, view, create, edit, delete
    pages.py            # HTML pages: /, /profile, /schools, /schools/<id>
    athlete.py          # swimmer profile CRUD (stubbed)
    schools.py          # search, match-score stub, JSON API under /api/schools
  services/
    __init__.py         # service layer package
    posts.py            # business logic for creating recruiting posts
frontend/
  pages/                # Jinja templates (base layout, pages, partials)
    auth/               # login, register
    posts/              # list, detail, form, _post_card
  static/css/main.css   # design system: navy + teal, Syne / Lora
  static/js/main.js     # mobile nav, flash dismiss, filter auto-submit, delete confirm
```

### Data model

- `users`: id, name, email (unique, stored lowercased), password_hash, role, created_at.
- `posts`: id, coach_id → users.id, program_name, division, recruiting_events (JSON list of
  event codes), target_times (JSON `{event: seconds}`), course (`SCY`/`LCM`), grad_year, message,
  created_at, updated_at. JSON columns are used because a post's events are always read and
  written together with the post. Move them to a related table if posts ever need to be filtered by event.
- Swimmer times and school standards use related tables (`swimmer_event_times`,
  `school_event_standards`), so matching can join on `event`. All times are stored as seconds (float).

## Next steps / out of scope for now

- Messaging and replies between swimmers and coaches (the "Contact coach" button is disabled)
- Swimmer stats profiles tied to accounts
- Filtering by event and bookmarking posts
- Multi-event match scoring in `compute_match_score`; wire up the profile form
- Women's standards and LCM → SCY conversion
