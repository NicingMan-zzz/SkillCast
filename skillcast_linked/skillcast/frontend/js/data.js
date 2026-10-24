// js/data.js
// Personas use the backend's skill names (GET /api/skills). Unknown names are ignored by the backend.
const PRESET_PERSONAS = {
  csStudent: ['Python', 'SQL', 'JavaScript', 'Communication'],
  businessAnalyst: ['Data Analysis', 'SQL', 'Communication', 'Project Management'],
  uiDesigner: ['UX Design', 'JavaScript', 'Communication']
};

// Filled by js/api.js from POST /api/recommend (same shape the old hardcoded catalogue had).
let ROLE_CATALOG = [];
