"""SkillCast engine: role outlook (per scenario), explainable matching, reskilling pathway.

Drop into ai_db/ next to db.py. Uses only tables already in schema.sql.
Untested against your data: run `python engine.py demo` after seeding roles/role_skills/courses.

Wire into api.py:
    from engine import register
    register(app)
"""
import json, math, sys
from datetime import date
from flask import request, jsonify
from db import get_conn


def _latest_growth(c):
    snap = c.execute("SELECT MAX(snapshot_date) FROM trend_signals").fetchone()[0]
    rows = c.execute("""SELECT t.skill_id, t.growth_rate, t.sample_size, k.category
                        FROM trend_signals t JOIN skills k USING(skill_id)
                        WHERE t.snapshot_date=?""", (snap,)).fetchall()
    return snap, {r["skill_id"]: dict(r) for r in rows}


def _adj_growth(sig, scen):
    """Same illustrative model as export_json: AI skills scale with demand_multiplier."""
    if not sig:
        return 0.0
    g = sig["growth_rate"]
    return g * (scen["demand_multiplier"] if sig["category"] == "ai" else 1.0)


def compute_role_outlook():
    """Fill role_outlook for every role x scenario. >0 rising, <0 declining."""
    with get_conn() as c:
        snap, sig = _latest_growth(c)
        if not snap:
            return {"error": "No trend data. Run ingest_jobs.py first."}
        scens = [dict(r) for r in c.execute("SELECT * FROM scenarios")]
        roles = [dict(r) for r in c.execute("SELECT role_id, automation_exposure FROM roles")]
        n = 0
        for r in roles:
            rs = c.execute("SELECT skill_id, importance FROM role_skills WHERE role_id=?",
                           (r["role_id"],)).fetchall()
            wsum = sum(x["importance"] for x in rs) or 1.0
            for s in scens:
                demand = sum(x["importance"] * _adj_growth(sig.get(x["skill_id"]), s) for x in rs) / wsum
                penalty = (r["automation_exposure"] or 0) * s["automation_multiplier"] * 0.5
                score = demand - penalty
                avg_n = sum((sig.get(x["skill_id"]) or {"sample_size": 0})["sample_size"] for x in rs) / max(len(rs), 1)
                band = 0.5 / math.sqrt(avg_n) if avg_n > 0 else 0.5  # wider band for thin data
                c.execute("""INSERT OR REPLACE INTO role_outlook
                             (role_id, scenario_id, snapshot_date, outlook_score, ci_low, ci_high)
                             VALUES (?,?,?,?,?,?)""",
                          (r["role_id"], s["scenario_id"], snap, round(score, 4),
                           round(score - band, 4), round(score + band, 4)))
                n += 1
        return {"snapshot_date": snap, "rows": n}


def match(user_id, role_id, scenario_id):
    """Transparent score: skill overlap weighted by importance and demand trend."""
    with get_conn() as c:
        snap, sig = _latest_growth(c)
        scen = dict(c.execute("SELECT * FROM scenarios WHERE scenario_id=?", (scenario_id,)).fetchone())
        have = {r["skill_id"]: r["level"] for r in
                c.execute("SELECT skill_id, level FROM user_skills WHERE user_id=?", (user_id,))}
        rows = c.execute("""SELECT rs.skill_id, k.name, rs.importance, rs.required_level
                            FROM role_skills rs JOIN skills k USING(skill_id)
                            WHERE rs.role_id=?""", (role_id,)).fetchall()
        got = tot = 0.0
        breakdown = []
        for r in rows:
            trend = max(_adj_growth(sig.get(r["skill_id"]), scen), 0)
            w = r["importance"] * (1 + min(trend, 1.0))  # cap so one hot skill can't dominate
            lvl = have.get(r["skill_id"], 0)
            cover = min(lvl / r["required_level"], 1.0)
            got += w * cover
            tot += w
            breakdown.append({"skill_id": r["skill_id"], "skill": r["name"], "weight": round(w, 3),
                              "have_level": lvl, "required_level": r["required_level"],
                              "coverage": round(cover, 2), "status": "have" if cover >= 1 else "gap"})
        score = round(100 * got / tot, 1) if tot else 0.0
        cur = c.execute("""INSERT INTO matches (user_id, role_id, scenario_id, match_score, breakdown_json)
                           VALUES (?,?,?,?,?)""",
                        (user_id, role_id, scenario_id, score, json.dumps(breakdown)))
        return {"match_id": cur.lastrowid, "match_score": score, "breakdown": breakdown}


def rank_roles(user_id, scenario_id, top=5):
    with get_conn() as c:
        role_ids = [r[0] for r in c.execute("SELECT role_id FROM roles")]
    results = []
    for rid in role_ids:
        m = match(user_id, rid, scenario_id)
        with get_conn() as c:
            title = c.execute("SELECT title FROM roles WHERE role_id=?", (rid,)).fetchone()[0]
            o = c.execute("""SELECT outlook_score, ci_low, ci_high FROM role_outlook
                             WHERE role_id=? AND scenario_id=? ORDER BY snapshot_date DESC LIMIT 1""",
                          (rid, scenario_id)).fetchone()
        results.append({"role_id": rid, "title": title, "match_id": m["match_id"],
                        "match_score": m["match_score"], "outlook": dict(o) if o else None,
                        "missing": [b["skill"] for b in m["breakdown"] if b["status"] == "gap"]})
    return sorted(results, key=lambda x: x["match_score"], reverse=True)[:top]


def build_pathway(match_id):
    """Ordered steps from real catalogue courses only. No course -> step is flagged, never invented."""
    with get_conn() as c:
        m = dict(c.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone())
        hrs_week = c.execute("SELECT hours_per_week FROM user_profiles WHERE user_id=?",
                             (m["user_id"],)).fetchone()[0] or 5
        gaps = sorted([b for b in json.loads(m["breakdown_json"]) if b["status"] == "gap"],
                      key=lambda b: b["weight"], reverse=True)
        pid = c.execute("INSERT INTO pathways (match_id) VALUES (?)", (match_id,)).lastrowid
        total, steps = 0.0, []
        for i, g in enumerate(gaps, 1):
            course = c.execute("""SELECT co.course_id, co.title, co.provider, co.url, co.cost_myr,
                                         co.hours, co.hrdcorp_claimable
                                  FROM course_skills cs JOIN courses co USING(course_id)
                                  WHERE cs.skill_id=? AND cs.level_gained >= ?
                                  ORDER BY co.cost_myr ASC, co.hrdcorp_claimable DESC, co.hours ASC
                                  LIMIT 1""", (g["skill_id"], min(g["required_level"], 3))).fetchone()
            hours = course["hours"] if course else None
            why = f"Closes {round(g['weight'] * (1 - g['coverage']), 2)} weighted gap points"
            c.execute("""INSERT INTO pathway_steps (pathway_id, step_no, skill_id, course_id, est_hours, why)
                         VALUES (?,?,?,?,?,?)""",
                      (pid, i, g["skill_id"], course["course_id"] if course else None, hours, why))
            total += hours or 0
            steps.append({"step": i, "skill": g["skill"], "course": dict(course) if course else None,
                          "est_hours": hours, "why": why,
                          "note": None if course else "No catalogue course yet"})
        c.execute("UPDATE pathways SET total_hours=? WHERE pathway_id=?", (total, pid))
        return {"pathway_id": pid, "total_hours": total,
                "est_weeks": round(total / hrs_week, 1), "steps": steps,
                "disclaimer": "Estimates, not guarantees. You make the final decision."}


def sdg_for_role(role_id):
    with get_conn() as c:
        return [dict(r) for r in c.execute("""SELECT g.sdg_id, g.name, rs.strength, rs.rationale
                                              FROM role_sdg rs JOIN sdgs g USING(sdg_id)
                                              WHERE rs.role_id=? ORDER BY rs.strength DESC""", (role_id,))]


def register(app):
    @app.post("/api/recommend")
    def recommend():
        b = request.get_json(force=True)
        return jsonify(rank_roles(b["user_id"], b["scenario_id"], b.get("top", 5)))

    @app.post("/api/pathway")
    def pathway():
        b = request.get_json(force=True)
        return jsonify(build_pathway(b["match_id"]))

    @app.get("/api/roles/<int:role_id>/sdgs")
    def role_sdgs(role_id):
        return jsonify(sdg_for_role(role_id))

    @app.post("/api/outlook/recompute")
    def recompute():
        return jsonify(compute_role_outlook())


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "demo":
    print(compute_role_outlook())
    top = rank_roles(user_id=1, scenario_id=1)
    print(json.dumps(top, indent=2))
    if top:
        print(json.dumps(build_pathway(top[0]["match_id"]), indent=2))
