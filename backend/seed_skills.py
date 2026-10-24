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
        if r:
            c.execute("INSERT OR IGNORE INTO skill_aliases VALUES(?,?)", (a, r[0]))
    print("Skills in DB:", c.execute("SELECT COUNT(*) FROM skills").fetchone()[0])
