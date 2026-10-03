# SwimMatch

SwimMatch helps prospective swimmers find U.S. college swimming programs that fit them.
Instead of reducing a swimmer to a single rating, it models each athlete as a **set of event
times** (50 Free, 100 Free, 200 Free, 500 Free, 100 Back, 100 Breast, 100 Fly, 200 IM — all in
short-course yards) and compares them against each program's **per-event recruiting standards**.

> **Status: draft scaffold.** The layout, pages, data model and design are in place, populated
> with fictional sample data. Match scoring is a hardcoded placeholder
> (`# TODO: implement multi-event match scoring` in `backend/routes/schools.py`), and the
> profile edit form doesn't save yet.

## Running locally

Requires Python 3.10+.

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:5000>.

On first start the app creates `swim.db` (SQLite) in the project root and seeds 8 sample
programs and 1 sample swimmer. Delete `swim.db` and restart to reset the data.

Optional config lives in `.env` — copy `.env.example` to see the available settings. No API
keys or external services are needed.

## Project structure

```
run.py                  # entry point — calls create_app()
requirements.txt
.env.example            # documents optional config
backend/
  app.py                # create_app(): config, SQLite, blueprints, template filters, db.create_all()
  seed.py               # fictional sample schools + swimmer
  models/
    __init__.py         # db instance + canonical EVENTS list
    swimmer.py          # Swimmer + SwimmerEventTime (one row per event)
    school.py           # School + SchoolEventStandard (recruit / walk-on per event)
  routes/
    pages.py            # HTML pages: /, /profile, /schools, /schools/<id>
    athlete.py          # swimmer profile CRUD (stubbed)
    schools.py          # search, match-score stub, JSON API under /api/schools
frontend/
  pages/                # Jinja templates (base layout, pages, partials)
  static/css/main.css   # design system: navy + teal, Syne / Lora
  static/js/main.js     # mobile nav, flash dismiss, filter auto-submit
```

### Data model

Event times are stored in related tables (`swimmer_event_times`, `school_event_standards`)
rather than JSON columns, so matching can be a straight join on `event`, uniqueness can be
enforced per event, and per-time metadata (meet, date, course) is just another column.
All times are stored as seconds (float) in SCY.

## Next steps

- Implement multi-event match scoring in `compute_match_score`
- Wire up the profile form (parse `m:ss.xx` times, upsert event times)
- Accounts / auth so each swimmer has their own profile
- Women's standards and LCM → SCY conversion
