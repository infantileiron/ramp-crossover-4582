import { sign, routeMap } from '../components/common/signs.js';
import { heading, empty } from '../components/common/shell.js';
import { sequences } from '../constants/domain.js';
import { isComplete } from '../types/field.js';
import { e } from '../utils/format.js';

export function routesPage(root, { route, pairs }) {
  if (!route) {
    root.innerHTML = heading('路线与方案', '浏览现场登记的试测路线。') + empty('暂无路线', '启用演示数据后可查看北门坡道现场案例。');
    return;
  }
  root.innerHTML = `${heading('路线与方案', '同一条坡道交替更换两套指引，记录每位参与者的两轮到达时间。', '<a class="button primary" href="#pairs">查看配对记录 <span aria-hidden="true">→</span></a>')}
    <section class="route-feature"><div class="route-story"><div class="route-id"><span>${e(route.code)}</span> 试测路线</div>
      <h2>${e(route.name)}</h2><p>${e(route.description)}</p>
      <div class="route-meta"><span><strong>${route.length_m}</strong> 米</span><span>${e(route.start_at)} <span aria-hidden="true">→</span> ${e(route.finish_at)}</span></div></div>
      ${routeMap(route)}</section>
    <div class="overview-grid">
      <section class="panel sign-sheet"><div class="panel-title"><h2>指引样牌</h2><p>两轮采用同一计时口径，由起点出发至到达平台。</p></div>
        <div class="sign-gallery"><div>${sign('A', route.sign_a)}<p>现用方案</p></div><div>${sign('B', route.sign_b)}<p>拟替换样牌</p></div></div>
      </section>
      <section class="panel enrolment"><div class="panel-title"><h2>顺序分配</h2><p>按人配对。两轮齐全才进入对照计算。</p></div>
        ${Object.entries(sequences).map(([seq, [first, second]]) => {
          const group = pairs.filter(item => item.sequence === seq);
          return `<div class="enrolment-row"><span aria-label="${seq}">${sign(first)} <b aria-hidden="true">→</b> ${sign(second)}</span><span><strong>${group.filter(isComplete).length}</strong> / ${group.length} 完整</span></div>`;
        }).join('')}
      </section>
    </div>`;
}
