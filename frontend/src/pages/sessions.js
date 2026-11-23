import { api } from '../api/client.js';
import { empty, heading } from '../components/common/shell.js';
import { sign } from '../components/common/signs.js';
import { sequences } from '../constants/domain.js';
import { bindForm, notice } from '../hooks/forms.js';
import { e, sec, time } from '../utils/format.js';

function memberSeat(session, member, edit) {
  const assignment = session.assignment.find(item => item.seat === Number(member.seat));
  const sequence = assignment?.sequence;
  const [first, second] = sequence ? sequences[sequence] : [];
  const locked = session.locked;
  return `<div class="seat-row" data-seat="${member.seat}">
    <span class="seat-index">${member.seat}</span>
    <div class="seat-person"><strong class="code">${e(member.participant_code)}</strong>
      ${locked ? `<small>${sequence ? `${e(sequence)} · ${sign(first)} → ${sign(second)}` : '已锁定，但分派记录缺失'}</small>`
        : `<small>开走前可更换成员</small>`}</div>
    ${locked ? `<div class="seat-times"><span>第 1 轮 <b>${sec(member.period1)}</b></span><span>第 2 轮 <b>${sec(member.period2)}</b></span></div>` : ''}
    ${edit ? `<div class="seat-actions">
      ${locked ? '' : `<button type="button" class="quiet" data-swap="${member.seat}">换人</button>`}
      ${locked ? '' : `<button type="button" class="secondary" data-start="${member.seat}" data-code="${e(member.participant_code)}">开走并揭晓</button>`}
      ${locked ? `<button type="button" class="text-button" data-times="${member.seat}">录入用时</button>` : ''}
    </div>` : ''}
    ${edit ? `<form class="seat-time-form" data-form="${member.seat}" hidden>
      <label>第 1 轮用时<input name="period1" type="number" min="0.01" max="900" step="0.01" value="${member.period1 ?? ''}" placeholder="秒"></label>
      <label>第 2 轮用时<input name="period2" type="number" min="0.01" max="900" step="0.01" value="${member.period2 ?? ''}" placeholder="秒"></label>
      <p class="form-error" role="alert" hidden></p><div class="form-actions"><button type="submit" class="primary">保存用时</button><button type="button" class="quiet" data-cancel="${member.seat}">收起</button></div>
    </form>` : ''}
  </div>`;
}

function sessionCard(session, edit) {
  const status = session.locked
    ? `<span class="status ok">已开走 · 锁定</span>`
    : `<span class="status neutral">待开走</span>`;
  return `<article class="panel session-card" data-session="${session.id}">
    <div class="panel-title title-row"><div><h2><span class="code">${e(session.slot_code)}</span> · ${time(session.starts_at)}</h2>
      <p>两人成组，开走时揭晓相反顺序并锁住整组。${session.locked ? `由 ${e(session.started_code)} 开走。` : ''}</p></div>${status}</div>
    <div class="seat-list">${session.members.map(member => memberSeat(session, member, edit)).join('')}</div>
  </article>`;
}

function editor() {
  return `<aside class="panel edit-panel"><div class="panel-title"><h2>新增时段分组</h2><p>顺序先封存，任一人开走时才揭晓。</p></div>
    <form id="session-form">
      <label>时段编号<input name="slot_code" pattern="[A-Z0-9][A-Z0-9\\-]{1,19}" placeholder="如 T0920" required maxlength="20"></label>
      <label>开始时间<input name="starts_at" type="datetime-local" required></label>
      <label>席位 1 参与者<input name="seat1_code" pattern="[A-Z0-9][A-Z0-9\\-]{1,19}" placeholder="如 AB09" required maxlength="20"></label>
      <label>席位 2 参与者<input name="seat2_code" pattern="[A-Z0-9][A-Z0-9\\-]{1,19}" placeholder="如 BA09" required maxlength="20"></label>
      <p class="form-error" role="alert" hidden></p><button type="submit" class="primary">封存分组</button>
    </form></aside>`;
}

export function sessionsPage(root, { route, sessions, user, refresh }) {
  if (!route) { root.innerHTML = empty('暂无路线', '导入现场路线后可建立时段分组。'); return; }
  const edit = user.role === 'analyst';
  const started = sessions.filter(item => item.locked).length;
  root.innerHTML = `${heading('时段分组', `${e(route.code)} · ${e(route.name)}　/　${sessions.length} 个时段 · ${started} 个已开走`, '')}
    <div class="split ${edit ? '' : 'single'}"><section class="session-column">
      ${sessions.length ? sessions.map(session => sessionCard(session, edit)).join('')
        : empty('暂无时段分组', '按开始时间建立两人一组，封存随机顺序后等待现场开走。')}
    </section>${edit ? editor() : ''}</div>`;
  if (!edit) return;

  function findSession(id) {
    return sessions.find(item => String(item.id) === String(id));
  }
  function memberOf(session, seat) {
    return session.members.find(item => Number(item.seat) === Number(seat));
  }

  root.querySelectorAll('[data-swap]').forEach(button => {
    button.onclick = async () => {
      const card = button.closest('[data-session]');
      const session = findSession(card.dataset.session);
      const seat = Number(button.dataset.swap);
      const current = memberOf(session, seat);
      const code = window.prompt(`席位 ${seat} 的替换参与者编号`, '');
      if (!code || code.trim() === current.participant_code) return;
      button.disabled = true;
      try {
        await api.swapMember(session.id, seat, { participant_code: code.trim() });
        notice(`席位 ${seat} 已更换为 ${code.trim()}，原记录用时已清空`);
        await refresh();
      } catch (err) {
        notice(err.message);
        button.disabled = false;
      }
    };
  });

  root.querySelectorAll('[data-start]').forEach(button => {
    button.onclick = async () => {
      const card = button.closest('[data-session]');
      const session = findSession(card.dataset.session);
      const seat = Number(button.dataset.start);
      if (!window.confirm(`确认席位 ${seat} 的 ${button.dataset.code} 已开走？揭晓后整组锁定，不能再换人。`)) return;
      button.disabled = true;
      try {
        await api.startSession(session.id, { seat, participant_code: button.dataset.code });
        notice('顺序已揭晓，整组已锁定');
        await refresh();
      } catch (err) {
        notice(err.message);
        button.disabled = false;
      }
    };
  });

  root.querySelectorAll('[data-times]').forEach(button => {
    button.onclick = () => {
      const card = button.closest('[data-session]');
      card.querySelector(`[data-form="${button.dataset.times}"]`).hidden = false;
      button.hidden = true;
    };
  });
  root.querySelectorAll('[data-cancel]').forEach(button => {
    button.onclick = () => {
      const card = button.closest('[data-session]');
      card.querySelector(`[data-form="${button.dataset.cancel}"]`).hidden = true;
      card.querySelector(`[data-times="${button.dataset.cancel}"]`).hidden = false;
    };
  });
  root.querySelectorAll('[data-form]').forEach(form => {
    const error = form.querySelector('.form-error');
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const card = form.closest('[data-session]');
      const session = findSession(card.dataset.session);
      const seat = Number(form.dataset.form);
      const values = Object.fromEntries(new FormData(form));
      const button = form.querySelector('button[type=submit]');
      button.disabled = true;
      error.hidden = true;
      try {
        await api.sessionTimes(session.id, seat, { period1: values.period1 || null, period2: values.period2 || null });
        notice('用时已保存到该席位');
        await refresh();
      } catch (err) {
        error.textContent = err.message;
        error.hidden = false;
        button.disabled = false;
      }
    });
  });
  bindForm('session-form', async values => {
    await api.createSession(route.code, {
      slot_code: values.slot_code,
      starts_at: new Date(values.starts_at).toISOString(),
      seat1_code: values.seat1_code,
      seat2_code: values.seat2_code,
    });
    notice(`已封存时段「${values.slot_code}」`);
    await refresh();
  });
}
