// js/app.js

const AppState = {
  currentScenario: 'moderate', // 'moderate' or 'accelerated'
  selectedRoleId: null,
  activeSkills: ['Python', 'SQL', 'Communication'],
  currentTab: 'roles', // 'roles', 'radar', 'roadmap', 'audit'
  radarChartInstance: null
};

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await Backend.init();
    await recompute(true);
  } catch (e) {
    updateBotDialogue(`"Cannot reach the backend (${e.message}). Start it with run.bat, then open http://localhost:5000/"`, "Offline");
    const src = document.getElementById('signalSource');
    if (src) src.textContent = 'Backend offline';
  }
  renderSkills();
  switchTab(AppState.currentTab);
});

// Ask the backend for fresh rankings, then redraw everything that depends on them.
async function recompute(pickTop = false) {
  await Backend.refresh(AppState.activeSkills);
  if (pickTop || !ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId)) {
    AppState.selectedRoleId = ROLE_CATALOG.length ? ROLE_CATALOG[0].id : null;   // best match first
  }
  renderRoleGrid();
  await renderPathway();
  if (AppState.currentTab === 'radar') initOrUpdateRadar();
  if (AppState.currentTab === 'audit') renderAuditData();
}

function renderAll() { renderSkills(); renderRoleGrid(); renderPathway(); switchTab(AppState.currentTab); }

// ---------------------------------------------------------------------------
// Tab Navigation
// ---------------------------------------------------------------------------

function switchTab(tabName) {
  AppState.currentTab = tabName;

  const tabs = ['roles', 'radar', 'roadmap', 'audit'];
  tabs.forEach(tab => {
    const pane = document.getElementById(`pane-${tab}`);
    const btn = document.getElementById(`tab-btn-${tab}`);
    if (pane && btn) {
      if (tab === tabName) {
        pane.classList.remove('hidden');
        btn.className = "px-4 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white shadow-xs transition-all";
      } else {
        pane.classList.add('hidden');
        btn.className = "px-4 py-2 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-all";
      }
    }
  });

  if (tabName === 'radar') {
    initOrUpdateRadar();
  } else if (tabName === 'audit') {
    renderAuditData();
  }
}

// ---------------------------------------------------------------------------
// CastBot Dialogue Triggers
// ---------------------------------------------------------------------------

function updateBotDialogue(text, mood = "Analyzing...") {
  const speech = document.getElementById('botSpeechText');
  const moodEl = document.getElementById('botMood');
  if (speech) {
    speech.style.opacity = '0';
    setTimeout(() => {
      speech.innerText = text;
      speech.style.opacity = '1';
    }, 150);
  }
  if (moodEl) moodEl.innerText = mood;
}

// ---------------------------------------------------------------------------
// Skills Inventory Management (Requirement 1)
// ---------------------------------------------------------------------------

function renderSkills() {
  const container = document.getElementById('skillsInputContainer');
  const input = document.getElementById('skillInput');
  const existingBadges = container.querySelectorAll('span');
  existingBadges.forEach(b => b.remove());

  AppState.activeSkills.forEach(skill => {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = Components.createSkillBadge(skill);
    container.insertBefore(tempDiv.firstElementChild, input);
  });
}

function handleSkillAdd(e) {
  if (e.key === 'Enter' && e.target.value.trim() !== '') {
    const raw = e.target.value.trim();
    const val = Backend.resolveSkill(raw);          // canonical name or alias ("ml" -> Machine Learning)
    e.target.value = '';
    if (!val) {
      updateBotDialogue(`"'${raw}' isn't in the skill taxonomy yet. Try: ${Object.values(Backend.lookup).filter((v, i, a) => a.indexOf(v) === i).slice(0, 8).join(', ')}..."`, "Unknown skill");
      return;
    }
    if (!AppState.activeSkills.includes(val)) {
      AppState.activeSkills.push(val);
      renderSkills();
      recompute();
      updateBotDialogue(`"Added '${val}'! Match percentages and competency radar have recalibrated."`, "Skills Updated");
    }
  }
}

function removeSkill(btn) {
  const skillText = btn.parentElement.textContent.trim();
  AppState.activeSkills = AppState.activeSkills.filter(s => s !== skillText);
  btn.parentElement.remove();
  recompute();
  updateBotDialogue(`"Removed '${skillText}'. Updated transition feasibility."`, "Skills Updated");
}

async function loadPersona(key) {
  if (!PRESET_PERSONAS[key]) return;
  AppState.activeSkills = [...PRESET_PERSONAS[key]];
  renderSkills();
  await recompute(true);                              // backend ranks; best-fit role is selected
  const roleName = ROLE_CATALOG.length ? ROLE_CATALOG[0].title : '--';
  updateBotDialogue(`"Loaded persona profile! Re-ranked best-fit role: '${roleName}'. Check each tab view for details."`, "Persona Applied");
}

async function simulateResumeUpload() {
  const text = prompt('Paste CV / bio text (synthetic data only). The AI will extract skills from our skill list:');
  if (!text) return;
  const statusEl = document.getElementById('uploadStatus');
  statusEl.classList.remove('hidden');
  statusEl.innerHTML = `<span class="text-indigo-600 font-medium flex items-center gap-1.5"><i class="ph ph-spinner animate-spin"></i> Asking the AI (first call can take a minute)...</span>`;
  updateBotDialogue(`"Scanning text... extracting competencies from the approved skill list."`, "CV Scanning");
  try {
    const found = await Backend.extractSkills(text);
    found.forEach(n => { if (!AppState.activeSkills.includes(n)) AppState.activeSkills.push(n); });
    renderSkills();
    await recompute();
    statusEl.innerHTML = `<span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-semibold">${found.length} skills extracted</span>`;
  } catch (e) {
    statusEl.innerHTML = `<span class="text-red-600 text-[11px]">AI unavailable: ${e.message}</span>`;
  }
  setTimeout(() => { statusEl.classList.add('hidden'); }, 5000);
}

// ---------------------------------------------------------------------------
// Role Recommendations & Roadmap (Requirements 3, 4, 5)
// ---------------------------------------------------------------------------

function renderRoleGrid() {
  const grid = document.getElementById('rolesGrid');
  if (!grid) return;

  grid.innerHTML = ROLE_CATALOG.map(role =>
    Components.createRoleCard(role, AppState.currentScenario, role.id === AppState.selectedRoleId)   // scores come from the backend
  ).join('');
}

function selectRole(roleId) {
  AppState.selectedRoleId = roleId;
  const role = ROLE_CATALOG.find(r => r.id === roleId);
  renderRoleGrid();
  renderPathway();   // fetches the real pathway
  if (AppState.currentTab === 'radar') initOrUpdateRadar();
  if (AppState.currentTab === 'audit') renderAuditData();

  updateBotDialogue(`"Target role selected: '${role.title}'. Switch tabs to inspect the competency radar or milestone roadmap."`, "Role Selected");
}

async function renderPathway() {
  const role = ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId);
  if (!role) return;

  const titleEl = document.getElementById('pathwayTitle');
  const durEl = document.getElementById('pathwayDuration');
  const stepsContainer = document.getElementById('pathwaySteps');
  if (titleEl) titleEl.innerText = role.title;
  if (stepsContainer) stepsContainer.innerHTML = '<p class="text-xs text-slate-400">Building pathway from the course catalogue...</p>';
  try {
    await Backend.loadPathway(role, AppState.activeSkills);
  } catch (e) {
    if (stepsContainer) stepsContainer.innerHTML = `<p class="text-xs text-red-600">${e.message}</p>`;
    return;
  }
  if (durEl) durEl.innerText = role.duration;
  if (stepsContainer) {
    stepsContainer.innerHTML = role.steps.length
      ? role.steps.map((step, idx) => Components.createStepItem(step, idx)).join('')
      : '<p class="text-xs text-slate-500">No skill gaps for this role with your current skills.</p>';
  }
}

// ---------------------------------------------------------------------------
// Scenario Switcher (Requirement 6: Handling Uncertainty)
// ---------------------------------------------------------------------------

function setScenario(type) {
  AppState.currentScenario = type;
  const modBtn = document.getElementById('scenarioModBtn');
  const accBtn = document.getElementById('scenarioAccBtn');

  if (type === 'moderate') {
    modBtn.className = "px-3 py-1 text-xs rounded-md font-bold bg-indigo-600 text-white shadow-xs";
    accBtn.className = "px-3 py-1 text-xs rounded-md font-semibold text-slate-600 hover:text-slate-900";
    updateBotDialogue(`"Switched to Moderate scenario: Transition curves modeled over standard horizon."`, "Scenario: Moderate");
  } else {
    accBtn.className = "px-3 py-1 text-xs rounded-md font-bold bg-indigo-600 text-white shadow-xs";
    modBtn.className = "px-3 py-1 text-xs rounded-md font-semibold text-slate-600 hover:text-slate-900";
    updateBotDialogue(`"Accelerated disruption active: Routine workflows penalized, human-in-the-loop roles prioritized."`, "Scenario: Disruption");
  }

  Backend.setScenario(type);
  recompute();
}

// ---------------------------------------------------------------------------
// Explainable AI Audit Rendering
// ---------------------------------------------------------------------------

function renderAuditData() {
  const container = document.getElementById('auditDetailsContainer');
  const role = ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId) || ROLE_CATALOG[0];
  if (!container || !role) return;
  const t = Backend.trends || {}, a = Backend.audit || { runs: [], total_rejected: 0 };
  const sc = Backend.scenarios.find(x => x.scenario_id === Backend.scenarioId) || {};
  const models = [...new Set(a.runs.map(r => r.model))].join(', ') || 'none';
  const lowData = (t.skills || []).some(s => s.low_confidence);
  container.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-4 bg-slate-50 rounded-xl border border-slate-200">
        <span class="text-xs font-bold text-slate-700 block mb-1">Skills Covered</span>
        <div class="text-2xl font-black text-emerald-600 mb-1">${role.skillsHave.length} / ${role.breakdown.length}</div>
        <p class="text-xs text-slate-500">Required skills fully covered by your ${AppState.activeSkills.length} listed skills.</p>
      </div>
      <div class="p-4 bg-slate-50 rounded-xl border border-slate-200">
        <span class="text-xs font-bold text-slate-700 block mb-1">Scenario: ${sc.name || '--'}</span>
        <div class="text-2xl font-black text-indigo-600 mb-1">x${sc.demand_multiplier ?? '--'}</div>
        <p class="text-xs text-slate-500">AI-skill demand multiplier. Data: ${(t.source || {}).name || 'n/a'}, snapshot ${t.snapshot_date || '--'}, ${(t.skills && t.skills[0]) ? t.skills[0].sample_size : 0} tagged postings.${lowData ? ' Small sample and no earlier period yet, so growth is 0 and scores rest mainly on skill coverage.' : ''}</p>
      </div>
      <div class="p-4 bg-slate-50 rounded-xl border border-slate-200">
        <span class="text-xs font-bold text-slate-700 block mb-1">AI Guardrail Log</span>
        <div class="text-2xl font-black text-emerald-600 mb-1">${a.total_rejected} rejected</div>
        <p class="text-xs text-slate-500">Invented skills the validator dropped. Models used: ${models}. Scoring uses skills only.</p>
      </div>
    </div>

    <div class="mt-6 p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl">
      <div class="text-xs font-bold text-indigo-900">Computed Compatibility Score: ${role.baseMatch}% (${role.title})</div>
      <div class="text-xs text-indigo-700 mt-0.5">score = sum(weight x min(your level / required level, 1)) / sum(weight); weight = importance x (1 + min(growth, 1)). Estimates, not guarantees.</div>
    </div>

    <div class="mt-4 overflow-x-auto">
      <table class="w-full text-xs">
        <tr class="text-left text-slate-500"><th class="py-1">Skill</th><th>Weight</th><th>You / Need</th><th>Coverage</th></tr>
        ${role.breakdown.map(b => `<tr class="border-t border-slate-100"><td class="py-1">${b.skill}</td><td>${b.weight}</td><td>${b.have_level} / ${b.required_level}</td><td>${Math.round(b.coverage * 100)}%</td></tr>`).join('')}
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Chart.js Radar Initialization & Dynamic Refresh
// ---------------------------------------------------------------------------

function initOrUpdateRadar() {
  const canvas = document.getElementById('skillsRadarChart');
  if (!canvas) return;

  const role = ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId) || ROLE_CATALOG[0];
  const dynamicCurrentCompetency = role.radarData.current;   // your level x20, from the backend breakdown

  if (AppState.radarChartInstance) {
    AppState.radarChartInstance.destroy();
  }

  const ctx = canvas.getContext('2d');
  AppState.radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: role.radarData.labels,
      datasets: [
        {
          label: 'Your Current Competency',
          data: dynamicCurrentCompetency,
          fill: true,
          backgroundColor: 'rgba(79, 70, 229, 0.2)',
          borderColor: '#4f46e5',
          pointBackgroundColor: '#4f46e5'
        },
        {
          label: 'Market Target Benchmark',
          data: role.radarData.target,
          fill: true,
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          borderColor: '#d97706',
          pointBackgroundColor: '#d97706'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 100,
          angleLines: { color: '#e2e8f0' },
          grid: { color: '#f1f5f9' },
          pointLabels: {
            color: '#334155',
            font: { size: 11, family: 'Plus Jakarta Sans', weight: '600' }
          },
          ticks: { display: false, min: 0, max: 100 }
        }
      },
      plugins: {
        legend: {
          labels: {
            color: '#1e293b',
            font: { size: 12, family: 'Plus Jakarta Sans', weight: '600' }
          }
        }
      }
    }
  });
}