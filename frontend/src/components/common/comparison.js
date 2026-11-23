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
