// js/tabs/overview.js — Overview tab: stats cards, heatmap, charts, wizard
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { gamesState } from './games.js';
import { getDeviceConnected, getDeviceConnectReason } from '../state.js';

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

// ── Platform badge helper (duplicated for module scope) ───────────────────────
const _PLAT_CLASS = {
  gba: 'gba', 'game boy advance': 'gba',
  snes: 'snes', 'super nintendo': 'snes',
  nes: 'nes', 'nintendo': 'nes',
  gb: 'gb', 'game boy': 'gb',
  gbc: 'gbc', 'game boy color': 'gbc',
  nds: 'nds', 'nintendo ds': 'nds',
  '3ds': '3ds', 'nintendo 3ds': '3ds',
  n64: 'snes', 'nintendo 64': 'snes',
  psx: 'psx', 'playstation': 'psx',
  ps2: 'ps2', 'playstation 2': 'ps2',
  psp: 'psp', 'playstation portable': 'psp',
  genesis: 'genesis', 'mega drive': 'md', md: 'md',
  sms: 'sms', 'master system': 'sms',
  gg: 'gg', 'game gear': 'gg',
};
function _platBadge(plat) {
  if (!plat) return '<span class="plat plat-other">?</span>';
  const cls = _PLAT_CLASS[plat.toLowerCase()] || 'other';
  return `<span class="plat plat-${cls}">${_h(plat)}</span>`;
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
const _heatmapState = { cellMap: new Map() };

export async function _renderActivityHeatmap() {
  const canvas = document.getElementById('ov-heatmap');
  if (!canvas) return;
  try {
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];

    const today = new Date();
    const dayActivity = {};
    games.forEach(g => {
      if (!g.last_played_at) return;
      const dateStr = g.last_played_at.split('T')[0];
      dayActivity[dateStr] = (dayActivity[dateStr] || 0) + 1;
    });

    const maxVal = Math.max(...Object.values(dayActivity), 0);
    const ctx = canvas.getContext('2d');
    const cellSize = 12;
    const cellGap  = 2;
    const padding  = 10;

    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    _heatmapState.cellMap.clear();

    const weeks = 52;
    const days  = 7;
    let cellX = padding;
    for (let week = 0; week < weeks; week++) {
      let cellY = padding;
      for (let day = 0; day < days; day++) {
        const daysAgo = (weeks - 1 - week) * 7 + (6 - day);
        const d = new Date(today);
        d.setDate(d.getDate() - daysAgo);
        const dateStr = d.toISOString().split('T')[0];

        const count     = dayActivity[dateStr] || 0;
        const intensity = maxVal > 0 ? count / maxVal : 0;

        ctx.fillStyle = _getHeatmapColor(intensity);
        ctx.fillRect(cellX, cellY, cellSize, cellSize);
        ctx.strokeStyle = '#1a1a2e';
        ctx.lineWidth   = 0.5;
        ctx.strokeRect(cellX, cellY, cellSize, cellSize);

        _heatmapState.cellMap.set(week + ',' + day, { x: cellX, y: cellY, dateStr, count, cellSize });
        cellY += cellSize + cellGap;
      }
      cellX += cellSize + cellGap;
    }

    canvas.onmousemove  = (e) => _handleHeatmapHover(e, canvas);
    canvas.onmouseleave = () => { canvas.title = ''; };
  } catch(err) {
    console.error('Heatmap error:', err);
  }
}

function _getHeatmapColor(intensity) {
  if (intensity === 0)    return 'var(--c-deep)';
  if (intensity < 0.25)   return '#0d3922';
  if (intensity < 0.5)    return '#0d5c2c';
  if (intensity < 0.75)   return '#1a7938';
  return '#3fb950';
}

function _handleHeatmapHover(e, canvas) {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  let found = false;
  for (const [, cell] of _heatmapState.cellMap) {
    if (x >= cell.x && x <= cell.x + cell.cellSize && y >= cell.y && y <= cell.y + cell.cellSize) {
      const d = new Date(cell.dateStr);
      const dateStr = d.toLocaleDateString('es-ES', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
      canvas.title = `${dateStr}: ${cell.count} juego${cell.count !== 1 ? 's' : ''}`;
      found = true;
      break;
    }
  }
  if (!found) canvas.title = '';
}

// ── Game suggestion (stale games) ─────────────────────────────────────────────
let _currentGameSuggestion = null;

export async function _loadNewGameSuggestion() {
  try {
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    const staleGames = games.filter(g => {
      if (!g.last_played_at) return true;
      return new Date(g.last_played_at) < sixMonthsAgo;
    });

    if (staleGames.length === 0) {
      const container = document.getElementById('ov-game-suggestion');
      if (container) container.innerHTML = '<div style="padding:20px;color:var(--c-hint);text-align:center;width:100%">¡Excelente! No tienes juegos olvidados. ¡Sigue jugando!</div>';
      return;
    }

    const suggestion = staleGames[Math.floor(Math.random() * staleGames.length)];
    _currentGameSuggestion = suggestion;

    const titleEl = document.getElementById('ov-game-suggestion-title');
    const metaEl  = document.getElementById('ov-game-suggestion-meta');
    const imgEl   = document.getElementById('ov-game-suggestion-img');

    if (titleEl) titleEl.textContent = suggestion.canonical_title || suggestion.original_filename;
    if (metaEl) {
      const lastPlay = suggestion.last_played_at ? _relTime(suggestion.last_played_at) : 'Nunca';
      metaEl.innerHTML = `${_platBadge(suggestion.platform || '')} · Última vez: ${lastPlay}`;
    }
    if (imgEl) {
      imgEl.src     = `/api/asset-image?game_id=${suggestion.id}`;
      imgEl.onerror = () => { imgEl.classList.add('hidden'); };
    }
  } catch(err) {
    console.error('Game suggestion error:', err);
  }
}

// ── Monthly activity chart ────────────────────────────────────────────────────
export async function _renderMonthlyChart() {
  const canvas = document.getElementById('ov-monthly-chart');
  if (!canvas) return;
  try {
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];

    const monthlyData = {};
    const platforms   = new Set();
    const now         = new Date();
    const startDate   = new Date(now);
    startDate.setMonth(startDate.getMonth() - 11);

    games.forEach(g => {
      if (!g.last_played_at) return;
      const playDate = new Date(g.last_played_at);
      if (playDate < startDate) return;
      const monthKey = playDate.toISOString().substring(0, 7);
      if (!monthlyData[monthKey]) monthlyData[monthKey] = {};
      const plat = g.platform || 'Unknown';
      if (!monthlyData[monthKey][plat]) monthlyData[monthKey][plat] = new Set();
      monthlyData[monthKey][plat].add(g.id);
      platforms.add(plat);
    });

    const months = Object.keys(monthlyData).sort();
    const ctx    = canvas.getContext('2d');

    if (months.length === 0) {
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#555';
      ctx.font      = '12px monospace';
      ctx.fillText('Sin datos. Escanea la biblioteca primero.', 20, canvas.height / 2);
      return;
    }

    const colors     = ['var(--c-blue)', 'var(--c-teal)', 'var(--c-yellow)', 'var(--c-orange)', 'var(--c-lblue)', 'var(--c-purple)', '#a7ec21', 'var(--c-red)'];
    const platArray  = Array.from(platforms).sort();
    const barWidth   = 8;
    const groupGap   = 16;
    const padding    = 40;
    const chartHeight = canvas.height - padding * 1.5;

    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    let maxVal = 0;
    months.forEach(m => platArray.forEach(p => {
      maxVal = Math.max(maxVal, monthlyData[m]?.[p]?.size || 0);
    }));
    maxVal = Math.max(maxVal, 1);

    let x = padding;
    months.forEach(month => {
      platArray.forEach((plat, platIdx) => {
        const count     = monthlyData[month]?.[plat]?.size || 0;
        const barHeight = (count / maxVal) * chartHeight;
        ctx.fillStyle = colors[platIdx % colors.length];
        ctx.fillRect(x, canvas.height - padding + 20 - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      });
      x += groupGap;
    });

    // Axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth   = 1;
    ctx.beginPath(); ctx.moveTo(padding, canvas.height - padding); ctx.lineTo(canvas.width - padding, canvas.height - padding); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(padding, canvas.height - padding); ctx.lineTo(padding, padding); ctx.stroke();

    // Month labels
    ctx.fillStyle   = '#666';
    ctx.font        = '10px monospace';
    ctx.textAlign   = 'center';
    x = padding + (barWidth * platArray.length + 1) * 0.5 + groupGap * 0.5;
    months.forEach((month, idx) => {
      if (idx % 2 === 0) ctx.fillText(month.substring(5), x, canvas.height - padding + 15);
      x += (barWidth + 1) * platArray.length + groupGap;
    });

    // Legend
    ctx.textAlign = 'left';
    ctx.font      = '11px monospace';
    let legX = padding;
    let legY = 20;
    platArray.forEach((plat, idx) => {
      ctx.fillStyle = colors[idx % colors.length];
      ctx.fillRect(legX, legY, 10, 10);
      ctx.fillStyle = '#d4d4d4';  // canvas can't resolve CSS vars; chart bg is always dark
      ctx.fillText(plat, legX + 15, legY + 9);
      legX += 120;
      if (legX > canvas.width - 100) { legX = padding; legY += 14; }
    });
  } catch(err) {
    console.error('Monthly chart error:', err);
  }
}

// ── Additional local helpers (duplicated for module scope) ────────────────────
const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

function fmtSize(n) {
  const units = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

function _updateKpis(d) {
  const sc = d.status_counts || {};
  const _set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  _set('kpi-size-val',      d.total_size_bytes != null ? fmtSize(d.total_size_bytes) : '—');
  _set('kpi-completed-val', (sc['completed'] || 0).toLocaleString());
  _set('kpi-playing-val',   (sc['playing']   || 0).toLocaleString());
  _set('kpi-pending-val',   (sc['pending']   || 0).toLocaleString());
  _set('kpi-abandoned-val', (sc['abandoned'] || 0).toLocaleString());
}

const _PLAT_HEX = {
  gba: 'var(--c-teal)', snes: 'var(--c-blue)', nes: 'var(--c-red)', gb: 'var(--c-yellow)',
  gbc: '#d7ba7d', nds: 'var(--c-purple)', '3ds': 'var(--c-lblue)', n64: 'var(--c-teal)',
  psx: 'var(--c-lblue)', ps2: 'var(--c-blue)', psp: '#79c0ff',
  genesis: 'var(--c-orange)', md: 'var(--c-orange)', sms: 'var(--c-green)', gg: 'var(--c-teal)',
};
function _platHex(plat) {
  const cls = _PLAT_CLASS[(plat||'').toLowerCase()] || 'other';
  return _PLAT_HEX[cls] || '#555';
}

// UX-1/2-4: Update device connectivity badge
function _updateDeviceConnectivityBadge() {
  const badge = document.getElementById('ov-ab-device-badge');
  if (!badge) return;

  const connected = getDeviceConnected();
  const reason = getDeviceConnectReason();

  if (connected) {
    badge.classList.add('hidden');
  } else {
    badge.classList.remove('hidden');
    badge.style.color = 'var(--c-red)';
    badge.style.borderColor = '#4a2a2a';
    badge.style.backgroundColor = '#2a1a1a';
    badge.textContent = '● No conectado';
    badge.title = reason || 'Consola Android no disponible';
  }
}

// ── Overview load ─────────────────────────────────────────────────────────────
export async function loadOverview() {
  try {
    const _t = Date.now();
    const cfg = await apiFetch('/api/config?t=' + _t);

    // Apply device name to all labels
    _applyDeviceName(cfg.device_name || 'Consola Android');

    // UX-1/2-4: Update device connectivity badge
    _updateDeviceConnectivityBadge();

    // Populate path inputs (only if empty)
    const pcInput = document.getElementById('ov-pc-path');
    const abInput = document.getElementById('ov-ab-path');
    const pcPath  = pcInput?.value.trim() || cfg.library_root || '';
    const abStored = cfg.anbernic_root || localStorage.getItem('anbernic_path') || '';
    const abAdbPath = localStorage.getItem('anbernic_adb_path') || '';
    const abPath   = abInput?.value.trim() || abStored || abAdbPath;
    if (pcInput && !pcInput.value) pcInput.value = pcPath;
    if (abInput && !abInput.value) abInput.value = abPath;

    // Update path labels in stats columns
    const pcLbl = document.getElementById('ov-pc-path-label');
    const abLbl = document.getElementById('ov-ab-path-label');
    if (pcLbl) pcLbl.textContent = pcPath ? '— ' + pcPath : '';
    if (abLbl) abLbl.textContent = abPath ? '— ' + abPath : '';

    // Update scan checkboxes
    const pcLabel = document.getElementById('scan-pc-label');
    const abLabel = document.getElementById('scan-ab-label');
    const abCb    = document.getElementById('scan-include-ab');
    if (pcLabel) pcLabel.textContent = pcPath || '(configura la ruta arriba)';
    if (abLabel) abLabel.textContent = abPath || '(configura la ruta arriba)';
    if (abCb) { abCb.disabled = !abPath; if (abPath && !abCb.checked) abCb.checked = true; }

    // Enable/disable Anbernic device button
    const devAb = document.getElementById('dev-anbernic');
    if (devAb) devAb.disabled = !abPath;

    // Config summary
    const cfgEl = document.getElementById('ov-config-summary');
    if (cfgEl) {
      cfgEl.innerHTML = `<div class="config-grid" style="max-width:560px">
        <span class="cfg-key">library_root</span>
        <span class="cfg-val ${cfg.library_root ? '' : 'missing'}">${cfg.library_root || '(not set — configura en Settings)'}</span>
        <span class="cfg-key">rclone remote</span>
        <span class="cfg-val ${cfg.rclone_remote ? '' : 'missing'}">${cfg.rclone_remote || '(not set)'}</span>
        <span class="cfg-key">ScreenScraper</span>
        <span class="cfg-val ${cfg.screenscraper_user ? '' : 'missing'}">${cfg.screenscraper_user || '(not set)'}</span>
        <span class="cfg-key">web</span>
        <span class="cfg-val">${cfg.web_host}:${cfg.web_port}</span>
      </div>`;
    }

    // Fetch PC stats (filter by library_root)
    const pcCardsEl = document.getElementById('ov-pc-cards');
    try {
      const pcParam = (pcPath ? '?root=' + encodeURIComponent(pcPath) + '&' : '?') + 't=' + _t;
      const d = await apiFetch('/api/status' + pcParam);
      const matchPct = d.total_games > 0 ? Math.round(d.matched_games / d.total_games * 100) : 0;
      if (pcCardsEl) pcCardsEl.innerHTML =
        card('Games',      d.total_games,     null, () => goToGames(pcPath, ''), '', d.total_games > 0 ? [{label:'Ver juegos', fn:()=>showTab('games')}] : null)          +
        card('Matched',    d.matched_games,    matchPct + '% matched', () => goToGames(pcPath, 'matched'), 'blue')    +
        card('Unmatched',  d.unmatched_games,  null, () => goToGames(pcPath, 'unmatched'), 'orange', d.unmatched_games > 0 ? [{label:'Identificar →', fn:()=>showTab('plan')}] : null)  +
        card('Saves',      d.total_saves,      null, d.total_saves > 0 ? () => goToGames(pcPath, '', 'save') : null, 'purple')      +
        card('Assets',     d.total_assets,     null, d.total_assets > 0 ? () => { showTab('assets'); } : null)     +
        card('Duplicados', d.duplicate_groups, fmtSize(d.wasted_bytes) + ' wasted', d.duplicate_groups > 0 ? () => showTab('duplicates') : null, d.duplicate_groups > 0 ? 'red' : '', d.duplicate_groups > 0 ? [{label:'Ver', fn:()=>showTab('duplicates')}] : null) +
        card('Último scan', d.last_scan_at ? d.last_scan_at.replace('T',' ').slice(0,16) : 'nunca');
      // UI-2: populate dashboard bar
      const dsGames     = document.getElementById('ds-games');
      const dsPlatforms = document.getElementById('ds-platforms');
      const dsSync      = document.getElementById('ds-sync');
      const dsHealth    = document.getElementById('ds-health');
      if (dsGames)     dsGames.textContent     = d.total_games.toLocaleString();
      if (dsPlatforms) dsPlatforms.textContent = d.total_platforms || '—';
      if (dsSync) {
        dsSync.textContent = d.last_sync_at ? _relTime(d.last_sync_at) : 'nunca';
        dsSync.title = d.last_sync_at ? d.last_sync_at.replace('T',' ').slice(0,16) : '';
      }
      if (dsHealth) {
        const h = d.health || {};
        if (h.last_ok !== undefined) {
          const problems = (h.last_corrupted || 0) + (h.last_missing || 0);
          if (problems === 0) {
            dsHealth.innerHTML = `<span style="color:var(--accent-grn)">${h.last_ok.toLocaleString()} OK ✓</span>`;
          } else {
            dsHealth.innerHTML = `<span style="color:var(--fg)">${h.last_ok.toLocaleString()} OK</span> <span style="color:var(--accent-red);margin-left:4px">${problems} ⚠</span>`;
          }
        } else {
          dsHealth.innerHTML = '<span style="color:var(--fg-4)">sin datos</span>';
        }
      }
      // Bloque 7: KPI row
      _updateKpis(d);
      // Auto-collapse guide when library already has data
      const guide = document.getElementById('ov-guide');
      if (guide && d.total_games > 0 && localStorage.getItem('guide_closed') !== '0') {
        guide.removeAttribute('open');
      } else if (guide && d.total_games === 0) {
        guide.setAttribute('open', '');
      }
      // D8-P1: setup banner + auto-show wizard on first run
      const setupBanner = document.getElementById('ov-setup-banner');
      if (setupBanner) {
        if (d.first_run || !d.setup_complete) {
          setupBanner.classList.remove('hidden');
          const cl = d.setup_checklist || {};
          const chk = (ok, label, hint) =>
            '<div>' + (ok ? '<span style="color:var(--c-teal)">&#x2611;</span>' : '<span style="color:var(--c-hint)">&#x2610;</span>') +
            ' <span style="color:' + (ok ? 'var(--c-text)' : '#888') + '">' + label + '</span>' +
            (hint && !ok ? ' <span style="color:var(--c-dim);font-size:11px">— ' + hint + '</span>' : '') + '</div>';
          const clEl = document.getElementById('ov-setup-checklist');
          if (clEl) clEl.innerHTML =
            chk(cl.library_root_set, 'Carpeta configurada', 'Configura en Settings') +
            chk(cl.scanned, 'Biblioteca escaneada', 'Lanza el asistente') +
            chk(cl.catalogs_loaded, 'Catalogos DAT cargados', 'Copia .dat/.xml a .rommgr/catalogs/nointro/') +
            chk(cl.matched, 'Juegos identificados', 'Ejecuta Match catalogo');
        } else {
          setupBanner.classList.add('hidden');
        }
      }
      // Auto-show wizard only on first page load if first_run
      if (d.first_run && !localStorage.getItem('wizard_dismissed')) {
        showWizard(pcPath || cfg.library_root || '', cfg.anbernic_root || '');
      }
    } catch(e) {
      if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
    }

    // Fetch Anbernic stats (if path configured)
    const abCardsEl  = document.getElementById('ov-ab-cards');
    const abDot      = document.getElementById('ov-ab-dot');
    const abStaleBadge = document.getElementById('ov-ab-stale-badge');
    const abScanBtn    = document.getElementById('ov-ab-scan-btn');
    if (abPath && abCardsEl) {
      try {
        const ab = await apiFetch('/api/status?root=' + encodeURIComponent(abPath) + '&t=' + _t);
        const abMatchPct = ab.total_games > 0 ? Math.round(ab.matched_games / ab.total_games * 100) : 0;
        if (abDot) _txtCls(abDot, ab.total_games > 0 ? 'txt-ok' : 'txt-dim');
        if (abStaleBadge) abStaleBadge.classList.toggle('hidden', !(ab.stale));
        if (abScanBtn)    abScanBtn.classList.toggle('hidden', !((ab.stale || ab.total_games === 0)));
        const lastScans = ab.last_scans_by_root || {};
        const abLastScan = Object.entries(lastScans).find(([k]) => abPath && k.toLowerCase().startsWith(abPath.toLowerCase()))?.[1] || null;
        if (ab.total_games === 0) {
          if (abCardsEl) abCardsEl.innerHTML = `<p id="ov-ab-empty-msg" style="color:var(--c-yellow);font-size:12px;padding:10px 0">&#x26A0; Ruta configurada pero sin datos escaneados. Activa el checkbox de <em>${_devName}</em> en <em>Gestión de biblioteca</em> y lanza un Scan.</p>`;
        } else {
          const lastScanStr = abLastScan ? abLastScan.replace('T',' ').slice(0,16) : 'nunca';
          const daysAgo = ab.scan_days_ago !== null && ab.scan_days_ago !== undefined ? ab.scan_days_ago : null;
          const scanSub = daysAgo !== null ? 'hace ' + daysAgo + ' día' + (daysAgo !== 1 ? 's' : '') : 'nunca';
          if (abCardsEl) abCardsEl.innerHTML =
            card('Games',      ab.total_games,    null, () => goToGames(abPath, ''), '')          +
            card('Matched',    ab.matched_games,   abMatchPct + '% matched', () => goToGames(abPath, 'matched'), 'blue')  +
            card('Unmatched',  ab.unmatched_games, null, () => goToGames(abPath, 'unmatched'), 'orange')  +
            card('Saves',      ab.total_saves,     null, ab.total_saves > 0 ? () => goToGames(abPath, '', 'save') : null, 'purple')     +
            card('Assets',     ab.total_assets,   null, ab.total_assets > 0 ? () => { showTab('assets'); } : null)   +
            card('Último scan', lastScanStr, scanSub);
        }
      } catch(e) {
        if (abCardsEl) abCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
      }
    } else if (!abPath && abCardsEl) {
      abCardsEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px;padding:10px 0">Configura la ruta de la consola Android en el panel de abajo para ver sus estadísticas.</p>';
      if (abStaleBadge) abStaleBadge.classList.add('hidden');
      if (abScanBtn)    abScanBtn.classList.add('hidden');
    }

    // Recently played (hero card + horizontal scroll)
    const recentEl     = document.getElementById('ov-recently-played');
    const heroEl       = document.getElementById('ov-hero-game');
    const contSection  = document.getElementById('ov-continue-section');
    const contScroll   = document.getElementById('ov-continue-scroll');
    try {
      const pcParam2 = (pcPath ? '?root=' + encodeURIComponent(pcPath) + '&' : '?') + 't=' + (_t+2);
      const dRecent = await apiFetch('/api/status' + pcParam2);
      if (dRecent.recently_played && dRecent.recently_played.length > 0) {
        const games = dRecent.recently_played;
        const last = games[0];
        if (heroEl) {
          heroEl.classList.remove('hidden');
          heroEl.innerHTML = `<div class="hero-game" style="border-left-color:${_platHex(last.platform)};cursor:pointer" onclick="openGamePanel(${JSON.stringify(last).replace(/</g,'\\u003c')})">
            <img src="/api/asset-image?game_id=${last.id}" onerror="this.classList.add('hidden')" alt="">
            <div class="hg-body">
              <div class="hg-label">Continuar jugando</div>
              <div class="hg-title">${_h(last.canonical_title || last.original_filename)}</div>
              <div class="hg-meta">${_platBadge(last.platform)} · ${_relTime(last.last_played_at)}</div>
            </div>
          </div>`;
        }
        if (contScroll && contSection) {
          contSection.classList.remove('hidden');
          contScroll.innerHTML = games.slice(0, 6).map(g => {
            const gj = JSON.stringify(g).replace(/</g,'\\u003c');
            return `<div class="continue-card" onclick="openGamePanel(${gj})" title="${_h(g.canonical_title||g.original_filename)}">
              <div class="cc-cover">
                <img src="/api/asset-image?game_id=${g.id}" onerror="this.parentElement.innerHTML='&#127918;'" alt="">
              </div>
              <div class="cc-info">
                <div class="cc-title">${_h(g.canonical_title||g.original_filename)}</div>
                <div class="cc-plat">${_h(g.platform||'')} · ${_relTime(g.last_played_at)}</div>
              </div>
            </div>`;
          }).join('');
        }
        if (recentEl) recentEl.innerHTML = games.map(g => {
          const title = g.canonical_title || g.original_filename;
          return `<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--c-panel);font-size:12px;cursor:pointer" onclick="openGamePanel(${JSON.stringify(g).replace(/</g,'\\u003c')})">
            <span>${_platBadge(g.platform)} <span style="color:var(--c-text)">${_h(title)}</span></span>
            <span style="color:var(--c-dim)">${_relTime(g.last_played_at)}</span>
          </div>`;
        }).join('');
      } else {
        if (heroEl) heroEl.classList.add('hidden');
        if (contSection) contSection.classList.add('hidden');
        if (recentEl) recentEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Juega un rato y vuelve aquí.</p>';
      }
    } catch(_) {
      if (heroEl) heroEl.classList.add('hidden');
      if (contSection) contSection.classList.add('hidden');
      if (recentEl) recentEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px">—</p>';
    }

    // Platform breakdown chart
    const chartEl = document.getElementById('ov-platform-chart');
    if (chartEl && pcPath) {
      try {
        const ps = await apiFetch('/api/platform-stats?root=' + encodeURIComponent(pcPath));
        if (ps.platforms && ps.platforms.length > 0) {
          const maxCount = ps.platforms[0].count;
          chartEl.innerHTML = ps.platforms.slice(0, 15).map(p => {
            const pct = Math.round(p.count / maxCount * 100);
            return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:12px">
              <span style="width:110px;color:var(--c-muted);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(p.platform)}">${_h(p.platform)}</span>
              <div style="flex:1;background:var(--c-panel);border-radius:2px;height:14px">
                <div style="width:${pct}%;background:var(--c-blue);height:14px;border-radius:2px;transition:width 0.3s"></div>
              </div>
              <span style="width:40px;color:var(--c-text);font-size:11px">${p.count}</span>
            </div>`;
          }).join('');
        } else {
          chartEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Sin datos. Escanea la biblioteca primero.</p>';
        }
      } catch(_) { /* silent */ }
    }

    // Show report available notice
    try {
      const pcStatusForReport = await apiFetch('/api/status' + (pcPath ? '?root=' + encodeURIComponent(pcPath) + '&t=' + (_t+1) : ('?t=' + (_t+1))));
      const reportNoticeEl = document.getElementById('ov-report-notice');
      if (reportNoticeEl) {
        if (pcStatusForReport.last_report_at && pcStatusForReport.last_report_mins_ago !== null) {
          const mins = pcStatusForReport.last_report_mins_ago;
          const timeStr = mins < 60 ? ('hace ' + mins + ' min') : ('hace ' + Math.round(mins/60) + 'h');
          reportNoticeEl.classList.remove('hidden');
          reportNoticeEl.innerHTML = '<span style="color:var(--c-yellow);font-size:12px">&#x1F4CA; Informe disponible — generado ' + timeStr + '</span> '
            + '<a href="/api/report/html' + (pcPath ? '?path=' + encodeURIComponent(pcPath) : '') + '" target="_blank" class="btn" style="padding:2px 8px;font-size:11px;margin-left:8px">Ver informe</a>';
        } else {
          reportNoticeEl.classList.add('hidden');
        }
      }
    } catch(_) {}

    // Render platform grid
    if (pcPath) {
      try { _renderPlatformGrid(pcPath); } catch(_) { /* silent */ }
    }

    // Render activity heatmap
    try { _renderActivityHeatmap(); } catch(e) { console.error('Heatmap error:', e); }

    // Render monthly analysis chart
    try { _renderMonthlyChart(); } catch(e) { console.error('Monthly chart error:', e); }

    // Load collection completeness
    try { loadCollectionCompleteness(pcPath); } catch(e) { console.error('Completeness error:', e); }

    // Load game suggestion
    try { _loadNewGameSuggestion(); } catch(e) { console.error('Game suggestion error:', e); }

  } catch(e) {
    const pcCardsEl = document.getElementById('ov-pc-cards');
    if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Collection completeness ───────────────────────────────────────────────────
export async function loadCollectionCompleteness(root) {
  const el = document.getElementById('ov-completeness');
  if (!el) return;
  try {
    const params = root ? `?root=${encodeURIComponent(root)}` : '';
    const d = await apiFetch('/api/collection-completeness' + params);
    const platforms = d.platforms || [];
    if (!platforms.length) { el.innerHTML = '<span style="color:var(--c-dim)">Sin catálogos cargados. Descarga DATs en Ajustes → Catálogos.</span>'; return; }
    const rows = platforms.map(p => {
      const pct = p.pct ?? null;
      const barW = pct !== null ? Math.min(pct, 100) : 0;
      const clr = pct === null ? 'var(--c-dim)' : pct >= 80 ? 'var(--c-teal)' : pct >= 30 ? 'var(--c-amber)' : 'var(--c-softred)';
      const totalTxt = p.total !== null ? `${p.owned} / ${p.total}` : `${p.owned}`;
      const pctTxt = pct !== null ? ` (${pct}%)` : '';
      return `<div style="display:grid;grid-template-columns:1fr 90px 120px;align-items:center;gap:8px;padding:3px 0;font-size:12px">
        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--c-text)">${p.label}</div>
        <div style="color:${clr};text-align:right;white-space:nowrap">${totalTxt}${pctTxt}</div>
        <div style="background:var(--c-panel);border-radius:3px;height:6px;overflow:hidden">
          <div style="background:${clr};height:100%;width:${barW}%;transition:width .4s"></div>
        </div>
      </div>`;
    });
    el.innerHTML = rows.join('');
  } catch(e) { el.innerHTML = `<span style="color:var(--c-softred);font-size:12px">Error: ${e.message}</span>`; }
}

// ── Platform grid ─────────────────────────────────────────────────────────────
export async function _renderPlatformGrid(pcPath) {
  const gridEl = document.getElementById('ov-platform-grid');
  if (!gridEl) return;

  try {
    const ps = await apiFetch('/api/platform-stats?root=' + encodeURIComponent(pcPath));
    if (!ps.platforms || ps.platforms.length === 0) {
      gridEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Sin datos. Escanea la biblioteca primero.</p>';
      return;
    }

    const maxCount = Math.max(...ps.platforms.map(p => p.count));

    gridEl.innerHTML = ps.platforms.slice(0, 12).map((p, idx) => {
      const logo = _getPlatformLogo(p.platform);
      const size = Math.max(40, Math.round(p.count / maxCount * 100));
      const platName = _h(p.platform || '?');
      return `<div class="platform-tile" data-idx="${idx}"
        style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:12px;background:var(--c-panel);border:1px solid #2a2a3a;border-radius:6px;cursor:pointer;transition:all 0.2s;text-align:center"
        onmouseover="this.style.background='#252535';this.style.borderColor='#3a3a5c'"
        onmouseout="this.style.background='var(--c-panel)';this.style.borderColor='#2a2a3a'">
        <div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center">${logo}</div>
        <div style="font-size:11px;font-weight:600;color:var(--c-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%" title="${platName}">${platName}</div>
        <div style="font-size:10px;color:var(--c-muted)">${p.count} game${p.count !== 1 ? 's' : ''}</div>
      </div>`;
    }).join('');

    ps.platforms.slice(0, 12).forEach((p, idx) => {
      const tile = gridEl.querySelector(`[data-idx="${idx}"]`);
      if (tile) {
        tile.addEventListener('click', () => {
          gamesState.root = pcPath;
          gamesState.status = '';
          gamesState.platform = p.platform || '';
          gamesState.filetype = '';
          showTab('games');
        });
      }
    });
  } catch(_) {
    gridEl.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Error al cargar plataformas.</p>';
  }
}

// ── Setup Wizard ──────────────────────────────────────────────────────────────
let _wizardPollingTimer = null;

export function showWizard(prefillPcPath, prefillAndroidPath) {
  const modal = document.getElementById('wizard-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  document.getElementById('wizard-page-1').classList.remove('hidden');
  document.getElementById('wizard-page-2').classList.add('hidden');
  document.getElementById('wizard-page-3').classList.add('hidden');
  const pcInp = document.getElementById('wiz-library-root');
  if (pcInp && !pcInp.value && prefillPcPath) pcInp.value = prefillPcPath;
  const andInp = document.getElementById('wiz-android-root');
  if (andInp && !andInp.value && prefillAndroidPath) andInp.value = prefillAndroidPath;
}

export function closeWizard() {
  const modal = document.getElementById('wizard-modal');
  if (modal) modal.classList.add('hidden');
  localStorage.setItem('wizard_dismissed', '1');
  if (_wizardPollingTimer) { clearInterval(_wizardPollingTimer); _wizardPollingTimer = null; }
}

export async function wizardAutoDetect() {
  const btn = document.getElementById('wiz-detect-btn');
  const msg = document.getElementById('wiz-detect-msg');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando\u2026'; }
  if (msg) { msg.classList.add('hidden'); }
  try {
    const d = await apiFetch('/api/wizard-detect');
    const lines = [];
    const pcInp = document.getElementById('wiz-library-root');
    if (pcInp && !pcInp.value && d.library_root_suggestion) {
      pcInp.value = d.library_root_suggestion;
      lines.push('\u2705 Carpeta PC detectada: <strong>' + d.library_root_suggestion + '</strong>');
    } else if (!d.library_root_suggestion) {
      lines.push('\u26A0\uFE0F No se encontr\u00F3 RetroArch en rutas habituales. Introduce la carpeta manualmente.');
    }
    const andInp = document.getElementById('wiz-android-root');
    if (andInp && !andInp.value && d.android_suggestion) {
      andInp.value = d.android_suggestion;
      lines.push('\u2705 Consola Android conectada: <strong>' + (d.device_display || d.android_suggestion) + '</strong>');
    } else if (!d.android_suggestion && d.adb_ok) {
      lines.push('\u{1F4F1} ADB listo pero no hay consola conectada.');
    }
    if (msg) {
      msg.innerHTML = lines.join('<br>') || '\u{1F50D} Detecci\u00F3n completada.';
      msg.classList.remove('hidden');
    }
  } catch(e) {
    if (msg) { msg.innerHTML = '\u274C Error al detectar: ' + e.message; msg.classList.remove('hidden'); }
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '&#x1F50D; Detectar autom&#xe1;ticamente'; }
  }
}

export async function startSetup() {
  const libRoot     = (document.getElementById('wiz-library-root')?.value || '').trim();
  const androidRoot = (document.getElementById('wiz-android-root')?.value || '').trim();
  if (!libRoot) { alert('Introduce la carpeta de biblioteca (PC) primero.'); return; }
  const cleanJunk   = document.getElementById('wiz-clean-junk')?.checked || false;
  const extractZips = document.getElementById('wiz-extract-zips')?.checked !== false;
  const deleteZips  = document.getElementById('wiz-delete-zips')?.checked || false;
  const doMatch     = document.getElementById('wiz-match')?.checked !== false;

  document.getElementById('wizard-page-1').classList.add('hidden');
  document.getElementById('wizard-page-2').classList.remove('hidden');
  _renderWizSteps(null);

  try {
    await apiPost('/api/setup-run', {
      library_root:  libRoot,
      android_root:  androidRoot,
      clean_junk:    cleanJunk,
      extract_zips:  extractZips,
      delete_zips:   deleteZips,
      scan:          true,
      match:         doMatch,
    });
    startPolling();
    _wizardPollingTimer = setInterval(_pollSetupProgress, 2000);
  } catch(e) {
    document.getElementById('wizard-page-2').classList.add('hidden');
    document.getElementById('wizard-page-1').classList.remove('hidden');
    alert('Error al iniciar: ' + e.message + '\n\nConsulta los logs para más detalles.');
  }
}

export function _renderWizSteps(progress) {
  const stepsEl = document.getElementById('wiz-steps');
  if (!stepsEl) return;
  const steps = [
    'Limpiando archivos no relacionados',
    'Extrayendo ZIPs',
    'Escaneando biblioteca',
    'Cruzando con catalogos No-Intro/Redump',
    'Preparando plan de renombrado',
  ];
  const current = progress ? (progress.step_num || 0) : 0;
  const pct = progress ? (progress.pct || 0) : 0;
  stepsEl.innerHTML = steps.map((s, i) => {
    const n = i + 1;
    let icon, color;
    if (n < current) { icon = '&#x2705;'; color = 'var(--c-teal)'; }
    else if (n === current) { icon = '&#x23F3;'; color = '#c9bcf5'; }
    else { icon = '&nbsp;&nbsp;&nbsp;'; color = '#444'; }
    return '<div style="font-size:13px;color:' + color + ';margin-bottom:6px">' + icon + ' <span style="color:var(--c-muted);font-size:11px">Paso ' + n + '/5</span>  ' + s + '</div>';
  }).join('');
  const bar = document.getElementById('wiz-prog-bar');
  if (bar) bar.style.width = pct + '%';
  const fileEl = document.getElementById('wiz-prog-file');
  if (fileEl) fileEl.textContent = progress ? (progress.current_file || '') : '';
}

export async function _pollSetupProgress() {
  try {
    const s = await apiFetch('/api/setup-status');
    if (s.setup_progress) _renderWizSteps(s.setup_progress);
    if (!s.setup_running && s.setup_result) {
      if (_wizardPollingTimer) { clearInterval(_wizardPollingTimer); _wizardPollingTimer = null; }
      _showSetupResult(s.setup_result);
    }
  } catch(_) {}
}

export function _showSetupResult(r) {
  document.getElementById('wizard-page-2').classList.add('hidden');
  document.getElementById('wizard-page-3').classList.remove('hidden');
  const el = document.getElementById('wiz-result-stats');
  if (!el) return;
  if (r.error) {
    el.innerHTML = '<span style="color:var(--c-red)">Error: ' + _h(r.error) + '</span><span style="color:var(--c-muted);font-size:12px;margin-left:8px">— Recarga la página o comprueba que hay ROMs escaneados.</span>';
    return;
  }
  const fmtB = (b) => b >= 1048576 ? (b/1048576).toFixed(1) + ' MB' : b >= 1024 ? (b/1024).toFixed(0) + ' KB' : b + ' B';
  let html = '';
  html += '<div>&#x2022; <strong>' + (r.games_found || 0) + '</strong> juegos encontrados</div>';
  html += '<div>&#x2022; <strong>' + (r.games_matched || 0) + '</strong> identificados con nombre canonico</div>';
  if (r.junk_deleted > 0) html += '<div>&#x2022; <strong>' + r.junk_deleted + '</strong> archivos basura eliminados (' + fmtB(r.junk_freed_bytes || 0) + ' liberados)</div>';
  if (r.zips_extracted > 0) html += '<div>&#x2022; <strong>' + r.zips_extracted + '</strong> ZIPs extraidos</div>';
  html += '<div>&#x2022; <strong>' + (r.plan_pending || 0) + '</strong> archivos listos para renombrar</div>';
  el.innerHTML = html;
  loadOverview();
}

export function wizardGoToOrganize() {
  closeWizard();
  showTab('plan');
}

export async function loadActivityHeatmap() {
  const grid = document.getElementById('ov-heatmap-grid');
  if (!grid) return;
  try {
    const data = await apiFetch('/api/activity-heatmap');
    const byDate = {};
    (data.days || []).forEach(d => { byDate[d.date] = d.count; });
    // Build 52-week grid (364 days), oldest first
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const cells = [];
    for (let i = 363; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const cnt = byDate[key] || 0;
      const lvl = cnt === 0 ? '' : cnt === 1 ? 'l1' : cnt <= 3 ? 'l2' : 'l3';
      cells.push(`<div class="hm-cell ${lvl}" title="${cnt ? cnt + ' juego' + (cnt !== 1 ? 's' : '') + ' — ' + key : key}"></div>`);
    }
    grid.innerHTML = cells.join('');
  } catch (_) {
    if (grid) grid.textContent = '';
  }
}
