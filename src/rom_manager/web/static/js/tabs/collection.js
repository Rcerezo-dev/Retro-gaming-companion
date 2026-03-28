// js/tabs/collection.js — Colección: Missing, Gallery, Export, Stats
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// ── Module state ──────────────────────────────────────────────────────────────
let _collectionPlatforms = [];
let _colPlatform = '';
let _colSearch = '';
let _colOffset = 0;
const _COL_PAGE = 30;
let _colRoot = null;

// ── Colección: Missing + Estadísticas ────────────────────────────────────────
async function loadCollectionStats() {
  const el = document.getElementById('collection-stats');
  if (!el) return;
  el.innerHTML = '<p class="loading">Calculando estadísticas…</p>';
  try {
    const d = await apiFetch('/api/collection-stats');
    if (!d.platforms || d.platforms.length === 0) {
      el.innerHTML = '<p style="color:#888;font-size:13px">No hay catálogos DAT cargados. Importa archivos DAT en <strong>Herramientas → Catálogos DAT</strong>.</p>';
      return;
    }
    let html = '<h4 style="color:#569cd6;margin-bottom:12px">Completitud por plataforma</h4>';
    html += '<div style="max-height:320px;overflow-y:auto">';
    for (const p of d.platforms) {
      const pct = p.coverage_pct;
      const barColor = pct >= 80 ? '#4ec9b0' : pct >= 40 ? '#dcdcaa' : '#f44747';
      html += `<div style="margin-bottom:8px">`;
      html += `<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px">`;
      html += `<span style="color:#ccc">${window._h(p.platform)}</span>`;
      html += `<span style="color:#888">${p.in_library} / ${p.total} &nbsp;<strong style="color:${barColor}">${pct}%</strong></span>`;
      html += `</div>`;
      html += `<div style="background:#222;border-radius:3px;height:6px;width:100%">`;
      html += `<div style="background:${barColor};border-radius:3px;height:6px;width:${pct}%"></div>`;
      html += `</div></div>`;
    }
    html += '</div>';
    const totalDat = d.platforms.reduce((s, p) => s + p.total, 0);
    const totalLib = d.platforms.reduce((s, p) => s + p.in_library, 0);
    const totalPct = totalDat > 0 ? (100 * totalLib / totalDat).toFixed(1) : 0;
    html += `<p style="color:#666;font-size:12px;margin-top:8px">Total: ${totalLib} de ${totalDat} ROMs en catálogo (${totalPct}%)</p>`;
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function loadMissingRoms() {
  const sec = document.getElementById('missing-section');
  const listEl = document.getElementById('missing-list');
  const sel = document.getElementById('missing-plat-filter');
  if (!sec || !listEl) return;
  listEl.innerHTML = '<p class="loading">Cargando faltantes…</p>';
  sec.classList.remove('hidden');
  try {
    const d = await apiFetch('/api/missing');
    _collectionPlatforms = d.platforms || [];
    if (sel) {
      sel.innerHTML = '<option value="">Todas las plataformas</option>';
      _collectionPlatforms.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.platform;
        opt.textContent = `${p.platform} (${p.missing} faltantes)`;
        sel.appendChild(opt);
      });
    }
    _renderMissingList('');
  } catch (e) {
    listEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function filterMissingByPlatform() {
  const sel = document.getElementById('missing-plat-filter');
  _renderMissingList(sel ? sel.value : '');
}

function _renderMissingList(platformFilter) {
  const listEl = document.getElementById('missing-list');
  const countEl = document.getElementById('missing-count');
  if (!listEl) return;

  const platforms = platformFilter
    ? _collectionPlatforms.filter(p => p.platform === platformFilter)
    : _collectionPlatforms;

  const totalMissing = platforms.reduce((s, p) => s + p.missing, 0);
  if (countEl) countEl.textContent = `${totalMissing} ROMs faltantes`;

  if (totalMissing === 0) {
    listEl.innerHTML = '<p style="color:#4ec9b0;font-size:13px">✓ Tienes todos los ROMs de los catálogos cargados.</p>';
    return;
  }

  let html = '<table style="font-size:12px;width:100%;border-collapse:collapse">';
  html += '<thead><tr style="color:#888;border-bottom:1px solid #333">';
  html += '<th style="text-align:left;padding:4px 6px">Plataforma</th>';
  html += '<th style="text-align:left;padding:4px 6px">Título</th>';
  html += '<th style="text-align:left;padding:4px 6px">Búsqueda</th>';
  html += '<th style="text-align:left;padding:4px 6px">Internet Archive</th>';
  html += '<th style="text-align:left;padding:4px 6px">Wishlist</th>';
  html += '</tr></thead><tbody>';

  for (const p of platforms) {
    for (const entry of p.entries) {
      const query = `${entry.title} ${p.platform} No-Intro site:archive.org`;
      const qh = window._h(query);
      const iaUrl = 'https://archive.org/search?query=' + encodeURIComponent(entry.title + ' ' + p.platform + ' No-Intro');
      const iaUrlEsc = iaUrl.replace(/'/g, "\\'");
      const wlKey = `wl_${entry.sha1}`;
      html += `<tr style="border-bottom:1px solid #1e1e1e" id="${window._h(wlKey)}">`;
      html += `<td style="padding:3px 6px;color:#888;white-space:nowrap">${window._h(p.platform)}</td>`;
      html += `<td style="padding:3px 6px;color:#ccc">${window._h(entry.title)}</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button onclick="navigator.clipboard.writeText('${query.replace(/'/g,"\\'")}').then(()=>showToast('Copiado','ok'))" `;
      html += `style="font-size:11px;padding:1px 6px;background:#2d2d2d;border:1px solid #444;color:#ccc;border-radius:3px;cursor:pointer" title="${qh}">Copiar</button>`;
      html += `</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button onclick="navigator.clipboard.writeText('${iaUrlEsc}').then(()=>showToast('Link copiado — pégalo en JDownloader','ok'))" `;
      html += `style="font-size:11px;padding:1px 6px;background:#1a2a1a;border:1px solid #2d4a2d;color:#4ec9b0;border-radius:3px;cursor:pointer" title="${window._h(iaUrl)}">&#x1F517; Link IA</button>`;
      html += `</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button id="wlbtn_${window._h(entry.sha1)}" onclick="toggleWishlist('${window._h(entry.sha1)}','${entry.title.replace(/'/g,"\\'")}','${window._h(p.platform)}','searching')" `;
      html += `style="font-size:11px;padding:1px 6px;background:#2d2d2d;border:1px solid #444;color:#888;border-radius:3px;cursor:pointer">+ Wishlist</button>`;
      html += `</td></tr>`;
    }
  }
  html += '</tbody></table>';
  listEl.innerHTML = html;
}

async function toggleWishlist(sha1, title, platform, currentStatus) {
  const btn = document.getElementById(`wlbtn_${sha1}`);
  if (!btn) return;
  const isAdded = btn.textContent.trim() === '✓ Buscando';
  if (isAdded) {
    await apiPost('/api/wishlist', { sha1, remove: true });
    btn.textContent = '+ Wishlist';
    _txtCls(btn, 'txt-muted');
    btn.onclick = () => toggleWishlist(sha1, title, platform, 'searching');
    showToast('Quitado de wishlist', 'ok');
  } else {
    await apiPost('/api/wishlist', { sha1, title, platform, status: currentStatus });
    btn.textContent = '✓ Buscando';
    _txtCls(btn, 'txt-ok');
    btn.onclick = () => toggleWishlist(sha1, title, platform, currentStatus);
    showToast('Añadido a wishlist', 'ok');
  }
}

// ── S35-5: Collection gallery ────────────────────────────────────────────────
async function loadCollection() {
  const root = window._deviceRoot();
  _colRoot = root;
  const gridEl = document.getElementById('col-grid');
  const barEl = document.getElementById('col-platform-bar');
  const loadMoreBtn = document.getElementById('col-load-more');
  if (!gridEl || !barEl) return;

  gridEl.innerHTML = '<p class="loading" style="grid-column:1/-1">Cargando colección…</p>';
  try {
    const stats = await apiFetch(`/api/platform-stats?root=${encodeURIComponent(root || '')}`);
    const platforms = stats.platforms || [];

    barEl.innerHTML = '';
    const allBtn = document.createElement('button');
    allBtn.className = 'btn' + (_colPlatform === '' ? ' active' : '');
    allBtn.textContent = 'Todos (' + platforms.reduce((s, p) => s + p.total_games, 0) + ')';
    allBtn.onclick = () => { _colPlatform = ''; _colOffset = 0; loadCollection(); };
    allBtn.style.fontSize = '12px';
    barEl.appendChild(allBtn);

    for (const p of platforms) {
      const btn = document.createElement('button');
      btn.className = 'btn platform-tile' + (_colPlatform === p.platform ? ' active' : '');
      btn.textContent = `${window._h(p.platform)} (${p.total_games})`;
      btn.onclick = () => colSetPlatform(p.platform);
      btn.style.fontSize = '12px';
      barEl.appendChild(btn);
    }

    const params = new URLSearchParams({
      root: root || '',
      platform: _colPlatform,
      search: _colSearch,
      offset: _colOffset,
      limit: _COL_PAGE
    });
    const games = await apiFetch(`/api/games?${params}`);
    const gameList = games.games || [];

    if (gameList.length === 0 && _colOffset === 0) {
      gridEl.innerHTML = '<p class="empty" style="grid-column:1/-1">Sin juegos. Escanea tu biblioteca en Inicio.</p>';
      loadMoreBtn.classList.add('hidden');
      return;
    }

    _renderColGrid(gameList, _colOffset > 0);
    loadMoreBtn.classList.toggle('hidden', !(gameList.length >= _COL_PAGE));
  } catch (e) {
    gridEl.innerHTML = `<p class="error-msg" style="grid-column:1/-1">${e.message}</p>`;
  }
}

function colSetPlatform(p) {
  _colPlatform = p;
  _colOffset = 0;
  loadCollection();
}

function colSearch(v) {
  _colSearch = v;
  _colOffset = 0;
  loadCollection();
}

async function colLoadMore() {
  _colOffset += _COL_PAGE;
  const root = window._deviceRoot();
  const gridEl = document.getElementById('col-grid');
  if (!gridEl) return;

  try {
    const params = new URLSearchParams({
      root: root || '',
      platform: _colPlatform,
      search: _colSearch,
      offset: _colOffset,
      limit: _COL_PAGE
    });
    const games = await apiFetch(`/api/games?${params}`);
    const gameList = games.games || [];

    _renderColGrid(gameList, true);
    const loadMoreBtn = document.getElementById('col-load-more');
    if (loadMoreBtn) {
      loadMoreBtn.classList.toggle('hidden', !(gameList.length >= _COL_PAGE));
    }
  } catch (e) {
    showToast(`Error: ${e.message}`, 'err');
  }
}

function _renderColGrid(games, append) {
  const gridEl = document.getElementById('col-grid');
  if (!gridEl) return;

  if (!append) gridEl.innerHTML = '';

  for (const g of games) {
    const tile = document.createElement('div');
    tile.className = 'col-tile';
    tile.onclick = () => window.openGamePanel(g);
    tile.innerHTML = `
      <div class="col-cover skeleton">
        <img src="/api/asset-image?game_id=${g.id}"
          onload="this.parentElement.classList.remove('skeleton')"
          onerror="this.parentElement.classList.remove('skeleton');this.parentElement.innerHTML='<span>🎮</span>'">
      </div>
      <div class="col-title">${window._h(g.canonical_title || g.original_filename)}</div>
      <div class="col-plat">${window._h(g.platform || '')}</div>
    `;
    gridEl.appendChild(tile);
  }
}

// ── S36: Export & Stats ──────────────────────────────────────────────────────
async function exportCollection(fmt) {
  const root = window._deviceRoot() || '';
  try {
    const res = await fetch(`/api/export-library?root=${encodeURIComponent(root)}&format=${fmt}`);
    if (!res.ok) {
      showToast('Error exportando', 'err');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `retro-vault-${fmt}.${fmt}`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`✓ Descargado: retro-vault-${fmt}.${fmt}`, 'ok');
  } catch (e) {
    showToast(`Error: ${e.message}`, 'err');
  }
}

async function exportWishlist() {
  const root = window._deviceRoot() || '';
  try {
    const res = await fetch(`/api/export-wishlist?root=${encodeURIComponent(root)}`);
    if (!res.ok) {
      showToast('Sin wishlist o error', 'err');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wishlist.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('✓ Wishlist descargada', 'ok');
  } catch (e) {
    showToast(`Error: ${e.message}`, 'err');
  }
}

async function loadCollectionStatsV2() {
  const root = window._deviceRoot() || '';
  try {
    const d = await apiFetch(`/api/collection-stats-v2?root=${encodeURIComponent(root)}`);
    document.getElementById('col-stat-total').innerHTML =
      `<div style="font-size:2em;font-weight:700">${d.total}</div>
       <div style="color:#888;font-size:11px">juegos  ★${d.favorites} favs</div>`;
    _renderStatBars('col-bar-status', d.by_status, 'status_label', d.total);
    _renderStatBars('col-bar-region', d.by_region, 'region_label', d.total);
    _renderPie('col-pie', d.by_platform.slice(0, 8));
  } catch (e) {
    showToast(`Error cargando stats: ${e.message}`, 'err');
  }
}

function _renderStatBars(containerId, rows, labelKey, total) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = rows.map(r => {
    const pct = total ? Math.round(r.n / total * 100) : 0;
    const label = r.s || r.r || '?';
    return `<div style="margin-bottom:5px">
      <div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;margin-bottom:2px">
        <span>${window._h(label)}</span><span>${r.n}</span>
      </div>
      <div style="background:#1e1e2e;border-radius:3px;height:6px">
        <div style="background:#7c3aed;width:${pct}%;height:100%;border-radius:3px;transition:width .4s"></div>
      </div>
    </div>`;
  }).join('');
}

function _renderPie(canvasId, rows) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx = 60, cy = 60, r = 50;
  const total = rows.reduce((s, x) => s + x.n, 0);
  const colors = ['#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626', '#0891b2', '#7c3aed', '#64748b'];
  let angle = -Math.PI / 2;
  ctx.clearRect(0, 0, 120, 120);
  rows.forEach((row, i) => {
    const slice = (row.n / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, angle, angle + slice);
    ctx.closePath();
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    angle += slice;
  });
}

function toggleColStats() {
  const panel = document.getElementById('col-stats-panel');
  if (panel.classList.contains('hidden')) {
    panel.classList.remove('hidden');
    loadCollectionStatsV2();
  } else {
    panel.classList.add('hidden');
  }
}

// ── Public exports ────────────────────────────────────────────────────────────
export {
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  loadCollection, colSetPlatform, colSearch, colLoadMore,
  exportCollection, exportWishlist,
  loadCollectionStatsV2, toggleColStats,
};
