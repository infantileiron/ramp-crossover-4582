import { empty, heading } from '../components/common/shell.js';
import { decisions, states } from '../constants/domain.js';
import { e, time } from '../utils/format.js';

export function reportsPage(root, { reports, user }) {
  const runLink = user.role === 'analyst' ? '<a href="#runs" class="button primary">新建运行 →</a>' : '';
  root.innerHTML = heading('实验报告', user.role === 'viewer' ? '查看业务复核员已发布的对照结果。' : '查阅运行状态与报告，已发布的决定对观察员可见。', runLink);
  root.insertAdjacentHTML('beforeend', reports.length ? `<section class="panel records"><div class="panel-title"><h2>报告档案</h2><p>${reports.length} 份可阅报告</p></div>
    <div class="table-wrap"><table><thead><tr><th>编号</th><th>参数版本</th><th>创建时间</th><th>状态</th><th>复核决定</th><th><span class="sr-only">操作</span></th></tr></thead>
    <tbody>${reports.map(row => `<tr><th scope="row" class="code">RPT-${row.id}</th><td>${e(row.edition)}</td><td>${time(row.created_at)}</td>
      <td><span class="status ${row.state === 'published' ? 'ok' : 'warn'}">${states[row.state]}</span></td>
      <td>${decisions[row.decision] || '—'}</td><td><a href="#reports/${row.id}">查看报告 →</a></td></tr>`).join('')}</tbody></table></div></section>` :
    empty('暂无可阅报告', user.role === 'viewer' ? '待复核员发布后，报告会显示在此归档。' : '提交一次对照运行后，可在这里查看状态及回溯快照。'));
}
