import os, sqlite3
from dotenv import load_dotenv
HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))
_p = os.getenv("DB_PATH", "aiversecity.db")
DB_PATH = _p if os.path.isabs(_p) else os.path.join(HERE, _p)   # always next to the code, whatever the cwd

def get_conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

def init_db():
    with get_conn() as c:
        exists = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources'").fetchone()
        if exists:
            print("DB already set up:", DB_PATH); return
        c.executescript(open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read())
        c.executescript(open(os.path.join(HERE, "seed_sdgs.sql"), encoding="utf-8").read())
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
