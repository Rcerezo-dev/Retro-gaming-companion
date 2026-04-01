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
  if (intensity === 0)    return '#0d1117';
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
      if (container) container.innerHTML = '<div style="padding:20px;color:#666;text-align:center;width:100%">¡Excelente! No tienes juegos olvidados. ¡Sigue jugando!</div>';
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

    const colors     = ['#569cd6', '#4ec9b0', '#dcdcaa', '#ce9178', '#9cdcfe', '#c586c0', '#a7ec21', '#f44747'];
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
      ctx.fillStyle = '#d4d4d4';
      ctx.fillText(plat, legX + 15, legY + 9);
      legX += 120;
      if (legX > canvas.width - 100) { legX = padding; legY += 14; }
    });
  } catch(err) {
    console.error('Monthly chart error:', err);
  }
}
