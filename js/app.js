// js/app.js

const AppState = {
  currentScenario: 'moderate', // 'moderate' or 'accelerated'
  selectedRoleId: 1,
  activeSkills: ['JavaScript', 'SQL', 'Web Development'],
  radarChartInstance: null
};

document.addEventListener('DOMContentLoaded', () => {
  renderAll();
});

function renderAll() {
  renderSkills();
  renderRoleGrid();
  renderPathway();
  initOrUpdateRadar();
}

// Requirement 1: Skills Management
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
    const val = e.target.value.trim();
    if (!AppState.activeSkills.includes(val)) {
      AppState.activeSkills.push(val);
      renderSkills();
    }
    e.target.value = '';
  }
}

function removeSkill(btn) {
  const skillText = btn.parentElement.textContent.trim();
  AppState.activeSkills = AppState.activeSkills.filter(s => s !== skillText);
  btn.parentElement.remove();
}

function loadPersona(key) {
  if (PRESET_PERSONAS[key]) {
    AppState.activeSkills = [...PRESET_PERSONAS[key]];
    renderSkills();
    renderRoleGrid();
    initOrUpdateRadar();
  }
}

// Simulated Resume Parser with light feedback
function simulateResumeUpload() {
  const statusEl = document.getElementById('uploadStatus');
  statusEl.classList.remove('hidden');
  statusEl.innerHTML = `<span class="text-indigo-600 font-medium flex items-center gap-1.5"><i class="ph ph-spinner animate-spin"></i> Parsing CV structure & skills...</span>`;

  setTimeout(() => {
    loadPersona('csStudent');
    statusEl.innerHTML = `<span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1.5"><i class="ph ph-check-circle text-emerald-600"></i> Successfully parsed 5 verified skills from CV</span>`;
    setTimeout(() => {
      statusEl.classList.add('hidden');
    }, 4000);
  }, 1200);
}

// Requirement 3 & 5: Role Grid
function renderRoleGrid() {
  const grid = document.getElementById('rolesGrid');
  grid.innerHTML = ROLE_CATALOG.map(role => 
    Components.createRoleCard(role, AppState.currentScenario, role.id === AppState.selectedRoleId)
  ).join('');
}

function selectRole(roleId) {
  AppState.selectedRoleId = roleId;
  renderRoleGrid();
  renderPathway();
  initOrUpdateRadar();
  document.getElementById('pathwaySection').scrollIntoView({ behavior: 'smooth' });
}

// Requirement 4: Pathway Roadmap
function renderPathway() {
  const role = ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId);
  if (!role) return;

  document.getElementById('pathwayTitle').innerText = role.title;
  document.getElementById('pathwayDuration').innerText = role.duration;

  const stepsContainer = document.getElementById('pathwaySteps');
  stepsContainer.innerHTML = role.steps.map((step, idx) => 
    Components.createStepItem(step, idx)
  ).join('');
}

// Requirement 6: Handling Uncertainty & Scenario Switcher
function setScenario(type) {
  AppState.currentScenario = type;
  const modBtn = document.getElementById('scenarioModBtn');
  const accBtn = document.getElementById('scenarioAccBtn');
  const label = document.getElementById('currentScenarioLabel');

  if (type === 'moderate') {
    modBtn.className = "px-3 py-1.5 text-xs rounded-lg font-semibold transition-all bg-indigo-600 text-white shadow-sm";
    accBtn.className = "px-3 py-1.5 text-xs rounded-lg font-semibold transition-all text-slate-600 hover:text-slate-900";
    label.innerText = "Moderate AI Progression (Standard Horizon)";
    label.className = "font-semibold text-emerald-700";
  } else {
    accBtn.className = "px-3 py-1.5 text-xs rounded-lg font-semibold transition-all bg-indigo-600 text-white shadow-sm";
    modBtn.className = "px-3 py-1.5 text-xs rounded-lg font-semibold transition-all text-slate-600 hover:text-slate-900";
    label.innerText = "Accelerated Disruption (Aggressive Disruption Multiplier)";
    label.className = "font-semibold text-amber-700";
  }

  renderRoleGrid();
  initOrUpdateRadar();
}

// Light-themed Radar Chart (High contrast)
function initOrUpdateRadar() {
  const canvas = document.getElementById('skillsRadarChart');
  if (!canvas) return;

  const role = ROLE_CATALOG.find(r => r.id === AppState.selectedRoleId) || ROLE_CATALOG[0];

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
          label: 'Current Capability',
          data: role.radarData.current,
          fill: true,
          backgroundColor: 'rgba(79, 70, 229, 0.15)',
          borderColor: '#4f46e5',
          pointBackgroundColor: '#4f46e5',
          pointBorderColor: '#ffffff',
          pointHoverBackgroundColor: '#ffffff',
          pointHoverBorderColor: '#4f46e5'
        },
        {
          label: 'Role Requirement',
          data: role.radarData.target,
          fill: true,
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          borderColor: '#d97706',
          pointBackgroundColor: '#d97706',
          pointBorderColor: '#ffffff',
          pointHoverBackgroundColor: '#ffffff',
          pointHoverBorderColor: '#d97706'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: '#e2e8f0' },
          grid: { color: '#f1f5f9' },
          pointLabels: {
            color: '#475569',
            font: { size: 11, family: 'Plus Jakarta Sans', weight: '600' }
          },
          ticks: { display: false, min: 0, max: 100 }
        }
      },
      plugins: {
        legend: {
          labels: {
            color: '#1e293b',
            font: { size: 12, family: 'Plus Jakarta Sans', weight: '500' }
          }
        }
      }
    }
  });
}