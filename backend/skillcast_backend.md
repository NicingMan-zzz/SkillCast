# SkillCast Backend (`backend/`)

Python + SQLite + Groq. Backend code is now stored in one folder named `backend/`.

## Setup & run order

```bash
cd backend
pip install flask requests python-dotenv groq
python db.py
python seed_skills.py
python ingest_jobs.py
python export_json.py
python api.py
```

## Files

- `.env.example`
- `schema.sql`
- `seed_sdgs.sql`
- `seed_skills.py`
- `db.py`
- `groq_layer.py`
- `ingest_jobs.py`
- `export_json.py`
- `api.py`
- `engine.py`
