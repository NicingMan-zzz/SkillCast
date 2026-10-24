"""SkillCast API + frontend host. Run:  py api.py  ->  http://localhost:5000/"""
import os, json
from flask import Flask, jsonify, request, send_from_directory
from db import get_conn
from export_json import build
from engine import register, _have_from_request, _latest_growth, score_profile

HERE = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.abspath(os.path.join(HERE, "..", "frontend"))
app = Flask(__name__, static_folder=None)


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp


@app.route("/api/<path:_>", methods=["OPTIONS"])
def preflight(_):
    return ("", 204)


# ---------- frontend ----------
@app.get("/")
def index():
    return send_from_directory(FRONT, "index.html")


@app.get("/<path:p>")
def static_files(p):
    if p.startswith("api/"):
        return jsonify({"error": "not found"}), 404
    return send_from_directory(FRONT, p)


# ---------- data ----------
@app.get("/api/health")
def health():
    with get_conn() as c:
        n = lambda t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        models = [r[0] for r in c.execute("SELECT model FROM llm_runs GROUP BY model ORDER BY MAX(run_id) DESC")]
        snap = c.execute("SELECT MAX(snapshot_date) FROM trend_signals").fetchone()[0]
        return jsonify({"ok": True, "snapshot_date": snap, "postings": n("raw_postings"),
                        "tagged_postings": c.execute("SELECT COUNT(*) FROM raw_postings WHERE processed=1").fetchone()[0],
                        "roles": n("roles"), "users": n("user_profiles"), "courses": n("courses"),
                        "ai_models_used": models})


@app.get("/api/trends")
def trends():
    return jsonify(build())


@app.get("/api/skills")
def skills():
    with get_conn() as c:
        al = {}
        for r in c.execute("SELECT alias, skill_id FROM skill_aliases"):
            al.setdefault(r["skill_id"], []).append(r["alias"])
        return jsonify([{**dict(r), "aliases": al.get(r["skill_id"], [])}
                        for r in c.execute("SELECT skill_id, name, category FROM skills ORDER BY name")])


@app.get("/api/roles")
def roles():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT role_id, title, description, is_emerging FROM roles ORDER BY title")])


@app.get("/api/users")
def users():
    with get_conn() as c:
        out = []
        for u in c.execute("SELECT user_id, display_name, persona, current_role, hours_per_week FROM user_profiles"):
            d = dict(u)
            d["skills"] = [dict(r) for r in c.execute(
                "SELECT k.name AS skill, us.level FROM user_skills us JOIN skills k USING(skill_id) WHERE us.user_id=?", (u["user_id"],))]
            out.append(d)
        return jsonify(out)


@app.get("/api/scenarios")
def scenarios():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT * FROM scenarios ORDER BY demand_multiplier")])


@app.get("/api/sdgs")
def sdgs():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT sdg_id, name FROM sdgs")])


@app.get("/api/audit")
def audit():
    """Real audit info: which models ran, how many items the validator rejected."""
    with get_conn() as c:
        runs = [dict(r) for r in c.execute("""SELECT model, purpose, COUNT(*) AS runs,
                      SUM(CASE WHEN rejected_items IS NOT NULL AND rejected_items != '[]' THEN 1 ELSE 0 END) AS runs_with_rejections,
                      MAX(created_at) AS last_run FROM llm_runs GROUP BY model, purpose""")]
        rejected = []
        for r in c.execute("SELECT rejected_items FROM llm_runs WHERE rejected_items IS NOT NULL AND rejected_items != '[]'"):
            try: rejected += [str(x) for x in json.loads(r[0])]
            except Exception: pass
        return jsonify({"runs": runs, "total_rejected": len(rejected), "sample_rejected": sorted(set(rejected))[:15]})


# ---------- LLM-backed (lazy import so the app still runs if the key/endpoint is missing) ----------
@app.post("/api/extract_skills")
def api_extract():
    text = (request.get_json(force=True).get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        from llm_layer import extract_skills
        ids, run_id = extract_skills(text, purpose="cv_parse")
    except Exception as e:
        return jsonify({"error": f"LLM unavailable: {type(e).__name__}: {str(e)[:160]}"}), 503
    with get_conn() as c:
        names = [c.execute("SELECT name FROM skills WHERE skill_id=?", (i,)).fetchone()[0] for i in ids]
    return jsonify({"skills": names, "run_id": run_id})


@app.post("/api/explain")
def api_explain():
    b = request.get_json(force=True)
    have, _ = _have_from_request(b)
    with get_conn() as c:
        snap, sig = _latest_growth(c)
        scen = dict(c.execute("SELECT * FROM scenarios WHERE scenario_id=?", (b.get("scenario_id", 2),)).fetchone())
        role = c.execute("SELECT title FROM roles WHERE role_id=?", (b["role_id"],)).fetchone()["title"]
        score, bd = score_profile(c, have, b["role_id"], scen, sig)
        names = {r["skill_id"]: r["name"] for r in c.execute("SELECT skill_id, name FROM skills")}
        facts = [{"skill": names[k], "demand_share": round(v.get("demand_share", 0), 3) if "demand_share" in v else None,
                  "sample_size": v["sample_size"], "growth_rate": v["growth_rate"]} for k, v in sig.items()
                 if any(x["skill_id"] == k for x in bd)]
    try:
        from llm_layer import explain_match
        text = explain_match({"role": role, "match_score": score, "scenario": scen["name"], "skills": bd}, facts)
    except Exception as e:
        return jsonify({"error": f"LLM unavailable: {type(e).__name__}: {str(e)[:160]}"}), 503
    return jsonify({"text": text})


register(app)

if __name__ == "__main__":
    print("SkillCast running -> http://localhost:%s/" % os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
