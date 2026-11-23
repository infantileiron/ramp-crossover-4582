let noticeTimer;

export function clearNotice() {
  clearTimeout(noticeTimer);
  document.querySelector('#notice').hidden = true;
}

export function notice(message) {
  const banner = document.querySelector('#notice');
  banner.textContent = message;
  banner.hidden = false;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(clearNotice, 3500);
}

export function bindForm(id, submit) {
  const form = document.getElementById(id);
  if (!form) return;
  const error = form.querySelector('.form-error');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type=submit]');
    button.disabled = true;
    error.hidden = true;
    try {
      await submit(Object.fromEntries(new FormData(form)), form);
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
}
