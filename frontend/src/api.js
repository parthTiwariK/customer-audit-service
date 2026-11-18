async function request(path, options = {}) {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!res.ok) {
    const err = new Error(data?.detail?.message || data?.detail || res.statusText);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

export const api = {
  me: () => request("/api/v1/auth/me"),
  searchAudits: (qs) => request(`/api/v1/audits?${qs}`),
  getAudit: (id) => request(`/api/v1/audits/${id}`),
  caseExists: (caseId) => request(`/api/v1/audits/case/${encodeURIComponent(caseId)}/exists`),
  submitAudit: (body) => request("/api/v1/audits", { method: "POST", body: JSON.stringify(body) }),
  latestQuestionnaires: () => request("/api/v1/questionnaires/latest"),
  dashboard: (qs = "") => request(`/api/v1/reports/summary?${qs}`),
};