// js/tabs/games.js — Games tab: list, filters, pagination, game panel, TV mode
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { _showConfirm } from '../components/modal.js';

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
// TV-UX-1: si el último lote vino completo (== _TV_LIMIT), puede haber más.
let _tvHasMore = true;
// TV-UX-3: pestaña desde la que se entró, para volver ahí al salir en vez de fijo a 'games'.
let _tvSourceTab = 'games';
let _tvEndFlashTimer = null;

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
  // JUEGOS-FIX-3: los índices de celda hardcodeados (`tr.cells[N]`) se
  // desincronizaban cada vez que se añadía/quitaba una columna a la tabla
  // (p.ej. el 📦 de Anbernic) — con una preferencia guardada de ocultar
  // "Identificación" acababa ocultando el Título en su lugar. `data-col`
  // en el `<td>` (fijado en el template de la fila) hace esto inmune al
  // orden real de columnas.
  document.querySelectorAll('#games-tbody tr').forEach(tr => {
    Object.entries(prefs).forEach(([key, visible]) => {
      const td = tr.querySelector(`[data-col="${key}"]`);
      if (td) td.classList.toggle('hidden', !visible);
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

// source_path del juego abierto en el panel — enruta a la BD correcta (DEVSEL-FIX-2)
const _gpSrc = () => document.getElementById('game-panel')?.dataset.sourcePath || '';

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
    _populate('games-genre',    r.genres    || []);
    _populate('games-year',     r.years     || []);
    // Bug real: el desplegable de plataforma solo se rellenaba con las
    // plataformas presentes en la página actual de resultados (loadGames,
    // máx. 100 filas) — con la biblioteca ordenada por plataforma, esa
    // primera página cae entera en una sola plataforma (o "Unknown"),
    // dejando el filtro casi inútil. filter-options ya devuelve la lista
    // completa y distinta de la BD, igual que genre/year.
    _populate('games-platform', r.platforms || []);
    platformsLoaded = true;
  } catch (_) {}
}

export function toggleFavoritesFilter() {
  const btn = document.getElementById('btn-filter-favorites');
  if (!btn) return;
  gamesState.favorite = !gamesState.favorite;
  _txtCls(btn, gamesState.favorite ? 'txt-fav' : 'txt-muted');
  btn.style.borderColor = gamesState.favorite ? 'var(--c-amber)' : '#444';
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

// ANBERNIC-PICK-1: marca/desmarca con el tag "anbernic" TODOS los juegos que
// cumplen el filtro actual de la pestaña (mismos parámetros que loadGames),
// no solo la página visible — el backend recalcula el conjunto server-side.
export function markFilteredForAnbernic(unmark) {
  const q = document.getElementById('games-search')?.value.trim() || '';
  const body = { tag: 'anbernic', action: unmark ? 'remove' : 'add' };
  if (gamesState.platform) body.platform = gamesState.platform;
  if (gamesState.status)   body.status   = gamesState.status;
  if (q)                   body.search   = q;
  const ft = document.getElementById('games-filetype')?.value;
  if (ft !== undefined && ft !== 'all') body.filetype = ft;
  const ps = document.getElementById('games-play-status')?.value;
  if (ps) body.play_status = ps;
  if (gamesState.favorite) body.favorite = true;
  const tagF = document.getElementById('games-tag-filter')?.value;
  if (tagF) body.existing_tag = tagF;
  const genreF = document.getElementById('games-genre')?.value;
  if (genreF) body.genre = genreF;
  const yearF = document.getElementById('games-year')?.value;
  if (yearF) body.year = yearF;
  const root = gamesState.root || _deviceRoot();
  if (root) body.root = root;

  const verb = unmark ? 'Desmarcar' : 'Marcar';
  _showConfirm(
    `${verb} para la Anbernic`,
    `¿${verb.toLowerCase()} para la Anbernic <b>todos los juegos que cumplen el filtro actual</b> (${gamesState.total} en total)?`,
    verb,
    async () => {
      const r = await apiPost('/api/tag-bulk', body);
      if (r.error) { showToast(r.error, 'error'); return; }
      showToast(`${r.count} juego${r.count !== 1 ? 's' : ''} ${unmark ? 'desmarcados' : 'marcados'} para la Anbernic`, 'success');
      _refreshTagFilter();
      loadGames(gamesState.offset);
    },
  );
}

export async function toggleRowFavorite(gameId, btn) {
  try {
    const r = await apiPost('/api/toggle-favorite', { game_id: gameId, source_path: btn.dataset.path || '' });
    btn.classList.toggle('active', r.is_favorite);
    btn.title = r.is_favorite ? 'Quitar favorito' : 'Marcar favorito';
    // If the panel is open for this game, update its star too
    if (_gpGameId === gameId) _gpSetFavStar(r.is_favorite);
    // If filtering by favorites, refresh list
    if (gamesState.favorite) loadGames(gamesState.offset);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ANBERNIC-PICK-7: marcar/desmarcar un juego suelto (selector individual),
// mismo tag 'anbernic' que markFilteredForAnbernic pero sin depender del filtro.
export async function toggleRowAnbernic(gameId, btn) {
  const isSet = btn.classList.contains('active');
  try {
    const r = await apiPost('/api/tag', {
      game_id: gameId,
      tag: 'anbernic',
      action: isSet ? 'remove' : 'add',
      source_path: btn.dataset.path || '',
    });
    const nowSet = (r.tags || []).includes('anbernic');
    btn.classList.toggle('active', nowSet);
    btn.title = nowSet ? 'Quitar de Anbernic' : 'Marcar para Anbernic';
    if (document.getElementById('games-tag-filter')?.value === 'anbernic') loadGames(gamesState.offset);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ── ANBERNIC-PICK-7: asistente guiado "¿qué te llevas a la Anbernic?" ──────────
// ponytail: umbral fijo para "pequeña" vs "grande" — ajustar si 2 GiB no encaja
// con el tamaño real de SD del usuario.
const _WIZARD_SMALL_THRESHOLD_BYTES = 2 * 1024 ** 3;

export async function openAnbernicWizard() {
  const modal = document.getElementById('anbernic-wizard-modal');
  const body = document.getElementById('anbernic-wizard-body');
  if (!modal || !body) return;
  modal.classList.remove('hidden');
  body.innerHTML = '<p class="loading">Cargando plataformas…</p>';
  try {
    const d = await apiFetch('/api/platform-stats');
    _renderAnbernicWizard(d.platforms || []);
  } catch(e) {
    body.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

export function closeAnbernicWizard() {
  document.getElementById('anbernic-wizard-modal')?.classList.add('hidden');
}

function _renderAnbernicWizard(platforms) {
  const body = document.getElementById('anbernic-wizard-body');
  if (!body) return;
  const small = platforms.filter(p => p.total_size <= _WIZARD_SMALL_THRESHOLD_BYTES);
  const large = platforms.filter(p => p.total_size > _WIZARD_SMALL_THRESHOLD_BYTES);

  const row = (p, actionHtml) => `
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--c-border)">
      <div style="flex:1;min-width:0">
        <div style="color:var(--c-text);font-size:13px">${_h(p.platform)}</div>
        <div style="color:var(--c-dim);font-size:11px">${p.total_games} juego${p.total_games !== 1 ? 's' : ''} · ${fmtSize(p.total_size)} · ${p.tagged_count}/${p.total_games} marcados</div>
      </div>
      ${actionHtml}
    </div>`;

  const smallHtml = small.map(p => {
    const done = p.tagged_count >= p.total_games && p.total_games > 0;
    return row(p, done
      ? `<span style="color:var(--c-teal);font-size:12px">&#x2713; Toda marcada</span>`
      : `<button class="btn" style="font-size:12px" onclick="wizardMarkPlatform('${_h(p.platform).replace(/'/g, "\\'")}', this)">Marcar toda</button>`);
  }).join('') || '<p class="empty" style="font-size:12px">Ninguna.</p>';

  const largeHtml = large.map(p => row(p,
    `<button class="btn" style="font-size:12px;border-color:var(--c-teal);color:var(--c-teal)" onclick="wizardPickIndividually('${_h(p.platform).replace(/'/g, "\\'")}')">Elegir juego a juego &#x2192;</button>`
  )).join('') || '<p class="empty" style="font-size:12px">Ninguna.</p>';

  body.innerHTML = `
    <p style="color:var(--c-muted);font-size:12px;margin-bottom:10px">
      Plataformas pequeñas: llévatelas enteras de un clic. Plataformas grandes: elige juego a juego
      en Juegos (usa el 📦 por fila, o filtra y busca ahí).
    </p>
    <div style="margin-bottom:6px;color:var(--c-teal);font-size:11px;text-transform:uppercase;letter-spacing:1px">Pequeñas — llévatelas enteras (&le; ${fmtSize(_WIZARD_SMALL_THRESHOLD_BYTES)})</div>
    ${smallHtml}
    <div style="margin:14px 0 6px;color:var(--c-orange);font-size:11px;text-transform:uppercase;letter-spacing:1px">Grandes — elige juego a juego</div>
    ${largeHtml}
  `;
}

export async function wizardMarkPlatform(platform, btn) {
  if (btn) { btn.disabled = true; btn.textContent = 'Marcando…'; }
  try {
    const r = await apiPost('/api/tag-bulk', { platform, tag: 'anbernic', action: 'add' });
    if (r.error) { showToast(r.error, 'err'); return; }
    showToast(`${r.count} juego${r.count !== 1 ? 's' : ''} de ${platform} marcados para la Anbernic`, 'ok');
    openAnbernicWizard(); // re-render with fresh tagged_count
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export function wizardPickIndividually(platform) {
  closeAnbernicWizard();
  goToGames(null, '', 'rom', platform);
  const sortSel = document.getElementById('games-sort-by');
  if (sortSel) sortSel.value = 'added';
}

// ── Platform helpers (duplicated for module scope) ────────────────────────────
export function fmtSize(n) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

export function badge(cls, text, title) {
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
  gba: 'var(--c-teal)', snes: 'var(--c-blue)', nes: 'var(--c-red)', gb: 'var(--c-yellow)',
  gbc: '#d7ba7d', nds: 'var(--c-purple)', '3ds': 'var(--c-lblue)', n64: 'var(--c-teal)',
  psx: 'var(--c-lblue)', ps2: 'var(--c-blue)', psp: '#79c0ff',
  genesis: 'var(--c-orange)', md: 'var(--c-orange)', sms: 'var(--c-green)', gg: 'var(--c-teal)',
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
  tbody.innerHTML = '<tr><td colspan="10" class="loading">Cargando…</td></tr>';
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
      rootBanner.innerHTML = `<span style="color:var(--c-muted);font-size:12px">Filtrando por: <code style="color:var(--c-orange)">${gamesState.root}</code></span> <button class="btn" style="padding:2px 8px;font-size:11px" onclick="gamesState.root=null;document.getElementById('games-root-banner').classList.add('hidden');loadGames(0)">&#x2715; Quitar filtro</button>`;
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
        _datBanner.innerHTML = `<span style="color:var(--c-yellow)">⚠</span> Sin catálogos DAT — identificación por SHA1 no disponible. Los juegos sin catálogo no pueden renombrarse de forma fiable. <a href="#" onclick="showTab('settings');return false;" style="color:var(--c-lblue);text-decoration:underline">→ Descargar catálogos</a>`;
        _datBanner.classList.remove('hidden');
      } else if (d.dat_count > 0 && _unmatched > 0) {
        _datBanner.innerHTML = `<span style="color:var(--c-teal)">✓</span> ${d.dat_count} catálogo${d.dat_count !== 1 ? 's' : ''} DAT cargado${d.dat_count !== 1 ? 's' : ''} · <span style="color:var(--c-muted)">${_unmatched} sin identificar</span>`;
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
        const thumb = g.id ? `<img src="/api/asset-image?game_id=${g.id}" style="width:32px;height:32px;object-fit:contain;border-radius:2px;background:var(--c-input)" onerror="this.style.display=\'none\'">` : '';
        const statusVal = g.play_status || '';
        const statusSel = `<select style="background:var(--c-panel);border:1px solid var(--c-border);color:var(--c-text);padding:2px 5px;border-radius:3px;font:inherit;font-size:11px;cursor:pointer" onchange="setPlayStatus(${g.id}, '${_srcPath.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}', this.value)">
          <option value=""${statusVal === '' ? ' selected' : ''}>—</option>
          <option value="playing"${statusVal === 'playing' ? ' selected' : ''}>&#x1F3AE; Jugando</option>
          <option value="completed"${statusVal === 'completed' ? ' selected' : ''}>&#x2705; Completado</option>
          <option value="100pct"${statusVal === '100pct' ? ' selected' : ''}>&#x1F4AF; Al 100%</option>
          <option value="abandoned"${statusVal === 'abandoned' ? ' selected' : ''}>&#x23F8; Abandonado</option>
        </select>`;
        const accentColor = _platHex(g.platform);
        const favActive = g.is_favorite ? ' active' : '';
        return `<tr style="cursor:pointer;border-left:2px solid ${accentColor}20" onclick="openGamePanel(${_h(JSON.stringify(g))})">
          <td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()"><button class="fav-star${favActive}" data-fav-id="${g.id}" data-path="${_h(g.source_path || '')}" onclick="toggleRowFavorite(${g.id},this)" title="${g.is_favorite ? 'Quitar favorito' : 'Marcar favorito'}">&#x2605;</button></td>
          <td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()"><button class="fav-star${g.is_anbernic ? ' active' : ''}" data-path="${_h(g.source_path || '')}" onclick="toggleRowAnbernic(${g.id},this)" title="${g.is_anbernic ? 'Quitar de Anbernic' : 'Marcar para Anbernic'}">&#x1F4E6;</button></td>
          <td style="padding:4px 6px">${thumb}</td>
          <td>${_platBadge(g.platform)}</td>
          <td title="${_h(g.canonical_title || '')}">${g.canonical_title || '<span style="color:var(--c-ghost)">—</span>'}</td>
          <td class="mono" title="${_h(g.original_filename)}" style="color:var(--c-lblue);font-size:12px">${_h(g.original_filename)}
            <a href="/api/download-rom?path=${encodeURIComponent(g.source_path || '')}" onclick="event.stopPropagation()" title="Descargar este ROM" style="margin-left:6px;text-decoration:none">&#x2B07;</a>
          </td>
          <td style="white-space:nowrap" onclick="event.stopPropagation()">${statusSel}</td>
          <td data-col="region"><span style="font-size:11px;color:var(--c-muted)">${_h(g.region || '')}</span></td>
          <td data-col="match">${matchBadge(g.match_confidence)}</td>
          <td data-col="size" style="color:var(--c-hint);font-size:12px">${fmtSize(g.size_bytes)}</td>
          <td data-col="sha1" class="mono" style="color:var(--c-ghost);font-size:11px">${(g.sha1 || '').slice(0, 10)}…</td>
        </tr>`;
      }).join('');
      applyColVisibility();
      _renderGamesGrid(rows);
    }

    renderPagination();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="10" class="error-msg">${e.message}</td></tr>`;
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
    <select style="background:var(--c-panel);border:1px solid #444;color:var(--c-text);padding:4px 8px;border-radius:4px;font:inherit;font-size:13px" onchange="gamesState.limit=+this.value;loadGames(0)">
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
    return `<div class="game-card" style="border-top:2px solid ${accentGc}40" onclick="openGamePanel(${_h(JSON.stringify(g))})">
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
    ['Región',    g.region    ? _h(g.region)    : '<span style="color:var(--c-ghost)">—</span>'],
    ['Año',       g.year      ? _h(g.year)      : '<span style="color:var(--c-ghost)">—</span>'],
    ['Género',    g.genre     ? _h(g.genre)     : '<span style="color:var(--c-ghost)">—</span>'],
    ['Jugadores', g.players   ? _h(g.players)   : '<span style="color:var(--c-ghost)">—</span>'],
    ['Publisher', g.publisher ? _h(g.publisher) : '<span style="color:var(--c-ghost)">—</span>'],
    ['Developer', g.developer ? _h(g.developer) : null],
    ['Nota',      g.rating    ? _h(g.rating)    : '<span style="color:var(--c-ghost)">—</span>'],
    ['Tamaño',    fmtSize(g.size_bytes)],
    ['SHA1',      `<span style="color:var(--c-ghost);font-family:Consolas,monospace;font-size:11px">${(g.sha1 || '').slice(0, 10)}…</span>`],
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

// JUEGOS-UX-8: total automático desde los .lrtl de RetroArch, por origen
function _fmtMinutes(m) {
  if (!m) return '0m';
  const h = Math.floor(m / 60);
  return h > 0 ? `${h}h ${m % 60}m` : `${m}m`;
}

function _relTimeStr(iso) {
  const d = iso ? new Date(iso) : null;
  if (!d || isNaN(d)) return '';
  const diffMs    = Date.now() - d;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays  = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays >= 365) return `Hace ${Math.floor(diffDays / 365)} años`;
  if (diffDays >= 30)  return `Hace ${Math.floor(diffDays / 30)} meses`;
  if (diffDays > 1)    return `Hace ${diffDays} días`;
  if (diffHours > 1)   return `Hace ${diffHours} horas`;
  return 'Hace menos de una hora';
}

export function gpShowPlaytimeInfo(g) {
  const wrap = document.getElementById('gp-playtime-wrap');
  if (!wrap) return;
  wrap.classList.remove('hidden');
  const infoEl   = document.getElementById('gp-playtime-info');
  const detailEl = document.getElementById('gp-playtime-detail');
  if (!infoEl || !detailEl) return;

  const pc = g.playtime_minutes_pc || 0;
  const android = g.playtime_minutes_android || 0;
  const total = pc + android;
  const last = _relTimeStr(g.last_played_at);

  if (total > 0) {
    infoEl.innerHTML = `<strong>${_fmtMinutes(total)}</strong> totales${last ? ` · última sesión: ${last}` : ''}`;
    // JUEGOS-UX-9: el desglose deja claro qué origen aún no tiene datos
    const pcPart = pc > 0 ? `PC: ${_fmtMinutes(pc)}` : 'PC: sin datos';
    const abPart = android > 0 ? `Consola: ${_fmtMinutes(android)}` : 'Consola: sin datos';
    detailEl.textContent = `${pcPart} · ${abPart}`;
  } else {
    infoEl.textContent = last ? `Última sesión: ${last}` : 'Nunca jugado';
    detailEl.textContent = 'Sin datos de RetroArch aún — pulsa ↻ Actualizar para leer los logs de tiempo.';
  }
}

export async function gpRefreshPlaytime() {
  const btn = document.getElementById('gp-playtime-refresh');
  const gameId = _gpGameId;
  if (btn) { btn.disabled = true; btn.textContent = 'Escaneando…'; }
  try {
    const r = await apiPost('/api/playtime-scan', {});
    if (r.status === 'already_running') { showToast('Ya hay un escaneo en curso', 'info'); return; }
    // Poll hasta que el job termine (el pull adb puede tardar)
    const result = await new Promise((resolve, reject) => {
      const t = setInterval(async () => {
        try {
          const s = await apiFetch('/api/job-status');
          if (!s.playtime_scan_running) { clearInterval(t); resolve(s.playtime_scan_result || {}); }
        } catch(e) { clearInterval(t); reject(e); }
      }, 2000);
    });
    const notes = [result.pc_note, result.android_note].filter(Boolean).join(' · ');
    showToast(`✓ Tiempo actualizado — PC: ${result.pc_matched || 0} juegos, Consola: ${result.android_matched || 0}${notes ? ` (${notes})` : ''}`, 'ok', 5000);
    if (gameId && gameId === _gpGameId) {
      const full = await apiFetch('/api/game?id=' + gameId);
      if (!full.error) gpShowPlaytimeInfo(full);
    }
  } catch(e) {
    showToast('Error al escanear tiempo de juego: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '&#x21BB; Actualizar'; }
  }
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
  tagsList.innerHTML = '<span style="color:var(--c-dim);font-size:11px">cargando…</span>';
  apiFetch('/api/game-tags?id=' + g.id).then(r => _gpRenderTags(r.tags || [])).catch(() => { tagsList.innerHTML = ''; });
  // Screenshots — load async (NEW-2)
  loadGameScreenshots(g.original_filename);
  // Stateshot grid — load async (NEW-4)
  loadGameStatshots(g.id);
  // Reset RA section + saves info
  const _raSection = document.getElementById('gp-ra-section');
  if (_raSection) _raSection.classList.add('hidden');
  const _raProgress = document.getElementById('gp-ra-user-progress');
  if (_raProgress) _raProgress.textContent = '';
  const _raAch = document.getElementById('gp-ra-achievements');
  if (_raAch) _raAch.innerHTML = '';
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
    const color = pct >= 100 ? '#ffcc00' : pct >= 50 ? 'var(--c-teal)' : '#888';
    el.innerHTML = `<span style="color:${color};font-weight:600">${d.unlocked}/${d.total} logros (${pct}%)</span>${hc}${pts}`;
    _gpRenderAchievements(d.achievements || []);
  } catch(_) {
    el.textContent = '';
  }
}

// JUEGOS-UX-2/3: lista de logros desbloqueados/pendientes con iconos lazy
let _gpAchUid = 0;

function _gpAchRow(a) {
  const badge = a.badge_url
    ? `<img src="${a.badge_url}" loading="lazy" width="24" height="24" style="border-radius:3px;flex-shrink:0${a.earned ? '' : ';filter:grayscale(1)'}" alt="">`
    : '';
  const hcTag = a.earned_hardcore ? ' · <span style="color:#ffcc00">hardcore</span>' : '';
  return `<div style="display:flex;gap:8px;align-items:center;padding:3px 0;border-bottom:1px solid #1c1c2a${a.earned ? '' : ';opacity:.55'}">
    ${badge}
    <div style="min-width:0;flex:1">
      <div style="color:var(--c-text)">${a.earned ? '🏆' : '🔒'} ${_h(a.title)} <span style="color:var(--c-dim)">· ${a.points} pts${hcTag}</span></div>
      <div style="color:var(--c-hint);font-size:10px">${_h(a.description)}</div>
    </div>
  </div>`;
}

function _gpAchGroup(label, labelColor, items, limit = 10) {
  if (!items.length) return '';
  const uid = 'gpach_' + (++_gpAchUid);
  const visible = items.slice(0, limit).map(_gpAchRow).join('');
  const rest = items.slice(limit);
  let html = `<div style="color:${labelColor};font-weight:600;margin:8px 0 2px">${label} (${items.length})</div>`;
  html += visible;
  if (rest.length) {
    html += `<div id="${uid}_rest" class="hidden">${rest.map(_gpAchRow).join('')}</div>`;
    html += `<button id="${uid}_btn" onclick="(function(){var r=document.getElementById('${uid}_rest'),b=document.getElementById('${uid}_btn');var open=!r.classList.contains('hidden');r.classList.toggle('hidden',open);b.textContent=open?'▼ Ver todos (${items.length})':'▲ Mostrar menos';})()" style="background:none;border:none;color:var(--c-blue);font-size:11px;cursor:pointer;padding:3px 0">▼ Ver todos (${items.length})</button>`;
  }
  return html;
}

function _gpRenderAchievements(achievements) {
  const el = document.getElementById('gp-ra-achievements');
  if (!el) return;
  if (!achievements.length) { el.innerHTML = ''; return; }
  const earned  = achievements.filter(a => a.earned);
  const pending = achievements.filter(a => !a.earned);
  el.innerHTML =
    _gpAchGroup('Desbloqueados', 'var(--c-teal)', earned) +
    _gpAchGroup('Pendientes', 'var(--c-muted)', pending);
}

export function closeGamePanel() {
  document.getElementById('game-panel-overlay').classList.remove('open');
  document.getElementById('game-panel').classList.remove('open');
}

export async function gpSetStatus(status) {
  if (!_gpGameId) return;
  try {
    await apiPost('/api/set-play-status', { game_id: _gpGameId, status: status || null, source_path: _gpSrc() });
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
    const r = await apiPost('/api/toggle-favorite', { game_id: _gpGameId, source_path: _gpSrc() });
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
  // Bloque 9: M3U download links per tag
  const m3uEl = document.getElementById('gp-tags-m3u-links');
  if (m3uEl) {
    m3uEl.innerHTML = tags.map(t =>
      `<a href="/api/export-m3u?tag=${encodeURIComponent(t)}" download title="Descargar playlist RetroArch para tag '${_h(t)}'"
         style="font-size:10px;color:var(--c-teal);text-decoration:none;border:1px solid var(--c-teal);padding:1px 6px;border-radius:10px;opacity:.75" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.75">.m3u</a>`
    ).join('');
  }
}

export async function gpAddTag() {
  if (!_gpGameId) return;
  const input = document.getElementById('gp-tag-input');
  const tag = input.value.trim();
  if (!tag) return;
  try {
    const r = await apiPost('/api/tag', { game_id: _gpGameId, tag, action: 'add', source_path: _gpSrc() });
    _gpRenderTags(r.tags || []);
    input.value = '';
    _refreshTagFilter();
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

export async function gpRemoveTag(tag) {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/tag', { game_id: _gpGameId, tag, action: 'remove', source_path: _gpSrc() });
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
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--c-panel)">
      <span style="color:var(--c-muted)">${_h(s.timestamp)}<span style="color:var(--c-ghost);margin-left:4px">${_h(ext)}</span></span>
      <span style="color:var(--c-dim)">${sizeFmt}</span>
      <button onclick="restoreBackup(${JSON.stringify(bkPath)},${JSON.stringify(origSav)})" style="background:var(--rv-tint-ok-bg);border:1px solid var(--c-teal);color:var(--c-teal);padding:1px 8px;border-radius:3px;font-size:11px;cursor:pointer">Restaurar</button>
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
  const statusEl = document.getElementById('gp-notes-status');
  if (statusEl) statusEl.textContent = '…';
  clearTimeout(_gpNotesTimer);
  _gpNotesTimer = setTimeout(async () => {
    if (!_gpGameId) return;
    const val = document.getElementById('gp-notes')?.value ?? '';
    try {
      await apiPost('/api/set-metadata', { game_id: _gpGameId, notes: val, source_path: _gpSrc() });
      if (statusEl) {
        statusEl.textContent = '✓ guardado';
        statusEl.style.color = 'var(--c-teal)';
        setTimeout(() => { if (statusEl) { statusEl.textContent = ''; statusEl.style.color = 'var(--c-ghost)'; } }, 1500);
      }
    } catch (_) {
      if (statusEl) { statusEl.textContent = '⚠ error'; statusEl.style.color = 'var(--c-softred)'; }
    }
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
  const payload = { game_id: _gpGameId, source_path: _gpSrc() };
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
  if (previewEl) { previewEl.classList.remove('hidden'); previewEl.innerHTML = '<span style="color:var(--c-dim)">Consultando ScreenScraper…</span>'; }
  try {
    const r = await apiPost('/api/scrape-single', { game_id: _gpGameId, preview: true });
    if (!r.found) {
      if (previewEl) previewEl.innerHTML = `<span style="color:var(--c-red)">No encontrado: ${_h(r.error || 'sin resultados')}</span>`;
      return;
    }
    const rows = [
      ['Título', r.title], ['Año', r.year], ['Género', r.genre],
      ['Publisher', r.publisher], ['Developer', r.developer], ['Nota', r.rating],
    ].filter(([, v]) => v).map(([k, v]) => `<span style="color:var(--c-muted)">${k}:</span> <span style="color:var(--c-text)">${_h(v)}</span>`).join(' &nbsp;·&nbsp; ');
    if (previewEl) previewEl.innerHTML = `<div style="margin-bottom:8px;line-height:1.8">${rows}</div>
      <button onclick="gpApplyScrape()" style="background:var(--rv-tint-ok-bg);border:1px solid var(--c-teal);color:var(--c-teal);padding:3px 12px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Aplicar</button>
      <button onclick="document.getElementById('gp-scrape-preview').classList.add('hidden')" style="margin-left:6px;background:none;border:1px solid #444;color:var(--c-muted);padding:3px 10px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Cancelar</button>`;
  } catch(e) {
    if (previewEl) previewEl.innerHTML = `<span style="color:var(--c-red)">Error: ${_h(e.message)}</span>`;
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
      const clr = h.result === 'ok' ? 'var(--c-teal)' : 'var(--c-softred)';
      const dir = h.direction === 'up' ? '&#x2191;' : h.direction === 'down' ? '&#x2193;' : '&#x21C4;';
      return `<div style="display:flex;gap:6px;align-items:center;padding:3px 0;border-bottom:1px solid #1a1a2a">
        <span style="color:${clr};font-size:11px">${dir} ${_h(h.result || '')}</span>
        <span style="color:var(--c-dim);font-size:10px;flex:1">${_h(h.created_at?.substring(0, 16) || '')}</span>
        ${h.message ? `<span style="color:var(--c-hint);font-size:10px">${_h(h.message.substring(0, 40))}</span>` : ''}
      </div>`;
    }).join('');
  } catch(_) {}
}

// ── TV Mode ───────────────────────────────────────────────────────────────────
export async function enterTvMode() {
  // TV-UX-3: recuerda desde dónde se entró (el atajo 't' funciona desde cualquier
  // pestaña) — solo la primera vez, no si 't' se repite estando ya en TV.
  if (!_tvActive) {
    _tvSourceTab = document.querySelector('.tab.active')?.id?.replace('tab-', '') || 'games';
  }
  _tvActive = true;
  showTab('tv');
  try {
    await document.documentElement.requestFullscreen();
  } catch(_) {
    // TV-UX-5: antes fallaba en silencio — Modo TV sigue funcionando en ventana, avisamos y ya.
    showToast('No se pudo activar pantalla completa — Modo TV sigue funcionando en ventana', 'warn');
  }
  await _tvLoadPlatformBar();
  await loadTvGrid('', 0);
}

export function exitTvMode() {
  _tvActive = false;
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  showTab(_tvSourceTab);
}

// TV-UX-2: la barra de plataformas nunca se rellenaba — reutiliza el mismo
// endpoint que ya usan los filtros de Juegos y Scraper.
async function _tvLoadPlatformBar() {
  const bar = document.getElementById('tv-platform-bar');
  if (!bar) return;
  try {
    const d = await apiFetch('/api/games/filter-options');
    const platforms = d.platforms || [];
    bar.innerHTML = '';
    const _chip = (label, value) => {
      const btn = document.createElement('button');
      btn.textContent = label;
      btn.className = 'tv-plat-chip' + (value === _tvPlatform ? ' active' : '');
      btn.style.cssText = 'padding:4px 10px;background:transparent;border:1px solid var(--border);border-radius:12px;color:var(--fg-2);cursor:pointer;font-size:12px';
      btn.addEventListener('click', () => _tvSelectPlatform(value));
      bar.appendChild(btn);
    };
    _chip('Todas', '');
    platforms.forEach(p => _chip(p, p));
  } catch(_) {}
}

async function _tvSelectPlatform(platform) {
  const label = document.getElementById('tv-platform-label');
  if (label) label.textContent = platform || 'Toda la colección';
  document.querySelectorAll('#tv-platform-bar .tv-plat-chip').forEach(b => {
    b.classList.toggle('active', b.textContent === (platform || 'Todas'));
  });
  await loadTvGrid(platform, 0);
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
    _tvHasMore = games.length === _TV_LIMIT;
    _tvPlatform = platform;
    _tvOffset = offset;
    _renderTvGrid(games, offset > 0);
  } catch(e) {
    // TV-UX-4: antes se quedaba en blanco sin ningún aviso — modo a pantalla completa, hace falta un mensaje visible.
    console.error('loadTvGrid failed:', e);
    if (offset === 0) {
      const gridEl = document.getElementById('tv-grid');
      if (gridEl) gridEl.innerHTML = '<p style="color:var(--c-red);padding:20px;grid-column:1/-1">No se pudo cargar la colección — comprueba la conexión con el servidor.</p>';
    }
  }
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
  // Solo recentra el foco en una carga nueva — al añadir página, mantiene la posición actual.
  if (!append && _tvGames.length > 0) _tvMoveFocus(0);
}

// TV-UX-5: _tvCols no se recalculaba al redimensionar la ventana.
window.addEventListener('resize', () => {
  if (!_tvActive) return;
  const gridEl = document.getElementById('tv-grid');
  if (gridEl) _tvCols = Math.max(1, Math.round(gridEl.offsetWidth / 196));
});

export async function _tvMoveFocus(idx) {
  // TV-UX-1: la colección se cortaba en _TV_LIMIT juegos sin forma de cargar más.
  if (idx >= _tvGames.length) {
    if (_tvHasMore) {
      await loadTvGrid(_tvPlatform, _tvOffset + _TV_LIMIT);
    } else {
      _tvFlashEnd();
      idx = _tvGames.length - 1;
    }
  }
  document.querySelector('.tv-tile.tv-focused')?.classList.remove('tv-focused');
  _tvFocusIdx = Math.max(0, Math.min(idx, _tvGames.length - 1));
  const tile = document.querySelector(`.tv-tile[data-tv-idx="${_tvFocusIdx}"]`);
  if (tile) { tile.classList.add('tv-focused'); tile.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  if (_tvGames[_tvFocusIdx]) _updateTvInfoBar(_tvGames[_tvFocusIdx]);
}

const _TV_HELP_TEXT = '↑↓←→ navegar · Enter abrir · Esc salir';
function _tvFlashEnd() {
  const el = document.getElementById('tv-info-keys');
  if (!el) return;
  el.textContent = 'No hay más juegos por aquí';
  el.style.color = 'var(--c-red)';
  clearTimeout(_tvEndFlashTimer);
  _tvEndFlashTimer = setTimeout(() => { el.textContent = _TV_HELP_TEXT; el.style.color = 'var(--c-ghost)'; }, 1000);
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
      const score = it.score != null ? `<span style="color:var(--c-dim);font-size:10px">${Math.round(it.score * 100)}%</span>` : '';
      const reason = it.reason ? `<div style="font-size:10px;color:var(--c-dim);margin-top:2px">${_h(it.reason)}</div>` : '';
      const gameData = it.id ? ` onclick="apiFetch('/api/game?id=${it.id}').then(g=>{if(g.id)openGamePanel(g)}).catch(()=>{})"` : '';
      return `<div class="rec-card"${gameData}>
        <div style="font-size:12px;font-weight:600;color:var(--c-text)">${title} ${score}</div>
        <div style="font-size:11px;color:var(--c-muted)">${plat}</div>
        ${reason}
      </div>`;
    }).join('');
  } catch(_) {}
}

export function dismissRecommendations() {
  document.getElementById('rec-panel')?.classList.add('hidden');
}

// ── NEW-2: Screenshot gallery ─────────────────────────────────────────────────

export async function loadGameStatshots(gameId) {
  const wrap = document.getElementById('gp-stateshot-wrap');
  const grid = document.getElementById('gp-stateshot-grid');
  if (!wrap || !grid) return;
  wrap.classList.add('hidden');
  grid.innerHTML = '';
  if (!gameId) return;
  try {
    const data = await apiFetch('/api/stateshots?id=' + gameId);
    if (!data.slots?.length) return;
    grid.innerHTML = data.slots.map(s => {
      const src = 'data:image/png;base64,' + s.data;
      return `<div style="position:relative">
        <img src="${src}" alt="slot ${s.slot}"
          style="width:100%;border-radius:4px;border:1px solid var(--c-border);display:block;aspect-ratio:4/3;object-fit:cover">
        <span style="position:absolute;bottom:3px;right:5px;font-size:10px;color:#fff;text-shadow:0 1px 2px #000">&#x1F4BE;${s.slot}</span>
      </div>`;
    }).join('');
    if (grid.children.length) wrap.classList.remove('hidden');
  } catch (_) {}
}

export async function loadGameScreenshots(originalFilename) {
  const wrap = document.getElementById('gp-screenshots-wrap');
  const grid = document.getElementById('gp-screenshots-grid');
  if (!wrap || !grid) return;
  wrap.classList.add('hidden');
  grid.innerHTML = '';
  if (!originalFilename) return;
  const stem = originalFilename.replace(/\.[^.]+$/, ''); // strip extension
  try {
    const data = await apiFetch('/api/screenshots?stem=' + encodeURIComponent(stem));
    if (!data.screenshots?.length) return;
    grid.innerHTML = data.screenshots.slice(0, 6).map(s => {
      const url = '/api/screenshot-file?name=' + encodeURIComponent(s.filename);
      const date = s.taken_at ? new Date(s.taken_at * 1000).toLocaleDateString() : '';
      return `<a href="${url}" target="_blank" rel="noopener" title="${s.filename}&#10;${date}">
        <img src="${url}" loading="lazy" alt="${s.filename}"
          style="width:100%;border-radius:4px;border:1px solid var(--c-border);display:block;aspect-ratio:16/9;object-fit:cover"
          onerror="this.closest('a').remove()">
      </a>`;
    }).join('');
    if (grid.children.length) wrap.classList.remove('hidden');
  } catch (_) {}
}
