import { roles } from '../../constants/domain.js';
import { e } from '../../utils/format.js';

const nav = [
  ['routes', '↱', '路线与方案'], ['pairs', '▤', '配对记录'], ['sessions', '⧉', '时段分组'],
  ['runs', '▷', '对照运行'], ['reports', '▧', '实验报告'],
];

export function shell(page, user) {
  const active = page === 'detail' ? 'reports' : page;
  return `<div class="shell">
    <aside class="sidebar">
      <a href="#routes" class="brand"><span class="brand-mark" aria-hidden="true">↱</span><span>岔路导览<small>坡道指引交叉测试</small></span></a>
      <nav aria-label="工作台">${nav.filter(([key]) => key !== 'runs' || user.role !== 'viewer').map(([key, icon, label]) =>
        `<a href="#${key}" ${key === active ? 'aria-current="page"' : ''}><span class="nav-icon" aria-hidden="true">${icon}</span>${label}</a>`).join('')}</nav>
      <div class="account"><span class="avatar">${e(user.display_name[0])}</span><div><strong>${e(user.display_name)}</strong><small>${roles[user.role]}</small></div><button id="logout" class="icon-button" aria-label="退出登录" title="退出登录">↪</button></div>
    </aside>
    <div class="workspace">
      <div class="masthead"><span>青栈导览小组<span class="separator">/</span><strong>${nav.find(([key]) => key === active)?.[2] || '工作台'}</strong></span><span class="mast-tag">现场试测</span></div>
      <main id="view" tabindex="-1"></main>
    </div>
  </div>`;
}

export function heading(title, detail, action = '') {
  return `<header class="page-heading"><div><h1>${title}</h1><p>${detail}</p></div>${action}</header>`;
}

export function empty(title, detail, action = '') {
  return `<div class="empty"><strong>${title}</strong><p>${detail}</p>${action}</div>`;
}
