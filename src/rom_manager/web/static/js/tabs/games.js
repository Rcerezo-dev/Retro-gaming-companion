// js/tabs/games.js — Games tab: list, filters, pagination, game panel, TV mode
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Games pagination state ────────────────────────────────────────────────────
export let gamesState = { offset: 0, limit: 100, total: 0, platform: '', status: '', root: null };
export let _gamesViewMode = localStorage.getItem('games_view_mode') || 'list'; // 'list' | 'grid'
export let platformsLoaded = false;

// ── TV Mode state ─────────────────────────────────────────────────────────────
export let _tvActive = false;
export let _tvGames = [];
export let _tvFocusIdx = 0;
export let _tvPlatform = '';
export let _tvOffset = 0;
export let _tvCols = 5;
export const _TV_LIMIT = 120;

// ── Column visibility ─────────────────────────────────────────────────────────
const _COL_DEFAULTS = { region: true, match: true, size: false, sha1: false };

function _loadColPrefs() {
  try { return JSON.parse(localStorage.getItem('games_cols') || 'null') || _COL_DEFAULTS; }
  catch { return _COL_DEFAULTS; }
}

function _saveColPrefs(prefs) {
  localStorage.setItem('games_cols', JSON.stringify(prefs));
}

export function applyColVisibility() {
  const prefs = {
    region: document.getElementById('gcol-check-region')?.checked ?? _COL_DEFAULTS.region,
    match:  document.getElementById('gcol-check-match')?.checked  ?? _COL_DEFAULTS.match,
    size:   document.getElementById('gcol-check-size')?.checked   ?? _COL_DEFAULTS.size,
    sha1:   document.getElementById('gcol-check-sha1')?.checked   ?? _COL_DEFAULTS.sha1,
  };
  _saveColPrefs(prefs);
  const show = (id, vis) => { const el = document.getElementById(id); if (el) el.classList.toggle('hidden', !vis); };
  show('gcol-region', prefs.region);
  show('gcol-match',  prefs.match);
  show('gcol-size',   prefs.size);
  show('gcol-sha1',   prefs.sha1);
  // Update row cells (col index: 0=platform,1=title,2=filename,3=region,4=match,5=size,6=sha1)
  const COL = { region: 3, match: 4, size: 5, sha1: 6 };
  document.querySelectorAll('#games-tbody tr').forEach(tr => {
    Object.entries(COL).forEach(([key, idx]) => {
      const td = tr.cells[idx];
      if (td) td.classList.toggle('hidden', !(prefs[key]));
    });
  });
}

export function _initColPicker() {
  const prefs = _loadColPrefs();
  ['region', 'match', 'size', 'sha1'].forEach(key => {
    const cb = document.getElementById('gcol-check-' + key);
    if (cb) cb.checked = prefs[key];
  });
  applyColVisibility();
}

export function toggleColPicker(event) {
  event.stopPropagation();
  const picker = document.getElementById('col-picker');
  if (!picker) return;
  picker.classList.toggle('hidden');
  if (!picker.classList.contains('hidden')) {
    const close = (e) => { if (!picker.contains(e.target)) { picker.classList.add('hidden'); document.removeEventListener('click', close); } };
    setTimeout(() => document.addEventListener('click', close), 0);
  }
}

// ── Local helpers (app.js globals duplicated for module scope) ────────────────
const _h = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// Forward declaration — set and used by game panel functions (2c-4)
export let _gpGameId = null;

// ── Filter helpers ────────────────────────────────────────────────────────────

// Navigate to Games tab pre-filtered by device root, match status, and filetype
export function goToGames(root, status, filetype, platform) {
  gamesState.root     = root     || null;
  gamesState.status   = status   || '';
  gamesState.platform = platform || '';
  gamesState.filetype = filetype || '';
  platformsLoaded = false;
  const statusSel = document.getElementById('games-matched');
  if (statusSel) statusSel.value = status || '';
  const ftSel = document.getElementById('games-filetype');
  if (ftSel && filetype !== undefined) ftSel.value = filetype || 'all';
  showTab('games');
}

let _gamesSearchTimer = null;
export function onGamesSearchChange() {
  clearTimeout(_gamesSearchTimer);
  _gamesSearchTimer = setTimeout(() => { loadGames(0); }, 300);
}

export function onGamesFilterChange() {
  gamesState.platform = document.getElementById('games-platform').value;
  gamesState.status   = document.getElementById('games-matched').value;
  gamesState.filetype = document.getElementById('games-filetype').value;
  gamesState.genre    = document.getElementById('games-genre')?.value || '';
  gamesState.year     = document.getElementById('games-year')?.value  || '';
  gamesState.sortBy   = document.getElementById('games-sort-by')?.value || '';
  loadGames(0);
}

let _filterOptionsLoaded = false;
export async function loadFilterOptions() {
  if (_filterOptionsLoaded) return;
  try {
    const r = await apiFetch('/api/games/filter-options');
    _filterOptionsLoaded = true;
    const _populate = (id, items) => {
      const sel = document.getElementById(id);
      if (!sel) return;
      const cur = sel.value;
      while (sel.options.length > 1) sel.remove(1);
      items.forEach(v => { const o = document.createElement('option'); o.value = v; o.text = v; sel.add(o); });
      if (cur) sel.value = cur;
    };
    _populate('games-genre', r.genres || []);
    _populate('games-year',  r.years  || []);
  } catch (_) {}
}

export function toggleFavoritesFilter() {
  const btn = document.getElementById('btn-filter-favorites');
  if (!btn) return;
  gamesState.favorite = !gamesState.favorite;
  _txtCls(btn, gamesState.favorite ? 'txt-fav' : 'txt-muted');
  btn.style.borderColor = gamesState.favorite ? '#f9c74f' : '#444';
  loadGames(0);
}

export async function _refreshTagFilter() {
  try {
    const r = await apiFetch('/api/tags');
    const sel = document.getElementById('games-tag-filter');
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML = '<option value="">Todos los tags</option>' +
      (r.tags || []).map(t => `<option value="${_h(t)}"${t === cur ? ' selected' : ''}>${_h(t)}</option>`).join('');
  } catch (_) {}
}

export async function toggleRowFavorite(gameId, btn) {
  try {
    const r = await apiPost('/api/toggle-favorite', { game_id: gameId });
    btn.classList.toggle('active', r.is_favorite);
    btn.title = r.is_favorite ? 'Quitar favorito' : 'Marcar favorito';
    // If the panel is open for this game, update its star too
    if (_gpGameId === gameId) _gpSetFavStar(r.is_favorite);
    // If filtering by favorites, refresh list
    if (gamesState.favorite) loadGames(gamesState.offset);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ── Platform helpers (duplicated for module scope) ────────────────────────────
export function fmtSize(n) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

function badge(cls, text, title) {
  const t = title ? ` title="${window._h(title)}"` : '';
  return `<span class="badge ${cls}"${t}>${text}</span>`;
}

const _MATCH_BADGE = {
  high:   { cls: 'high', text: 'SHA1 ✓', tip: 'Identificado por hash SHA1 exacto en catálogo DAT' },
  medium: { cls: 'high', text: 'DAT ~',  tip: 'Identificado por nombre de archivo en catálogo DAT' },
  low:    { cls: 'low',  text: '? DAT',  tip: 'Varios juegos con este nombre — coincidencia ambigua' },
};

function matchBadge(confidence) {
  const m = _MATCH_BADGE[confidence];
  if (m) return badge(m.cls, m.text, m.tip);
  return badge('none', '—', 'Sin identificar — sin catálogo DAT o sin coincidencia');
}

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

export function _platBadge(plat) {
  if (!plat) return '<span class="plat plat-other">?</span>';
  const key = plat.toLowerCase();
  const cls = _PLAT_CLASS[key] || 'other';
  return `<span class="plat plat-${cls}">${_h(plat)}</span>`;
}

const _PLAT_HEX = {
  gba: '#4ec9b0', snes: '#569cd6', nes: '#f44747', gb: '#dcdcaa',
  gbc: '#d7ba7d', nds: '#c586c0', '3ds': '#9cdcfe', n64: '#4ec9b0',
  psx: '#9cdcfe', ps2: '#569cd6', psp: '#79c0ff',
  genesis: '#ce9178', md: '#ce9178', sms: '#6a9955', gg: '#4ec9b0',
};

export function _platHex(plat) {
  const cls = _PLAT_CLASS[(plat || '').toLowerCase()] || 'other';
  return _PLAT_HEX[cls] || '#555';
}

function _emptyState(icon, title, sub, ctaLabel, ctaFn) {
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

// ── Core load / render ────────────────────────────────────────────────────────
export async function loadGames(offset) {
  gamesState.offset = offset ?? 0;
  const tbody = document.getElementById('games-tbody');
  tbody.innerHTML = '<tr><td colspan="9" class="loading">Cargando…</td></tr>';
  // Apply view mode visibility on each load
  const _listV = document.getElementById('games-list-view');
  const _gridV = document.getElementById('games-grid-view');
  const _btnL  = document.getElementById('btn-view-list');
  const _btnG  = document.getElementById('btn-view-grid');
  if (_listV) _listV.classList.toggle('hidden', !(_gamesViewMode === 'list'));
  if (_gridV) _gridV.classList.toggle('hidden', !(_gamesViewMode === 'grid'));
  if (_btnL)  _btnL.classList.toggle('active', _gamesViewMode === 'list');
  if (_btnG)  _btnG.classList.toggle('active', _gamesViewMode === 'grid');

  // Show active root filter if set
  const rootBanner = document.getElementById('games-root-banner');
  if (rootBanner) {
    if (gamesState.root) {
      rootBanner.classList.remove('hidden');
      rootBanner.innerHTML = `<span style="color:#888;font-size:12px">Filtrando por: <code style="color:#ce9178">${gamesState.root}</code></span> <button class="btn" style="padding:2px 8px;font-size:11px" onclick="gamesState.root=null;document.getElementById('games-root-banner').classList.add('hidden');loadGames(0)">&#x2715; Quitar filtro</button>`;
    } else {
      rootBanner.classList.add('hidden');
    }
  }

  const q = document.getElementById('games-search').value.trim();
  const params = new URLSearchParams({
    offset: gamesState.offset,
    limit:  gamesState.limit,
  });
  if (gamesState.platform) params.set('platform', gamesState.platform);
  if (gamesState.status)   params.set('status',   gamesState.status);
  if (q)                   params.set('search',   q);
  const ft = document.getElementById('games-filetype')?.value;
  if (ft !== undefined && ft !== 'all') params.set('filetype', ft);
  const ps = document.getElementById('games-play-status')?.value;
  if (ps) params.set('play_status', ps);
  if (gamesState.favorite) params.set('favorite', '1');
  const tagF = document.getElementById('games-tag-filter')?.value;
  if (tagF) params.set('tag', tagF);
  const genreF = document.getElementById('games-genre')?.value;
  if (genreF) params.set('genre', genreF);
  const yearF = document.getElementById('games-year')?.value;
  if (yearF) params.set('year', yearF);
  const sortBy = document.getElementById('games-sort-by')?.value;
  if (sortBy) params.set('sort_by', sortBy);
  const _gamesRoot = gamesState.root || _deviceRoot();
  if (_gamesRoot) params.set('root', _gamesRoot);

  try {
    const d = await apiFetch('/api/games?' + params);

    // Populate platform filter from current page (best effort)
    if (!platformsLoaded) {
      platformsLoaded = true;
      const plats = [...new Set(d.games.map(g => g.platform || 'Unknown'))].sort();
      const sel = document.getElementById('games-platform');
      while (sel.options.length > 1) sel.remove(1);
      plats.forEach(p => {
        const o = document.createElement('option');
        o.value = p; o.text = p;
        sel.add(o);
      });
    }

    gamesState.total = d.total;
    document.getElementById('games-count').textContent =
      `${d.total} juego${d.total !== 1 ? 's' : ''} (página ${Math.floor(gamesState.offset / gamesState.limit) + 1} de ${Math.max(1, Math.ceil(d.total / gamesState.limit))})`;

    // DAT matching mode banner
    const _datBanner = document.getElementById('games-dat-banner');
    if (_datBanner) {
      const _unmatched = d.games.filter(g => !g.match_confidence).length;
      if (d.dat_count === 0 && d.total > 0) {
        _datBanner.innerHTML = `<span style="color:#e5c200">⚠</span> Sin catálogos DAT — identificación por SHA1 no disponible. Los juegos sin catálogo no pueden renombrarse de forma fiable. <a href="#" onclick="showTab('settings');return false;" style="color:#7aadff;text-decoration:underline">→ Descargar catálogos</a>`;
        _datBanner.classList.remove('hidden');
      } else if (d.dat_count > 0 && _unmatched > 0) {
        _datBanner.innerHTML = `<span style="color:#4ec9b0">✓</span> ${d.dat_count} catálogo${d.dat_count !== 1 ? 's' : ''} DAT cargado${d.dat_count !== 1 ? 's' : ''} · <span style="color:#888">${_unmatched} sin identificar</span>`;
        _datBanner.classList.remove('hidden');
      } else if (d.dat_count > 0) {
        _datBanner.classList.add('hidden');
      }
    }

    const rows = d.games;
    const empty = document.getElementById('games-empty');
    if (rows.length === 0) {
      tbody.innerHTML = '';
      _renderGamesGrid([]);
      if (d.total === 0 && _activeDevice === 'anbernic' && !gamesState.root) {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || '';
        if (!ab) {
          empty.innerHTML = _emptyState('📱', `Sin ROMs de ${_devName}`, 'Configura primero la ruta de la consola en Ajustes.', 'Ir a Ajustes', () => showTab('settings'));
        } else {
          empty.innerHTML = _emptyState('🔍', `Sin ROMs de ${_devName}`, `Ruta: <code>${_h(ab)}</code><br>Escanea la consola desde Inicio para ver sus juegos aquí.`, 'Ir a Inicio', () => showTab('overview'));
        }
      } else if (d.total === 0) {
        empty.innerHTML = _emptyState('🎮', 'Sin juegos aún', 'Escanea tu biblioteca y ejecuta "Identificar (catálogos)" para ver tus juegos aquí.', 'Ir a Inicio', () => showTab('overview'));
      } else {
        empty.innerHTML = _emptyState('🔎', 'Sin resultados', 'Prueba con otros filtros o borra la búsqueda.');
      }
      empty.classList.remove('hidden');
    } else {
      empty.classList.add('hidden');
      const _srcPath = gamesState.root || _deviceRoot() || '';
      tbody.innerHTML = rows.map(g => {
        const thumb = g.id ? `<img src="/api/asset-image?game_id=${g.id}" style="width:32px;height:32px;object-fit:contain;border-radius:2px;background:#0a0a0a" onerror="this.style.display=\'none\'">` : '';
        const statusVal = g.play_status || '';
        const statusSel = `<select style="background:#1e1e2e;border:1px solid #333;color:#d4d4d4;padding:2px 5px;border-radius:3px;font:inherit;font-size:11px;cursor:pointer" onchange="setPlayStatus(${g.id}, '${_srcPath.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}', this.value)">
          <option value=""${statusVal === '' ? ' selected' : ''}>—</option>
          <option value="playing"${statusVal === 'playing' ? ' selected' : ''}>&#x1F3AE; Jugando</option>
          <option value="completed"${statusVal === 'completed' ? ' selected' : ''}>&#x2705; Completado</option>
          <option value="100pct"${statusVal === '100pct' ? ' selected' : ''}>&#x1F4AF; Al 100%</option>
          <option value="abandoned"${statusVal === 'abandoned' ? ' selected' : ''}>&#x23F8; Abandonado</option>
        </select>`;
        const accentColor = _platHex(g.platform);
        const favActive = g.is_favorite ? ' active' : '';
        return `<tr style="cursor:pointer;border-left:2px solid ${accentColor}20" onclick="openGamePanel(${JSON.stringify(g).replace(/</g, '\\u003c').replace(/>/g, '\\u003e')})">
          <td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()"><button class="fav-star${favActive}" data-fav-id="${g.id}" onclick="toggleRowFavorite(${g.id},this)" title="${g.is_favorite ? 'Quitar favorito' : 'Marcar favorito'}">&#x2605;</button></td>
          <td style="padding:4px 6px">${thumb}</td>
          <td>${_platBadge(g.platform)}</td>
          <td title="${_h(g.canonical_title || '')}">${g.canonical_title || '<span style="color:#444">—</span>'}</td>
          <td class="mono" title="${_h(g.original_filename)}" style="color:#9cdcfe;font-size:12px">${_h(g.original_filename)}</td>
          <td style="white-space:nowrap" onclick="event.stopPropagation()">${statusSel}</td>
          <td><span style="font-size:11px;color:#888">${_h(g.region || '')}</span></td>
          <td>${matchBadge(g.match_confidence)}</td>
          <td style="color:#666;font-size:12px">${fmtSize(g.size_bytes)}</td>
          <td class="mono" style="color:#444;font-size:11px">${(g.sha1 || '').slice(0, 10)}…</td>
        </tr>`;
      }).join('');
      applyColVisibility();
      _renderGamesGrid(rows);
    }

    renderPagination();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="9" class="error-msg">${e.message}</td></tr>`;
  }
}

export async function setPlayStatus(gameId, sourcePath, status) {
  try {
    await apiPost('/api/set-play-status', { game_id: gameId, status: status || null, source_path: sourcePath });
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export function renderPagination() {
  const pg = document.getElementById('games-pagination');
  const total = gamesState.total;
  const limit = gamesState.limit;
  const offset = gamesState.offset;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  const prevDisabled = offset === 0 ? 'disabled style="opacity:.4;cursor:default"' : '';
  const nextDisabled = offset + limit >= total ? 'disabled style="opacity:.4;cursor:default"' : '';

  pg.innerHTML = `
    <button class="btn" ${prevDisabled} onclick="loadGames(${Math.max(0, offset - limit)})">&#x2190; Anterior</button>
    <span>Página ${currentPage} de ${totalPages}</span>
    <button class="btn" ${nextDisabled} onclick="loadGames(${offset + limit})">Siguiente &#x2192;</button>
    <select style="background:#1e1e2e;border:1px solid #444;color:#d4d4d4;padding:4px 8px;border-radius:4px;font:inherit;font-size:13px" onchange="gamesState.limit=+this.value;loadGames(0)">
      ${[50, 100, 200, 500].map(n => `<option value="${n}"${n === limit ? ' selected' : ''}>${n} por página</option>`).join('')}
    </select>`;
}

export function setGamesView(mode) {
  _gamesViewMode = mode;
  localStorage.setItem('games_view_mode', mode);
  const listView = document.getElementById('games-list-view');
  const gridView = document.getElementById('games-grid-view');
  const btnList  = document.getElementById('btn-view-list');
  const btnGrid  = document.getElementById('btn-view-grid');
  if (listView) listView.classList.toggle('hidden', !(mode === 'list'));
  if (gridView) gridView.classList.toggle('hidden', !(mode === 'grid'));
  if (btnList)  btnList.classList.toggle('active', mode === 'list');
  if (btnGrid)  btnGrid.classList.toggle('active', mode === 'grid');
  loadGames(gamesState.offset);
}

export function _renderGamesGrid(games) {
  const grid = document.getElementById('games-grid');
  if (!grid) return;
  if (games.length === 0) { grid.innerHTML = ''; return; }
  const statusIcon = { playing: '▶', completed: '✅', '100pct': '💯', abandoned: '⏸' };
  grid.innerHTML = games.map(g => {
    const thumb = g.id
      ? `<img src="/api/asset-image?game_id=${g.id}" alt="" onerror="this.parentElement.innerHTML='<span class=gc-no-art>&#x1F3AE;</span>'">`
      : `<span class="gc-no-art">&#x1F3AE;</span>`;
    const title = _h(g.canonical_title || g.original_filename || '—');
    const accentGc = _platHex(g.platform);
    const statusBadge = (g.play_status && statusIcon[g.play_status])
      ? `<span class="gc-status-badge" title="${g.play_status}">${statusIcon[g.play_status]}</span>` : '';
    const favBadge = g.is_favorite ? `<span class="gc-fav-badge" title="Favorito">★</span>` : '';
    return `<div class="game-card" style="border-top:2px solid ${accentGc}40" onclick="openGamePanel(${JSON.stringify(g).replace(/</g, '\\u003c').replace(/>/g, '\\u003e')})">
      <div class="gc-thumb">${thumb}${statusBadge}${favBadge}</div>
      <div class="gc-body">
        <div class="gc-title" title="${title}">${title}</div>
        <div class="gc-meta">${_platBadge(g.platform)}</div>
      </div>
    </div>`;
  }).join('');
}

// ── Game panel ────────────────────────────────────────────────────────────────
export function _gpSetFavStar(isFav) {
  const btn = document.getElementById('gp-fav-btn');
  if (!btn) return;
  _txtCls(btn, isFav ? 'txt-fav' : 'txt-dim');
  btn.title = isFav ? 'Quitar de favoritos' : 'Marcar como favorito';
}

function _gpFillMeta(g) {
  document.getElementById('gp-title').textContent = g.canonical_title || g.original_filename || '—';
  document.getElementById('gp-filename').textContent = g.original_filename || '';
  const rows = [
    ['Plataforma', _platBadge(g.platform)],
    ['Región',    g.region    ? _h(g.region)    : '<span style="color:#444">—</span>'],
    ['Año',       g.year      ? _h(g.year)      : '<span style="color:#444">—</span>'],
    ['Género',    g.genre     ? _h(g.genre)     : '<span style="color:#444">—</span>'],
    ['Jugadores', g.players   ? _h(g.players)   : '<span style="color:#444">—</span>'],
    ['Publisher', g.publisher ? _h(g.publisher) : '<span style="color:#444">—</span>'],
    ['Developer', g.developer ? _h(g.developer) : null],
    ['Nota',      g.rating    ? _h(g.rating)    : '<span style="color:#444">—</span>'],
    ['Tamaño',    fmtSize(g.size_bytes)],
    ['SHA1',      `<span style="color:#444;font-family:Consolas,monospace;font-size:11px">${(g.sha1 || '').slice(0, 10)}…</span>`],
  ];
  document.getElementById('gp-meta').innerHTML = rows.filter(([, v]) => v).map(([k, v]) => `<span class="gk">${k}</span><span class="gv">${v}</span>`).join('');
  const desc = document.getElementById('gp-desc');
  if (g.description) { desc.textContent = g.description; desc.classList.remove('hidden'); }
  else { desc.classList.add('hidden'); }
  const sel = document.getElementById('gp-status-sel');
  if (sel) sel.value = g.play_status || '';
  const notesEl = document.getElementById('gp-notes');
  if (notesEl) { notesEl.value = g.notes || ''; _txtCls(notesEl, g.notes ? null : 'txt-dim'); }
  // NLP-REC: rating stars + play count
  _gpRenderStars(g.user_rating || null);
  const pcEl = document.getElementById('gp-play-count');
  if (pcEl) {
    const n = g.play_count || 0;
    pcEl.textContent = n > 0 ? `${n} sesión${n !== 1 ? 'es' : ''} detectada${n !== 1 ? 's' : ''}` : '';
  }
  // Populate metadata edit fields
  _gpSetEditField('gme-title',       g.canonical_title || g.ss_title || '');
  _gpSetEditField('gme-year',        g.year        || '');
  _gpSetEditField('gme-genre',       g.genre       || '');
  _gpSetEditField('gme-publisher',   g.publisher   || '');
  _gpSetEditField('gme-developer',   g.developer   || '');
  _gpSetEditField('gme-rating',      g.rating      || '');
  _gpSetEditField('gme-description', g.description || '');
}

function _gpSetEditField(id, val) {
  const el = document.getElementById(id);
  if (el && val !== undefined) el.value = val;
}

export function gpShowPlaytimeInfo(g) {
  const wrap = document.getElementById('gp-playtime-wrap');
  if (!wrap) return;
  wrap.classList.remove('hidden');
  const infoEl  = document.getElementById('gp-playtime-info');
  const hoursEl = document.getElementById('gp-playtime-hours');
  const minsEl  = document.getElementById('gp-playtime-mins');
  if (!infoEl || !hoursEl || !minsEl) return;
  const lastPlayed = g.last_played_at ? new Date(g.last_played_at) : null;
  if (lastPlayed) {
    const diffMs    = Date.now() - lastPlayed;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays  = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    let timeStr = '';
    if (diffDays >= 365)      timeStr = `Hace ${Math.floor(diffDays / 365)} años`;
    else if (diffDays >= 30)  timeStr = `Hace ${Math.floor(diffDays / 30)} meses`;
    else if (diffDays > 1)    timeStr = `Hace ${diffDays} días`;
    else if (diffHours > 1)   timeStr = `Hace ${diffHours} horas`;
    else                      timeStr = 'Hace menos de una hora';
    infoEl.innerHTML = timeStr || 'Nunca jugado';
  } else {
    infoEl.innerHTML = 'Nunca jugado';
  }
  hoursEl.value = '';
  minsEl.value  = '';
}

export function gpLogPlaytime() {
  const hoursEl = document.getElementById('gp-playtime-hours');
  const minsEl  = document.getElementById('gp-playtime-mins');
  if (!hoursEl || !minsEl) return;
  const hours = parseInt(hoursEl.value) || 0;
  const mins  = parseInt(minsEl.value)  || 0;
  if (hours === 0 && mins === 0) { alert('Ingresa al menos 1 minuto de juego'); return; }
  if (mins > 59) { alert('Los minutos deben estar entre 0 y 59'); return; }
  alert(`Sesión registrada: ${hours}h ${mins}m (${hours * 60 + mins} min)`);
  hoursEl.value = '';
  minsEl.value  = '';
}

export function openGamePanel(g) {
  _gpGameId = g.id;
  // Cover
  const coverWrap = document.getElementById('gp-cover-wrap');
  coverWrap.innerHTML = `<img src="/api/asset-image?game_id=${g.id}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'gp-no-art',innerHTML:'&#127918;'}))" alt="">`;
  // Platform accent color
  document.getElementById('game-panel').style.borderLeftColor = _platHex(g.platform);
  // Fill metadata
  _gpFillMeta(g);
  // Favorite star
  _gpSetFavStar(g.is_favorite);
  // Tags — load async
  const tagsList = document.getElementById('gp-tags-list');
  tagsList.innerHTML = '<span style="color:#555;font-size:11px">cargando…</span>';
  apiFetch('/api/game-tags?id=' + g.id).then(r => _gpRenderTags(r.tags || [])).catch(() => { tagsList.innerHTML = ''; });
  // Stateshot — load async
  document.getElementById('gp-stateshot-wrap').classList.add('hidden');
  apiFetch('/api/stateshot?id=' + g.id).then(r => {
    if (r.found && r.data) {
      const img = document.getElementById('gp-stateshot');
      img.src = 'data:image/png;base64,' + r.data;
      document.getElementById('gp-stateshot-wrap').classList.remove('hidden');
    }
  }).catch(() => {});
  // Reset RA section + saves info
  const _raSection = document.getElementById('gp-ra-section');
  if (_raSection) _raSection.classList.add('hidden');
  const _raProgress = document.getElementById('gp-ra-user-progress');
  if (_raProgress) _raProgress.textContent = '';
  const _savesInfo = document.getElementById('gp-saves-info');
  if (_savesInfo) _savesInfo.classList.add('hidden');
  document.getElementById('game-panel').dataset.sourcePath = g.source_path || '';
  // Reset asset info
  const _assetInfo = document.getElementById('gp-asset-info');
  if (_assetInfo) _assetInfo.classList.add('hidden');
  // Reset meta editor state
  const _editWrap = document.getElementById('gp-meta-edit-wrap');
  if (_editWrap) _editWrap.classList.add('hidden');
  const _editToggle = document.getElementById('gp-meta-edit-toggle');
  if (_editToggle) _editToggle.style.color = '#444';
  const _scrapePreview = document.getElementById('gp-scrape-preview');
  if (_scrapePreview) _scrapePreview.classList.add('hidden');
  const _gmeResult = document.getElementById('gme-result');
  if (_gmeResult) _gmeResult.textContent = '';
  // Backup history — load async
  const bkWrap = document.getElementById('gp-backups-wrap');
  if (bkWrap) {
    bkWrap.classList.add('hidden');
    document.getElementById('gp-backups-list').innerHTML = '';
    apiFetch('/api/save-backups?id=' + g.id).then(r => {
      if (r.backups?.length) { loadSaveBackupsResult(r.backups, g.id); bkWrap.classList.remove('hidden'); }
    }).catch(() => {});
  }
  // Sync history
  loadGameSyncHistory(g.source_path);
  // Playtime info
  gpShowPlaytimeInfo(g);
  // Launch button
  const launchBtn = document.getElementById('gp-launch-btn');
  if (launchBtn) launchBtn.classList.remove('hidden');
  // Open panel
  document.getElementById('game-panel-overlay').classList.add('open');
  document.getElementById('game-panel').classList.add('open');
  // Load full game data async (meta, RA, saves)
  if (g.id) {
    apiFetch('/api/game?id=' + g.id).then(full => {
      if (full.id !== _gpGameId) return;
      _gpFillMeta(full);
      _gpGameId = full.id;
      const _ai = document.getElementById('gp-asset-info');
      const _ap = document.getElementById('gp-asset-path');
      if (_ai && _ap && full.box_art_path) { _ap.textContent = full.box_art_path; _ai.classList.remove('hidden'); }
      const _raSec = document.getElementById('gp-ra-section');
      if (_raSec && full.ra_game_id) {
        document.getElementById('gp-ra-count').textContent =
          full.ra_achievements > 0 ? `${full.ra_achievements} logros desbloqueables` : 'Juego en RA (sin logros)';
        const _pts = document.getElementById('gp-ra-points');
        if (_pts) _pts.textContent = full.ra_points > 0 ? `${full.ra_points} puntos` : '';
        const _rl = document.getElementById('gp-ra-link');
        if (_rl) _rl.href = `https://retroachievements.org/game/${full.ra_game_id}`;
        _raSec.classList.remove('hidden');
        _gpLoadRaProgress(full.ra_game_id);
      }
      const _si = document.getElementById('gp-saves-info');
      const _sb = document.getElementById('gp-saves-badge');
      if (_si && _sb && full.saves_count !== undefined && full.saves_count > 0) {
        _sb.innerHTML = `&#x1F4BE; ${full.saves_count} save${full.saves_count !== 1 ? 's' : ''} detectado${full.saves_count !== 1 ? 's' : ''}`;
        _si.classList.remove('hidden');
      }
      document.getElementById('game-panel').dataset.sourcePath = full.source_path || '';
    }).catch(() => {});
  }
}

async function _gpLoadRaProgress(raGameId) {
  const el = document.getElementById('gp-ra-user-progress');
  if (!el) return;
  el.textContent = 'Cargando progreso…';
  try {
    const d = await apiFetch('/api/ra-user-progress?ra_game_id=' + raGameId);
    if (d.error) {
      el.textContent = '';
      return;
    }
    if (d.total === 0) { el.textContent = ''; return; }
    const pct = Math.round(d.unlocked / d.total * 100);
    const hc  = d.hardcore > 0 ? ` · ${d.hardcore} hardcore` : '';
    const pts = d.points_earned > 0 ? ` · ${d.points_earned}/${d.points_total} pts` : '';
    const color = pct >= 100 ? '#ffcc00' : pct >= 50 ? '#4ec9b0' : '#888';
    el.innerHTML = `<span style="color:${color};font-weight:600">${d.unlocked}/${d.total} logros (${pct}%)</span>${hc}${pts}`;
  } catch(_) {
    el.textContent = '';
  }
}

export function closeGamePanel() {
  document.getElementById('game-panel-overlay').classList.remove('open');
  document.getElementById('game-panel').classList.remove('open');
}

export async function gpSetStatus(status) {
  if (!_gpGameId) return;
  try {
    await apiPost('/api/set-play-status', { game_id: _gpGameId, status: status || null, source_path: '' });
    if (document.getElementById('tab-games')?.classList.contains('active')) loadGames(gamesState.offset);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

function _gpRenderStars(rating) {
  document.querySelectorAll('#gp-stars .gp-star').forEach(el => {
    const v = parseInt(el.dataset.v);
    el.textContent = v <= (rating || 0) ? '★' : '☆';
    el.classList.toggle('active', v <= (rating || 0));
  });
}

export async function gpSetRating(n) {
  if (!_gpGameId) return;
  // Toggle off if clicking the same star again
  const current = parseInt(document.querySelector('#gp-stars .gp-star.active:last-of-type')?.dataset.v || '0');
  const newRating = current === n ? null : n;
  try {
    await apiPost('/api/play-history', { game_id: _gpGameId, rating: newRating });
    _gpRenderStars(newRating);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export async function gpToggleFavorite() {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/toggle-favorite', { game_id: _gpGameId });
    _gpSetFavStar(r.is_favorite);
    const rowStar = document.querySelector(`[data-fav-id="${_gpGameId}"]`);
    if (rowStar) rowStar.classList.toggle('active', r.is_favorite);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

function _gpRenderTags(tags) {
  const el = document.getElementById('gp-tags-list');
  if (!el) return;
  el.innerHTML = tags.map(t =>
    `<span class="tag-chip">${_h(t)}<span class="tag-remove" onclick="gpRemoveTag('${_h(t)}')" title="Eliminar tag">&times;</span></span>`
  ).join('');
}

export async function gpAddTag() {
  if (!_gpGameId) return;
  const input = document.getElementById('gp-tag-input');
  const tag = input.value.trim();
  if (!tag) return;
  try {
    const r = await apiPost('/api/tag', { game_id: _gpGameId, tag, action: 'add' });
    _gpRenderTags(r.tags || []);
    input.value = '';
    _refreshTagFilter();
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export async function gpRemoveTag(tag) {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/tag', { game_id: _gpGameId, tag, action: 'remove' });
    _gpRenderTags(r.tags || []);
    _refreshTagFilter();
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export async function gpLaunch() {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/launch', { game_id: _gpGameId });
    if (r.ok) showToast('RetroArch lanzado', 'ok');
    else showToast(r.error || 'Error al lanzar', 'err');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export async function gpOpenFolder() {
  const panel = document.getElementById('game-panel');
  const sp = panel?.dataset.sourcePath || '';
  if (!sp) { showToast('Ruta del juego no disponible', 'err'); return; }
  try {
    const r = await apiPost('/api/open-folder', { path: sp });
    if (!r.ok) showToast(r.error || 'No se pudo abrir la carpeta', 'err');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export function loadSaveBackupsResult(saves, gameId) {
  const el = document.getElementById('gp-backups-list');
  if (!el) return;
  el.innerHTML = saves.map(s => {
    const sizeFmt = s.size > 1024 ? (s.size / 1024).toFixed(1) + ' KB' : s.size + ' B';
    const bkPath  = s.backup_path.replace(/\\/g, '/');
    const origSav = s.original_save.replace(/\\/g, '/');
    const ext     = s.extension || '';
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid #1e1e2e">
      <span style="color:#888">${_h(s.timestamp)}<span style="color:#444;margin-left:4px">${_h(ext)}</span></span>
      <span style="color:#555">${sizeFmt}</span>
      <button onclick="restoreBackup(${JSON.stringify(bkPath)},${JSON.stringify(origSav)})" style="background:#1a2a1a;border:1px solid #4ec9b0;color:#4ec9b0;padding:1px 8px;border-radius:3px;font-size:11px;cursor:pointer">Restaurar</button>
    </div>`;
  }).join('');
}

export async function restoreBackup(backupPath, originalSave) {
  if (!confirm('¿Restaurar este backup? El save actual será reemplazado.\nEl siguiente sync lo subirá a Dropbox y llegará a la consola.')) return;
  try {
    const r = await apiPost('/api/restore-backup', { backup_path: backupPath, original_save: originalSave });
    if (r.ok) showToast('Save restaurado → ' + (r.restored_to || ''), 'ok');
    else showToast(r.error || 'Error al restaurar', 'err');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

let _gpNotesTimer = null;
export function gpNotesInput() {
  clearTimeout(_gpNotesTimer);
  _gpNotesTimer = setTimeout(async () => {
    if (!_gpGameId) return;
    const val = document.getElementById('gp-notes')?.value ?? '';
    try { await apiPost('/api/set-metadata', { game_id: _gpGameId, notes: val }); } catch(_) {}
  }, 800);
}

export function gpToggleMetaEdit() {
  const wrap = document.getElementById('gp-meta-edit-wrap');
  const btn  = document.getElementById('gp-meta-edit-toggle');
  if (!wrap) return;
  const open = !wrap.classList.contains('hidden');
  wrap.classList.toggle('hidden', open);
  if (btn) _txtCls(btn, open ? null : 'txt-ok');
}

export async function gpSaveMetaFields() {
  if (!_gpGameId) return;
  const payload = { game_id: _gpGameId };
  const title = document.getElementById('gme-title')?.value.trim();
  if (title) payload.canonical_title = title;
  ['year', 'genre', 'publisher', 'developer', 'rating'].forEach(k => {
    const v = document.getElementById('gme-' + k)?.value.trim();
    if (v !== undefined) payload[k] = v;
  });
  const desc = document.getElementById('gme-description')?.value.trim();
  if (desc !== undefined) payload.description = desc;
  const res = document.getElementById('gme-result');
  try {
    await apiPost('/api/set-metadata', payload);
    if (res) { _txtCls(res, 'txt-ok'); res.textContent = '✓ Guardado'; setTimeout(() => { if (res) res.textContent = ''; }, 2000); }
    if (title) document.getElementById('gp-title').textContent = title;
    apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
  } catch(e) {
    if (res) { _txtCls(res, 'txt-err'); res.textContent = 'Error: ' + e.message; }
  }
}

export async function gpScrapeSingle() {
  if (!_gpGameId) return;
  const previewEl = document.getElementById('gp-scrape-preview');
  const res = document.getElementById('gme-result');
  if (previewEl) { previewEl.classList.remove('hidden'); previewEl.innerHTML = '<span style="color:#555">Consultando ScreenScraper…</span>'; }
  try {
    const r = await apiPost('/api/scrape-single', { game_id: _gpGameId, preview: true });
    if (!r.found) {
      if (previewEl) previewEl.innerHTML = `<span style="color:#f44747">No encontrado: ${_h(r.error || 'sin resultados')}</span>`;
      return;
    }
    const rows = [
      ['Título', r.title], ['Año', r.year], ['Género', r.genre],
      ['Publisher', r.publisher], ['Developer', r.developer], ['Nota', r.rating],
    ].filter(([, v]) => v).map(([k, v]) => `<span style="color:#888">${k}:</span> <span style="color:#d4d4d4">${_h(v)}</span>`).join(' &nbsp;·&nbsp; ');
    if (previewEl) previewEl.innerHTML = `<div style="margin-bottom:8px;line-height:1.8">${rows}</div>
      <button onclick="gpApplyScrape()" style="background:#1a3a2a;border:1px solid #4ec9b0;color:#4ec9b0;padding:3px 12px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Aplicar</button>
      <button onclick="document.getElementById('gp-scrape-preview').classList.add('hidden')" style="margin-left:6px;background:none;border:1px solid #444;color:#888;padding:3px 10px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Cancelar</button>`;
  } catch(e) {
    if (previewEl) previewEl.innerHTML = `<span style="color:#f44747">Error: ${_h(e.message)}</span>`;
  }
}

export async function gpApplyScrape() {
  if (!_gpGameId) return;
  const previewEl = document.getElementById('gp-scrape-preview');
  const res = document.getElementById('gme-result');
  try {
    const r = await apiPost('/api/scrape-single', { game_id: _gpGameId, preview: false });
    if (r.applied) {
      if (previewEl) previewEl.classList.add('hidden');
      if (res) { _txtCls(res, 'txt-ok'); res.textContent = '✓ Metadatos actualizados'; setTimeout(() => { if (res) res.textContent = ''; }, 2500); }
      apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
    } else {
      if (res) { _txtCls(res, 'txt-err'); res.textContent = r.error || 'Error'; }
    }
  } catch(e) {
    if (res) { _txtCls(res, 'txt-err'); res.textContent = 'Error: ' + e.message; }
  }
}

export async function gpCopyAssetToEsde() {
  const resultEl = document.getElementById('gp-asset-copy-result');
  if (resultEl) resultEl.textContent = 'Copiando…';
  try {
    const d = await apiFetch('/api/copy-assets-to-esde');
    if (d.error) { if (resultEl) resultEl.textContent = '✗ ' + d.error; return; }
    if (resultEl) resultEl.textContent = `✓ ${d.copied} copiadas`;
  } catch(e) { if (resultEl) resultEl.textContent = '✗ ' + e.message; }
}

export async function loadGameSyncHistory(sourcePath) {
  const wrap = document.getElementById('gp-sync-history-wrap');
  const list = document.getElementById('gp-sync-history-list');
  if (!wrap || !list || !sourcePath) return;
  wrap.classList.add('hidden');
  list.innerHTML = '';
  try {
    const d = await apiFetch('/api/game-sync-history?source_path=' + encodeURIComponent(sourcePath));
    const hist = d.history || [];
    if (!hist.length) return;
    wrap.classList.remove('hidden');
    list.innerHTML = hist.map(h => {
      const clr = h.result === 'ok' ? '#4ec9b0' : '#e06c75';
      const dir = h.direction === 'up' ? '&#x2191;' : h.direction === 'down' ? '&#x2193;' : '&#x21C4;';
      return `<div style="display:flex;gap:6px;align-items:center;padding:3px 0;border-bottom:1px solid #1a1a2a">
        <span style="color:${clr};font-size:11px">${dir} ${_h(h.result || '')}</span>
        <span style="color:#555;font-size:10px;flex:1">${_h(h.created_at?.substring(0, 16) || '')}</span>
        ${h.message ? `<span style="color:#666;font-size:10px">${_h(h.message.substring(0, 40))}</span>` : ''}
      </div>`;
    }).join('');
  } catch(_) {}
}

// ── TV Mode ───────────────────────────────────────────────────────────────────
export async function enterTvMode() {
  _tvActive = true;
  showTab('tv');
  try { await document.documentElement.requestFullscreen(); } catch(_) {}
  await loadTvGrid('', 0);
}

export function exitTvMode() {
  _tvActive = false;
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  showTab('collection');
}

export async function loadTvGrid(platform, offset) {
  try {
    const params = new URLSearchParams({ limit: _TV_LIMIT, offset, sort_by: 'canonical_title' });
    if (platform) params.append('platform', platform);
    const resp = await fetch(`/api/games?${params}`);
    const data = await resp.json();
    const games = data.games || [];
    if (offset === 0) {
      _tvGames = games;
    } else {
      _tvGames.push(...games);
    }
    _tvPlatform = platform;
    _tvOffset = offset;
    _renderTvGrid(games, offset > 0);
  } catch(e) { console.error('loadTvGrid failed:', e); }
}

function _renderTvGrid(games, append) {
  const gridEl = document.getElementById('tv-grid');
  if (!gridEl) return;
  if (!append) gridEl.innerHTML = '';
  games.forEach((g, idx) => {
    const tile = document.createElement('div');
    tile.className = 'tv-tile';
    tile.setAttribute('data-tv-idx', _tvOffset + idx);
    tile.innerHTML = `
      <div class="tv-cover skeleton">
        <img src="/api/asset-image?game_id=${g.id}" alt="${g.canonical_title || ''}"
          onload="this.parentElement.classList.remove('skeleton')"
          onerror="this.parentElement.classList.remove('skeleton');this.parentElement.innerHTML='<span>🎮</span>'">
      </div>
      <div class="tv-label">${_h(g.canonical_title || g.original_filename)}</div>
      <div class="tv-plat">${_h(g.platform || '')}</div>
    `;
    tile.addEventListener('click', () => {
      _tvMoveFocus(_tvOffset + idx);
      openGamePanel(g);
    });
    gridEl.appendChild(tile);
  });
  _tvCols = Math.max(1, Math.round(gridEl.offsetWidth / 196));
  if (_tvGames.length > 0) _tvMoveFocus(0);
}

export function _tvMoveFocus(idx) {
  document.querySelector('.tv-tile.tv-focused')?.classList.remove('tv-focused');
  _tvFocusIdx = Math.max(0, Math.min(idx, _tvGames.length - 1));
  const tile = document.querySelector(`.tv-tile[data-tv-idx="${_tvFocusIdx}"]`);
  if (tile) { tile.classList.add('tv-focused'); tile.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  if (_tvGames[_tvFocusIdx]) _updateTvInfoBar(_tvGames[_tvFocusIdx]);
}

function _updateTvInfoBar(g) {
  document.getElementById('tv-info-title').textContent = g.canonical_title || '';
  document.getElementById('tv-info-platform').textContent = g.platform || '';
  const statusEl = document.getElementById('tv-info-status');
  if (statusEl) statusEl.textContent = g.play_status || '';
}

// ── NLP-REC: Recommendations panel ───────────────────────────────────────────

export async function loadRecommendations() {
  try {
    const r = await apiFetch('/api/recommendations');
    const panel = document.getElementById('rec-panel');
    if (!panel) return;
    if (!r.items || r.items.length === 0) {
      panel.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');
    const updEl = document.getElementById('rec-updated-at');
    if (updEl && r.updated_at) {
      const d = new Date(r.updated_at);
      updEl.textContent = `· ${d.toLocaleDateString('es-ES', { day:'2-digit', month:'short' })}`;
    }
    const list = document.getElementById('rec-list');
    list.innerHTML = r.items.map(it => {
      const title = _h(it.title || '—');
      const plat  = _h(it.platform || '');
      const score = it.score != null ? `<span style="color:#555;font-size:10px">${Math.round(it.score * 100)}%</span>` : '';
      const reason = it.reason ? `<div style="font-size:10px;color:#555;margin-top:2px">${_h(it.reason)}</div>` : '';
      const gameData = it.id ? ` onclick="apiFetch('/api/game?id=${it.id}').then(g=>{if(g.id)openGamePanel(g)}).catch(()=>{})"` : '';
      return `<div class="rec-card"${gameData}>
        <div style="font-size:12px;font-weight:600;color:#d4d4d4">${title} ${score}</div>
        <div style="font-size:11px;color:#888">${plat}</div>
        ${reason}
      </div>`;
    }).join('');
  } catch(_) {}
}

export function dismissRecommendations() {
  document.getElementById('rec-panel')?.classList.add('hidden');
}
