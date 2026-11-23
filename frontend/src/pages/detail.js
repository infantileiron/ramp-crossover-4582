import { api } from '../api/client.js';
import { comparison, diagnostics } from '../components/common/comparison.js';
import { empty, heading } from '../components/common/shell.js';
import { decisions, states } from '../constants/domain.js';
import { bindForm, notice } from '../hooks/forms.js';
import { e, sec, time } from '../utils/format.js';

function reviewSection(report, user) {
  if (report.state === 'published') {
    return `<section class="panel review-panel"><div class="panel-title"><h2>标牌更换建议</h2><p>${e(report.reviewed_by)} · ${time(report.reviewed_at)}</p></div>
      <p class="decision"><span class="status ok">已发布</span> ${decisions[report.decision]}</p><p class="review-note">${e(report.review_note)}</p></section>`;
  }
  if (user.role !== 'reviewer') {
    return `<section class="panel review-panel"><div class="panel-title"><h2>标牌更换建议</h2><p>等待业务复核员查看完整配对和诊断后发布现场建议。</p></div></section>`;
  }
  return `<section class="panel review-panel"><div class="panel-title"><h2>标牌更换建议</h2><p>结合样本量、顺序差与现场记录，选择下一步。</p></div>
    <form id="review-form"><label>复核决定<select name="decision">${report.result.decisions.map(key => `<option value="${key}">${decisions[key]}</option>`).join('')}</select></label>
    <label>复核说明<textarea name="note" placeholder="写下补测安排或保留现牌的依据" required minlength="4" maxlength="500" rows="3"></textarea></label>
    <p class="form-error" role="alert" hidden></p><button type="submit" class="primary">发布建议</button></form></section>`;
}

function metric(label, value, help, className = '') {
  return `<div class="metric ${className}"><dt>${label}</dt><dd class="metric-value">${sec(value, true)}${value == null ? '' : ' <small>秒</small>'}</dd><dd class="metric-help">${help}</dd></div>`;
}

export function detailPage(root, { report, user, refresh }) {
  const { id, state, snapshot, result } = report;
  const route = snapshot.route;
  const plan = snapshot.plan;
  const title = `对照报告 <span class="report-id">RPT-${id}</span>`;
  const detail = `${e(route.code)} · ${e(route.name)}　/　${e(plan.edition)}`;
  const back = '<a class="button secondary" href="#reports">返回档案</a>';
  if (!result) {
    const queued = state === 'queued';
    root.innerHTML = heading(title, detail, back) + empty(states[state], queued ? '台账及参数均已冻结，后台正在处理本次任务。' : e(report.error), !queued && user.role === 'analyst' ? '<a href="#runs">回到对照运行 →</a>' : '');
    return;
  }
  root.innerHTML = `${heading(title, detail, `<div class="actions">${back}<button id="export" class="primary">下载 CSV ↓</button></div>`)}
    <div class="report-bar"><span class="status ${state === 'published' ? 'ok' : 'neutral'}">${states[state]}</span>
      <span>${result.complete} 人完整配对 · 每序列门槛 ${plan.min_pairs} 对 · ${time(report.finished_at)} 完成</span>
      ${result.blocked ? '<span class="status warn">估计受阻</span>' : ''}</div>
    <dl class="metrics">${metric('处理差估计 · B − A', result.treatment, '序列等权，负值表示 B 用时较短。', 'treatment')}
      ${metric('时期差估计 · 第 2 轮 − 第 1 轮', result.period, '序列等权，含路线熟悉等共同影响。')}
      ${metric('总体变化 · 第 2 轮 − 第 1 轮', result.raw_change, '实际样本人数加权的描述值。')}</dl>
    <div class="report-grid">${comparison(result)}${diagnostics(result, plan)}</div>
    <p class="report-boundary">估计依赖时期影响可相加、无实质差异性延续等假设。此报告用于安排复测或局部试挂。</p>
    ${reviewSection(report, user)}
    <details class="snapshot"><summary>计算快照与复现口径</summary><p>方法 <code>${e(result.method)}</code> · 参数版本 #${plan.id}</p><p>快照 SHA-256 <code>${e(report.fingerprint)}</code></p><p>Δ 为每组第 2 轮均值减第 1 轮均值。处理差 = (ΔAB − ΔBA) / 2，时期差 = (ΔAB + ΔBA) / 2。CSV 保留完整与缺测试走记录。</p></details>`;
  root.querySelector('#export').onclick = async event => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      const blob = await api.export(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ramp-report-${id}.csv`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) { notice(err.message); }
    finally { button.disabled = false; }
  };
  bindForm('review-form', async values => {
    await api.publish(id, values);
    notice('建议已发布，观察员现在可以查看这份报告。');
    await refresh();
  });
}
