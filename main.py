"""Kelasa Dhwani prototype: FastAPI backend.

Run:  uvicorn main:app --reload
Open: http://localhost:8000   (use Chrome for voice input)
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import matching
import profile_parser
import store

app = FastAPI(title="Kelasa Dhwani MVP")
INDEX = Path(__file__).parent / "index.html"


class VoiceNote(BaseModel):
    text: str


class JobIn(BaseModel):
    trade: str
    area: str
    wage: int
    day: str = "anytime"
    employer: str = "Employer"


class CompleteIn(BaseModel):
    worker_id: int


class RatingIn(BaseModel):
    worker_id: int
    stars: int


@app.get("/")
def home():
    return FileResponse(str(INDEX))


@app.post("/api/voice-note")
def voice_note(body: VoiceNote):
    """Worker's spoken text -> profile, skill card, matching jobs and a spoken-style reply."""
    profile = profile_parser.parse_voice_text(body.text)
    missing = profile_parser.missing_fields(profile)
    if missing:
        ask = {"trade": "what work you do (for example electrician or plumber)",
               "area": "which area you are in (for example Hebbal or Indiranagar)"}
        reply = "Sorry, I did not catch " + " and ".join(ask[m] for m in missing) + ". Please say it again."
        return {"status": "need_more", "missing": missing, "reply": reply}

    worker = store.add_worker(profile)
    all_jobs = list(store.jobs.values())
    matches = matching.rank_jobs(worker, all_jobs)
    typical = matching.typical_wage(worker["trade"], all_jobs)
    tip = profile_parser.LEARNING_TIPS.get(worker["trade"])
    reply = matching.build_reply(worker, matches, typical, tip)
    return {"status": "ok", "worker_id": worker["id"], "profile": profile,
            "skill_card": store.skill_card(worker["id"]), "matches": matches,
            "typical_wage": typical, "tip": tip, "reply": reply}


@app.get("/api/jobs")
def list_jobs():
    return list(store.jobs.values())


@app.post("/api/jobs")
def post_job(body: JobIn):
    trade = body.trade.strip().lower()
    area = body.area.strip().lower()
    if trade not in profile_parser.TRADE_WORDS:
        raise HTTPException(400, "Trade must be one of: " + ", ".join(profile_parser.TRADE_WORDS))
    if area not in matching.AREAS:
        raise HTTPException(400, "Area must be one of: " + ", ".join(matching.AREAS))
    if body.wage <= 0:
        raise HTTPException(400, "Wage must be more than 0.")
    return store.add_job(trade, area, body.wage, body.day, body.employer)


@app.post("/api/jobs/{job_id}/complete")
def complete_job(job_id: int, body: CompleteIn):
    ok, message = store.complete_job(job_id, body.worker_id)
    if not ok:
        raise HTTPException(400, message)
    return {"message": message}


@app.post("/api/jobs/{job_id}/rating")
def rate_job(job_id: int, body: RatingIn):
    ok, message = store.add_rating(body.worker_id, job_id, body.stars)
    if not ok:
        raise HTTPException(400, message)
    return {"message": message, "skill_card": store.skill_card(body.worker_id)}


@app.get("/api/workers/{worker_id}/card")
def worker_card(worker_id: int):
    if worker_id not in store.workers:
        raise HTTPException(404, "Worker not found.")
    return store.skill_card(worker_id)
