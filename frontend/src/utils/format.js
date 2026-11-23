const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export function e(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => entities[char]);
}

const decimal = new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 });
export function sec(value, signed = false) {
  if (value == null) return '—';
  const number = Number(value);
  return `${signed && number > 0 ? '+' : ''}${decimal.format(number)}`;
}

export function time(value) {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value));
}
