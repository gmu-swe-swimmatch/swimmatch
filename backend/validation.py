"""Server-side validation for auth and post forms.

Each validator returns (clean_data, errors). `errors` maps field name -> message;
an empty dict means the input is valid. Nothing is saved unless errors is empty.
"""
import re
from datetime import date

from backend.models import EVENT_CODES, EVENT_LABELS
from backend.models.post import COURSES
from backend.models.user import ROLES
from backend.routes.schools import DIVISIONS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TIME_RE = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2})(?:\.(\d{1,2}))?$")
PASSWORD_MIN_LENGTH = 8

# Rough plausibility bounds in seconds. The floor sits just under SCY world-record pace so
# obvious typos ("4.65" for 46.50) are caught; the ceiling catches swapped minutes/seconds.
EVENT_TIME_BOUNDS = {
    "50_FREE": (17, 60),
    "100_FREE": (39, 120),
    "200_FREE": (88, 240),
    "500_FREE": (240, 720),
    "100_BACK": (43, 120),
    "100_BREAST": (49, 130),
    "100_FLY": (42, 120),
    "200_IM": (95, 260),
}
# Events that only exist in yards (LCM swims 400 Free instead of 500 Free).
SCY_ONLY_EVENTS = {"500_FREE"}

POST_LIMITS = {"program_name": 160, "message": 4000}


def parse_swim_time(text):
    """Parse '46.50', '46.5', '46' or '1:41.80' into seconds. Returns None if malformed."""
    match = TIME_RE.match((text or "").strip())
    if not match:
        return None
    minutes, seconds, hundredths = match.groups()
    seconds = int(seconds)
    if minutes is not None and seconds >= 60:
        return None
    total = int(minutes or 0) * 60 + seconds + int((hundredths or "0").ljust(2, "0")) / 100
    return round(total, 2)


def grad_year_choices():
    this_year = date.today().year
    return list(range(this_year, this_year + 7))


def validate_registration(form):
    data = {
        "name": (form.get("name") or "").strip(),
        "email": (form.get("email") or "").strip().lower(),
        "role": (form.get("role") or "").strip(),
    }
    password = form.get("password") or ""
    confirm = form.get("confirm_password") or ""
    errors = {}

    if not data["name"]:
        errors["name"] = "Name is required."
    elif len(data["name"]) > 80:
        errors["name"] = "Name must be 80 characters or fewer."

    if not data["email"]:
        errors["email"] = "Email is required."
    elif len(data["email"]) > 254 or not EMAIL_RE.match(data["email"]):
        errors["email"] = "Enter a valid email address."

    if data["role"] not in ROLES:
        errors["role"] = "Choose whether you're a coach or a swimmer."

    if len(password) < PASSWORD_MIN_LENGTH:
        errors["password"] = f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
    elif len(password) > 128:
        errors["password"] = "Password must be 128 characters or fewer."
    elif password != confirm:
        errors["confirm_password"] = "Passwords don't match."

    data["password"] = password  # returned for hashing only; never rendered or logged
    return data, errors


def validate_post(form):
    """Validate the coach post form. Returns (clean_data, errors)."""
    errors = {}
    data = {
        "program_name": (form.get("program_name") or "").strip(),
        "division": (form.get("division") or "").strip(),
        "course": (form.get("course") or "").strip().upper(),
        "message": (form.get("message") or "").strip(),
    }

    if not data["program_name"]:
        errors["program_name"] = "Program name is required."
    elif len(data["program_name"]) > POST_LIMITS["program_name"]:
        errors["program_name"] = f"Program name must be {POST_LIMITS['program_name']} characters or fewer."

    if data["division"] not in DIVISIONS:
        errors["division"] = "Choose a division."

    if data["course"] not in COURSES:
        errors["course"] = "Choose a course (SCY or LCM)."

    raw_year = (form.get("grad_year") or "").strip()
    try:
        data["grad_year"] = int(raw_year)
    except ValueError:
        data["grad_year"] = None
    if data["grad_year"] not in grad_year_choices():
        errors["grad_year"] = "Choose a graduation year."

    if not data["message"]:
        errors["message"] = "Add a message describing what you're looking for."
    elif len(data["message"]) > POST_LIMITS["message"]:
        errors["message"] = f"Message must be {POST_LIMITS['message']} characters or fewer."

    # Events + target times. Only known event codes are ever read from the form.
    selected = [code for code in EVENT_CODES if form.get(f"event_{code}")]
    target_times = {}
    time_errors = []
    for code in EVENT_CODES:
        label = EVENT_LABELS[code]
        raw = (form.get(f"time_{code}") or "").strip()
        if code not in selected:
            if raw:
                time_errors.append(f"You entered a time for {label} but didn't select it as a recruiting event.")
            continue
        if data["course"] == "LCM" and code in SCY_ONLY_EVENTS:
            time_errors.append(f"{label} is a yards-only event; it can't be used with LCM.")
            continue
        if not raw:
            time_errors.append(f"Enter a target time for {label}.")
            continue
        seconds = parse_swim_time(raw)
        if seconds is None:
            time_errors.append(f"{label}: “{raw}” isn't a valid time. Use 46.50 or 1:41.80.")
            continue
        low, high = EVENT_TIME_BOUNDS[code]
        if not (low <= seconds <= high):
            time_errors.append(f"{label}: “{raw}” is outside the realistic range for this event.")
            continue
        target_times[code] = seconds

    if not selected:
        time_errors.insert(0, "Select at least one recruiting event.")
    if time_errors:
        errors["events"] = " ".join(time_errors)

    data["recruiting_events"] = selected
    data["target_times"] = target_times
    return data, errors
