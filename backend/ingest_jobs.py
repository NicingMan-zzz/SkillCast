import re
import requests
from datetime import datetime, timedelta, timezone
from db import get_conn, get_or_create_source
from groq_layer import extract_skills

ARBEITNOW = "https://www.arbeitnow.com/api/job-board-api"


def fetch_arbeitnow(pages=3):
    with get_conn() as c:
        sid = get_or_create_source(c, "Arbeitnow Job Board API", "job_postings",
                                   "https://www.arbeitnow.com/api/job-board-api", "see site terms")
        for p in range(1, pages + 1):
            data = requests.get(ARBEITNOW, params={"page": p}, timeout=30).json().get("data", [])
            for j in data:
                posted = datetime.fromtimestamp(j["created_at"], tz=timezone.utc).date().isoformat()
                c.execute(
                    """INSERT OR IGNORE INTO raw_postings
                    (source_id,external_ref,title,company,location,description,url,posted_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (sid, j["slug"], j["title"], j["company_name"], j["location"],
                     j["description"], j["url"], posted),
                )


def tag_new_postings(limit=30):
    with get_conn() as c:
        rows = c.execute("SELECT posting_id,title,description FROM raw_postings WHERE processed=0 LIMIT ?", (limit,)).fetchall()
    for i, r in enumerate(rows, 1):
        clean = re.sub(r"<[^>]+>", " ", r["description"] or "")
        clean = re.sub(r"\s+", " ", clean)[:1200]
        ids, run_id = extract_skills(f"{r['title']}\n{clean}")
        with get_conn() as c:
            c.executemany("INSERT OR IGNORE INTO posting_skills VALUES(?,?,?)", [(r["posting_id"], s, run_id) for s in ids])
            c.execute("UPDATE raw_postings SET processed=1 WHERE posting_id=?", (r["posting_id"],))
        print(f"Tagged {i}/{len(rows)}")


def compute_trends(window_days=30, today=None):
    today = today or datetime.now(timezone.utc).date()
    t1, t0 = (today - timedelta(days=window_days)).isoformat(), (today - timedelta(days=2 * window_days)).isoformat()
    with get_conn() as c:
        n_rec = c.execute("SELECT COUNT(*) FROM raw_postings WHERE processed=1 AND posted_at>=?", (t1,)).fetchone()[0]
        n_pri = c.execute("SELECT COUNT(*) FROM raw_postings WHERE processed=1 AND posted_at>=? AND posted_at<?", (t0, t1)).fetchone()[0]
        if n_rec == 0:
            print("No recent postings; skip.")
            return
        sid = c.execute("SELECT source_id FROM sources WHERE kind='job_postings' ORDER BY fetched_at DESC").fetchone()[0]
        for s in c.execute("SELECT skill_id FROM skills").fetchall():
            q = """SELECT COUNT(*) FROM posting_skills ps JOIN raw_postings p USING(posting_id)
                   WHERE ps.skill_id=? AND p.posted_at>=? AND p.posted_at<?"""
            rec = c.execute(q, (s[0], t1, today.isoformat() + "z")).fetchone()[0]
            pri = c.execute(q, (s[0], t0, t1)).fetchone()[0]
            share_r, share_p = rec / n_rec, (pri / n_pri if n_pri else 0)
            growth = (share_r - share_p) / (share_p + 0.02)
            if n_pri < 20:
                growth = 0.0
            growth = max(-1.0, min(3.0, growth))
            c.execute(
                """INSERT OR REPLACE INTO trend_signals
                (skill_id,snapshot_date,window_days,postings_recent,postings_prior,demand_share,growth_rate,sample_size,source_id)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (s[0], today.isoformat(), window_days, rec, pri, share_r, growth, n_rec, sid),
            )


if __name__ == "__main__":
    fetch_arbeitnow()
    tag_new_postings()
    compute_trends()
