# Skillcast
 
> Skillcast tracks live AI and job-market trend data to forecast which skills will rise or fade, matches working adults and career switchers to future-ready roles, and builds a personalised reskilling pathway linked to the UN SDGs.
 
**Tagline:** *Forecast the skills. Plan the pivot. Power the SDGs.*
 
---
 
## Team Information
 
| Field                  | Details                                                    |
| ---------------------- | ---------------------------------------------------------- |
| **Team Name**          | Ctrl+Alt+Three                                             |
| **Team Domain**        | Domain 1 — The Aiversecity Future-Ready Workforce Domain   |
| **SDG Track (1–17)**   | SDG 4 — Quality Education (also SDG 5, 8, 9, 10)           |
| **Team Leader**        | QISTINA                                                    |
| **University**         | NATIONAL DEFENCE UNIVERSITY OF MALAYSIA                    |
| **Number of Members**  | 3                                                          |
 
## Links
 
| Resource          | Link                                                 |
| ----------------- | ---------------------------------------------------- |
| GitHub Repository | https://github.com/NicingMan-zzz/skillcast           |
| Replit Project    | https://replit.com/NicingMan-zzz/skillcast           |
| Live Demo         | https://Skillcast.replit.app                         |
| RunPod Endpoint   | https://api.runpod.ai/v2/[your-endpoint-id]          |
| Slide Deck        | [ADD LINK]                                           |
| Demo Video        | [ADD LINK]                                           |
 
---
 
## Overview
 
### Problem
 
AI is changing which jobs exist faster than training programmes and skills frameworks can be updated. In Malaysia, 56% of professionals already use AI tools at work, yet only 26% have received formal training (Hays Asia Salary Guide 2025), and the Ministry of Science, Technology and Innovation has said more than 600,000 workers will need reskilling within three to five years. Workers don't know which skills to learn, employers can't tell which roles to train their people for, and learning pathways are usually static lists that are out of date by the time they are published. A one-time skills assessment isn't enough, because AI progress is unpredictable.
 
**Our focus user:** [PICK ONE, e.g. mid-career admin and customer-service workers in Malaysia whose tasks are increasingly automated, deciding what to learn next].
 
### Solution
 
Skillcast is a decision-support web app that takes a user from "who I am today" to "where I can be in the AI era". Instead of "upload a CV and ask a chatbot for jobs", Skillcast works as a pipeline:
 
1. **Trend signals → skill forecasts.** An updatable signal layer ingests public AI and job-market sources and turns them into a rising/declining score for each skill, with the source and date shown.
2. **Scenarios, not one prediction.** Every forecast is computed under at least two futures (moderate vs fast AI disruption), so users see a range and are told clearly that predictions are estimates.
3. **Explainable matching.** The user's skills are compared to future roles, producing a match score and a skills-gap breakdown that shows exactly why a role ranked where it did.
4. **Personalised pathway.** Each gap becomes an ordered learning plan with estimated time, using free or low-cost resources.
5. **SDG-aware choices.** Every role and skill is tagged to at least one SDG, and the user can see how a career path contributes to the goals and use that as a ranking factor.
Skillcast **supports** human career decisions. It does not make hiring decisions or replace human judgement.
 
### Key Features
 
These map to the six must-have features in the Domain 1 brief.
 
| # | Must-have feature | How Skillcast delivers it |
| - | ----------------- | ------------------------- |
| 1 | **Skills profile intake** | Short questionnaire/form for skills, experience and interests. Demo uses synthetic sample profiles only. |
| 2 | **AI-trend signal layer** | Fetches at least one updatable public source (e.g. job-posting datasets, research or news feeds) and stores each signal with its source name and retrieval date. Re-running the fetch changes the radar. |
| 3 | **Future-role matching** | Ranks roles with a transparent score (skill overlap weighted by skill demand trend) and lists missing skills. |
| 4 | **Personalised reskilling pathway** | Ordered steps with estimated hours/weeks, drawn from a curated list of free/low-cost courses and HRD Corp-claimable programmes, each with a source link. |
| 5 | **SDG mapping** | Each role and skill is tagged to one or more SDGs; the pathway view shows the user's SDG contribution. |
| 6 | **Handling uncertainty** | Moderate vs fast disruption scenarios side by side, with ranges and an "estimates, not facts" notice. |
 
### Guardrails (per the Domain 1 rules)
 
- **Data:** public, open or synthetic data only. No real personal data or real CVs.
- **No invented content:** the system never invents jobs, courses or statistics. Every recommendation cites a source, and roles/courses come from a fixed, sourced catalogue.
- **LLM disclosure:** [STATE WHICH LANGUAGE MODEL YOU USE, or "No language model is used"]. If used, it only explains or summarises catalogue results; it does not generate new jobs, courses or numbers.
- **Human-centred:** recommendations are suggestions. The user makes the final decision.
### Tech Stack
 
| Layer         | Technology                                                              |
| ------------- | ----------------------------------------------------------------------- |
| Frontend      | [e.g. HTML + JavaScript / React]                                        |
| Backend       | [e.g. Python, FastAPI or Flask]                                         |
| Database      | SQLite (22 tables), Python sqlite3                                      |
| Data sources  | Arbeitnow public job API (live, dated trend feed) + synthetic profiles  |
| AI / Compute  | Groq API, openai/gpt-oss-20b for skill extraction                       |
| Hosting / Dev | Replit                                                                  |
 
> Fill in the exact libraries, datasets and licences you end up using, and keep them consistent with `submission/SDC2026_[TeamName]_TechDeclaration.pdf`.
 
---
 
## Project Structure
 
```
.
├── docs/                    # Screenshots, diagrams
├── runpod/
│   └── handler.py           # RunPod serverless handler (GPU workload)
├── src/
│   ├── main.py              # Application entry point
│   └── utils.py             # Helper functions
├── submission/              # Required submission documents
│   ├── SDC2026_TeamName_Preliminary.pdf      # Preliminary submission
│   ├── SDC2026_TeamName_TechDeclaration.pdf  # Technology declaration
│   ├── SDC2026_TeamName_Replit_POU.pdf       # Replit proof of use
│   └── SDC2026_TeamName_Runpod_POU.pdf       # RunPod proof of use
├── tests/
│   └── test_utils.py        # Unit tests
├── .env.example             # Example environment variables
├── .gitignore
├── .replit                  # Replit run configuration
├── LICENSE
├── requirements.txt         # Python dependencies
└── README.md
```
 
### Architecture
 
```
Public trend sources ──► Signal layer (fetch + date-stamp) ──► Skill forecast (moderate / fast scenarios)
                                                                      │
User profile ──► Replit App / API ──► Role matching + skills gap ◄────┘
                      │                       │
                      │                       └──► Reskilling pathway + SDG mapping
                      │
                      └──► RunPod Endpoint (GPU model) ──► Response returned to user
```
 
---
 
## How to Run
 
### Option 1 — Run on Replit (Recommended)
 
1. Open the [Replit Project](https://replit.com/@your-username/skillcast), or import this repository via **Create Repl → Import from GitHub**.
2. Open the **Secrets** tab (🔒) and add the variables listed in `.env.example`:
   - `RUNPOD_API_KEY`
   - `RUNPOD_ENDPOINT_ID`
3. Click **Run**. Replit uses the `.replit` file to start `python src/main.py`.
### Option 2 — Run Locally
 
```bash
# 1. Clone the repository
git clone https://github.com/your-username/skillcast.git
cd skillcast
 
# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
 
# 3. Install dependencies
pip install -r requirements.txt
 
# 4. Configure environment variables
cp .env.example .env            # then fill in your values
 
# 5. Run the app
python src/main.py
```
 
### Run Tests
 
```bash
python -m unittest discover tests
```
 
---
 
## How We Use Replit *(Required)*
 
- **Development:** [Describe, e.g. collaborative coding in a shared Repl using Multiplayer.]
- **Hosting:** The app is deployed with Replit Deployments at the Live Demo link above.
- **Secrets:** API keys are stored in Replit Secrets, never in the code.
📄 Proof of use: [`submission/SDC2026_TeamName_Replit_POU.pdf`](submission/SDC2026_TeamName_Replit_POU.pdf)
 
## How We Use RunPod *(Required)*
 
- **Workload:** [Describe, e.g. embedding-based skill similarity / LLM explanation of match results] runs on a RunPod GPU.
- **Setup:** `runpod/handler.py` is deployed as a **RunPod Serverless Endpoint**.
- **Integration:** The Replit app sends requests to the endpoint using `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`.
Example request:
 
```bash
curl -X POST https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello"}}'
```
 
📄 Proof of use: [`submission/SDC2026_TeamName_Runpod_POU.pdf`](submission/SDC2026_TeamName_Runpod_POU.pdf)
 
---
 
## Challenges & Learnings
 
**Hardest risks and our fallbacks**
 
| Risk | Plan / fallback |
| ---- | --------------- |
| Reliable, updatable trend data | Use more than one public source. If a live fetch fails, fall back to the last cached snapshot and show its date, so the user always knows how fresh the data is. |
| Matching quality | Start with a transparent skill-overlap score weighted by trend, test against synthetic profiles, and only add embeddings if they measurably improve results. |
| AI inventing jobs or courses | Roles and courses come only from a sourced catalogue. The language model (if used) may explain results but cannot add new items or numbers. |
| Scenario forecasts look more certain than they are | Always show a range across scenarios, label outputs as estimates, and cite the data behind each score. |
 
**Learnings:** [Add what your team learned while building.]
 
## Future Improvements
 
- [ ] Employer / HR view: team-level skills-gap heatmap and reskilling plan
- [ ] Automatic re-planning when new trend data changes recommendations
- [ ] Multi-language support (English, Bahasa Malaysia, Chinese) and a low-bandwidth mobile experience
- [ ] Progress tracking and skill badges
- [ ] Fairness checks so recommendations don't discriminate by age, gender or background
- [ ] SDG contribution view aggregated for a person, company or region
## Team
 
| Name        | Role                | GitHub                                             |
| ----------- | ------------------- | ---------------------------------------------------|
| Qis         | Team Lead / Frontend| [@syxe7](https://github.com/syxe7)                 |
| Josh        | Backend             | [@Joshify](https://github.com/Joshify79)           |
| Al          | AI / RunPod         | [@NicingMan-zzz](https://github.com/nicingman-zzz) |
 
---
 
## Submission Checklist
 
- [ ] Team name, domain (Domain 1) and SDG track filled in
- [ ] Slide deck link added
- [ ] Demo video link added
- [ ] Replit used, with proof of use in `submission/`
- [ ] RunPod used, with proof of use in `submission/`
- [ ] Preliminary submission completed (`SDC2026_TeamName_Preliminary.pdf`)
- [ ] Technology declaration completed (`SDC2026_TeamName_TechDeclaration.pdf`)
- [ ] Submission files renamed with your team name (replace `TeamName`)
- [ ] "How to Run" steps verified
- [ ] No API keys or secrets committed to the repository
## License
 
This project is licensed under the [Apache License 2.0](LICENSE).
