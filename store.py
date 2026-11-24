"""In-memory data for the prototype. Data resets when the server restarts.

The jobs below are SAMPLE data for the demo, not real listings.
(In the full version this layer is DynamoDB.)
"""
SAMPLE_JOBS = [
    ("electrician", "hebbal", 900, "tomorrow", "Sample employer A"),
    ("electrician", "yelahanka", 850, "anytime", "Sample employer B"),
    ("electrician", "whitefield", 950, "anytime", "Sample employer C"),
    ("plumber", "indiranagar", 800, "today", "Sample employer D"),
    ("plumber", "jayanagar", 780, "tomorrow", "Sample employer E"),
    ("mason", "whitefield", 1000, "anytime", "Sample employer F"),
    ("helper", "marathahalli", 600, "today", "Sample employer G"),
    ("painter", "koramangala", 850, "anytime", "Sample employer H"),
]

workers = {}
jobs = {}
ratings = []          # {"worker_id", "job_id", "stars"}
_ids = {"worker": 0, "job": 0}


def _next(kind):
    _ids[kind] += 1
    return _ids[kind]


def reset():
    workers.clear(); jobs.clear(); ratings.clear()
    _ids["worker"] = 0; _ids["job"] = 0
    for trade, area, wage, day, employer in SAMPLE_JOBS:
        add_job(trade, area, wage, day, employer)


def add_worker(profile):
    wid = _next("worker")
    workers[wid] = dict(profile, id=wid)
    return workers[wid]


def add_job(trade, area, wage, day="anytime", employer="Employer"):
    jid = _next("job")
    jobs[jid] = {"id": jid, "trade": trade, "area": area, "wage": wage, "day": day,
                 "employer": employer, "status": "open", "worker_id": None}
    return jobs[jid]


def complete_job(job_id, worker_id):
    job = jobs.get(job_id)
    if job is None or worker_id not in workers:
        return False, "Job or worker not found."
    if job["status"] != "open":
        return False, "This job is already completed."
    if job["trade"] != workers[worker_id]["trade"]:
        return False, "This job is for a different trade."
    job["status"] = "completed"
    job["worker_id"] = worker_id
    return True, "Job marked as completed."


def add_rating(worker_id, job_id, stars):
    """Ratings count only for a completed job done by that worker, once per job."""
    job = jobs.get(job_id)
    if not 1 <= stars <= 5:
        return False, "Stars must be between 1 and 5."
    if job is None or job["status"] != "completed" or job["worker_id"] != worker_id:
        return False, "You can only rate a job after it is completed by this worker."
    if any(r["job_id"] == job_id for r in ratings):
        return False, "This job is already rated."
    ratings.append({"worker_id": worker_id, "job_id": job_id, "stars": stars})
    return True, "Rating saved."


def skill_card(worker_id):
    w = workers[worker_id]
    mine = [r["stars"] for r in ratings if r["worker_id"] == worker_id]
    done = sum(1 for j in jobs.values() if j["worker_id"] == worker_id)
    years = w.get("years") or 0
    level = "Beginner" if years < 2 else "Experienced" if years < 6 else "Senior"
    avg = round(sum(mine) / len(mine), 1) if mine else None
    return {"worker_id": worker_id, "trade": w["trade"], "years": w.get("years"),
            "area": w["area"], "level": level, "jobs_completed": done,
            "ratings": len(mine), "average_rating": avg,
            "verified_by_employers": len(mine) >= 3 and avg is not None and avg >= 4.0}


reset()
