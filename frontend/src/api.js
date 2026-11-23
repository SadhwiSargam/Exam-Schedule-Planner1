const API = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  getPlans: () => request("/api/plans"),
  getPlan: (id) => request(`/api/plans/${id}`),
  createPlan: (plan) => request("/api/plans", { method: "POST", body: JSON.stringify(plan) }),
  updatePlan: (id, plan) => request(`/api/plans/${id}`, { method: "PUT", body: JSON.stringify(plan) }),
  deletePlan: (id) => request(`/api/plans/${id}`, { method: "DELETE" }),

  getSubjects: (planId) => request(`/api/plans/${planId}/subjects`),
  getSubject: (planId, id) => request(`/api/plans/${planId}/subjects/${id}`),
  createSubject: (planId, subject) => request(`/api/plans/${planId}/subjects`, { method: "POST", body: JSON.stringify(subject) }),
  updateSubject: (planId, id, subject) => request(`/api/plans/${planId}/subjects/${id}`, { method: "PUT", body: JSON.stringify(subject) }),
  deleteSubject: (planId, id) => request(`/api/plans/${planId}/subjects/${id}`, { method: "DELETE" }),

  getHolidays: (planId) => request(`/api/plans/${planId}/holidays`),
  createHoliday: (planId, holiday) => request(`/api/plans/${planId}/holidays`, { method: "POST", body: JSON.stringify(holiday) }),
  deleteHoliday: (planId, id) => request(`/api/plans/${planId}/holidays/${id}`, { method: "DELETE" }),

  getConfig: (planId) => request(`/api/plans/${planId}/config`),
  updateConfig: (planId, config) => request(`/api/plans/${planId}/config`, { method: "PUT", body: JSON.stringify(config) }),

  generateSchedule: (planId, regenerate = false) => request(`/api/plans/${planId}/schedule/generate`, { method: "POST", body: JSON.stringify({ plan_id: planId, regenerate }) }),
  getSchedule: (planId) => request(`/api/plans/${planId}/schedule`),
  validateSchedule: (planId) => request(`/api/plans/${planId}/schedule/validate`, { method: "POST" }),
  validateScheduleEntries: (planId, entries) => request(`/api/plans/${planId}/schedule/validate-entries`, { method: "POST", body: JSON.stringify({ entries }) }),
  updateScheduleEntry: (planId, id, entry) => request(`/api/plans/${planId}/schedule/entries/${id}`, { method: "PUT", body: JSON.stringify(entry) }),
  deleteScheduleEntry: (planId, id) => request(`/api/plans/${planId}/schedule/entries/${id}`, { method: "DELETE" }),

  exportPDF: (planId) => fetch(`${API}/api/plans/${planId}/schedule/export/pdf`).then(r => { if (!r.ok) throw new Error("Export failed"); return r.blob(); }),

  orderSubjects: (subjects) => request("/api/subjects/order", { method: "POST", body: JSON.stringify(subjects) }),
  createIAT: (payload) => request("/api/timetable/iat", { method: "POST", body: JSON.stringify(payload) }),
};