// js/tabs/overview.js — Overview tab: stats cards, heatmap, charts, wizard
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Local helpers (duplicated for module scope) ───────────────────────────────
const _h = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function _relTime(isoStr) {
  if (!isoStr) return '';
  const ms = Date.now() - new Date(isoStr).getTime();
  const mins = Math.round(ms / 60000);
  if (mins < 2) return 'ahora mismo';
  if (mins < 60) return `hace ${mins} min`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  return `hace ${Math.round(hours / 24)}d`;
}

export function _emptyState(icon, title, sub, ctaLabel, ctaFn) {
  const cta = (ctaLabel && ctaFn)
    ? `<button class="btn es-cta" onclick="(${ctaFn.toString()})()">${ctaLabel}</button>`
    : '';
  return `<div class="empty-state">
    <span class="es-icon">${icon}</span>
    <div class="es-title">${title}</div>
    ${sub ? `<div class="es-sub">${sub}</div>` : ''}
    ${cta}
  </div>`;
}

// ── Overview card widget ──────────────────────────────────────────────────────
export function card(label, value, sub, onclick, colorCls, actions) {
  const clickStyle = onclick ? 'cursor:pointer' : '';
  const clickAttr  = onclick ? `onclick="(${onclick.toString()})()"` : '';
  const cls = colorCls ? ` ${colorCls}` : '';
  const actHtml = actions?.length
    ? '<div class="card-actions">' + actions.map(a =>
        `<button class="btn card-actions" style="font-size:11px;padding:3px 8px;min-height:unset" onclick="event.stopPropagation();(${a.fn.toString()})()">${a.label}</button>`
      ).join('') + '</div>'
    : '';
  return `<div class="card${cls}" style="${clickStyle}" ${clickAttr} title="${onclick ? 'Ver lista' : ''}">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    ${sub ? `<div class="sub">${sub}</div>` : ''}
    ${actHtml}
  </div>`;
}

// ── Platform logos (SVG) ──────────────────────────────────────────────────────
const _platformLogos = {
  'Atari 2600':           '<svg viewBox="0 0 40 40"><rect fill="#d32f2f" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="20" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">A2K</text></svg>',
  'NES':                  '<svg viewBox="0 0 40 40"><rect fill="#4a90e2" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="18" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">NES</text></svg>',
  'SNES':                 '<svg viewBox="0 0 40 40"><rect fill="#9c27b0" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="16" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">SNES</text></svg>',
  'Game Boy':             '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#a0a0a0" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#222" text-anchor="middle" dominant-baseline="middle">GB</text></svg>',
  'Game Boy Color':       '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#90ee90" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#222" text-anchor="middle" dominant-baseline="middle">GBC</text></svg>',
  'Game Boy Advance':     '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#6600cc" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">GBA</text></svg>',
  'Nintendo 64':          '<svg viewBox="0 0 40 40"><rect fill="#c41e3a" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">N64</text></svg>',
  'Nintendo DS':          '<svg viewBox="0 0 40 40"><rect fill="#e5a35f" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">NDS</text></svg>',
  'Nintendo 3DS':         '<svg viewBox="0 0 40 40"><rect fill="#ffc000" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">3DS</text></svg>',
  'Sega Genesis':         '<svg viewBox="0 0 40 40"><rect fill="#0066cc" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">MD</text></svg>',
  'Sega Master System':   '<svg viewBox="0 0 40 40"><rect fill="#333" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">SMS</text></svg>',
  'Game Gear':            '<svg viewBox="0 0 40 40"><rect fill="#333" width="40" height="40" rx="2"/><rect fill="#ffcc00" x="5" y="5" width="30" height="30" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">GG</text></svg>',
  'PlayStation':          '<svg viewBox="0 0 40 40"><rect fill="#003087" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PS1</text></svg>',
  'PlayStation 2':        '<svg viewBox="0 0 40 40"><rect fill="#111" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PS2</text></svg>',
  'PlayStation Portable': '<svg viewBox="0 0 40 40"><rect fill="#003087" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PSP</text></svg>',
  'Dreamcast':            '<svg viewBox="0 0 40 40"><rect fill="#f4c300" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">DC</text></svg>',
  'Arcade':               '<svg viewBox="0 0 40 40"><rect fill="#ff6600" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">ARC</text></svg>',
  'MAME':                 '<svg viewBox="0 0 40 40"><rect fill="#ff6600" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">MAME</text></svg>',
};

export function _getPlatformLogo(platformName) {
  if (!platformName) return null;
  return _platformLogos[platformName] ||
    `<svg viewBox="0 0 40 40"><rect fill="#666" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">${platformName.slice(0, 3).toUpperCase()}</text></svg>`;
}
