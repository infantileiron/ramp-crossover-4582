import { api } from '../api/client.js';
import { sign } from '../components/common/signs.js';
import { empty, heading } from '../components/common/shell.js';
import { sequences } from '../constants/domain.js';
import { bindForm, notice } from '../hooks/forms.js';
import { isComplete } from '../types/field.js';
import { e, sec } from '../utils/format.js';

function editor() {
  return `<aside class="panel edit-panel"><div class="panel-title"><h2 id="pair-heading">录入试走</h2><p>以匿名编号保存。缺测周期可留空。</p></div>
    <form id="pair-form">
      <label>参与者编号<input name="code" pattern="[A-Z0-9][A-Z0-9\\-]{1,19}" placeholder="如 AB08" required maxlength="20"></label>
      <label>分配顺序<select name="sequence"><option value="AB">AB · 先 A 后 B</option><option value="BA">BA · 先 B 后 A</option></select></label>
      <div class="form-inline"><label>第 1 轮 <span id="first-sign" class="field-sign">A</span><input name="period1" type="number" min="0.01" max="900" step="0.01" placeholder="秒"></label>
      <label>第 2 轮 <span id="second-sign" class="field-sign">B</span><input name="period2" type="number" min="0.01" max="900" step="0.01" placeholder="秒"></label></div>
      <p class="form-error" role="alert" hidden></p>
      <div class="form-actions"><button type="submit" class="primary">保存记录</button><button type="button" id="pair-reset" class="quiet">重置</button></div>
    </form></aside>`;
}

export function pairsPage(root, { route, pairs, user, refresh }) {
  const edit = user.role === 'analyst';
  if (!route) { root.innerHTML = empty('暂无路线', '导入现场路线后可查看配对记录。'); return; }
  root.innerHTML = `${heading('配对记录', `${e(route.code)} · ${e(route.name)}　/　用时单位为秒`, edit ? '<a class="button secondary" href="#runs">进入对照运行 →</a>' : '')}
    <div class="split ${edit ? '' : 'single'}"><section class="panel records">
      <div class="panel-title title-row"><div><h2>试走台账</h2><p>${pairs.length} 人登记 · ${pairs.filter(isComplete).length} 人完整配对</p></div>
        <label class="filter-label">顺序<select id="sequence-filter"><option value="">全部</option><option>AB</option><option>BA</option></select></label></div>
      <div class="table-wrap" id="pair-list"></div></section>${edit ? editor() : ''}</div>`;
  const list = root.querySelector('#pair-list');
  const filter = root.querySelector('#sequence-filter');
  function fill() {
    const rows = pairs.filter(row => !filter.value || filter.value === row.sequence);
    list.innerHTML = rows.length ? `<table><thead><tr><th>参与者</th><th>顺序</th><th>第 1 轮</th><th>第 2 轮</th><th>配对状态</th>${edit ? '<th><span class="sr-only">操作</span></th>' : ''}</tr></thead>
      <tbody>${rows.map(row => `<tr><th scope="row" class="code">${e(row.code)}</th><td>${sequences[row.sequence].map(code => sign(code)).join(' ')}</td>
        <td class="number">${sec(row.period1)}</td><td class="number">${sec(row.period2)}</td><td><span class="status ${isComplete(row) ? 'ok' : 'warn'}">${isComplete(row) ? '齐全' : '缺测'}</span></td>
        ${edit ? `<td><button type="button" class="text-button" data-pair="${e(row.code)}">补录／编辑</button></td>` : ''}</tr>`).join('')}</tbody></table>` : empty('此顺序暂无记录', '可切回全部顺序，或登记首位参与者。');
  }
  filter.addEventListener('change', fill);
  fill();
  if (!edit) return;
  const form = root.querySelector('#pair-form');
  const fields = form.elements;
  function showSigns() {
    const [first, second] = sequences[fields.sequence.value];
    root.querySelector('#first-sign').textContent = first;
    root.querySelector('#second-sign').textContent = second;
  }
  fields.sequence.addEventListener('change', showSigns);
  root.querySelector('#pair-reset').onclick = () => {
    form.reset(); fields.code.readOnly = false; fields.sequence.disabled = false;
    root.querySelector('#pair-heading').textContent = '录入试走';
    form.querySelector('.form-error').hidden = true;
    showSigns();
  };
  list.onclick = event => {
    const code = event.target.closest('[data-pair]')?.dataset.pair;
    if (!code) return;
    const row = pairs.find(item => item.code === code);
    for (const name of ['code', 'sequence', 'period1', 'period2']) fields[name].value = row[name] ?? '';
    fields.code.readOnly = true;
    fields.sequence.disabled = true;
    root.querySelector('#pair-heading').textContent = `编辑 ${code}`;
    form.querySelector('.form-error').hidden = true;
    showSigns();
    fields.period1.focus();
  };
  bindForm('pair-form', async (values, node) => {
    await api.savePair(route.code, values.code, { sequence: node.elements.sequence.value, period1: values.period1 || null, period2: values.period2 || null });
    notice(`已保存 ${values.code} 的现场记录`);
    await refresh();
  });
}
