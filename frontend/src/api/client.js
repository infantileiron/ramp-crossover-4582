const TOKEN = 'ramp-session';
export const readToken = () => sessionStorage.getItem(TOKEN);
export const setToken = token => token ? sessionStorage.setItem(TOKEN, token) : sessionStorage.removeItem(TOKEN);

async function request(path, method = 'GET', body, file = false) {
  const headers = {};
  const token = readToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers['Content-Type'] = 'application/json';
  let response;
  try {
    response = await fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new Error('无法连接工作台，请重试。');
  }
  if (!response.ok) {
    if (response.status === 401 && path !== '/login') {
      setToken(null);
      window.dispatchEvent(new Event('session-expired'));
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || '操作未能完成，请重试。');
  }
  return file ? response.blob() : response.json();
}

export const api = {
  login: body => request('/login', 'POST', body),
  me: () => request('/me'),
  routes: () => request('/routes'),
  pairs: route => request(`/routes/${route}/pairs`),
  savePair: (route, code, body) => request(`/routes/${route}/pairs/${encodeURIComponent(code)}`, 'PUT', body),
  plans: route => request(`/routes/${route}/plans`),
  createPlan: body => request('/plans', 'POST', body),
  reports: () => request('/reports'),
  run: plan_id => request('/reports', 'POST', { plan_id }),
  report: id => request(`/reports/${id}`),
  export: id => request(`/reports/${id}/export`, 'GET', undefined, true),
  publish: (id, body) => request(`/reports/${id}/publish`, 'POST', body),
};
