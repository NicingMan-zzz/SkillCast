"""Option B: tiny Flask API over the same data.
Run:  py api.py   then open  http://localhost:5000/api/trends
Needs:  pip install flask"""
import os
from flask import Flask, jsonify
from db import get_conn
from export_json import build

app = Flask(__name__)


@app.after_request
def cors(resp):
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
