// js/data.js

const PRESET_PERSONAS = {
  csStudent: ['JavaScript', 'SQL', 'Web Development', 'Git', 'Node.js'],
  businessAnalyst: ['Excel', 'SQL', 'Financial Modeling', 'Risk Assessment'],
  uiDesigner: ['Figma', 'UI Design', 'User Research', 'HTML/CSS']
};

const ROLE_CATALOG = [
  {
    id: 1,
    title: "AI Integration & Workflow Engineer",
    sdg: {
      number: 8,
      label: "SDG 8: Decent Work & Economic Growth",
      color: "bg-amber-50 text-amber-800 border-amber-200"
    },
    sdgSub: "Target 8.2: Upgrade productivity through technological automation",
    baseMatch: 82,
    acceleratedMatch: 88,
    risk: "High Demand",
    riskColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
    skillsHave: ["JavaScript", "Web Development", "SQL"],
    skillsNeed: ["LLM API Orchestration", "Vector Databases", "Prompt Engineering"],
    radarData: {
      labels: ['API Integration', 'Data Modeling', 'Workflow Auto', 'ML Foundations', 'Cloud Deploy'],
      current: [85, 75, 80, 50, 60],
      target: [95, 85, 90, 85, 85]
    },
    duration: "8 - 10 Weeks (Part-Time)",
    steps: [
      {
        phase: "Step 1: Core Foundations",
        desc: "Master LLM orchestration, structured output formats, and token management.",
        res: "DeepLearning.AI / Coursera (Free)",
        time: "2 Weeks"
      },
      {
        phase: "Step 2: Applied System Architecture",
        desc: "Construct Retrieval-Augmented Generation (RAG) pipelines with ChromaDB and Node.js.",
        res: "Open Source Documentation & Labs",
        time: "4 Weeks"
      },
      {
        phase: "Step 3: Enterprise Capstone",
        desc: "Automate a live business operational workflow with human verification fail-safes.",
        res: "HRD Corp Claimable Applied AI Bootcamp",
        time: "3 Weeks"
      }
    ]
  },
  {
    id: 2,
    title: "Clean-Tech Data Analyst",
    sdg: {
      number: 7,
      label: "SDG 7: Affordable & Clean Energy",
      color: "bg-yellow-50 text-yellow-800 border-yellow-200"
    },
    sdgSub: "Target 7.3: Improve global energy efficiency and resource optimization",
    baseMatch: 68,
    acceleratedMatch: 76,
    risk: "Stable Growth",
    riskColor: "bg-blue-50 text-blue-700 border-blue-200",
    skillsHave: ["SQL"],
    skillsNeed: ["Python Fundamentals", "Energy IoT Sensors", "Predictive Modeling"],
    radarData: {
      labels: ['Data Wrangling', 'IoT Streams', 'Predictive Stats', 'Green Tech ESG', 'Dashboarding'],
      current: [70, 30, 40, 55, 65],
      target: [85, 80, 80, 90, 85]
    },
    duration: "12 - 14 Weeks (Part-Time)",
    steps: [
      {
        phase: "Step 1: Analytical Python",
        desc: "Pandas and NumPy for renewable energy and sensor dataset parsing.",
        res: "Kaggle Micro-courses (100% Free)",
        time: "3 Weeks"
      },
      {
        phase: "Step 2: Smart Grid Metrics",
        desc: "Energy load consumption forecasting and anomaly detection.",
        res: "MDEC / Coursera Renewable Analytics",
        time: "5 Weeks"
      },
      {
        phase: "Step 3: ESG Capstone Dashboard",
        desc: "Construct an interactive ESG energy performance monitor using open data.",
        res: "Open Source Malaysian Grid Repository",
        time: "4 Weeks"
      }
    ]
  },
  {
    id: 3,
    title: "Responsible AI & Ethics Evaluator",
    sdg: {
      number: 4,
      label: "SDG 4: Quality Education & Equity",
      color: "bg-rose-50 text-rose-800 border-rose-200"
    },
    sdgSub: "Target 4.4: Increase technical & vocational competence for decent careers",
    baseMatch: 60,
    acceleratedMatch: 74,
    risk: "Human-in-Loop Essential",
    riskColor: "bg-indigo-50 text-indigo-700 border-indigo-200",
    skillsHave: ["Human-Computer Interaction", "Web Development"],
    skillsNeed: ["AI Red Teaming", "Fairness Auditing", "Compliance Frameworks"],
    radarData: {
      labels: ['Safety Auditing', 'Bias Metrics', 'Policy Context', 'Prompt Injection', 'User Research'],
      current: [40, 45, 55, 60, 75],
      target: [90, 85, 80, 85, 80]
    },
    duration: "10 - 12 Weeks (Part-Time)",
    steps: [
      {
        phase: "Step 1: Bias & Safety Testing",
        desc: "Learn algorithmic fairness testing, jailbreak defense, and privacy compliance.",
        res: "Google AI Ethics / edX Free Tier",
        time: "3 Weeks"
      },
      {
        phase: "Step 2: Governance Standards",
        desc: "Study Malaysian National AI Office (NAIO) and UNESCO guidelines.",
        res: "National Policy Public Repositories",
        time: "3 Weeks"
      },
      {
        phase: "Step 3: Audit Certification",
        desc: "Conduct hands-on safety evaluations on open-weight model outputs.",
        res: "HRD Corp Digital Skills Track",
        time: "4 Weeks"
      }
    ]
  }
];