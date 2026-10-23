// js/components.js

const Components = {
  createSkillBadge(name) {
    return `
      <span class="inline-flex items-center gap-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-semibold px-2.5 py-1 rounded-md shadow-xs">
        ${name}
        <button onclick="removeSkill(this)" class="hover:text-red-500 focus:outline-none">
          <i class="ph ph-x"></i>
        </button>
      </span>
    `;
  },

  createRoleCard(role, currentScenario, isSelected) {
    const matchScore = currentScenario === 'moderate' ? role.baseMatch : role.acceleratedMatch;
    const selectedClass = isSelected ? 'role-card-selected' : 'bg-white';

    return `
      <div onclick="selectRole(${role.id})" class="role-card-item rounded-xl p-5 cursor-pointer flex flex-col justify-between ${selectedClass}">
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded border ${role.sdg.color}">
              ${role.sdg.label}
            </span>
            <span class="text-[11px] font-medium px-2 py-0.5 rounded border ${role.riskColor}">
              ${role.risk}
            </span>
          </div>

          <h4 class="text-base font-bold text-slate-900 mb-1 leading-tight">${role.title}</h4>
          <p class="text-xs text-slate-500 mb-4 line-clamp-1">${role.sdgSub}</p>

          <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 mb-4">
            <div class="flex justify-between items-center mb-1 text-xs">
              <span class="font-medium text-slate-600">Match Compatibility</span>
              <span class="font-bold text-indigo-600 text-sm">${matchScore}%</span>
            </div>
            <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
              <div class="bg-indigo-600 h-2 rounded-full transition-all duration-500" style="width: ${matchScore}%"></div>
            </div>
          </div>

          <div class="space-y-2">
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">Transferable</span>
              <div class="flex flex-wrap gap-1 mt-1">
                ${role.skillsHave.map(s => `<span class="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-medium px-2 py-0.5 rounded">${s}</span>`).join('')}
              </div>
            </div>
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">Skills to Bridge</span>
              <div class="flex flex-wrap gap-1 mt-1">
                ${role.skillsNeed.map(s => `<span class="bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-medium px-2 py-0.5 rounded">${s}</span>`).join('')}
              </div>
            </div>
          </div>
        </div>

        <button class="mt-4 w-full py-2 text-xs font-semibold rounded-lg border transition-all ${isSelected ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'}">
          ${isSelected ? 'Selected (View Workspace)' : 'Select Role'}
        </button>
      </div>
    `;
  },

  createStepItem(step, index) {
    return `
      <div class="flex gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 items-start">
        <div class="h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-sm">
          0${index + 1}
        </div>
        <div class="flex-1">
          <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
            <h5 class="text-sm font-bold text-slate-900">${step.phase}</h5>
            <span class="text-xs font-semibold text-slate-600 bg-white border border-slate-200 px-2.5 py-0.5 rounded-md shadow-2xs">${step.time}</span>
          </div>
          <p class="text-xs text-slate-600 mb-2 leading-relaxed">${step.desc}</p>
          <div class="text-xs text-slate-500 flex items-center gap-1.5">
            <i class="ph-bold ph-graduation-cap text-indigo-600"></i>
            <span>Learning Resource: <strong class="text-slate-800 font-semibold">${step.res}</strong></span>
          </div>
        </div>
      </div>
    `;
  }
};