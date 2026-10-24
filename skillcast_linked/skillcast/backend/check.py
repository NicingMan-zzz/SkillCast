"""Self-check. Run:  py check.py        (add --llm to also test the RunPod call)"""
import os, sys
from dotenv import load_dotenv
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
load_dotenv(os.path.join(HERE, ".env"))
bad = 0
def line(ok, msg, fix=""):
    global bad
    print(("OK    " if ok else "FAIL  ") + msg + ("" if ok or not fix else "\n      -> " + fix))
    bad += (not ok)

line(os.path.exists(".env"), ".env file found", "Create a file named .env in THIS folder (see .env.example). Not .env.txt!")
key = os.getenv("RUNPOD_API_KEY", "")
line(bool(key) and "your_" not in key, "RUNPOD_API_KEY is set", "Put the real key in .env (never in .env.example)")
line(bool(os.getenv("RUNPOD_MODEL")), "RUNPOD_MODEL is set", "e.g. RUNPOD_MODEL=openai/gpt-oss-120b")
line(bool(os.getenv("RUNPOD_BASE_URL") or os.getenv("RUNPOD_ENDPOINT_ID")), "RUNPOD_BASE_URL or RUNPOD_ENDPOINT_ID is set",
     "e.g. RUNPOD_BASE_URL=https://api.runpod.ai/v2/gpt-oss-120b/openai/v1")
db = os.getenv("DB_PATH", "aiversecity.db")
line(os.path.exists(db), f"database file {db} found", "Run: py db.py  then  py seed_skills.py  then  py seed_demo.py")
if os.path.exists(db):
    from db import get_conn
    with get_conn() as c:
        for t in ["skills", "roles", "raw_postings", "trend_signals", "user_profiles"]:
            n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            line(n > 0, f"{t}: {n} rows", f"{t} is empty - run the seed/ingest scripts")
if "--llm" in sys.argv and bad == 0:
    from llm_layer import extract_skills
    try:
        print("LLM test:", extract_skills("Python and SQL needed"))
        line(True, "RunPod call works")
    except Exception as e:
        line(False, f"RunPod call failed: {type(e).__name__}: {str(e)[:200]}",
             "401/403 = bad key or blocked network (try phone hotspot). 404 = wrong RUNPOD_MODEL/URL.")
print("\nAll good." if bad == 0 else f"\n{bad} problem(s) above. Fix the FAIL lines, then run check.py again.")
