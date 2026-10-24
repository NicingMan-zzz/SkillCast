-- Aiversecity Future-Ready Workforce: data layer (SQLite; Postgres-friendly)
PRAGMA foreign_keys = ON;

CREATE TABLE sources (
  source_id     INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('taxonomy','job_postings','report','news','course_catalog','sdg_reference','synthetic')),
  url           TEXT,
  licence       TEXT,
  published_at  TEXT,
  fetched_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE skills (
  skill_id      INTEGER PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  category      TEXT,
  external_id   TEXT,
  source_id     INTEGER REFERENCES sources(source_id)
);

CREATE TABLE skill_aliases (
  alias         TEXT PRIMARY KEY,
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id)
);

CREATE TABLE roles (
  role_id       INTEGER PRIMARY KEY,
  title         TEXT NOT NULL UNIQUE,
  description   TEXT,
  external_id   TEXT,
  is_emerging   INTEGER NOT NULL DEFAULT 0,
  automation_exposure REAL CHECK (automation_exposure BETWEEN 0 AND 1),
  source_id     INTEGER REFERENCES sources(source_id)
);

CREATE TABLE role_skills (
  role_id       INTEGER NOT NULL REFERENCES roles(role_id),
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  importance    REAL NOT NULL DEFAULT 0.5 CHECK (importance BETWEEN 0 AND 1),
  required_level INTEGER DEFAULT 3 CHECK (required_level BETWEEN 1 AND 5),
  source_id     INTEGER REFERENCES sources(source_id),
  PRIMARY KEY (role_id, skill_id)
);

CREATE TABLE raw_postings (
  posting_id    INTEGER PRIMARY KEY,
  source_id     INTEGER NOT NULL REFERENCES sources(source_id),
  external_ref  TEXT NOT NULL,
  title         TEXT,
  company       TEXT,
  location      TEXT,
  description   TEXT,
  url           TEXT,
  posted_at     TEXT,
  fetched_at    TEXT NOT NULL DEFAULT (datetime('now')),
  processed     INTEGER NOT NULL DEFAULT 0,
  UNIQUE (source_id, external_ref)
);

CREATE TABLE posting_skills (
  posting_id    INTEGER NOT NULL REFERENCES raw_postings(posting_id),
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  llm_run_id    INTEGER REFERENCES llm_runs(run_id),
  PRIMARY KEY (posting_id, skill_id)
);

CREATE TABLE trend_signals (
  signal_id     INTEGER PRIMARY KEY,
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  snapshot_date TEXT NOT NULL,
  window_days   INTEGER NOT NULL DEFAULT 30,
  postings_recent INTEGER NOT NULL,
  postings_prior  INTEGER NOT NULL,
  demand_share  REAL NOT NULL,
  growth_rate   REAL NOT NULL,
  sample_size   INTEGER NOT NULL,
  source_id     INTEGER REFERENCES sources(source_id),
  UNIQUE (skill_id, snapshot_date)
);

CREATE TABLE external_outlook (
  outlook_id    INTEGER PRIMARY KEY,
  subject_type  TEXT NOT NULL CHECK (subject_type IN ('skill','role')),
  subject_id    INTEGER NOT NULL,
  direction     TEXT NOT NULL CHECK (direction IN ('growing','declining','stable')),
  magnitude     REAL,
  horizon_year  INTEGER,
  quote_or_page TEXT,
  source_id     INTEGER NOT NULL REFERENCES sources(source_id)
);

CREATE TABLE scenarios (
  scenario_id   INTEGER PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  description   TEXT,
  demand_multiplier     REAL NOT NULL,
  automation_multiplier REAL NOT NULL,
  is_estimate   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE role_outlook (
  role_id       INTEGER NOT NULL REFERENCES roles(role_id),
  scenario_id   INTEGER NOT NULL REFERENCES scenarios(scenario_id),
  snapshot_date TEXT NOT NULL,
  outlook_score REAL NOT NULL,
  ci_low        REAL, ci_high REAL,
  PRIMARY KEY (role_id, scenario_id, snapshot_date)
);

CREATE TABLE sdgs (
  sdg_id        INTEGER PRIMARY KEY CHECK (sdg_id BETWEEN 1 AND 17),
  name          TEXT NOT NULL,
  colour        TEXT
);

CREATE TABLE role_sdg (
  role_id       INTEGER NOT NULL REFERENCES roles(role_id),
  sdg_id        INTEGER NOT NULL REFERENCES sdgs(sdg_id),
  target_code   TEXT,
  strength      REAL NOT NULL DEFAULT 0.5,
  rationale     TEXT NOT NULL,
  mapped_by     TEXT NOT NULL CHECK (mapped_by IN ('human','llm_reviewed','llm')),
  PRIMARY KEY (role_id, sdg_id, target_code)
);

CREATE TABLE skill_sdg (
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  sdg_id        INTEGER NOT NULL REFERENCES sdgs(sdg_id),
  strength      REAL NOT NULL DEFAULT 0.5,
  rationale     TEXT NOT NULL,
  mapped_by     TEXT NOT NULL CHECK (mapped_by IN ('human','llm_reviewed','llm')),
  PRIMARY KEY (skill_id, sdg_id)
);

CREATE TABLE courses (
  course_id     INTEGER PRIMARY KEY,
  title         TEXT NOT NULL,
  provider      TEXT NOT NULL,
  url           TEXT NOT NULL,
  cost_myr      REAL DEFAULT 0,
  hours         REAL,
  level         TEXT CHECK (level IN ('beginner','intermediate','advanced')),
  language      TEXT DEFAULT 'en',
  hrdcorp_claimable INTEGER DEFAULT 0,
  verified_at   TEXT,
  source_id     INTEGER REFERENCES sources(source_id)
);

CREATE TABLE course_skills (
  course_id     INTEGER NOT NULL REFERENCES courses(course_id),
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  level_gained  INTEGER DEFAULT 2,
  PRIMARY KEY (course_id, skill_id)
);

CREATE TABLE user_profiles (
  user_id       INTEGER PRIMARY KEY,
  display_name  TEXT NOT NULL,
  persona       TEXT,
  current_role  TEXT,
  years_exp     REAL,
  interests     TEXT,
  hours_per_week REAL DEFAULT 5,
  is_synthetic  INTEGER NOT NULL DEFAULT 1 CHECK (is_synthetic = 1)
);

CREATE TABLE user_skills (
  user_id       INTEGER NOT NULL REFERENCES user_profiles(user_id),
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  level         INTEGER NOT NULL DEFAULT 2 CHECK (level BETWEEN 1 AND 5),
  origin        TEXT DEFAULT 'form' CHECK (origin IN ('form','cv_extracted','inferred')),
  PRIMARY KEY (user_id, skill_id)
);

CREATE TABLE matches (
  match_id      INTEGER PRIMARY KEY,
  user_id       INTEGER NOT NULL REFERENCES user_profiles(user_id),
  role_id       INTEGER NOT NULL REFERENCES roles(role_id),
  scenario_id   INTEGER NOT NULL REFERENCES scenarios(scenario_id),
  match_score   REAL NOT NULL,
  breakdown_json TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE pathways (
  pathway_id    INTEGER PRIMARY KEY,
  match_id      INTEGER NOT NULL REFERENCES matches(match_id),
  total_hours   REAL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE pathway_steps (
  pathway_id    INTEGER NOT NULL REFERENCES pathways(pathway_id),
  step_no       INTEGER NOT NULL,
  skill_id      INTEGER NOT NULL REFERENCES skills(skill_id),
  course_id     INTEGER REFERENCES courses(course_id),
  est_hours     REAL,
  why           TEXT,
  PRIMARY KEY (pathway_id, step_no)
);

CREATE TABLE llm_runs (
  run_id        INTEGER PRIMARY KEY,
  purpose       TEXT NOT NULL,
  model         TEXT NOT NULL,
  prompt_hash   TEXT,
  output_json   TEXT,
  rejected_items TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_postings_posted ON raw_postings(posted_at);
CREATE INDEX idx_trend_skill ON trend_signals(skill_id, snapshot_date);
CREATE INDEX idx_roleskills_skill ON role_skills(skill_id);
