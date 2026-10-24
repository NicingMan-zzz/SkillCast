# SkillCast Backend (`ai_db/`)

Python + SQLite + Groq. Put all files below in one folder named `ai_db/`.

## Setup & run order

```bash
cd ai_db
pip install flask requests python-dotenv groq
python db.py              # creates aiversecity.db from schema.sql + seed_sdgs.sql
python seed_skills.py     # loads canonical skills + aliases
python ingest_jobs.py     # fetch jobs -> tag skills with Groq -> compute trends
python export_json.py     # writes ../data/trends.json (frontend option A)
python api.py             # OR run Flask API at http://localhost:5000/api/trends (option B)
```

Frontend either loads `fetch('data/trends.json')` or calls `http://localhost:5000/api/trends`.

## Files

| File | Purpose |
|---|---|
| `.env.example` | config template (copy to `.env`, add your own key) |
| `schema.sql` | all tables |
| `seed_sdgs.sql` | 17 SDGs + 3 AI scenarios |
| `seed_skills.py` | canonical skills + aliases |
| `db.py` | SQLite connection + init |
| `groq_layer.py` | LLM skill extraction / SDG tagging / explanations (guardrailed) |
| `ingest_jobs.py` | job API fetch, tagging, trend computation |
| `export_json.py` | builds trend snapshot JSON |
| `api.py` | Flask API |

---

## `.env.example`

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DB_PATH=aiversecity.db
PORT=5000
```

---

## `schema.sql`

```sql
-- Aiversecity Future-Ready Workforce: data layer (SQLite; Postgres-friendly)
PRAGMA foreign_keys = ON;

-- ========== PROVENANCE (every row traces back here: "cite a source" rule) ==========
CREATE TABLE sources (
  source_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,            -- e.g. 'O*NET 29.x', 'Arbeitnow API', 'WEF Future of Jobs 2025'
  kind TEXT NOT NULL CHECK (kind IN ('taxonomy','job_postings','report','news','course_catalog','sdg_reference','synthetic')),
  url TEXT,
  licence TEXT,
  published_at TEXT,             -- date the source itself was published/released
  fetched_at TEXT NOT NULL DEFAULT (datetime('now'))  -- shown in the UI ("source + date")
);

-- ========== TAXONOMY ==========
CREATE TABLE skills (
  skill_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,     -- canonical name (the ONLY skills the LLM may output)
  category TEXT,                 -- 'technical' | 'ai' | 'green' | 'human' ...
  external_id TEXT,              -- ESCO URI / O*NET element id
  source_id INTEGER REFERENCES sources(source_id)
);

CREATE TABLE skill_aliases (
  alias TEXT PRIMARY KEY,        -- 'ml' -> 'Machine Learning'
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id)
);

CREATE TABLE roles (
  role_id INTEGER PRIMARY KEY,
  title TEXT NOT NULL UNIQUE,
  description TEXT,
  external_id TEXT,              -- O*NET-SOC code / ESCO URI / MASCO
  is_emerging INTEGER NOT NULL DEFAULT 0,
  automation_exposure REAL CHECK (automation_exposure BETWEEN 0 AND 1),  -- from cited research
  source_id INTEGER REFERENCES sources(source_id)
);

CREATE TABLE role_skills (
  role_id INTEGER NOT NULL REFERENCES roles(role_id),
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  importance REAL NOT NULL DEFAULT 0.5 CHECK (importance BETWEEN 0 AND 1),  -- weight in match score
  required_level INTEGER DEFAULT 3 CHECK (required_level BETWEEN 1 AND 5),
  source_id INTEGER REFERENCES sources(source_id),
  PRIMARY KEY (role_id, skill_id)
);

-- ========== TREND SIGNAL LAYER (must be updatable + dated) ==========
CREATE TABLE raw_postings (
  posting_id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(source_id),
  external_ref TEXT NOT NULL,    -- slug / id from the API (dedupe key)
  title TEXT,
  company TEXT,
  location TEXT,
  description TEXT,
  url TEXT,
  posted_at TEXT,
  fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
  processed INTEGER NOT NULL DEFAULT 0,
  UNIQUE (source_id, external_ref)
);

CREATE TABLE posting_skills (
  posting_id INTEGER NOT NULL REFERENCES raw_postings(posting_id),
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  llm_run_id INTEGER REFERENCES llm_runs(run_id),
  PRIMARY KEY (posting_id, skill_id)
);

CREATE TABLE trend_signals (     -- one row per skill per snapshot -> time series -> Radar
  signal_id INTEGER PRIMARY KEY,
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  snapshot_date TEXT NOT NULL,
  window_days INTEGER NOT NULL DEFAULT 30,
  postings_recent INTEGER NOT NULL,
  postings_prior INTEGER NOT NULL,
  demand_share REAL NOT NULL,    -- share of postings mentioning skill
  growth_rate REAL NOT NULL,     -- smoothed relative change vs prior window
  sample_size INTEGER NOT NULL,  -- show this -> honesty about uncertainty
  source_id INTEGER REFERENCES sources(source_id),
  UNIQUE (skill_id, snapshot_date)
);

CREATE TABLE external_outlook (  -- curated, CITED reports (WEF, MyCOL, etc.) as a prior
  outlook_id INTEGER PRIMARY KEY,
  subject_type TEXT NOT NULL CHECK (subject_type IN ('skill','role')),
  subject_id INTEGER NOT NULL,   -- skill_id or role_id
  direction TEXT NOT NULL CHECK (direction IN ('growing','declining','stable')),
  magnitude REAL,                -- e.g. 0.4 = +40% (as stated in report)
  horizon_year INTEGER,
  quote_or_page TEXT,            -- page / table reference
  source_id INTEGER NOT NULL REFERENCES sources(source_id)
);

-- ========== SCENARIOS (Feature 6: uncertainty) ==========
CREATE TABLE scenarios (
  scenario_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,     -- 'Moderate AI adoption' | 'Fast AI disruption' | 'Slow'
  description TEXT,
  demand_multiplier REAL NOT NULL,      -- scales growth of AI-related skills
  automation_multiplier REAL NOT NULL,  -- scales automation_exposure penalty
  is_estimate INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE role_outlook (      -- computed by pipeline per scenario
  role_id INTEGER NOT NULL REFERENCES roles(role_id),
  scenario_id INTEGER NOT NULL REFERENCES scenarios(scenario_id),
  snapshot_date TEXT NOT NULL,
  outlook_score REAL NOT NULL,   -- >0 rising, <0 declining
  ci_low REAL, ci_high REAL,     -- uncertainty band
  PRIMARY KEY (role_id, scenario_id, snapshot_date)
);

-- ========== SDG MAPPING (Feature 5) ==========
CREATE TABLE sdgs (
  sdg_id INTEGER PRIMARY KEY CHECK (sdg_id BETWEEN 1 AND 17),
  name TEXT NOT NULL,
  colour TEXT
);

CREATE TABLE role_sdg (
  role_id INTEGER NOT NULL REFERENCES roles(role_id),
  sdg_id INTEGER NOT NULL REFERENCES sdgs(sdg_id),
  target_code TEXT,              -- e.g. '7.2'
  strength REAL NOT NULL DEFAULT 0.5,  -- 0-1
  rationale TEXT NOT NULL,       -- one sentence: WHY (keeps it non-decorative)
  mapped_by TEXT NOT NULL CHECK (mapped_by IN ('human','llm_reviewed','llm')),
  PRIMARY KEY (role_id, sdg_id, target_code)
);

CREATE TABLE skill_sdg (
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  sdg_id INTEGER NOT NULL REFERENCES sdgs(sdg_id),
  strength REAL NOT NULL DEFAULT 0.5,
  rationale TEXT NOT NULL,
  mapped_by TEXT NOT NULL CHECK (mapped_by IN ('human','llm_reviewed','llm')),
  PRIMARY KEY (skill_id, sdg_id)
);

-- ========== LEARNING RESOURCES (real ones only: no invented courses) ==========
CREATE TABLE courses (
  course_id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  provider TEXT NOT NULL,        -- Coursera, edX, Microsoft Learn, HRD Corp-claimable ...
  url TEXT NOT NULL,             -- must be a real, verified link
  cost_myr REAL DEFAULT 0,
  hours REAL,
  level TEXT CHECK (level IN ('beginner','intermediate','advanced')),
  language TEXT DEFAULT 'en',
  hrdcorp_claimable INTEGER DEFAULT 0,
  verified_at TEXT,              -- date a human checked the link
  source_id INTEGER REFERENCES sources(source_id)
);

CREATE TABLE course_skills (
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  level_gained INTEGER DEFAULT 2,
  PRIMARY KEY (course_id, skill_id)
);

-- ========== USERS (synthetic profiles only!) ==========
CREATE TABLE user_profiles (
  user_id INTEGER PRIMARY KEY,
  display_name TEXT NOT NULL,
  persona TEXT,                  -- 'displaced factory clerk', 'fresh grad' ...
  current_role TEXT,
  years_exp REAL,
  interests TEXT,
  hours_per_week REAL DEFAULT 5,
  is_synthetic INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic = 1)  -- enforces the "no real data" rule
);

CREATE TABLE user_skills (
  user_id INTEGER NOT NULL REFERENCES user_profiles(user_id),
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  level INTEGER NOT NULL DEFAULT 2 CHECK (level BETWEEN 1 AND 5),
  origin TEXT DEFAULT 'form' CHECK (origin IN ('form','cv_extracted','inferred')),
  PRIMARY KEY (user_id, skill_id)
);

-- ========== OUTPUTS ==========
CREATE TABLE matches (
  match_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES user_profiles(user_id),
  role_id INTEGER NOT NULL REFERENCES roles(role_id),
  scenario_id INTEGER NOT NULL REFERENCES scenarios(scenario_id),
  match_score REAL NOT NULL,     -- 0-100
  breakdown_json TEXT NOT NULL,  -- per-skill: have/gap/weight -> "explainable"
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE pathways (
  pathway_id INTEGER PRIMARY KEY,
  match_id INTEGER NOT NULL REFERENCES matches(match_id),
  total_hours REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE pathway_steps (
  pathway_id INTEGER NOT NULL REFERENCES pathways(pathway_id),
  step_no INTEGER NOT NULL,
  skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
  course_id INTEGER REFERENCES courses(course_id),
  est_hours REAL,
  why TEXT,                      -- e.g. "demand +18% (source, date); closes 22pt of gap"
  PRIMARY KEY (pathway_id, step_no)
);

-- ========== LLM AUDIT LOG (AI disclosure + guardrail evidence) ==========
CREATE TABLE llm_runs (
  run_id INTEGER PRIMARY KEY,
  purpose TEXT NOT NULL,         -- 'skill_extraction' | 'sdg_tagging' | 'explanation' | 'cv_parse'
  model TEXT NOT NULL,           -- e.g. 'llama-3.3-70b-versatile' (disclose in UI)
  prompt_hash TEXT,
  output_json TEXT,
  rejected_items TEXT,           -- hallucinated skills/jobs that the validator dropped
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_postings_posted ON raw_postings(posted_at);
CREATE INDEX idx_trend_skill ON trend_signals(skill_id, snapshot_date);
CREATE INDEX idx_roleskills_skill ON role_skills(skill_id);
```

---

## `seed_sdgs.sql`

```sql
INSERT INTO sdgs (sdg_id, name) VALUES
(1,'No Poverty'),(2,'Zero Hunger'),(3,'Good Health and Well-being'),(4,'Quality Education'),
(5,'Gender Equality'),(6,'Clean Water and Sanitation'),(7,'Affordable and Clean Energy'),
(8,'Decent Work and Economic Growth'),(9,'Industry, Innovation and Infrastructure'),
(10,'Reduced Inequalities'),(11,'Sustainable Cities and Communities'),
(12,'Responsible Consumption and Production'),(13,'Climate Action'),(14,'Life Below Water'),
(15,'Life on Land'),(16,'Peace, Justice and Strong Institutions'),(17,'Partnerships for the Goals');

INSERT INTO scenarios (name, description, demand_multiplier, automation_multiplier) VALUES
('Slow adoption','AI diffuses slowly; regulation and cost limit uptake',0.6,0.5),
('Moderate adoption','Current adoption trend continues',1.0,1.0),
('Fast disruption','Rapid capability gains and wide deployment',1.6,1.8);
```

---

## `db.py`

```python
import os, sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "aiversecity.db")

def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

def init_db():
    with get_conn() as c:
        exists = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sources'"
        ).fetchone()
        if exists:
            print("DB already set up:", DB_PATH)
            return
        c.executescript(open("schema.sql", encoding="utf-8").read())
        c.executescript(open("seed_sdgs.sql", encoding="utf-8").read())
        print("DB ready:", DB_PATH)

def get_or_create_source(c, name, kind, url=None, licence=None, published_at=None):
    r = c.execute("SELECT source_id FROM sources WHERE name=?", (name,)).fetchone()
    if r:
        c.execute("UPDATE sources SET fetched_at=datetime('now') WHERE source_id=?", (r[0],))
        return r[0]
    cur = c.execute("INSERT INTO sources(name,kind,url,licence,published_at) VALUES(?,?,?,?,?)",
                    (name, kind, url, licence, published_at))
    return cur.lastrowid

if __name__ == "__main__":
    init_db()
```

---

## `seed_skills.py`

```python
from db import get_conn

skills = [
    ("Python","technical"),("SQL","technical"),("JavaScript","technical"),
    ("Machine Learning","ai"),("Prompt Engineering","ai"),
    ("Natural Language Processing","ai"),("Data Analysis","technical"),
    ("Data Visualization","technical"),("Cloud Computing","technical"),
    ("Cybersecurity","technical"),("DevOps","technical"),("UX Design","technical"),
    ("Project Management","human"),("Communication","human"),
    ("Renewable Energy Systems","green"),
]
aliases = {"ml":"Machine Learning","nlp":"Natural Language Processing",
           "js":"JavaScript","aws":"Cloud Computing","azure":"Cloud Computing",
           "power bi":"Data Visualization","tableau":"Data Visualization",
           "ux":"UX Design","infosec":"Cybersecurity","llm":"Prompt Engineering"}

with get_conn() as c:
    c.executemany("INSERT OR IGNORE INTO skills(name, category) VALUES(?,?)", skills)
    for a, name in aliases.items():
        r = c.execute("SELECT skill_id FROM skills WHERE name=?", (name,)).fetchone()
        if r: c.execute("INSERT OR IGNORE INTO skill_aliases VALUES(?,?)", (a, r[0]))
    print("Skills in DB:", c.execute("SELECT COUNT(*) FROM skills").fetchone()[0])
```

---

## `groq_layer.py`

```python
import os, json, hashlib, time
from groq import Groq, RateLimitError
from dotenv import load_dotenv
from db import get_conn

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

def _call_json(system, user, temperature=0.0):
    for attempt in range(8):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},  # prompt MUST contain the word "JSON"
                temperature=temperature,
            )
            time.sleep(8)  # pace calls so we stay under the per-minute token limit
            return resp.choices[0].message.content
        except RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"Rate limit hit, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Groq rate limit: gave up after 8 tries")

def _log(c, purpose, prompt, out, rejected):
    cur = c.execute(
        "INSERT INTO llm_runs(purpose,model,prompt_hash,output_json,rejected_items) VALUES(?,?,?,?,?)",
        (purpose, MODEL, hashlib.md5(prompt.encode()).hexdigest(), out, json.dumps(rejected)))
    return cur.lastrowid

def extract_skills(text, purpose="skill_extraction"):
    """Free text (job post or synthetic CV) -> list of canonical skill_ids. Cannot invent skills."""
    with get_conn() as c:
        canon = {r["name"].lower(): r["skill_id"] for r in c.execute("SELECT skill_id,name FROM skills")}
        alias = {r["alias"].lower(): r["skill_id"] for r in c.execute("SELECT alias,skill_id FROM skill_aliases")}
        system = ("You extract skills from text. Respond in JSON: {\"skills\": [\"...\"]}. "
                  "ONLY use names from this allowed list, exactly as written. If none apply return an empty list.\n"
                  "ALLOWED: " + "; ".join(sorted(canon)))
        out = _call_json(system, text[:3000])
        try:
            proposed = json.loads(out).get("skills", [])
        except Exception:
            proposed = []
        ids, rejected = [], []
        for s in proposed:
            k = str(s).strip().lower()
            sid = canon.get(k) or alias.get(k)
            (ids if sid else rejected).append(sid if sid else s)  # hallucinations -> rejected + logged
        run_id = _log(c, purpose, text[:3000], out, rejected)
    return sorted(set(ids)), run_id

def tag_sdgs(kind, name, description):
    """Propose SDG links WITH a rationale; stored as mapped_by='llm' until a human reviews them."""
    system = ("Map the given occupation or skill to relevant UN SDGs. Respond in JSON: "
              "{\"links\": [{\"sdg_id\": int 1-17, \"strength\": 0-1, \"rationale\": \"one sentence\"}]}. "
              "Give at most 3 links; only include genuinely meaningful ones.")
    out = _call_json(system, f"{kind}: {name}\n{description or ''}")
    links = json.loads(out).get("links", [])
    valid = [l for l in links if isinstance(l.get("sdg_id"), int) and 1 <= l["sdg_id"] <= 17 and l.get("rationale")]
    with get_conn() as c:
        _log(c, "sdg_tagging", name, out, [l for l in links if l not in valid])
    return valid

def explain_match(match_row_breakdown, trend_facts):
    """LLM may ONLY rephrase facts we hand it (numbers + source names); no new claims."""
    system = ("Write 3 friendly sentences explaining this career match to the user. "
              "Use ONLY the facts in the JSON provided; do not add any numbers, jobs or courses. "
              "Respond in JSON: {\"text\": \"...\"}")
    out = _call_json(system, json.dumps({"breakdown": match_row_breakdown, "facts": trend_facts}), 0.3)
    return json.loads(out)["text"]
```

---

## `ingest_jobs.py`

```python
import re
import requests, json
from datetime import datetime, timedelta, timezone
from db import get_conn, get_or_create_source
from groq_layer import extract_skills

ARBEITNOW = "https://www.arbeitnow.com/api/job-board-api"  # free, no key, mostly Europe/remote

def fetch_arbeitnow(pages=3):
    with get_conn() as c:
        sid = get_or_create_source(c, "Arbeitnow Job Board API", "job_postings",
                                   "https://www.arbeitnow.com/api/job-board-api", "see site terms")
        for p in range(1, pages + 1):
            data = requests.get(ARBEITNOW, params={"page": p}, timeout=30).json().get("data", [])
            for j in data:
                posted = datetime.fromtimestamp(j["created_at"], tz=timezone.utc).date().isoformat()
                c.execute("""INSERT OR IGNORE INTO raw_postings
                    (source_id,external_ref,title,company,location,description,url,posted_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (sid, j["slug"], j["title"], j["company_name"], j["location"],
                     j["description"], j["url"], posted))

def tag_new_postings(limit=30):
    with get_conn() as c:
        rows = c.execute("SELECT posting_id,title,description FROM raw_postings WHERE processed=0 LIMIT ?", (limit,)).fetchall()
    for i, r in enumerate(rows, 1):
        clean = re.sub(r"<[^>]+>", " ", r["description"] or "")  # strip HTML tags
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
        if n_rec == 0: print("No recent postings; skip."); return
        sid = c.execute("SELECT source_id FROM sources WHERE kind='job_postings' ORDER BY fetched_at DESC").fetchone()[0]
        for s in c.execute("SELECT skill_id FROM skills").fetchall():
            q = """SELECT COUNT(*) FROM posting_skills ps JOIN raw_postings p USING(posting_id)
                   WHERE ps.skill_id=? AND p.posted_at>=? AND p.posted_at<?"""
            rec = c.execute(q, (s[0], t1, today.isoformat() + "z")).fetchone()[0]
            pri = c.execute(q, (s[0], t0, t1)).fetchone()[0]
            share_r, share_p = rec / n_rec, (pri / n_pri if n_pri else 0)
            growth = (share_r - share_p) / (share_p + 0.02)  # +0.02 smoothing so tiny counts don't explode
            c.execute("""INSERT OR REPLACE INTO trend_signals
                (skill_id,snapshot_date,window_days,postings_recent,postings_prior,demand_share,growth_rate,sample_size,source_id)
                VALUES(?,?,?,?,?,?,?,?,?)""", (s[0], today.isoformat(), window_days, rec, pri, share_r, growth, n_rec, sid))

if __name__ == "__main__":
    fetch_arbeitnow(); tag_new_postings(); compute_trends()
```

---

## `export_json.py`

```python
"""Option A (simplest): dump the latest trend snapshot to a JSON file the frontend can load.
Run: py export_json.py  -> writes ../data/trends.json
Frontend: fetch('data/trends.json').then(r => r.json())
Re-run after every ingest_jobs.py so the Radar changes when the data changes."""
import json, os, sys
from datetime import datetime, timezone
from db import get_conn

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "data", "trends.json")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

def build():
    with get_conn() as c:
        snap = c.execute("SELECT MAX(snapshot_date) FROM trend_signals").fetchone()[0]
        if not snap:
            return {"error": "No trend data yet. Run ingest_jobs.py first."}
        scen = [dict(r) for r in c.execute("SELECT name, description, demand_multiplier, automation_multiplier FROM scenarios")]
        src = c.execute("""SELECT s.name, s.url, s.fetched_at FROM sources s
                           WHERE s.kind='job_postings' ORDER BY s.fetched_at DESC LIMIT 1""").fetchone()
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
            "direction": "rising" if g > 0.15 else "declining" if g < -0.15 else "stable",
            "postings_recent": r["postings_recent"], "postings_prior": r["postings_prior"],
            "sample_size": r["sample_size"],
            "low_confidence": r["sample_size"] < 100 or r["postings_prior"] == 0,
            "scenarios": by_scen,
        })
    return {
        "snapshot_date": snap,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": dict(src) if src else None,
        "ai_model_used": MODEL,
        "disclaimer": "Trend scores are estimates from public job postings, not facts or guarantees.",
        "scenarios": scen,
        "skills": skills,
    }

if __name__ == "__main__":
    data = build()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), indent=2)
    print("Wrote", OUT, "-", len(data.get("skills", [])), "skills")
```

---

## `api.py`

```python
"""Option B: tiny Flask API over the same data.
Run: python api.py then open http://localhost:5000/api/trends
Needs: pip install flask"""
import os
from flask import Flask, jsonify
from db import get_conn
from export_json import build

app = Flask(__name__)

@app.after_request
def cors(resp):  # lets the frontend call this from another origin
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.get("/api/trends")
def trends():
    return jsonify(build())

@app.get("/api/skills")
def skills():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT skill_id, name, category FROM skills ORDER BY name")])

@app.get("/api/scenarios")
def scenarios():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT * FROM scenarios")])

@app.get("/api/sdgs")
def sdgs():
    with get_conn() as c:
        return jsonify([dict(r) for r in c.execute("SELECT sdg_id, name FROM sdgs")])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
```
