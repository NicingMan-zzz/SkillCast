# SkillCast Backend (`backend/`)

Python + SQLite + RunPod (OpenAI-compatible endpoint). All backend code lives in this folder.

## Setup & run order

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # then fill in RUNPOD_API_KEY (never commit .env)
python db.py                # skip if aiversecity.db already exists
python seed_skills.py
python seed_demo.py
python ingest_jobs.py       # fetch postings + tag skills with the LLM
python export_json.py       # writes trends.json
python api.py               # Flask API on port 5000
```

## Files

- `llm_layer.py` - LLM calls (RunPod). The model can only pick skills from our skills table; rejects are logged in `llm_runs`.
- `ingest_jobs.py` - Arbeitnow postings -> skills -> dated trend_signals
- `export_json.py` - trend snapshot as JSON (source, date, models used, scenarios)
- `engine.py` - role outlook per scenario, explainable matching, pathway
- `api.py` - Flask routes (`/api/trends`, `/api/recommend`, `/api/pathway`, ...)
- `schema.sql`, `seed_*.sql/py`, `db.py` - database


AI disclosure: RunPod-hosted `openai/gpt-oss-120b` (earlier runs used Groq `openai/gpt-oss-20b`; both are logged in `llm_runs`).
