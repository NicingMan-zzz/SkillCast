"""Seed roles, role->skill weights, role->SDG links, SYNTHETIC users and a starter course catalogue.
Run after seed_skills.py:   py seed_demo.py     (safe to re-run)
Roles/weights are TEAM-CURATED demo data (source kind 'synthetic'), not official statistics.
automation_exposure stays NULL on purpose: fill it only from a cited study.
COURSES: links are real public pages but verified_at is left NULL until a human clicks each one."""
from db import get_conn, get_or_create_source

ROLES = {
 "Data Analyst": ("Turns data into decisions with queries, analysis and dashboards.", 0,
   [("SQL",.9,3),("Python",.7,3),("Data Analysis",1.0,4),("Data Visualization",.8,3),("Communication",.5,3)],
   [(8,"8.2",.5,"Better data use helps organisations raise productivity through technology and innovation.")]),
 "Machine Learning Engineer": ("Builds and deploys machine-learning systems.", 1,
   [("Python",1.0,4),("Machine Learning",1.0,4),("Cloud Computing",.7,3),("SQL",.5,3),("Natural Language Processing",.4,3)],
   [(9,"9.5",.7,"Upgrades the technological capability of industry through applied AI research and engineering.")]),
 "AI Workflow Specialist": ("Designs prompts and AI-assisted workflows for teams.", 1,
   [("Prompt Engineering",1.0,4),("Natural Language Processing",.6,3),("Communication",.7,3),("Python",.4,2),("Project Management",.4,3)],
   [(8,"8.2",.7,"Raises team productivity by adopting AI tools responsibly."),
    (4,"4.4",.4,"Helps colleagues build the AI skills needed for decent work.")]),
 "Cloud / DevOps Engineer": ("Runs reliable, scalable cloud infrastructure.", 0,
   [("Cloud Computing",1.0,4),("DevOps",1.0,4),("Python",.6,3),("Cybersecurity",.5,3)],
   [(9,"9.1",.6,"Supports resilient digital infrastructure.")]),
 "Cybersecurity Analyst": ("Protects systems and data from threats.", 0,
   [("Cybersecurity",1.0,4),("Cloud Computing",.5,3),("Python",.4,2),("Communication",.4,3)],
   [(9,"9.1",.5,"Keeps digital infrastructure trustworthy and resilient.")]),
 "Renewable Energy Analyst": ("Analyses and plans clean-energy projects.", 1,
   [("Renewable Energy Systems",1.0,4),("Data Analysis",.8,3),("Project Management",.6,3),("Communication",.4,3)],
   [(7,"7.2",.9,"Directly expands the share of renewable energy."),
    (13,"13.2",.6,"Supports climate-mitigation planning.")]),
 "AI-Enabled Learning Coordinator": ("Plans and supports reskilling programmes using AI tools.", 1,
   [("Communication",1.0,4),("Project Management",.7,3),("Prompt Engineering",.6,3),("Data Analysis",.4,2)],
   [(4,"4.4",.9,"Helps adults gain skills relevant to decent work."),
    (8,"8.5",.5,"Supports productive employment through reskilling.")]),
}
USERS = [
 ("Aina (synthetic)", "Customer-service executive facing automation", "Customer Service Executive", 6, 6,
   {"Communication":4,"Project Management":2,"Data Analysis":1}),
 ("Daniel (synthetic)", "Fresh graduate exploring tech roles", "Fresh graduate", 0, 10,
   {"Python":3,"SQL":2,"JavaScript":2,"Communication":3}),
]
# (title, provider, url, cost_myr, hours, level, hrdcorp, [(skill, level_gained)])  -- hours are provider-advertised approximations
COURSES = [
 ("Intro to SQL", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-sql", 0, 4, "beginner", 0, [("SQL", 3)]),
 ("Advanced SQL", "Kaggle Learn", "https://www.kaggle.com/learn/advanced-sql", 0, 4, "intermediate", 0, [("SQL", 4)]),
 ("Python", "Kaggle Learn", "https://www.kaggle.com/learn/python", 0, 5, "beginner", 0, [("Python", 3)]),
 ("Pandas", "Kaggle Learn", "https://www.kaggle.com/learn/pandas", 0, 4, "beginner", 0, [("Data Analysis", 3)]),
 ("Data Visualization", "Kaggle Learn", "https://www.kaggle.com/learn/data-visualization", 0, 4, "beginner", 0, [("Data Visualization", 3)]),
 ("Intro to Machine Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-machine-learning", 0, 3, "beginner", 0, [("Machine Learning", 3)]),
 ("Natural Language Processing", "Kaggle Learn", "https://www.kaggle.com/learn/natural-language-processing", 0, 4, "intermediate", 0, [("Natural Language Processing", 3)]),
 ("ChatGPT Prompt Engineering for Developers", "DeepLearning.AI", "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/", 0, 1.5, "beginner", 0, [("Prompt Engineering", 3)]),
]

with get_conn() as c:
    src = get_or_create_source(c, "Team-curated demo catalogue", "synthetic")
    sk = {r["name"]: r["skill_id"] for r in c.execute("SELECT skill_id,name FROM skills")}
    for title, (desc, emerging, skills, sdgs) in ROLES.items():
        c.execute("INSERT OR IGNORE INTO roles(title,description,is_emerging,source_id) VALUES(?,?,?,?)", (title, desc, emerging, src))
        rid = c.execute("SELECT role_id FROM roles WHERE title=?", (title,)).fetchone()[0]
        for name, imp, lvl in skills:
            c.execute("INSERT OR REPLACE INTO role_skills(role_id,skill_id,importance,required_level,source_id) VALUES(?,?,?,?,?)",
                      (rid, sk[name], imp, lvl, src))
        for sdg, tgt, strength, why in sdgs:
            c.execute("INSERT OR REPLACE INTO role_sdg(role_id,sdg_id,target_code,strength,rationale,mapped_by) VALUES(?,?,?,?,?,'human')",
                      (rid, sdg, tgt, strength, why))
    for name, persona, cur, yrs, hrs, skills in USERS:
        if not c.execute("SELECT 1 FROM user_profiles WHERE display_name=?", (name,)).fetchone():
            uid = c.execute("INSERT INTO user_profiles(display_name,persona,current_role,years_exp,hours_per_week) VALUES(?,?,?,?,?)",
                            (name, persona, cur, yrs, hrs)).lastrowid
            for s, lvl in skills.items():
                c.execute("INSERT INTO user_skills(user_id,skill_id,level) VALUES(?,?,?)", (uid, sk[s], lvl))
    for title, prov, url, cost, hrs, lvl, hrd, skills in COURSES:
        if not c.execute("SELECT 1 FROM courses WHERE url=?", (url,)).fetchone():
            cid = c.execute("INSERT INTO courses(title,provider,url,cost_myr,hours,level,hrdcorp_claimable,verified_at,source_id) VALUES(?,?,?,?,?,?,?,NULL,?)",
                            (title, prov, url, cost, hrs, lvl, hrd, src)).lastrowid
            for s, g in skills:
                c.execute("INSERT INTO course_skills VALUES(?,?,?)", (cid, sk[s], g))
    n = lambda t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print("roles:", n("roles"), "| role_skills:", n("role_skills"), "| role_sdg:", n("role_sdg"),
          "| users:", n("user_profiles"), "| courses:", n("courses"))
