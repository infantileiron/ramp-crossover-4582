import { bindForm } from '../hooks/forms.js';
import { session } from '../stores/session.js';

export function login(root, done) {
  root.innerHTML = `<main class="login-layout">
    <section class="login-cover">
      <div class="cover-title"><span class="brand-mark" aria-hidden="true">↱</span><span>青栈导览小组</span></div>
      <div class="cover-copy"><p class="cover-label">北门连廊坡道 / R07</p><h1>岔路导览</h1><p class="cover-subtitle">坡道指引交叉测试</p></div>
      <div class="cover-signs" aria-hidden="true"><span>A <b>文字箭头牌</b> ↱</span><span>B <b>坡道图标牌</b> ↗</span></div>
      <div class="cover-foot">两套指引 <i></i> 两轮实测 <i></i> 同一条路线</div>
    </section>
    <section class="login-panel">
      <form id="login-form" class="login-form">
        <h2>登录现场工作台</h2><p>查看坡道试走记录、周期对照及复核报告。</p>
        <label>账号<input name="username" autocomplete="username" placeholder="输入工作台账号" required autofocus></label>
        <label>密码<input name="password" type="password" autocomplete="current-password" placeholder="输入密码" required></label>
        <p class="form-error" role="alert" hidden></p>
        <button type="submit" class="primary">登录 <span aria-hidden="true">→</span></button>
        <div class="login-help">演示账号与密码见项目 README。</div>
      </form>
    </section>
  </main>`;
  bindForm('login-form', async values => { await session.login(values); done(); });
}
