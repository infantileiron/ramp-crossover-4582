export function currentPage() {
  const match = location.hash.match(/^#reports\/([1-9]\d*)$/);
  if (match) return { page: 'detail', id: match[1] };
  const key = location.hash.slice(1);
  return { page: ['routes', 'pairs', 'runs', 'reports'].includes(key) ? key : 'routes' };
}

export function go(page) {
  location.hash = page;
}
