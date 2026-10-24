"""LLM layer on RunPod Serverless (vLLM worker, OpenAI-compatible API). Replaces groq_layer.py.
Pattern unchanged: the LLM proposes -> our code validates against the DB -> only validated items are stored."""
import os, json, hashlib, time, re
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError, APIStatusError, BadRequestError
from dotenv import load_dotenv
from db import get_conn
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "")
BASE_URL = os.getenv("RUNPOD_BASE_URL", f"https://api.runpod.ai/v2/{ENDPOINT_ID}/openai/v1")
MODEL = os.environ["RUNPOD_MODEL"]            # must match the model deployed on the endpoint (disclose it!)
client = OpenAI(api_key=os.environ["RUNPOD_API_KEY"], base_url=BASE_URL, timeout=120)  # long timeout: cold starts
_json_mode = True                              # auto-disabled if the endpoint rejects response_format

def _parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text or "", re.S)   # model wrapped JSON in extra text
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
    return {}

def _call_json(system, user, temperature=0.0):
    global _json_mode
    for attempt in range(6):
        try:
            kw = dict(model=MODEL, temperature=temperature, max_tokens=2000,
                      messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
            if _json_mode:
                kw["response_format"] = {"type": "json_object"}
            return client.chat.completions.create(**kw).choices[0].message.content or ""
        except BadRequestError:
            if _json_mode:
                _json_mode = False; print("Endpoint rejected JSON mode; continuing without it."); continue
            raise
        except (RateLimitError, APIConnectionError, APITimeoutError) as e:
            wait = 10 * (attempt + 1); print(f"{type(e).__name__}: waiting {wait}s (cold start?)..."); time.sleep(wait)
        except APIStatusError as e:
            if e.status_code >= 500:
                wait = 10 * (attempt + 1); print(f"Server {e.status_code}: waiting {wait}s..."); time.sleep(wait)
            else:
                raise
    raise RuntimeError("RunPod endpoint did not respond after 6 tries")

def _log(c, purpose, prompt, out, rejected):
    cur = c.execute("INSERT INTO llm_runs(purpose,model,prompt_hash,output_json,rejected_items) VALUES(?,?,?,?,?)",
                    (purpose, "runpod:" + MODEL, hashlib.md5(prompt.encode()).hexdigest(), out, json.dumps(rejected)))
    return cur.lastrowid

def extract_skills(text, purpose="skill_extraction"):
    """Free text -> list of canonical skill_ids. Cannot invent skills."""
    with get_conn() as c:
        canon = {r["name"].lower(): r["skill_id"] for r in c.execute("SELECT skill_id,name FROM skills")}
        alias = {r["alias"].lower(): r["skill_id"] for r in c.execute("SELECT alias,skill_id FROM skill_aliases")}
        system = ("You extract skills from text. Respond ONLY in JSON: {\"skills\": [\"...\"]}. "
                  "ONLY use names from this allowed list, exactly as written. If none apply return an empty list.\n"
                  "ALLOWED: " + "; ".join(sorted(canon)))
        out = _call_json(system, text[:3000])
        proposed = _parse_json(out).get("skills", [])
        if not isinstance(proposed, list): proposed = []
        ids, rejected = [], []
        for s in proposed:
            k = str(s).strip().lower()
            sid = canon.get(k) or alias.get(k)
            (ids if sid else rejected).append(sid if sid else s)   # hallucinations -> rejected + logged
        run_id = _log(c, purpose, text[:3000], out, rejected)
        return sorted(set(ids)), run_id

def tag_sdgs(kind, name, description):
    """Propose SDG links WITH a rationale; a human must review before mapped_by='human'."""
    system = ("Map the given occupation or skill to relevant UN SDGs. Respond ONLY in JSON: "
              "{\"links\": [{\"sdg_id\": int 1-17, \"strength\": 0-1, \"rationale\": \"one sentence\"}]}. "
              "Give at most 3 links; only include genuinely meaningful ones.")
    out = _call_json(system, f"{kind}: {name}\n{description or ''}")
    links = _parse_json(out).get("links", [])
    valid = [l for l in links if isinstance(l, dict) and isinstance(l.get("sdg_id"), int)
             and 1 <= l["sdg_id"] <= 17 and l.get("rationale")]
    with get_conn() as c:
        _log(c, "sdg_tagging", name, out, [l for l in links if l not in valid])
    return valid

def explain_match(match_row_breakdown, trend_facts):
    """LLM may ONLY rephrase facts we hand it; no new claims."""
    system = ("Write 3 friendly sentences explaining this career match to the user. "
              "Use ONLY the facts in the JSON provided; do not add any numbers, jobs or courses. "
              "Respond ONLY in JSON: {\"text\": \"...\"}")
    out = _call_json(system, json.dumps({"breakdown": match_row_breakdown, "facts": trend_facts}), 0.3)
    return _parse_json(out).get("text", "")
