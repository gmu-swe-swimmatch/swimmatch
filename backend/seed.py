"""Seed sample data so the pages render on first run.

All schools, people and times below are FICTIONAL placeholders.
"""
from datetime import date

from sqlalchemy import select

from backend.models import School, SchoolEventStandard, Swimmer, SwimmerEventTime, db

# Baseline men's SCY recruiting times (seconds) for a strong D1 program.
# Each sample school scales these by a factor so standards look realistic.
BASE_RECRUIT_TIMES = {
    "50_FREE": 20.40,
    "100_FREE": 44.60,
    "200_FREE": 97.80,
    "500_FREE": 263.50,
    "100_BACK": 48.60,
    "100_BREAST": 54.90,
    "100_FLY": 48.10,
    "200_IM": 108.90,
}
WALKON_MULTIPLIER = 1.035

SAMPLE_SCHOOLS = [
    {
        "name": "Lakeshore State University", "short_name": "LSU", "city": "Milwaukee", "state": "WI",
        "division": "NCAA D1", "conference": "Great Lakes Athletic", "enrollment": 31000,
        "avg_gpa": 3.7, "acceptance_rate": 0.58, "roster_size": 34, "primary_color": "#0a1f3c",
        "pool": "50m x 25yd natatorium, 10 lanes", "factor": 1.00,
        "description": "A large public research university with a nationally ranked distance group "
                       "and a strong engineering school.",
    },
    {
        "name": "Pacific Crest University", "short_name": "PCU", "city": "Monterey", "state": "CA",
        "division": "NCAA D1", "conference": "Coastal Pacific", "enrollment": 18500,
        "avg_gpa": 3.85, "acceptance_rate": 0.31, "roster_size": 28, "primary_color": "#1b4f72",
        "pool": "Outdoor 50m pool, year-round training", "factor": 0.985,
        "description": "Sprint-focused program with outdoor training and a top marine-science department.",
    },
    {
        "name": "Red Mesa University", "short_name": "RMU", "city": "Tucson", "state": "AZ",
        "division": "NCAA D1", "conference": "Desert Southwest", "enrollment": 26000,
        "avg_gpa": 3.5, "acceptance_rate": 0.72, "roster_size": 30, "primary_color": "#9c3b2b",
        "pool": "Outdoor 50m + indoor diving well", "factor": 1.025,
        "description": "Altitude-adjacent training base known for developing IMers and backstrokers.",
    },
    {
        "name": "Carolina Pines College", "short_name": "CPC", "city": "Asheville", "state": "NC",
        "division": "NCAA D2", "conference": "Blue Ridge Conference", "enrollment": 7200,
        "avg_gpa": 3.45, "acceptance_rate": 0.68, "roster_size": 26, "primary_color": "#1f5d4c",
        "pool": "25yd x 8 lanes, renovated 2022", "factor": 1.055,
        "description": "Close-knit mountain campus with consistent conference titles and small class sizes.",
    },
    {
        "name": "Gulf Coast A&M", "short_name": "GCA", "city": "Corpus Christi", "state": "TX",
        "division": "NCAA D2", "conference": "Gulf South Coastal", "enrollment": 11800,
        "avg_gpa": 3.3, "acceptance_rate": 0.79, "roster_size": 29, "primary_color": "#b5651d",
        "pool": "Outdoor 50m, covered for winter", "factor": 1.065,
        "description": "Growing program with generous athletic aid and a strong sprint free group.",
    },
    {
        "name": "Hudson Valley Institute of Technology", "short_name": "HVT", "city": "Troy", "state": "NY",
        "division": "NCAA D3", "conference": "Empire Athletic", "enrollment": 6900,
        "avg_gpa": 3.9, "acceptance_rate": 0.42, "roster_size": 32, "primary_color": "#7a1f2b",
        "pool": "25yd x 8 lanes", "factor": 1.085,
        "description": "Rigorous STEM institute where the team GPA routinely tops 3.5.",
    },
    {
        "name": "Northwoods College", "short_name": "NWC", "city": "Duluth", "state": "MN",
        "division": "NCAA D3", "conference": "North Star Collegiate", "enrollment": 3100,
        "avg_gpa": 3.6, "acceptance_rate": 0.64, "roster_size": 24, "primary_color": "#2e4a3a",
        "pool": "25yd x 6 lanes, new facility planned", "factor": 1.11,
        "description": "Liberal-arts college on Lake Superior with a welcoming, development-first culture.",
    },
    {
        "name": "Bluegrass Christian College", "short_name": "BCC", "city": "Lexington", "state": "KY",
        "division": "NAIA", "conference": "Mid-South Aquatics", "enrollment": 2400,
        "avg_gpa": 3.4, "acceptance_rate": 0.81, "roster_size": 22, "primary_color": "#283c8c",
        "pool": "25yd x 8 lanes", "factor": 1.10,
        "description": "NAIA contender with flexible scholarship packaging and a strong nursing program.",
    },
]

SAMPLE_SWIMMER = {
    "first_name": "Jordan", "last_name": "Rivera", "email": "jordan.rivera@example.com",
    "gender": "M", "grad_year": 2027, "hometown": "Naperville", "state": "IL",
    "club_team": "Prairie Aquatic Club", "high_school": "Naperville Central HS",
    "gpa": 3.72, "intended_major": "Mechanical Engineering",
    "bio": "Sprint/mid-distance freestyler and IMer. Looking for a strong engineering school "
           "with a team that trains year-round.",
}
SAMPLE_SWIMMER_TIMES = {
    "50_FREE": 21.10,
    "100_FREE": 46.20,
    "200_FREE": 101.80,
    "500_FREE": 278.50,
    "100_BACK": 51.40,
    "100_BREAST": 58.90,
    "100_FLY": 50.20,
    "200_IM": 113.60,
}


def seed_if_empty():
    """Insert sample schools and one sample swimmer if the tables are empty."""
    if db.session.execute(select(School).limit(1)).first() is None:
        for data in SAMPLE_SCHOOLS:
            data = dict(data)
            factor = data.pop("factor")
            school = School(website="#", **data)
            for event, base in BASE_RECRUIT_TIMES.items():
                recruit = round(base * factor, 2)
                school.standards.append(
                    SchoolEventStandard(
                        event=event,
                        gender="M",
                        recruit_time=recruit,
                        walkon_time=round(recruit * WALKON_MULTIPLIER, 2),
                    )
                )
            db.session.add(school)

    if db.session.execute(select(Swimmer).limit(1)).first() is None:
        swimmer = Swimmer(**SAMPLE_SWIMMER)
        for event, seconds in SAMPLE_SWIMMER_TIMES.items():
            swimmer.event_times.append(
                SwimmerEventTime(
                    event=event,
                    time_seconds=seconds,
                    course="SCY",
                    meet_name="Winter Sectionals (sample)",
                    swum_on=date(2026, 3, 14),
                )
            )
        db.session.add(swimmer)

    db.session.commit()
