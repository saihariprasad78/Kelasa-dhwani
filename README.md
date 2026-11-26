# Kelasa Dhwani

**Speak once. Get a skill card, a learning tip and a nearby job.**

Kelasa Dhwani ("work voice" in Kannada) is a voice-first assistant for informal and semi-skilled workers. A worker says what work they do, and the system builds a skill card, reads out nearby jobs with the usual pay, and gives a short learning tip. After a job, the employer's rating is added to the skill card.

Built for **wHACKiest 2026** (Mystery Track, UnlockED). This repository is the basic MVP we built for the ideathon.

## The problem

Informal workers (masons, electricians, plumbers, helpers) often have real skills but no way to prove them. Nearly 90% of India's workforce is informally employed (ILO & IHD, India Employment Report 2024). Many job apps depend on typing, English and resumes, so a skilled worker and a beginner can get the same offer.

## Try it online

After GitHub Pages is switched on for this repository, the demo runs at
https://saihariprasad78.github.io/Kelasa-dhwani/ (Chrome recommended, allow the microphone).
The page works on its own: when no server is running it uses a built-in copy of the same
parsing, matching and rating logic, so the demo never depends on a backend being up.

## What works in this prototype

- **Voice in and out in the browser.** The worker speaks (or types) and the reply is read aloud. This uses the browser's built-in speech recognition and speech synthesis, so no API key is needed. It works best in Chrome. Replies are given in the language the worker chose (English, Hindi or Kannada). If the device has no voice for a language, the reply is shown as text.
- **Profile from speech.** A rule-based parser pulls out trade, years of experience, area, availability and expected wage. It understands English, common Hindi and Kannada words, spoken number words ("eight years"), and the small spelling mistakes that speech recognition makes ("Hebal" for Hebbal).
- **Skill card.** Trade, years, level, jobs completed, average rating, and a "verified by employers" flag after 3 or more good ratings.
- **Job matching.** Open jobs for the worker's trade are ranked by distance, wage and day. The "usual pay" is the median pay of the jobs in the system.
- **Learning tip** for the worker's trade.
- **Employer page.** An employer can post a job (trade, area, daily wage, day).
- **Ratings with a rule.** A job must be marked completed by that worker before it can be rated, and each job can be rated once.

- **Guided demo screen.** A five-step tracker (speak, skill card, nearby jobs, job done and rating, card updated) and a Reset button for repeating the demo.
- **Employer view.** Posting a job refreshes the worker's matches.

Job data is **sample data**, stored in memory, and resets when the server restarts or when Reset is pressed. Area locations are approximate.

## Not built yet (planned)

| Planned | In this prototype |
|---|---|
| Telegram bot for voice notes | Browser page instead |
| ElevenLabs voice replies | Browser speech synthesis |
| LLM extraction of the profile | Rule-based parser (same output format) |
| Spoken replies in regional languages through ElevenLabs | Browser speech synthesis, depends on the voices installed on the device |
| AWS Lambda + S3, DynamoDB | Local FastAPI server, in-memory data |
| Employer verification, more areas and trades | 12 Bengaluru areas, 5 trades |

## Run it

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in Chrome, tap **Use example** and then **Find work**. For voice, tap **Speak** and allow the microphone.

Run the tests:

```
python -m unittest -v
```

## Files

| File | What it does |
|---|---|
| `main.py` | FastAPI server and API routes |
| `profile_parser.py` | Turns spoken text into profile fields, holds learning tips |
| `matching.py` | Distance, ranking, usual pay, spoken-style reply |
| `store.py` | In-memory jobs, workers, ratings, skill card |
| `index.html` | Demo page (worker and employer). Also contains a copy of the parsing, matching and rating logic so it works without the server |
| `test_core.py` | Unit tests for parsing, matching and ratings |

## API

| Route | Purpose |
|---|---|
| `POST /api/voice-note` | `{"text": "..."}` returns profile, skill card, matches and reply |
| `GET /api/jobs`, `POST /api/jobs` | List or post jobs |
| `POST /api/jobs/{id}/complete` | `{"worker_id": 1}` marks a job completed |
| `POST /api/jobs/{id}/rating` | `{"worker_id": 1, "stars": 5}` adds a rating |
| `GET /api/workers/{id}/card` | Current skill card |
| `GET /api/workers/{id}/matches` | Fresh matches for a worker already registered |
| `POST /api/reset` | Clear the demo and restore the sample jobs |

## Team

Sai Hariprasad D (lead), Subhashini B R, Rishika, Archisma. Cambridge Institute of Technology, Bengaluru.
