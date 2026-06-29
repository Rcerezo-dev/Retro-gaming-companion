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
let _colSortBy = '';
let _colOffset = 0;
const _COL_PAGE = 30;
let _colRoot = null;

function _fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
}

// ── Colección: Missing + Estadísticas ────────────────────────────────────────
async function loadCollectionStats() {
  const el = document.getElementById('collection-stats');
  if (!el) return;
  el.innerHTML = '<p class="loading">Calculando estadísticas…</p>';
  try {
    const d = await apiFetch('/api/collection-stats');
    if (!d.platforms || d.platforms.length === 0) {
      el.innerHTML = '<p style="color:var(--c-muted);font-size:13px">No hay catálogos DAT cargados. Importa archivos DAT en <strong>Herramientas → Catálogos DAT</strong>.</p>';
      return;
    }
    let html = '<h4 style="color:var(--c-blue);margin-bottom:12px">Completitud por plataforma</h4>';
    html += '<div style="max-height:320px;overflow-y:auto">';
    for (const p of d.platforms) {
      const pct = p.coverage_pct;
      const barColor = pct >= 80 ? 'var(--c-teal)' : pct >= 40 ? 'var(--c-yellow)' : 'var(--c-red)';
      html += `<div style="margin-bottom:8px">`;
      html += `<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px">`;
      html += `<span style="color:var(--c-strong)">${window._h(p.platform)}</span>`;
      html += `<span style="color:var(--c-muted)">${p.in_library} / ${p.total} &nbsp;<strong style="color:${barColor}">${pct}%</strong></span>`;
      html += `</div>`;
      html += `<div style="background:#222;border-radius:3px;height:6px;width:100%">`;
      html += `<div style="background:${barColor};border-radius:3px;height:6px;width:${pct}%"></div>`;
      html += `</div></div>`;
    }
    html += '</div>';
    const totalDat = d.platforms.reduce((s, p) => s + p.total, 0);
    const totalLib = d.platforms.reduce((s, p) => s + p.in_library, 0);
    const totalPct = totalDat > 0 ? (100 * totalLib / totalDat).toFixed(1) : 0;
    html += `<p style="color:var(--c-hint);font-size:12px;margin-top:8px">Total: ${totalLib} de ${totalDat} ROMs en catálogo (${totalPct}%)</p>`;
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
    listEl.innerHTML = '<p style="color:var(--c-teal);font-size:13px">✓ Tienes todos los ROMs de los catálogos cargados.</p>';
    return;
  }

  let html = '<table style="font-size:12px;width:100%;border-collapse:collapse">';
  html += '<thead><tr style="color:var(--c-muted);border-bottom:1px solid #333">';
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
      html += `<td style="padding:3px 6px;color:var(--c-muted);white-space:nowrap">${window._h(p.platform)}</td>`;
      html += `<td style="padding:3px 6px;color:var(--c-strong)">${window._h(entry.title)}</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button onclick="navigator.clipboard.writeText('${query.replace(/'/g,"\\'")}').then(()=>showToast('Copiado','ok'))" `;
      html += `style="font-size:11px;padding:1px 6px;background:#2d2d2d;border:1px solid #444;color:var(--c-strong);border-radius:3px;cursor:pointer" title="${qh}">Copiar</button>`;
      html += `</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button onclick="navigator.clipboard.writeText('${iaUrlEsc}').then(()=>showToast('Link copiado — pégalo en JDownloader','ok'))" `;
      html += `style="font-size:11px;padding:1px 6px;background:#1a2a1a;border:1px solid #2d4a2d;color:var(--c-teal);border-radius:3px;cursor:pointer" title="${window._h(iaUrl)}">&#x1F517; Link IA</button>`;
      html += `</td>`;
      html += `<td style="padding:3px 6px;white-space:nowrap">`;
      html += `<button id="wlbtn_${window._h(entry.sha1)}" onclick="toggleWishlist('${window._h(entry.sha1)}','${entry.title.replace(/'/g,"\\'")}','${window._h(p.platform)}','searching')" `;
      html += `style="font-size:11px;padding:1px 6px;background:#2d2d2d;border:1px solid #444;color:var(--c-muted);border-radius:3px;cursor:pointer">+ Wishlist</button>`;
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
      limit: _COL_PAGE,
      sort_by: _colSortBy,
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

function colSort(v) {
  _colSortBy = v;
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
      limit: _COL_PAGE,
      sort_by: _colSortBy,
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

    const playBadge = g.play_count > 0
      ? `<span class="col-play-badge" title="${g.play_count} sesión(es)">${g.play_count}▶</span>`
      : '';
    const raBadge = g.ra_achievements > 0
      ? `<span class="col-ra-badge" title="${g.ra_achievements} logros RetroAchievements">🏆${g.ra_achievements}</span>`
      : '';
    const lastPlayed = g.last_played_at
      ? `<div class="col-last-played">${_fmtDate(g.last_played_at)}</div>`
      : '';
    const stars = g.user_rating
      ? `<div class="col-stars">${'★'.repeat(g.user_rating)}${'☆'.repeat(5 - g.user_rating)}</div>`
      : '';

    tile.innerHTML = `
      <div class="col-cover skeleton" style="position:relative">
        <img src="/api/asset-image?game_id=${g.id}"
          onload="this.parentElement.classList.remove('skeleton')"
          onerror="this.parentElement.classList.remove('skeleton');this.parentElement.innerHTML='<span>🎮</span>'">
        ${playBadge}
        ${raBadge}
      </div>
      <div class="col-title">${window._h(g.canonical_title || g.original_filename)}</div>
      <div class="col-plat">${window._h(g.platform || '')}</div>
      ${stars}
      ${lastPlayed}
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
       <div style="color:var(--c-muted);font-size:11px">juegos  ★${d.favorites} favs</div>`;
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
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--c-soft);margin-bottom:2px">
        <span>${window._h(label)}</span><span>${r.n}</span>
      </div>
      <div style="background:var(--c-panel);border-radius:3px;height:6px">
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

// ── Library diff (B3) ──────────────────────────────────────────────────────────
function toggleDiff() {
  const panel = document.getElementById('col-diff-panel');
  if (panel.classList.contains('hidden')) {
    panel.classList.remove('hidden');
    _populateDiffPlatforms();
    loadLibraryDiff();
  } else {
    panel.classList.add('hidden');
  }
}

async function _populateDiffPlatforms() {
  const sel = document.getElementById('diff-platform-filter');
  if (sel.options.length > 1) return; // already populated
  try {
    const d = await apiFetch('/api/platform-stats');
    for (const p of d.platforms) {
      const opt = document.createElement('option');
      opt.value = p.platform;
      opt.textContent = `${p.platform} (${p.total_games})`;
      sel.appendChild(opt);
    }
  } catch (_) {}
}

async function loadLibraryDiff() {
  const platform = document.getElementById('diff-platform-filter')?.value || '';
  const url = '/api/library-diff' + (platform ? `?platform=${encodeURIComponent(platform)}` : '');

  const pcEl   = document.getElementById('diff-pc-list');
  const andEl  = document.getElementById('diff-and-list');
  const confEl = document.getElementById('diff-conf-list');
  const sumEl  = document.getElementById('diff-summary');
  [pcEl, andEl, confEl].forEach(el => { if (el) el.innerHTML = '<p class="loading">Cargando…</p>'; });

  try {
    const d = await apiFetch(url);
    document.getElementById('diff-pc-count').textContent  = d.only_pc.length;
    document.getElementById('diff-and-count').textContent = d.only_android.length;
    document.getElementById('diff-conf-count').textContent = d.conflicts.length;

    const syncIcon = d.parity ? '✓ Sincronizadas' : `${d.only_pc.length + d.only_android.length + d.conflicts.length} diferencias`;
    sumEl.innerHTML = `PC: <b style="color:var(--c-strong)">${d.total_pc}</b> ROMs &nbsp;|&nbsp; Android: <b style="color:var(--c-strong)">${d.total_android}</b> ROMs &nbsp;|&nbsp; En ambas: <b style="color:var(--c-strong)">${d.in_both.length}</b> &nbsp;|&nbsp; <span class="${d.parity ? 'txt-ok' : 'txt-warn'}">${syncIcon}</span>`;

    pcEl.innerHTML   = _renderDiffTable(d.only_pc,      'pc');
    andEl.innerHTML  = _renderDiffTable(d.only_android, 'android');
    confEl.innerHTML = _renderDiffConflicts(d.conflicts);
  } catch (e) {
    [pcEl, andEl, confEl].forEach(el => { if (el) el.innerHTML = `<p class="error-msg">${window._h(e.message)}</p>`; });
  }
}

function _renderDiffTable(entries, side) {
  if (!entries.length) return '<p style="color:var(--c-dim);font-size:11px;padding:4px">Sin diferencias.</p>';
  const selectAllId = `diff-sel-all-${side}`;
  const dirLabel = side === 'pc' ? 'PC &#x2192; Android' : 'Android &#x2192; PC';
  let html = `<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">`;
  html += `<label style="display:flex;align-items:center;gap:4px;font-size:11px;color:var(--c-dim);cursor:pointer">`;
  html += `<input type="checkbox" id="${selectAllId}" style="accent-color:var(--accent)" onchange="_diffToggleAll('${side}',this.checked)"> Todo`;
  html += `</label>`;
  html += `<button class="btn" style="padding:1px 10px;font-size:11px" onclick="_syncAllSide('${side}')" title="Copiar todos los ROMs de este lado al otro">Sincronizar ${dirLabel}</button>`;
  html += `</div>`;
  html += '<table style="width:100%;border-collapse:collapse">';
  html += '<thead><tr style="color:var(--c-dim);font-size:11px;border-bottom:1px solid #222">'
    + '<th style="padding:3px 6px;text-align:left">Plataforma</th>'
    + '<th style="padding:3px 6px;text-align:left">Título</th>'
    + '<th style="padding:3px 6px;text-align:center"></th>'
    + '</tr></thead><tbody>';
  for (const e of entries) {
    html += `<tr style="border-bottom:1px solid #1a1a1a" title="${window._h(e.source_path)}">`;
    html += `<td style="padding:3px 6px;color:var(--c-muted);white-space:nowrap">${window._h(e.platform)}</td>`;
    html += `<td style="padding:3px 6px;color:var(--c-strong);word-break:break-word">${window._h(e.title)}</td>`;
    html += `<td style="padding:3px 6px;text-align:center"><input type="checkbox" class="diff-sel" data-sha1="${window._h(e.sha1)}" data-side="${side}" style="accent-color:var(--accent)"></td>`;
    html += '</tr>';
  }
  html += '</tbody></table>';
  return html;
}

function _diffToggleAll(side, checked) {
  document.querySelectorAll(`#col-diff-panel .diff-sel[data-side="${side}"]`)
    .forEach(cb => { cb.checked = checked; });
}

async function _syncAllSide(side) {
  const checks = document.querySelectorAll(`#col-diff-panel .diff-sel[data-side="${side}"]`);
  if (!checks.length) { showToast('No hay diferencias en este lado', 'info'); return; }
  const direction = side === 'pc' ? 'pc_to_android' : 'android_to_pc';
  const items = Array.from(checks).map(cb => ({ sha1: cb.dataset.sha1, direction }));
  const statusEl = document.getElementById('diff-sync-status');
  if (statusEl) statusEl.textContent = `Copiando ${items.length} archivo(s)…`;
  try {
    const r = await apiPost('/api/sync-roms', { items });
    const msg = `✓ ${r.synced} copiado(s)` + (r.errors.length ? ` · ${r.errors.length} error(es)` : '');
    if (statusEl) statusEl.textContent = msg;
    showToast(msg, r.errors.length ? 'warn' : 'ok');
    if (r.synced > 0) await loadLibraryDiff();
  } catch (e) {
    if (statusEl) statusEl.textContent = '';
    showToast(`Error: ${e.message}`, 'err');
  }
}

function _renderDiffConflicts(conflicts) {
  if (!conflicts.length) return '<p style="color:var(--c-dim);font-size:11px;padding:4px">Sin conflictos.</p>';
  let html = '';
  for (const c of conflicts) {
    const pcSha1  = c.pc[0]?.sha1  || '';
    const andSha1 = c.android[0]?.sha1 || '';
    html += `<div style="border:1px solid #2a2a1a;border-radius:4px;margin-bottom:8px;padding:7px 10px">`;
    html += `<div style="color:#f9e2af;font-size:11px;margin-bottom:4px">${window._h(c.platform)} — ${window._h(c.title)}</div>`;
    html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px;margin-bottom:6px">`;
    for (const e of c.pc)      html += `<div style="color:var(--c-pink)">PC: ${window._h(e.source_path.split(/[\\/]/).pop())}</div>`;
    for (const e of c.android) html += `<div style="color:#89b4fa">Android: ${window._h(e.source_path.split(/[\\/]/).pop())}</div>`;
    html += '</div>';
    if (pcSha1 && andSha1) {
      html += `<div style="display:flex;gap:6px">`;
      html += `<button onclick="syncConflict('${pcSha1}','${andSha1}','pc')" style="font-size:11px;padding:2px 8px;background:#1a1215;border:1px solid var(--c-pink);color:var(--c-pink);border-radius:3px;cursor:pointer" title="Copiar versión PC a Android, sobreescribiendo la Android">Usar PC &#x2192;</button>`;
      html += `<button onclick="syncConflict('${pcSha1}','${andSha1}','android')" style="font-size:11px;padding:2px 8px;background:#12151a;border:1px solid #89b4fa;color:#89b4fa;border-radius:3px;cursor:pointer" title="Copiar versión Android a PC, sobreescribiendo la PC">&#x2190; Usar Android</button>`;
      html += `</div>`;
    }
    html += '</div>';
  }
  return html;
}

async function syncConflict(pcSha1, andSha1, winner) {
  const item = winner === 'pc'
    ? { sha1: pcSha1, direction: 'pc_to_android' }
    : { sha1: andSha1, direction: 'android_to_pc' };
  try {
    const r = await apiPost('/api/sync-roms', { items: [item] });
    if (r.synced) {
      showToast(`✓ Versión ${winner === 'pc' ? 'PC' : 'Android'} aplicada`, 'ok');
      await loadLibraryDiff();
    } else {
      showToast(r.errors[0]?.error || 'Error al sincronizar', 'err');
    }
  } catch (e) {
    showToast(`Error: ${e.message}`, 'err');
  }
}

// ── B3-3: Sync selected diff items ────────────────────────────────────────────
async function syncSelected() {
  const checks = document.querySelectorAll('#col-diff-panel .diff-sel:checked');
  if (!checks.length) {
    showToast('Selecciona al menos un juego', 'warn');
    return;
  }
  const items = Array.from(checks).map(cb => ({
    sha1: cb.dataset.sha1,
    direction: cb.dataset.side === 'pc' ? 'pc_to_android' : 'android_to_pc',
  }));
  const statusEl = document.getElementById('diff-sync-status');
  if (statusEl) statusEl.textContent = `Copiando ${items.length} archivo(s)…`;
  try {
    const r = await apiPost('/api/sync-roms', { items });
    const msg = `✓ ${r.synced} copiado(s)` + (r.errors.length ? ` · ${r.errors.length} error(es)` : '');
    if (statusEl) statusEl.textContent = msg;
    showToast(msg, r.errors.length ? 'warn' : 'ok');
    if (r.errors.length) console.error('Sync errors:', r.errors);
    if (r.synced > 0) await loadLibraryDiff();
  } catch (e) {
    if (statusEl) statusEl.textContent = '';
    showToast(`Error: ${e.message}`, 'err');
  }
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

// ── P5: Completeness toggle ───────────────────────────────────────────────────
function toggleCompleteness() {
  const panel = document.getElementById('col-completeness-panel');
  if (panel.classList.contains('hidden')) {
    panel.classList.remove('hidden');
    loadCollectionStats();
  } else {
    panel.classList.add('hidden');
  }
}

// ── P3: Disk usage panel ──────────────────────────────────────────────────────
function toggleDiskUsage() {
  const panel = document.getElementById('col-disk-panel');
  if (panel.classList.contains('hidden')) {
    panel.classList.remove('hidden');
    loadDiskUsage();
  } else {
    panel.classList.add('hidden');
  }
}

async function loadDiskUsage() {
  const el = document.getElementById('col-disk-content');
  if (!el) return;
  el.innerHTML = '<p class="loading">Calculando…</p>';
  const root = window._deviceRoot();
  const url = '/api/disk-usage' + (root ? `?root=${encodeURIComponent(root)}` : '');
  try {
    const d = await apiFetch(url);
    const platforms = d.platforms || [];
    const total = d.total_bytes || 0;

    let html = '';

    // Disk free/used bar (if available)
    if (d.disk_total) {
      const usedPct = Math.round(d.disk_used / d.disk_total * 100);
      const freePct = 100 - usedPct;
      html += `<div style="margin-bottom:14px">`;
      html += `<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--c-muted);margin-bottom:4px">`;
      html += `<span>Disco: <b style="color:var(--c-strong)">${d.total_human}</b> total</span>`;
      html += `<span><b style="color:var(--c-teal)">${_fmtBytes(d.disk_free)}</b> libre</span>`;
      html += `</div>`;
      html += `<div style="background:var(--c-panel);border-radius:4px;height:8px;width:100%;overflow:hidden">`;
      html += `<div style="background:#7c3aed;width:${usedPct}%;height:100%;border-radius:4px"></div>`;
      html += `</div>`;
      html += `<div style="font-size:10px;color:var(--c-dim);margin-top:2px">${usedPct}% usado · ${freePct}% libre</div>`;
      html += `</div>`;
    }

    // Per-platform bars
    html += `<div style="font-size:11px;color:var(--c-muted);margin-bottom:6px">ROMs: <b style="color:var(--c-strong)">${d.total_human}</b> total</div>`;
    for (const p of platforms) {
      const pct = total > 0 ? Math.round(p.size_bytes / total * 100) : 0;
      const missing = p.missing ? ` <span style="color:var(--c-pink)">(${p.missing} no encontrados)</span>` : '';
      html += `<div style="margin-bottom:7px">`;
      html += `<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px">`;
      html += `<span style="color:var(--c-strong)">${window._h(p.platform)}</span>`;
      html += `<span style="color:var(--c-muted)">${p.rom_count} ROMs &nbsp;<b style="color:var(--c-text)">${p.size_human}</b> &nbsp;<span style="color:var(--c-dim)">${pct}%</span>${missing}</span>`;
      html += `</div>`;
      html += `<div style="background:var(--c-panel);border-radius:3px;height:5px;width:100%">`;
      html += `<div style="background:#7aa2f7;width:${pct}%;height:100%;border-radius:3px"></div>`;
      html += `</div></div>`;
    }
    if (!platforms.length) html = '<p style="color:var(--c-dim);font-size:12px">Sin datos. Escanea tu biblioteca primero.</p>';
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<p class="error-msg">${window._h(e.message)}</p>`;
  }
}

function _fmtBytes(n) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(1)} ${units[i]}`;
}

// ── Public exports ────────────────────────────────────────────────────────────
export {
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  loadCollection, colSetPlatform, colSearch, colSort, colLoadMore,
  exportCollection, exportWishlist,
  loadCollectionStatsV2, toggleColStats,
  toggleDiff, loadLibraryDiff, syncSelected, syncConflict,
  _diffToggleAll, _syncAllSide,
  toggleDiskUsage, loadDiskUsage,
  toggleCompleteness,
};
