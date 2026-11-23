import { e } from '../../utils/format.js';

export function sign(code, label = '') {
  return `<span class="sign sign-${code.toLowerCase()}"><b>${code}</b>${label ? `<span>${e(label)}</span>` : ''}</span>`;
}

export function routeMap(route) {
  return `<figure class="route-map" aria-label="${e(route.start_at)}经花坛岔口到${e(route.finish_at)}的路径示意">
    <div class="map-segment vertical"></div><div class="map-segment horizontal"></div>
    <div class="map-point start"></div><div class="map-point turn"></div><div class="map-point finish"></div>
    <span class="map-label start-label">${e(route.start_at)}</span><span class="map-label turn-label">花坛岔口</span><span class="map-label finish-label">${e(route.finish_at)}</span>
    <span class="map-caption">动线示意 · 非等比</span><span class="map-arrow" aria-hidden="true">↑</span>
  </figure>`;
}
