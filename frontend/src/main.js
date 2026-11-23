import { api } from './api/client.js';
import { empty, shell } from './components/common/shell.js';
import { clearNotice } from './hooks/forms.js';
import { detailPage } from './pages/detail.js';
import { login } from './pages/login.js';
import { pairsPage } from './pages/pairs.js';
import { reportsPage } from './pages/reports.js';
import { routesPage } from './pages/routes.js';
import { runsPage } from './pages/runs.js';
import { sessionsPage } from './pages/sessions.js';
import { currentPage, go } from './router/hash.js';
import { session } from './stores/session.js';
import { e } from './utils/format.js';

const root = document.querySelector('#app');
const renderers = { routes: routesPage, pairs: pairsPage, sessions: sessionsPage, runs: runsPage, reports: reportsPage, detail: detailPage };
let version = 0;
let poll;

async function load(page, id) {
  if (page === 'detail') return { report: await api.report(id) };
  if (page === 'reports') return { reports: await api.reports() };
  const [route] = await api.routes();
  if (!route) return { route: null };
  const [pairs, plans, sessions] = await Promise.all([
    api.pairs(route.code),
    page === 'runs' ? api.plans(route.code) : [],
    page === 'sessions' ? api.sessions(route.code) : [],
  ]);
  return { route, pairs, plans, sessions };
}

async function render(refresh = false) {
  const requested = ++version;
  clearTimeout(poll);
  if (!session.user) { login(root, () => render()); return; }
  const { page, id } = currentPage();
  if (!refresh || !root.querySelector('#view')) {
    root.innerHTML = shell(page, session.user);
    root.querySelector('#logout').onclick = () => {
      session.clear();
      go('routes');
      render();
    };
    root.querySelector('#view').innerHTML = '<p class="loading" role="status">正在读取现场记录…</p>';
    window.scrollTo(0, 0);
  }
  const view = root.querySelector('#view');
  try {
    const data = await load(page, id);
    if (requested !== version) return;
    renderers[page](view, { ...data, user: session.user, refresh: () => render(true) });
    if (data.report?.state === 'queued') poll = setTimeout(() => render(true), 750);
  } catch (err) {
    if (requested !== version) return;
    view.innerHTML = empty('暂时无法读取', e(err.message), '<button id="retry" class="secondary">重新读取</button>');
    view.querySelector('#retry').onclick = () => render(true);
  }
}

window.addEventListener('hashchange', () => { clearNotice(); render(); });
window.addEventListener('session-expired', () => { session.clear(); render(); });
await session.restore().catch(() => {});
await render();
