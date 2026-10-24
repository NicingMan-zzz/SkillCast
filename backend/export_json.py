"""Option A (simplest): dump the latest trend snapshot to a JSON file the frontend can load.
Run:  py export_json.py            -> writes ../data/trends.json
Frontend:  fetch('data/trends.json').then(r => r.json())
Re-run after every ingest_jobs.py so the Radar changes when the data changes."""
import json, os, sys
from datetime import datetime, timezone
from db import get_conn

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "data", "trends.json")

def build():
    with get_conn() as c:
        snap = c.execute("SELECT MAX(snapshot_date) FROM trend_signals").fetchone()[0]
        if not snap:
            return {"error": "No trend data yet. Run ingest_jobs.py first."}
        scen = [dict(r) for r in c.execute("SELECT name, description, demand_multiplier, automation_multiplier FROM scenarios")]
        src = c.execute("""SELECT s.name, s.url, s.fetched_at FROM sources s
                           WHERE s.kind='job_postings' ORDER BY s.fetched_at DESC LIMIT 1""").fetchone()
        models = [r[0] for r in c.execute("SELECT model FROM llm_runs GROUP BY model ORDER BY MAX(run_id) DESC")]
        rows = c.execute("""SELECT k.skill_id, k.name, k.category, t.demand_share, t.growth_rate,
                                   t.postings_recent, t.postings_prior, t.sample_size
                            FROM trend_signals t JOIN skills k USING(skill_id)
                            WHERE t.snapshot_date=? ORDER BY t.demand_share DESC""", (snap,)).fetchall()
    skills = []
    for r in rows:
        g = r["growth_rate"]
        # Simple illustrative scenario model: AI-category skills grow faster under fast disruption.
        by_scen = {s["name"]: round(g * (s["demand_multiplier"] if r["category"] == "ai" else 1.0), 3) for s in scen}
        skills.append({
            "id": r["skill_id"], "name": r["name"], "category": r["category"],
            "demand_share": round(r["demand_share"], 3), "growth_rate": round(g, 3),
            "direction": ("insufficient_data" if r["postings_prior"] == 0 else
                          "rising" if g > 0.15 else "declining" if g < -0.15 else "stable"),
            "postings_recent": r["postings_recent"], "postings_prior": r["postings_prior"],
            "sample_size": r["sample_size"],
            "low_confidence": r["sample_size"] < 100 or r["postings_prior"] == 0,
            "scenarios": by_scen,
        })
    return {
        "snapshot_date": snap,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": dict(src) if src else None,
        "ai_model_used": models[0] if models else None,   # latest model that actually ran
        "ai_models_used": models,                          # every model logged in llm_runs (true disclosure)
        "disclaimer": "Trend scores are estimates from public job postings, not facts or guarantees.",
        "scenarios": scen,
        "skills": skills,
    }

if __name__ == "__main__":
    data = build()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), indent=2)
    print("Wrote", OUT, "-", len(data.get("skills", [])), "skills")
