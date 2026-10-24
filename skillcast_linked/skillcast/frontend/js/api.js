// js/api.js  --  talks to the Flask backend and converts replies into the shape components.js already expects.
const Backend = {
  // Served by Flask (localhost:5000 or Replit) -> same origin. Only live-server (:3000) or file:// need the full URL.
  base: (location.protocol === 'file:' || location.port === '3000') ? 'http://localhost:5000' : '',
  lookup: {}, scenarios: [], trends: null, audit: null, scenarioId: null, pathway: null, online: false,
  SDG_COLORS: { 4: 'bg-rose-50 text-rose-800 border-rose-200', 7: 'bg-yellow-50 text-yellow-800 border-yellow-200',
                8: 'bg-amber-50 text-amber-800 border-amber-200', 9: 'bg-orange-50 text-orange-800 border-orange-200',
                13: 'bg-green-50 text-green-800 border-green-200' },

  async call(path, body) {
    const r = await fetch(this.base + path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {});
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || ('HTTP ' + r.status));
    return j;
  },

  async init() {
    const [skills, scen, trends, audit] = await Promise.all(['/api/skills', '/api/scenarios', '/api/trends', '/api/audit'].map(p => this.call(p)));
    skills.forEach(k => { this.lookup[k.name.toLowerCase()] = k.name; k.aliases.forEach(a => this.lookup[a.toLowerCase()] = k.name); });
    this.scenarios = scen; this.trends = trends; this.audit = audit; this.online = true;
    this.setScenario('moderate');
    const src = document.getElementById('signalSource'), dt = document.getElementById('signalDate');
    if (src) src.textContent = trends.source ? trends.source.name : 'No trend data';
    if (dt) dt.textContent = trends.snapshot_date || '--';
  },

  // 'moderate' / 'accelerated' (your two buttons) -> backend scenario rows
  setScenario(type) {
    const want = type === 'accelerated' ? /fast/i : /moderate/i;
    const s = this.scenarios.find(x => want.test(x.name)) || this.scenarios[0];
    this.scenarioId = s.scenario_id;
  },

  resolveSkill(raw) { return this.lookup[String(raw).trim().toLowerCase()] || null; },
  skillsPayload(names) { const o = {}; names.forEach(n => { const c = this.resolveSkill(n); if (c) o[c] = 3; }); return o; },  // default level 3

  // POST /api/recommend -> ROLE_CATALOG (your card shape)
  async refresh(activeSkills) {
    const r = await this.call('/api/recommend', { skills: this.skillsPayload(activeSkills), scenario_id: this.scenarioId });
    this.snapshot = r.snapshot_date;
    ROLE_CATALOG = r.results.map(x => {
      const top = x.sdgs[0];
      return {
        id: x.role_id, title: x.title,
        sdg: top ? { number: top.sdg_id, label: `SDG ${top.sdg_id}: ${top.name}`, color: this.SDG_COLORS[top.sdg_id] || 'bg-slate-50 text-slate-700 border-slate-200' }
                 : { number: 0, label: 'No SDG mapped', color: 'bg-slate-50 text-slate-700 border-slate-200' },
        sdgSub: top ? `Target ${top.target_code}: ${top.rationale}` : (x.description || ''),
        baseMatch: x.match_score, acceleratedMatch: x.match_score,
        risk: x.is_emerging ? 'Emerging Role' : 'Established Role',
        riskColor: x.is_emerging ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-blue-50 text-blue-700 border-blue-200',
        skillsHave: x.have, skillsNeed: x.missing,
        radarData: { labels: x.breakdown.map(b => b.skill), current: x.breakdown.map(b => b.have_level * 20), target: x.breakdown.map(b => b.required_level * 20) },
        breakdown: x.breakdown, outlook: x.outlook, sdgs: x.sdgs,
        duration: '--', steps: []
      };
    });
    return ROLE_CATALOG;
  },

  // POST /api/pathway -> fills role.duration / role.steps in your step shape
  async loadPathway(role, activeSkills, hoursPerWeek = 5) {
    const p = await this.call('/api/pathway', { skills: this.skillsPayload(activeSkills), role_id: role.id, scenario_id: this.scenarioId, hours_per_week: hoursPerWeek });
    const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    role.duration = p.steps.length ? `${p.total_hours} h of courses (~${p.est_weeks} wks @ ${hoursPerWeek} h/wk)` : 'No gaps: you already cover this role';
    role.steps = p.steps.map(s => ({
      phase: `Step ${s.step}: ${s.skill}`,
      desc: s.why,
      res: s.course ? `<a href="${esc(s.course.url)}" target="_blank" rel="noopener" class="underline text-indigo-600">${esc(s.course.title)}</a> (${esc(s.course.provider)}${s.course.cost_myr ? ', RM' + s.course.cost_myr : ', free'}${s.course.hrdcorp_claimable ? ', HRD Corp claimable' : ''}${s.course.verified_at ? '' : ', link not yet verified'})`
                       : 'No catalogue course yet',
      time: s.est_hours ? `${s.est_hours} h` : 'n/a'
    }));
    return p;
  },

  async extractSkills(text) { return (await this.call('/api/extract_skills', { text })).skills; }
};
