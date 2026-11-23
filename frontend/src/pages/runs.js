import { api } from '../api/client.js';
import { empty, heading } from '../components/common/shell.js';
import { sign } from '../components/common/signs.js';
import { bindForm, notice } from '../hooks/forms.js';
import { go } from '../router/hash.js';
import { isComplete } from '../types/field.js';
import { e, sec } from '../utils/format.js';

export function runsPage(root, { route, pairs, plans, user, refresh }) {
  if (!route) { root.innerHTML = empty('暂无路线', '需要先准备现场路线与试走记录。'); return; }
  const edit = user.role === 'analyst';
  if (user.role === 'viewer') { root.innerHTML = empty('运行由分析员负责', '可前往实验报告查看已发布结果。', '<a href="#reports">实验报告 →</a>'); return; }
  root.innerHTML = `${heading('对照运行', '选择参数版本，冻结当前台账并提交后台计算。')}
    <div class="split"><div>
      <section class="panel">
        <div class="panel-title"><h2>计算范围</h2><p>${e(route.code)} · ${e(route.name)} · 两序列、两周期</p></div>
        <div class="run-groups">${[['AB', 'A', 'B'], ['BA', 'B', 'A']].map(([seq, first, second]) => {
          const group = pairs.filter(row => row.sequence === seq);
          return `<div><div aria-label="${seq}">${sign(first, first === 'A' ? route.sign_a : route.sign_b)} <span aria-hidden="true">→</span> ${sign(second)}</div>
            <strong>${group.filter(isComplete).length} / ${group.length}</strong><small>完整配对 / 登记</small></div>`;
        }).join('')}</div>
        ${edit && plans.length ? `<form id="run-form" class="run-form"><label>参数版本<select name="plan_id" id="plan-select">${plans.map(plan => `<option value="${plan.id}">${e(plan.edition)}</option>`).join('')}</select></label>
          <div id="plan-summary" class="plan-summary"></div><p class="form-error" role="alert" hidden></p>
          <button type="submit" class="primary">提交计算 <span aria-hidden="true">→</span></button></form>` : ''}
      </section>
      <section class="panel method"><div class="panel-title"><h2>计算与复核口径</h2></div>
        <dl><div><dt>完整配对</dt><dd>仅纳入同一人两轮均有用时的记录，缺测单独列出。</dd></div>
        <div><dt>序列等权</dt><dd>分别计算 AB 和 BA 的组内变化，两组等权计算处理差与时期差。</dd></div>
        <div><dt>顺序差复核线</dt><dd>检查双轮平均用时差。超过或达到阈值时，提示复核现场条件。</dd></div></dl>
      </section>
    </div><aside class="panel edit-panel"><div class="panel-title"><h2>参数版本</h2><p>每版有独立门槛，可重复运行取不同台账快照。</p></div>
      ${edit ? `<form id="plan-form"><label>版本名<input name="edition" required maxlength="40" placeholder="如 二轮上牌复核"></label>
        <label>每序列最少完整配对<input name="min_pairs" required type="number" min="2" max="50" value="3"></label>
        <label>顺序差复核线（秒）<input name="gap_limit" required type="number" min="0.01" max="120" step="0.01" value="8"></label>
        <p class="form-error" role="alert" hidden></p><button class="secondary" type="submit">保存新版本</button></form>` : ''}
      <ul class="version-list">${plans.map(plan => `<li><strong>${e(plan.edition)}</strong><small>每序列 ≥ ${plan.min_pairs} 对 · 顺序差线 ${sec(plan.gap_limit)} 秒</small></li>`).join('') || '<li>暂无版本</li>'}</ul></aside></div>`;
  const select = root.querySelector('#plan-select');
  if (select) {
    const summary = root.querySelector('#plan-summary');
    const show = () => {
      const plan = plans.find(item => item.id === Number(select.value));
      summary.textContent = `每序列至少 ${plan.min_pairs} 对 ∙ 顺序差达到 ${sec(plan.gap_limit)} 秒须复核`;
    };
    select.onchange = show;
    show();
  }
  bindForm('plan-form', async values => {
    await api.createPlan({ route_code: route.code, edition: values.edition, min_pairs: Number(values.min_pairs), gap_limit: values.gap_limit });
    notice(`已保存参数版本「${values.edition}」`);
    await refresh();
  });
  bindForm('run-form', async values => {
    const report = await api.run(Number(values.plan_id));
    go(`reports/${report.id}`);
  });
}
