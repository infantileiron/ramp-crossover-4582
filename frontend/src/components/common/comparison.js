import { sequences } from '../../constants/domain.js';
import { e, sec } from '../../utils/format.js';
import { sign } from './signs.js';

export function comparison(result) {
  const maximum = Math.max(20, ...Object.values(result.groups).flatMap(group => [group.period1 ?? 0, group.period2 ?? 0]));
  const scale = Math.ceil(maximum / 20) * 20;
  const bar = (value, letter) => `<div class="bar-row">${sign(letter)}<div class="bar-track"><span class="bar bar-${letter.toLowerCase()}" style="--fill:${(value ?? 0) / scale * 100}%"></span></div><strong>${sec(value)}</strong></div>`;
  return `<section class="panel comparison"><div class="panel-title"><h2>两序列的周期对照</h2><p>组内完整配对的平均用时（秒），共用 0–${scale} 秒刻度。</p></div>
    ${Object.entries(sequences).map(([seq, [first, second]]) => {
      const group = result.groups[seq];
      return `<div class="chart-group"><div class="chart-heading"><b class="code">${seq}</b><span>${group.complete} / ${group.enrolled} 完整</span><strong>${sec(group.change, true)} 秒</strong></div>
        ${bar(group.period1, first)}${bar(group.period2, second)}</div>`;
    }).join('')}</section>`;
}

export function diagnostics(result, plan) {
  const missing = Object.values(result.groups).flatMap(group => group.incomplete);
  return `<section class="panel diagnostics ${result.sequence_alert || result.blocked ? 'has-alert' : ''}">
    <div class="panel-title"><h2>顺序诊断</h2><p>检查基线、场地变化和可能的指引延续。</p></div>
    <dl><div><dt>双轮均值差 · BA − AB</dt><dd>${sec(result.sequence_gap, true)} 秒 <span class="status ${result.sequence_alert ? 'warn' : 'neutral'}">${result.sequence_alert ? '达到复核线' : `复核线 ${sec(plan.gap_limit)} 秒`}</span></dd></div>
      <div><dt>首轮 B − A · 完整配对者</dt><dd>${sec(result.first_period, true)} 秒</dd></div>
      <div><dt>缺测编号</dt><dd>${missing.length ? e(missing.join('、')) : '无'}</dd></div></dl>
    ${result.alerts.length ? `<ul class="alert-list">${result.alerts.map(alert => `<li>${e(alert)}</li>`).join('')}</ul>` : ''}
    <p class="caveat">顺序差只能提示可能的延续影响，两轮数据无法单独识别其大小。</p></section>`;
}

function probability(test) {
  const { p_numerator, p_denominator, p_method } = test;
  const value = Number(p_numerator) / Number(p_denominator);
  if (!Number.isFinite(value)) return '—';
  if (p_method === 'monte-carlo' && p_numerator === 0) {
    return `< 0.001（${p_denominator} 次抽样未见更极端结果）`;
  }
  return `${(value * 100).toFixed(value < 0.001 ? 3 : 1)}%`;
}

export function randomized(result) {
  const test = result.randomized;
  if (!test) return '';
  const method = test.p_method === 'monte-carlo' ? '蒙特卡洛估计' : test.p_method === 'exact' ? '精确枚举' : '';
  const header = `<div class="panel-title"><h2>随机分派检验</h2><p>按原分组互换两名成员的 AB/BA 顺序，计算随机分派下图标收益不低于实测值的概率。</p></div>`;
  if (test.status === 'blocked') {
    const missing = test.missing.map(item => {
      const who = item.participant_code || item.slot_code;
      return `${item.slot_code} / ${who}（${item.periods.join('、')}）`;
    });
    return `<section class="panel randomized has-alert">${header}<p class="caveat">${e(test.reason)}</p>
      ${missing.length ? `<ul class="alert-list">${missing.map(item => `<li>${e(item)}</li>`).join('')}</ul>` : ''}
      <p class="caveat">补齐缺测后重跑即可恢复检验，已确认的分派顺序不会被改写。</p></section>`;
  }
  if (test.status !== 'ready') {
    return `<section class="panel randomized">${header}<p class="caveat">${e(test.reason || '暂无可检验的已开走分组。')}</p></section>`;
  }
  return `<section class="panel randomized ${test.p_value <= 0.05 ? 'has-alert' : ''}">${header}
    <dl class="rand-metrics">
      <div><dt>图标收益 · A − B</dt><dd>${sec(test.benefit, true)} 秒 <small>正值为图标牌更快</small></dd></div>
      <div><dt>随机分派下不低于实测值的概率</dt><dd>${probability(test)} <small>${method ? `${test.p_method === 'monte-carlo' ? '蒙特卡洛' : '精确枚举'}` : ''}</small></dd></div>
      <div><dt>已开走分组</dt><dd>${test.complete_groups} 组完整 / ${test.started_groups} 组已开走</dd></div>
    </dl>
    <div class="table-wrap"><table><thead><tr><th>时段</th><th>席位</th><th>参与者</th><th>顺序</th><th>第 1 轮</th><th>第 2 轮</th></tr></thead>
      <tbody>${test.groups.map(group => group.members.map((member, index) => `<tr><th scope="row" class="code">${index === 0 ? e(group.slot_code) : ''}</th>
        <td>${member.seat}</td><td class="code">${e(member.participant_code)}</td><td>${e(member.sequence)}</td>
        <td class="number">${sec(member.period1)}</td><td class="number">${sec(member.period2)}</td></tr>`).join('')).join('')}</tbody></table></div>
    <p class="caveat">${e(test.reason)} 收益按每组处理差等权汇总，概率越小越不支持“图标牌并无优势”的随机波动解释。</p></section>`;
}

