// js/components.js

const Components = {
  // Requirement 1: Clear, readable skill badge
  createSkillBadge(name) {
    return `
      <span class="bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-2 shadow-sm transition-all hover:bg-indigo-100">
        ${name} 
        <button onclick="removeSkill(this)" class="text-indigo-400 hover:text-red-500 focus:outline-none">
          <i class="ph ph-x font-bold"></i>
        </button>
      </span>
    `;
  },

  // Requirements 3, 5, 6: Future Role Card with generous spacing
  createRoleCard(role, currentScenario, isSelected) {
    const matchScore = currentScenario === 'moderate' ? role.baseMatch : role.acceleratedMatch;
    const selectedClass = isSelected ? 'card-selected' : 'saas-card';

    return `
      <div class="rounded-2xl p-6 transition-all cursor-pointer flex flex-col justify-between ${selectedClass}" onclick="selectRole(${role.id})">
        <div>
          <!-- Header Tags: SDG & Stability/Risk -->
          <div class="flex items-center justify-between gap-2 mb-4">
            <span class="text-xs font-semibold px-2.5 py-1 rounded-md border ${role.sdg.color}">
              ${role.sdg.label}
            </span>
            <span class="text-xs font-medium px-2 py-0.5 rounded-md border ${role.riskColor}">
              ${role.risk}
            </span>
          </div>

          <h4 class="text-lg font-bold text-slate-900 mb-1 leading-snug">${role.title}</h4>
          <p class="text-xs text-slate-500 mb-5">${role.sdgSub}</p>

          <!-- Match Score Bar -->
          <div class="mb-5 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs font-semibold text-slate-600">Match Compatibility</span>
              <span class="text-base font-bold text-indigo-600">${matchScore}%</span>
            </div>
            <div class="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
              <div class="bg-indigo-600 h-2.5 rounded-full transition-all duration-500" style="width: ${matchScore}%"></div>
            </div>
          </div>

          <!-- Skills Comparison (Have vs Gap) -->
          <div class="space-y-3 mb-6">
            <div>
              <span class="text-[11px] uppercase font-bold text-slate-400 tracking-wider block mb-1.5">Transferable Skills</span>
              <div class="flex flex-wrap gap-1.5">
                ${role.skillsHave.map(s => `<span class="bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium px-2.5 py-0.5 rounded-md">${s}</span>`).join('')}
              </div>
            </div>
            <div>
              <span class="text-[11px] uppercase font-bold text-slate-400 tracking-wider block mb-1.5">Required Next Skills</span>
              <div class="flex flex-wrap gap-1.5">
                ${role.skillsNeed.map(s => `<span class="bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium px-2.5 py-0.5 rounded-md">${s}</span>`).join('')}
              </div>
            </div>
          </div>
        </div>

        <button class="w-full py-2.5 text-xs font-semibold rounded-xl border transition-all ${isSelected ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-200' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}">
          ${isSelected ? 'Currently Viewing Pathway' : 'View Reskilling Roadmap'}
        </button>
      </div>
    `;
  },

  // Requirement 4: Reskilling Roadmap Step
  createStepItem(step, index) {
    return `
      <div class="flex gap-4 p-5 rounded-xl bg-white border border-slate-200 shadow-sm items-start hover:border-slate-300 transition-colors">
        <div class="h-8 w-8 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200 flex items-center justify-center font-bold text-sm shrink-0">
          ${index + 1}
        </div>
        <div class="flex-1">
          <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
            <h5 class="text-sm font-bold text-slate-900">${step.phase}</h5>
            <span class="text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-md border border-slate-200">${step.time}</span>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed mb-2">${step.desc}</p>
          <div class="text-xs text-slate-500 flex items-center gap-1.5">
            <i class="ph ph-graduation-cap text-indigo-600 text-sm"></i>
            <span>Resource: <strong class="text-slate-800 font-semibold">${step.res}</strong></span>
          </div>
        </div>
      </div>
    `;
  }
};