"""Job matching for Kelasa Dhwani.

Ranks open jobs for a worker by trade, distance, wage and day.
Area coordinates are approximate and only used for the demo.
"""
import math
import statistics

# Approximate centre points of a few Bengaluru areas (lat, lon).
AREAS = {
    "hebbal": (13.0358, 77.5970),
    "yelahanka": (13.1007, 77.5963),
    "indiranagar": (12.9784, 77.6408),
    "koramangala": (12.9352, 77.6245),
    "whitefield": (12.9698, 77.7500),
    "jayanagar": (12.9308, 77.5838),
    "rajajinagar": (12.9916, 77.5520),
    "malleshwaram": (13.0035, 77.5643),
    "yeshwanthpur": (13.0285, 77.5197),
    "btm layout": (12.9166, 77.6101),
    "electronic city": (12.8452, 77.6602),
    "marathahalli": (12.9591, 77.6974),
}

DEFAULT_DISTANCE_KM = 10.0
MAX_RADIUS_KM = 15.0


def label(area):
    """Display name for an area key."""
    if not area:
        return ""
    if area == "btm layout":
        return "BTM Layout"
    return area.title()


def haversine_km(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def distance_km(area_a, area_b):
    if area_a in AREAS and area_b in AREAS:
        return haversine_km(AREAS[area_a], AREAS[area_b])
    return DEFAULT_DISTANCE_KM


def _day_score(worker_day, job_day):
    if worker_day in (None, "anytime") or job_day == "anytime":
        return 1.0
    return 1.0 if worker_day == job_day else 0.3


def _wage_score(expected, offered):
    if not expected:
        return 0.5
    return min(1.0, offered / expected)


def rank_jobs(worker, jobs, limit=3):
    """Return up to `limit` open jobs for the worker's trade, best first."""
    ranked = []
    for job in jobs:
        if job["status"] != "open" or job["trade"] != worker["trade"]:
            continue
        dist = distance_km(worker["area"], job["area"])
        dist_score = max(0.0, 1.0 - dist / MAX_RADIUS_KM)
        score = (0.5 * dist_score
                 + 0.3 * _wage_score(worker.get("wage_expected"), job["wage"])
                 + 0.2 * _day_score(worker.get("availability"), job["day"]))
        ranked.append({"job": job, "score": round(score, 3), "distance_km": round(dist, 1)})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:limit]


def typical_wage(trade, jobs):
    """Median posted daily wage for a trade (from jobs in the system)."""
    wages = [j["wage"] for j in jobs if j["trade"] == trade]
    return int(statistics.median(wages)) if wages else None


def build_reply(profile, matches, typical, tip):
    """Plain-language reply that is shown and read aloud."""
    trade, area = profile["trade"], label(profile["area"])
    years = profile.get("years")
    art = "an" if trade[0] in "aeiou" else "a"
    who = f"{art} {trade} with {years} years of experience" if years else f"{art} {trade}"
    parts = [f"Thank you. I noted that you are {who} in {area}."]
    if not matches:
        parts.append(f"I could not find open {trade} jobs near you right now.")
    else:
        n = len(matches)
        parts.append(f"I found {n} nearby job{'s' if n > 1 else ''}.")
        for m in matches:
            j = m["job"]
            near = ("in your area" if m["distance_km"] < 0.5
                    else f"about {m['distance_km']} kilometres away")
            parts.append(f"{label(j['area'])}, {near}, {j['wage']} rupees a day, {j['day']}.")
    if typical:
        parts.append(f"The usual pay for {trade} work here is about {typical} rupees a day.")
    if tip:
        parts.append(f"Tip: {tip}")
    return " ".join(parts)
