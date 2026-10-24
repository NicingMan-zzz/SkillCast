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
                response_format={"type": "json_object"},
                temperature=temperature,
            )
            time.sleep(8)
            return resp.choices[0].message.content
        except RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"Rate limit hit, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Groq rate limit: gave up after 8 tries")


def _log(c, purpose, prompt, out, rejected):
    cur = c.execute(
        "INSERT INTO llm_runs(purpose,model,prompt_hash,output_json,rejected_items) VALUES(?,?,?,?,?)",
        (purpose, MODEL, hashlib.md5(prompt.encode()).hexdigest(), out, json.dumps(rejected)),
    )
    return cur.lastrowid


def extract_skills(text, purpose="skill_extraction"):
    """Free text (job post or synthetic CV) -> list of canonical skill_ids. Cannot invent skills."""
    with get_conn() as c:
        canon = {r["name"].lower(): r["skill_id"] for r in c.execute("SELECT skill_id,name FROM skills")}
        alias = {r["alias"].lower(): r["skill_id"] for r in c.execute("SELECT alias,skill_id FROM skill_aliases")}
        system = (
            "You extract skills from text. Respond in JSON: {\"skills\": [\"...\"]}. "
            "ONLY use names from this allowed list, exactly as written. If none apply return an empty list.\n"
            "ALLOWED: " + "; ".join(sorted(canon))
        )
        out = _call_json(system, text[:3000])
        try:
            proposed = json.loads(out).get("skills", [])
        except Exception:
            proposed = []
        ids, rejected = [], []
        for s in proposed:
            k = str(s).strip().lower()
            sid = canon.get(k) or alias.get(k)
            (ids if sid else rejected).append(sid if sid else s)
        run_id = _log(c, purpose, text[:3000], out, rejected)
        return sorted(set(ids)), run_id


def tag_sdgs(kind, name, description):
    """Propose SDG links WITH a rationale; stored as mapped_by='llm' until a human reviews them."""
    system = (
        "Map the given occupation or skill to relevant UN SDGs. Respond in JSON: "
        "{\"links\": [{\"sdg_id\": int 1-17, \"strength\": 0-1, \"rationale\": \"one sentence\"}]}. "
        "Give at most 3 links; only include genuinely meaningful ones."
    )
    out = _call_json(system, f"{kind}: {name}\n{description or ''}")
    links = json.loads(out).get("links", [])
    valid = [l for l in links if isinstance(l.get("sdg_id"), int) and 1 <= l["sdg_id"] <= 17 and l.get("rationale")]
    with get_conn() as c:
        _log(c, "sdg_tagging", name, out, [l for l in links if l not in valid])
    return valid


def explain_match(match_row_breakdown, trend_facts):
    """LLM may ONLY rephrase facts we hand it (numbers + source names); no new claims."""
    system = (
        "Write 3 friendly sentences explaining this career match to the user. "
        "Use ONLY the facts in the JSON provided; do not add any numbers, jobs or courses. "
        "Respond in JSON: {\"text\": \"...\"}"
    )
    out = _call_json(system, json.dumps({"breakdown": match_row_breakdown, "facts": trend_facts}), 0.3)
    return json.loads(out)["text"]
