"use strict";

// ── Visibility helpers ─────────────────────────────────────────────────────
const _hide    = el => el && el.classList.add('hidden');
const _show    = el => el && el.classList.remove('hidden');
const _showIf  = (el, vis) => el && el.classList.toggle('hidden', !vis);

// ── Status text colour helper ──────────────────────────────────────────────
const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// Pagination state for Games tab
let gamesState = { offset: 0, limit: 100, total: 0, platform: '', status: '', root: null };
let _gamesViewMode = localStorage.getItem('games_view_mode') || 'list'; // 'list' | 'grid'
let platformsLoaded = false;

// ── TV Mode state (S36-1) ──────────────────────────────────────────────────────
let _tvActive = false;
let _tvGames = [];
let _tvFocusIdx = 0;
let _tvPlatform = '';
let _tvOffset = 0;
let _tvCols = 5;
const _TV_LIMIT = 120;

// ── Column visibility ─────────────────────────────────────────────────────────
const _COL_DEFAULTS = { region: true, match: true, size: false, sha1: false };
function _loadColPrefs() {
  try { return JSON.parse(localStorage.getItem('games_cols') || 'null') || _COL_DEFAULTS; }
  catch { return _COL_DEFAULTS; }
}
function _saveColPrefs(prefs) {
  localStorage.setItem('games_cols', JSON.stringify(prefs));
}
function applyColVisibility() {
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
function _initColPicker() {
  const prefs = _loadColPrefs();
  ['region','match','size','sha1'].forEach(key => {
    const cb = document.getElementById('gcol-check-' + key);
    if (cb) cb.checked = prefs[key];
  });
  applyColVisibility();
}
function toggleColPicker(event) {
  event.stopPropagation();
  const picker = document.getElementById('col-picker');
  if (!picker) return;
  picker.classList.toggle('hidden');
  if (!picker.classList.contains('hidden')) {
    // Close when clicking outside
    const close = (e) => { if (!picker.contains(e.target)) { picker.classList.add('hidden'); document.removeEventListener('click', close); }};
    setTimeout(() => document.addEventListener('click', close), 0);
  }
}
let _pollingTimer = null;
// Track result timestamps already shown, so toasts/banners fire only once per result
const _shownResultTs = {};

// ── Desktop notifications ──────────────────────────────────────────────────
function _requestNotifPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}
function _sendNotif(title, body) {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'granted') {
    new Notification(title, { body, icon: '' });
  }
}

// ── Device selector ───────────────────────────────────────────────────────────
let _activeDevice = 'pc';  // 'pc' | 'both' | 'anbernic'
var _devName = 'Consola Android';  // display name for the Android device — updated from config; var → window._devName for ES modules

/** Update every UI element that shows the device name. Called once after config loads. */
function _applyDeviceName(name) {
  _devName = name || 'Consola Android';
  // Simple text replacements
  const simple = {
    'dev-anbernic':        _devName,
    'ov-ab-column-title':  _devName,
    'ov-ab-path-label-text': _devName,
    'scan-ab-device-name': _devName,
    'scan-adb-device-name': _devName,
    'cable-mode-label':    _devName,
  };
  for (const [id, text] of Object.entries(simple)) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }
  // Direction labels include arrow
  const toEl   = document.getElementById('cable-dir-to-dev');
  const fromEl = document.getElementById('cable-dir-from-dev');
  if (toEl)   toEl.textContent   = `PC → ${_devName}`;
  if (fromEl) fromEl.textContent = `${_devName} → PC`;
  // Tooltip on ADB row
  const adbRow = document.getElementById('scan-adb-row');
  if (adbRow) adbRow.title = `Escanea la ${_devName} por USB sin sacar la SD card — requiere ADB configurado en Settings`;
}

function setDevice(d) {
  _activeDevice = d;
  ['pc','both','anbernic'].forEach(id => {
    const b = document.getElementById('dev-' + id);
    if (b) b.classList.toggle('active', id === d);
  });
  // Reload current active tab
  const activeTab = document.querySelector('.nav-item.active')?.id?.replace('nav-','');
  if (activeTab) {
    if (activeTab === 'games')      { loadFilterOptions(); loadGames(0); }
    if (activeTab === 'plan')       loadPlan();
    if (activeTab === 'duplicates') loadDuplicates();
    if (activeTab === 'assets')     loadAssets();
  }
}

function _deviceRoot() {
  if (_activeDevice === 'pc')       return document.getElementById('ov-pc-path')?.value.trim() || null;
  if (_activeDevice === 'anbernic') return document.getElementById('ov-ab-path')?.value.trim() || null;
  return null; // 'both' = sin filtro
}

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(name) {
  // Always close game panel on tab switch (prevents overlay covering the sidebar)
  closeGamePanel();
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById('tab-' + name);
  tab.classList.add('active', 'fading-in');
  tab.addEventListener('animationend', () => tab.classList.remove('fading-in'), { once: true });
  const navBtn = document.getElementById('nav-' + name);
  if (navBtn) navBtn.classList.add('active');
  else if (event?.currentTarget) event.currentTarget.classList.add('active');
  if (name === 'overview')   loadOverview();
  if (name === 'games')      { loadFilterOptions(); loadGames(0); _refreshTagFilter(); }
  if (name === 'plan')       loadPlan();
  if (name === 'duplicates') loadDuplicates();
  if (name === 'assets')     loadAssets();
  if (name === 'sync')       { loadSync(); loadManualBackups(); }
  if (name === 'cable')      loadCableSync();
  if (name === 'collection') loadCollection();
  if (name === 'scraper')    { loadScraperSummary(); loadScrapePlatforms(); _autoFillEsdeGamelistDir(); }
  if (name === 'settings')   { loadSettings(); loadCatalogStatus(); loadSsQuota(); loadAuthStatus(); loadLocalUrl(); loadSystemStatus(); loadAndroidSetupPanel(); loadAutostart(); }
  if (name === 'anbernic')   { loadAnbernicTab(); }
  if (name === 'formats')    { loadTools(); _initToolsContext(); }
  if (name === 'tools')      { loadTools(); _initToolsContext(); }
  if (name === 'inbox')      loadInbox();
  if (name === 'tv')         { /* enterTvMode() handles TV tab load */ }
}

// ── Guide toggle (update arrow icon) ─────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (!sidebar) return;
  const collapsed = sidebar.classList.toggle('collapsed');
  localStorage.setItem('sidebar_collapsed', collapsed ? '1' : '0');
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();  // S35-1: initialize theme from localStorage
  // Restore sidebar collapsed state
  if (localStorage.getItem('sidebar_collapsed') === '1')
    document.getElementById('app-sidebar')?.classList.add('collapsed');
  _initInboxBadge();  // 32-1: badge + interval polling
  const guide = document.getElementById('ov-guide');
  if (guide) {
    const updateArrow = () => {
      const arrow = document.getElementById('ov-guide-arrow');
      if (arrow) arrow.innerHTML = guide.open ? '&#x25BC;' : '&#x25B6;';
      localStorage.setItem('guide_closed', guide.open ? '0' : '1');
    };
    guide.addEventListener('toggle', updateArrow);
    // Restore saved state
    if (localStorage.getItem('guide_closed') === '1') guide.removeAttribute('open');
    updateArrow();
  }
});

// ── S28: Global search ────────────────────────────────────────────────────────
let _globalSearchTimer = null;
function onGlobalSearch(val) {
  clearTimeout(_globalSearchTimer);
  const results = document.getElementById('global-search-results');
  if (!val.trim()) { results.classList.add('hidden'); return; }
  _globalSearchTimer = setTimeout(async () => {
    try {
      const d = await apiFetch('/api/games?search=' + encodeURIComponent(val) + '&limit=8');
      if (!d.games || d.games.length === 0) { results.classList.add('hidden'); return; }
      results.classList.remove('hidden');
      results.innerHTML = d.games.map(g => {
        const title = _h(g.canonical_title || g.original_filename);
        const gj = JSON.stringify(g).replace(/</g,'\\u003c');
        return `<div class="sr-item" onclick="document.getElementById('global-search').value='';document.getElementById('global-search-results').classList.add('hidden');openGamePanel(${gj})">
          <img src="/api/asset-image?game_id=${g.id}" width="28" height="28" style="border-radius:3px;object-fit:cover" onerror="this.classList.add('hidden')">
          <div><div style="color:#d4d4d4">${title}</div><div style="font-size:11px;color:#555">${_h(g.platform||'')}</div></div>
        </div>`;
      }).join('');
    } catch(e) { results.classList.add('hidden'); }
  }, 200);
}
// Close global search results on outside click
document.addEventListener('click', e => {
  const wrap = document.getElementById('global-search-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const r = document.getElementById('global-search-results');
    if (r) r.classList.add('hidden');
  }
});

// ── S35-1: Theme (Dark/Light mode) ───────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('rv_theme') || 'dark';
  _applyTheme(saved);
}

function setTheme(theme) {
  // Validar que sea dark o light
  theme = (theme === 'light') ? 'light' : 'dark';
  _applyTheme(theme);
  // Toast visual
  const icon = theme === 'light' ? '☀️' : '🌙';
  const name = theme === 'light' ? 'Modo claro' : 'Modo oscuro';
  showToast(`${icon} ${name} activado`, 'ok');
}

function _applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : '');
  localStorage.setItem('rv_theme', theme);
  const darkRadio = document.getElementById('theme-dark');
  const lightRadio = document.getElementById('theme-light');
  if (darkRadio) darkRadio.checked = (theme === 'dark');
  if (lightRadio) lightRadio.checked = (theme === 'light');
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtSize(n) {
  const units = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

function badge(cls, text) {
  return `<span class="badge ${cls}">${text}</span>`;
}

const _PLAT_CLASS = {
  gba:'gba', 'game boy advance':'gba',
  snes:'snes', 'super nintendo':'snes',
  nes:'nes', 'nintendo':'nes',
  gb:'gb', 'game boy':'gb',
  gbc:'gbc', 'game boy color':'gbc',
  nds:'nds', 'nintendo ds':'nds',
  '3ds':'3ds', 'nintendo 3ds':'3ds',
  n64:'snes', 'nintendo 64':'snes',
  psx:'psx', 'playstation':'psx',
  ps2:'ps2', 'playstation 2':'ps2',
  psp:'psp', 'playstation portable':'psp',
  genesis:'genesis', 'mega drive':'md', md:'md',
  sms:'sms', 'master system':'sms',
  gg:'gg', 'game gear':'gg',
};
function _platBadge(plat) {
  if (!plat) return '<span class="plat plat-other">?</span>';
  const key = plat.toLowerCase();
  const cls = _PLAT_CLASS[key] || 'other';
  return `<span class="plat plat-${cls}">${_h(plat)}</span>`;
}

function _h(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// 27-4: Platform accent color (hex) — matches the CSS plat-* classes
const _PLAT_HEX = {
  gba: '#4ec9b0', snes: '#569cd6', nes: '#f44747', gb: '#dcdcaa',
  gbc: '#d7ba7d', nds: '#c586c0', '3ds': '#9cdcfe', n64: '#4ec9b0',
  psx: '#9cdcfe', ps2: '#569cd6', psp: '#79c0ff',
  genesis: '#ce9178', md: '#ce9178', sms: '#6a9955', gg: '#4ec9b0',
};
function _platHex(plat) {
  const cls = _PLAT_CLASS[(plat||'').toLowerCase()] || 'other';
  return _PLAT_HEX[cls] || '#555';
}

// 27-3: Game detail panel
let _gpGameId = null;
function _gpSetFavStar(isFav) {
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
    ['Región',     g.region   ? _h(g.region)   : '<span style="color:#444">—</span>'],
    ['Año',        g.year     ? _h(g.year)     : '<span style="color:#444">—</span>'],
    ['Género',     g.genre    ? _h(g.genre)    : '<span style="color:#444">—</span>'],
    ['Jugadores',  g.players  ? _h(g.players)  : '<span style="color:#444">—</span>'],
    ['Publisher',  g.publisher ? _h(g.publisher) : '<span style="color:#444">—</span>'],
    ['Developer',  g.developer ? _h(g.developer) : null],
    ['Nota',       g.rating   ? _h(g.rating)   : '<span style="color:#444">—</span>'],
    ['Tamaño',     fmtSize(g.size_bytes)],
    ['SHA1',       `<span style="color:#444;font-family:Consolas,monospace;font-size:11px">${(g.sha1||'').slice(0,10)}…</span>`],
  ];
  document.getElementById('gp-meta').innerHTML = rows.filter(([,v])=>v).map(([k,v])=>`<span class="gk">${k}</span><span class="gv">${v}</span>`).join('');
  const desc = document.getElementById('gp-desc');
  if (g.description) { desc.textContent = g.description; desc.classList.remove('hidden'); }
  else { desc.classList.add('hidden'); }
  const sel = document.getElementById('gp-status-sel');
  if (sel) sel.value = g.play_status || '';
  // S30: populate notes
  const notesEl = document.getElementById('gp-notes');
  if (notesEl) {
    notesEl.value = g.notes || '';
    _txtCls(notesEl, g.notes ? null : 'txt-dim');
  }
  // S30: populate metadata edit fields (only when data available)
  const t = g.canonical_title || g.ss_title || '';
  _gpSetEditField('gme-title',       t);
  _gpSetEditField('gme-year',        g.year || '');
  _gpSetEditField('gme-genre',       g.genre || '');
  _gpSetEditField('gme-publisher',   g.publisher || '');
  _gpSetEditField('gme-developer',   g.developer || '');
  _gpSetEditField('gme-rating',      g.rating || '');
  _gpSetEditField('gme-description', g.description || '');
}
function _gpSetEditField(id, val) {
  const el = document.getElementById(id);
  if (el && val !== undefined) el.value = val;
}
// S36-5: Playtime tracking
function gpShowPlaytimeInfo(g) {
  const wrap = document.getElementById('gp-playtime-wrap');
  if (!wrap) return;

  wrap.classList.remove('hidden');
  const infoEl = document.getElementById('gp-playtime-info');
  const hoursEl = document.getElementById('gp-playtime-hours');
  const minsEl = document.getElementById('gp-playtime-mins');

  if (!infoEl || !hoursEl || !minsEl) return;

  // Calculate time since last played
  const lastPlayed = g.last_played_at ? new Date(g.last_played_at) : null;
  if (lastPlayed) {
    const now = new Date();
    const diffMs = now - lastPlayed;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    let timeStr = '';
    if (diffDays >= 365) timeStr = `Hace ${Math.floor(diffDays / 365)} años`;
    else if (diffDays >= 30) timeStr = `Hace ${Math.floor(diffDays / 30)} meses`;
    else if (diffDays > 1) timeStr = `Hace ${diffDays} días`;
    else if (diffHours > 1) timeStr = `Hace ${diffHours} horas`;
    else timeStr = 'Hace menos de una hora';

    infoEl.innerHTML = timeStr || 'Nunca jugado';
  } else {
    infoEl.innerHTML = 'Nunca jugado';
  }

  // Clear input fields
  hoursEl.value = '';
  minsEl.value = '';
}

function gpLogPlaytime() {
  const hoursEl = document.getElementById('gp-playtime-hours');
  const minsEl = document.getElementById('gp-playtime-mins');
  if (!hoursEl || !minsEl) return;

  const hours = parseInt(hoursEl.value) || 0;
  const mins = parseInt(minsEl.value) || 0;

  if (hours === 0 && mins === 0) {
    alert('Ingresa al menos 1 minuto de juego');
    return;
  }

  if (mins > 59) {
    alert('Los minutos deben estar entre 0 y 59');
    return;
  }

  // For now, just show a confirmation (full implementation would save to backend)
  const totalMins = hours * 60 + mins;
  const msg = `Sesión registrada: ${hours}h ${mins}m (${totalMins} min)`;
  alert(msg);

  // Clear inputs
  hoursEl.value = '';
  minsEl.value = '';
}

function openGamePanel(g) {
  _gpGameId = g.id;
  // Cover
  const coverWrap = document.getElementById('gp-cover-wrap');
  const imgUrl = `/api/asset-image?game_id=${g.id}`;
  coverWrap.innerHTML = `<img src="${imgUrl}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'gp-no-art',innerHTML:'&#127918;'}))" alt="">`;
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
  // UI-4: reset RA section + saves info
  const _raSection = document.getElementById('gp-ra-section');
  if (_raSection) _raSection.classList.add('hidden');
  const _savesInfo = document.getElementById('gp-saves-info');
  if (_savesInfo) _savesInfo.classList.add('hidden');
  // UI-4: store source_path for open-folder
  document.getElementById('game-panel').dataset.sourcePath = g.source_path || '';
  // 34b-4: reset asset info
  const _assetInfo = document.getElementById('gp-asset-info');
  if (_assetInfo) _assetInfo.classList.add('hidden');
  // S30: reset meta editor state
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
      if (r.backups?.length) {
        loadSaveBackupsResult(r.backups, g.id);
        bkWrap.classList.remove('hidden');
      }
    }).catch(() => {});
  }
  // S33-4: Sync history
  loadGameSyncHistory(g.source_path);
  // S36-5: Playtime info
  gpShowPlaytimeInfo(g);
  // Launch button — show if retroarch configured
  const launchBtn = document.getElementById('gp-launch-btn');
  if (launchBtn) launchBtn.classList.remove('hidden');
  // Open
  document.getElementById('game-panel-overlay').classList.add('open');
  document.getElementById('game-panel').classList.add('open');
  // Load full game data async (meta, RA, saves)
  if (g.id) {
    apiFetch('/api/game?id=' + g.id).then(full => {
      if (full.id !== _gpGameId) return;
      _gpFillMeta(full);
      _gpGameId = full.id;
      // 34b-4: show asset path if available
      const _ai = document.getElementById('gp-asset-info');
      const _ap = document.getElementById('gp-asset-path');
      if (_ai && _ap && full.box_art_path) {
        _ap.textContent = full.box_art_path;
        _ai.classList.remove('hidden');
      }
      // UI-4: RetroAchievements
      const _raSection = document.getElementById('gp-ra-section');
      if (_raSection && full.ra_game_id) {
        document.getElementById('gp-ra-count').textContent =
          full.ra_achievements > 0
            ? `${full.ra_achievements} logros desbloqueables`
            : 'Juego en RA (sin logros)';
        const _pts = document.getElementById('gp-ra-points');
        if (_pts) _pts.textContent = full.ra_points > 0 ? `${full.ra_points} puntos` : '';
        const _rl = document.getElementById('gp-ra-link');
        if (_rl) _rl.href = `https://retroachievements.org/game/${full.ra_game_id}`;
        _raSection.classList.remove('hidden');
      }
      // UI-4: saves count badge
      const _savesInfo = document.getElementById('gp-saves-info');
      const _savesBadge = document.getElementById('gp-saves-badge');
      if (_savesInfo && _savesBadge && full.saves_count !== undefined) {
        if (full.saves_count > 0) {
          _savesBadge.innerHTML = `&#x1F4BE; ${full.saves_count} save${full.saves_count !== 1 ? 's' : ''} detectado${full.saves_count !== 1 ? 's' : ''}`;
          _savesInfo.classList.remove('hidden');
        }
      }
      // Update source_path for open-folder
      document.getElementById('game-panel').dataset.sourcePath = full.source_path || '';
    }).catch(() => {});
  }
}
function closeGamePanel() {
  document.getElementById('game-panel-overlay').classList.remove('open');
  document.getElementById('game-panel').classList.remove('open');
}
async function gpSetStatus(status) {
  if (!_gpGameId) return;
  try {
    await apiPost('/api/set-play-status', { game_id: _gpGameId, status: status || null, source_path: '' });
    if (document.getElementById('tab-games')?.classList.contains('active')) loadGames(gamesState.offset);
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
async function gpToggleFavorite() {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/toggle-favorite', { game_id: _gpGameId });
    _gpSetFavStar(r.is_favorite);
    // Update the row/card in the list if visible
    const rowStar = document.querySelector(`[data-fav-id="${_gpGameId}"]`);
    if (rowStar) { rowStar.classList.toggle('active', r.is_favorite); }
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
function _gpRenderTags(tags) {
  const el = document.getElementById('gp-tags-list');
  if (!el) return;
  el.innerHTML = tags.map(t =>
    `<span class="tag-chip">${_h(t)}<span class="tag-remove" onclick="gpRemoveTag('${_h(t)}')" title="Eliminar tag">&times;</span></span>`
  ).join('');
}
async function gpAddTag() {
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
async function gpRemoveTag(tag) {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/tag', { game_id: _gpGameId, tag, action: 'remove' });
    _gpRenderTags(r.tags || []);
    _refreshTagFilter();
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
async function gpLaunch() {
  if (!_gpGameId) return;
  try {
    const r = await apiPost('/api/launch', { game_id: _gpGameId });
    if (r.ok) { showToast('RetroArch lanzado', 'ok'); }
    else { showToast(r.error || 'Error al lanzar', 'err'); }
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
// UI-4: open containing folder in file explorer
async function gpOpenFolder() {
  const panel = document.getElementById('game-panel');
  const sp = panel?.dataset.sourcePath || '';
  if (!sp) { showToast('Ruta del juego no disponible', 'err'); return; }
  try {
    const r = await apiPost('/api/open-folder', { path: sp });
    if (!r.ok) showToast(r.error || 'No se pudo abrir la carpeta', 'err');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
// ── S29: Save backup helpers ───────────────────────────────────────────────────
function loadSaveBackupsResult(saves, gameId) {
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
async function restoreBackup(backupPath, originalSave) {
  if (!confirm('¿Restaurar este backup? El save actual será reemplazado.\nEl siguiente sync lo subirá a Dropbox y llegará a la consola.')) return;
  try {
    const r = await apiPost('/api/restore-backup', { backup_path: backupPath, original_save: originalSave });
    if (r.ok) { showToast('Save restaurado → ' + (r.restored_to || ''), 'ok'); }
    else { showToast(r.error || 'Error al restaurar', 'err'); }
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}
async function backupNow() {
  const btn = document.getElementById('btn-backup-now');
  if (btn) { btn.disabled = true; btn.textContent = 'Haciendo backup…'; }
  try {
    const r = await apiPost('/api/backup-now', {});
    if (r.status === 'started' || r.ok) { startPolling(); }
    else { showToast(r.error || 'Error al iniciar backup', 'err'); if (btn) { btn.disabled = false; btn.textContent = 'Hacer backup ahora'; } }
  } catch(e) { showToast('Error: ' + e.message, 'err'); if (btn) { btn.disabled = false; btn.textContent = 'Hacer backup ahora'; } }
}
async function loadManualBackups() {
  try {
    const r = await apiFetch('/api/manual-backups');
    const el = document.getElementById('manual-backups-list');
    if (!el) return;
    if (!r.zips?.length) { el.innerHTML = '<span style="color:#555">Sin backups ZIP guardados</span>'; return; }
    el.innerHTML = r.zips.map(z => {
      const sizeFmt = z.size > 1048576 ? (z.size / 1048576).toFixed(1) + ' MB' : (z.size / 1024).toFixed(1) + ' KB';
      return `<div style="padding:3px 0;border-bottom:1px solid #1a1a2a;display:flex;justify-content:space-between">
        <span style="color:#d4d4d4">${_h(z.filename)}</span>
        <span style="color:#555">${_h(z.timestamp)} &mdash; ${sizeFmt}</span>
      </div>`;
    }).join('');
  } catch(_) {}
}

// ── S30: Metadata editor + Notes ─────────────────────────────────────────────
let _gpNotesTimer = null;
function gpNotesInput() {
  clearTimeout(_gpNotesTimer);
  _gpNotesTimer = setTimeout(async () => {
    if (!_gpGameId) return;
    const val = document.getElementById('gp-notes')?.value ?? '';
    try { await apiPost('/api/set-metadata', { game_id: _gpGameId, notes: val }); }
    catch(_) {}
  }, 800);
}
function gpToggleMetaEdit() {
  const wrap = document.getElementById('gp-meta-edit-wrap');
  const btn  = document.getElementById('gp-meta-edit-toggle');
  if (!wrap) return;
  const open = !wrap.classList.contains('hidden');
  wrap.classList.toggle('hidden', open);
  if (btn) _txtCls(btn, open ? null : 'txt-ok');
}
async function gpSaveMetaFields() {
  if (!_gpGameId) return;
  const payload = { game_id: _gpGameId };
  const title = document.getElementById('gme-title')?.value.trim();
  if (title) payload.canonical_title = title;
  ['year','genre','publisher','developer','rating'].forEach(k => {
    const v = document.getElementById('gme-' + k)?.value.trim();
    if (v !== undefined) payload[k] = v;
  });
  const desc = document.getElementById('gme-description')?.value.trim();
  if (desc !== undefined) payload.description = desc;
  const res = document.getElementById('gme-result');
  try {
    await apiPost('/api/set-metadata', payload);
    if (res) { _txtCls(res, 'txt-ok'); res.textContent = '✓ Guardado'; setTimeout(() => { if (res) res.textContent = ''; }, 2000); }
    // Refresh display
    if (title) document.getElementById('gp-title').textContent = title;
    apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
  } catch(e) {
    if (res) { _txtCls(res, 'txt-err'); res.textContent = 'Error: ' + e.message; }
  }
}
async function gpScrapeSingle() {
  if (!_gpGameId) return;
  const previewEl = document.getElementById('gp-scrape-preview');
  const res = document.getElementById('gme-result');
  if (previewEl) { previewEl.classList.remove('hidden'); previewEl.innerHTML = '<span style="color:#555">Consultando ScreenScraper…</span>'; }
  try {
    const r = await apiPost('/api/scrape-single', { game_id: _gpGameId, preview: true });
    if (!r.found) {
      if (previewEl) previewEl.innerHTML = `<span style="color:#f44747">No encontrado: ${_h(r.error||'sin resultados')}</span>`;
      return;
    }
    const rows = [
      ['Título', r.title], ['Año', r.year], ['Género', r.genre],
      ['Publisher', r.publisher], ['Developer', r.developer], ['Nota', r.rating],
    ].filter(([,v]) => v).map(([k,v]) => `<span style="color:#888">${k}:</span> <span style="color:#d4d4d4">${_h(v)}</span>`).join(' &nbsp;·&nbsp; ');
    if (previewEl) previewEl.innerHTML = `<div style="margin-bottom:8px;line-height:1.8">${rows}</div>
      <button onclick="gpApplyScrape()" style="background:#1a3a2a;border:1px solid #4ec9b0;color:#4ec9b0;padding:3px 12px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Aplicar</button>
      <button onclick="document.getElementById('gp-scrape-preview').classList.add('hidden')" style="margin-left:6px;background:none;border:1px solid #444;color:#888;padding:3px 10px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Cancelar</button>`;
  } catch(e) {
    if (previewEl) previewEl.innerHTML = `<span style="color:#f44747">Error: ${_h(e.message)}</span>`;
  }
}
async function gpApplyScrape() {
  if (!_gpGameId) return;
  const previewEl = document.getElementById('gp-scrape-preview');
  const res = document.getElementById('gme-result');
  try {
    const r = await apiPost('/api/scrape-single', { game_id: _gpGameId, preview: false });
    if (r.applied) {
      if (previewEl) previewEl.classList.add('hidden');
      if (res) { _txtCls(res, 'txt-ok'); res.textContent = '✓ Metadatos actualizados'; setTimeout(() => { if(res) res.textContent = ''; }, 2500); }
      apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
    } else {
      if (res) { _txtCls(res, 'txt-err'); res.textContent = r.error || 'Error'; }
    }
  } catch(e) {
    if (res) { _txtCls(res, 'txt-err'); res.textContent = 'Error: ' + e.message; }
  }
}

async function gpCopyAssetToEsde() {
  const resultEl = document.getElementById('gp-asset-copy-result');
  if (resultEl) resultEl.textContent = 'Copiando…';
  try {
    const d = await apiFetch('/api/copy-assets-to-esde');
    if (d.error) { if (resultEl) resultEl.textContent = '✗ ' + d.error; return; }
    if (resultEl) resultEl.textContent = `✓ ${d.copied} copiadas`;
  } catch(e) { if (resultEl) resultEl.textContent = '✗ ' + e.message; }
}

async function toggleRowFavorite(gameId, btn) {
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
async function _refreshTagFilter() {
  try {
    const r = await apiFetch('/api/tags');
    const sel = document.getElementById('games-tag-filter');
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML = '<option value="">Todos los tags</option>' +
      (r.tags || []).map(t => `<option value="${_h(t)}"${t===cur?' selected':''}>${_h(t)}</option>`).join('');
  } catch(e) {}
}

// 24-2: relative time helper
function _relTime(isoStr) {
  if (!isoStr) return '';
  const ms = Date.now() - new Date(isoStr).getTime();
  const mins = Math.round(ms / 60000);
  if (mins < 2) return 'ahora mismo';
  if (mins < 60) return `hace ${mins} min`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  return `hace ${Math.round(hours / 24)}d`;
}

// 24-2: empty state widget
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


async function stopJob(name) {
  try {
    await apiPost('/api/stop-job', { job: name });
  } catch(_) {}
}

function openHtmlReport(customPath) {
  const path = customPath !== undefined ? customPath : (document.getElementById('report-path')?.value.trim() || '');
  const url = '/api/report/html' + (path ? '?path=' + encodeURIComponent(path) : '');
  window.open(url, '_blank');
}

async function openHtmlReportAndroid() {
  const abPath = document.getElementById('ov-ab-path')?.value.trim()
    || localStorage.getItem('anbernic_path') || '';
  if (!abPath) {
    alert('Configura la ruta de la consola Android en la sección Overview primero.');
    return;
  }
  openHtmlReport(abPath);
}

async function apiFetch(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ── Overview ─────────────────────────────────────────────────────────────────
// S36-2: Activity heatmap state and renderer
const _heatmapState = { cellMap: new Map() };

async function _renderActivityHeatmap() {
  const canvas = document.getElementById('ov-heatmap');
  if (!canvas) return;

  try {
    // Fetch all games (no limit, to get complete activity data)
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];

    // Calculate daily activity: group by date, count distinct games per day
    const today = new Date();
    const dayActivity = {}; // date string -> count

    games.forEach(g => {
      if (!g.last_played_at) return;
      const dateStr = g.last_played_at.split('T')[0];
      dayActivity[dateStr] = (dayActivity[dateStr] || 0) + 1;
    });

    // Find max count for color scaling
    const maxVal = Math.max(...Object.values(dayActivity), 0);

    // Draw on canvas
    const ctx = canvas.getContext('2d');
    const cellSize = 12;
    const cellGap = 2;
    const padding = 10;

    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Clear previous cell data
    _heatmapState.cellMap.clear();

    // Draw grid: 52 weeks (columns) × 7 days (rows)
    const weeks = 52;
    const days = 7;
    let cellX = padding;

    for (let week = 0; week < weeks; week++) {
      let cellY = padding;
      for (let day = 0; day < days; day++) {
        // Calculate date for this cell (from today going back)
        const daysAgo = (weeks - 1 - week) * 7 + (6 - day);
        const d = new Date(today);
        d.setDate(d.getDate() - daysAgo);
        const dateStr = d.toISOString().split('T')[0];

        // Color based on activity
        const count = dayActivity[dateStr] || 0;
        const intensity = maxVal > 0 ? count / maxVal : 0;
        const color = _getHeatmapColor(intensity);

        ctx.fillStyle = color;
        ctx.fillRect(cellX, cellY, cellSize, cellSize);
        ctx.strokeStyle = '#1a1a2e';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(cellX, cellY, cellSize, cellSize);

        // Store metadata for tooltip using week,day as key
        _heatmapState.cellMap.set(week + ',' + day, { x: cellX, y: cellY, dateStr, count, cellSize });

        cellY += cellSize + cellGap;
      }
      cellX += cellSize + cellGap;
    }

    // Add hover tooltip
    canvas.onmousemove = (e) => _handleHeatmapHover(e, canvas);
    canvas.onmouseleave = () => { canvas.title = ''; };
  } catch(err) {
    console.error('Heatmap error:', err);
  }
}

function _getHeatmapColor(intensity) {
  if (intensity === 0) return '#0d1117';
  if (intensity < 0.25) return '#0d3922';
  if (intensity < 0.5) return '#0d5c2c';
  if (intensity < 0.75) return '#1a7938';
  return '#3fb950';
}

function _handleHeatmapHover(e, canvas) {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  let found = false;
  for (const [key, cell] of _heatmapState.cellMap) {
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

// S36-3: Monthly time analysis chart
// S36-4: Game of the day suggestion
let _currentGameSuggestion = null;

async function _loadNewGameSuggestion() {
  try {
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];

    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    // Filter games not played in 6+ months
    const staleGames = games.filter(g => {
      if (!g.last_played_at) return true; // Never played
      const lastPlayed = new Date(g.last_played_at);
      return lastPlayed < sixMonthsAgo;
    });

    if (staleGames.length === 0) {
      const container = document.getElementById('ov-game-suggestion');
      if (container) {
        container.innerHTML = '<div style="padding:20px;color:#666;text-align:center;width:100%">¡Excelente! No tienes juegos olvidados. ¡Sigue jugando!</div>';
      }
      return;
    }

    // Pick a random game
    const suggestion = staleGames[Math.floor(Math.random() * staleGames.length)];
    _currentGameSuggestion = suggestion;

    // Display it
    const titleEl = document.getElementById('ov-game-suggestion-title');
    const metaEl = document.getElementById('ov-game-suggestion-meta');
    const imgEl = document.getElementById('ov-game-suggestion-img');

    if (titleEl) titleEl.textContent = suggestion.canonical_title || suggestion.original_filename;
    if (metaEl) {
      const lastPlay = suggestion.last_played_at
        ? _relTime(suggestion.last_played_at)
        : 'Nunca';
      metaEl.innerHTML = `${_platBadge(suggestion.platform || '')} · Última vez: ${lastPlay}`;
    }
    if (imgEl) {
      imgEl.src = `/api/asset-image?game_id=${suggestion.id}`;
      imgEl.onerror = () => { imgEl.classList.add('hidden'); };
    }
  } catch(err) {
    console.error('Game suggestion error:', err);
  }
}

async function _renderMonthlyChart() {
  const canvas = document.getElementById('ov-monthly-chart');
  if (!canvas) return;

  try {
    const resp = await apiFetch('/api/games?limit=10000&offset=0');
    const games = resp.games || [];

    // Build data: platform → month → set of games (to count distinct)
    const monthlyData = {}; // "2026-03" → { platform → Set<game_id> }
    const platforms = new Set();

    const now = new Date();
    const startDate = new Date(now);
    startDate.setMonth(startDate.getMonth() - 11); // Last 12 months

    games.forEach(g => {
      if (!g.last_played_at) return;
      const playDate = new Date(g.last_played_at);
      if (playDate < startDate) return;

      const monthKey = playDate.toISOString().substring(0, 7); // "YYYY-MM"
      if (!monthlyData[monthKey]) monthlyData[monthKey] = {};

      const plat = g.platform || 'Unknown';
      if (!monthlyData[monthKey][plat]) monthlyData[monthKey][plat] = new Set();
      monthlyData[monthKey][plat].add(g.id);
      platforms.add(plat);
    });

    // Get sorted months
    const months = Object.keys(monthlyData).sort();
    if (months.length === 0) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#555';
      ctx.font = '12px monospace';
      ctx.fillText('Sin datos. Escanea la biblioteca primero.', 20, canvas.height / 2);
      return;
    }

    // Draw chart
    const ctx = canvas.getContext('2d');
    const colors = ['#569cd6', '#4ec9b0', '#dcdcaa', '#ce9178', '#9cdcfe', '#c586c0', '#a7ec21', '#f44747'];
    const platArray = Array.from(platforms).sort();
    const barWidth = 8;
    const groupGap = 16;
    const padding = 40;
    const chartHeight = canvas.height - padding * 1.5;
    const chartWidth = canvas.width - padding * 2;

    // Background
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Max value for scaling
    let maxVal = 0;
    months.forEach(m => {
      platArray.forEach(p => {
        const count = monthlyData[m]?.[p]?.size || 0;
        maxVal = Math.max(maxVal, count);
      });
    });
    maxVal = Math.max(maxVal, 1);

    // Draw bars
    let x = padding;
    months.forEach((month, monthIdx) => {
      platArray.forEach((plat, platIdx) => {
        const count = monthlyData[month]?.[plat]?.size || 0;
        const barHeight = (count / maxVal) * chartHeight;

        ctx.fillStyle = colors[platIdx % colors.length];
        ctx.fillRect(x, canvas.height - padding + 20 - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      });
      x += groupGap;
    });

    // Draw axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(padding, padding);
    ctx.stroke();

    // Draw month labels (every 2 months)
    ctx.fillStyle = '#666';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    x = padding + (barWidth * platArray.length + 1) * 0.5 + groupGap * 0.5;
    months.forEach((month, idx) => {
      if (idx % 2 === 0) {
        const label = month.substring(5); // "MM"
        ctx.fillText(label, x, canvas.height - padding + 15);
      }
      x += (barWidth + 1) * platArray.length + groupGap;
    });

    // Draw legend
    ctx.textAlign = 'left';
    ctx.font = '11px monospace';
    let legX = padding;
    let legY = 20;
    platArray.forEach((plat, idx) => {
      ctx.fillStyle = colors[idx % colors.length];
      ctx.fillRect(legX, legY, 10, 10);
      ctx.fillStyle = '#d4d4d4';
      ctx.fillText(plat, legX + 15, legY + 9);
      legX += 120;
      if (legX > canvas.width - 100) {
        legX = padding;
        legY += 14;
      }
    });
  } catch(err) {
    console.error('Monthly chart error:', err);
  }
}

async function loadOverview() {
  try {
    const _t = Date.now();
    const cfg = await apiFetch('/api/config?t=' + _t);

    // Apply device name to all labels
    _applyDeviceName(cfg.device_name || 'Consola Android');

    // Populate path inputs (only if empty)
    const pcInput = document.getElementById('ov-pc-path');
    const abInput = document.getElementById('ov-ab-path');
    const pcPath  = pcInput?.value.trim() || cfg.library_root || '';
    const abStored = cfg.anbernic_root || localStorage.getItem('anbernic_path') || '';
    // If ADB scan was used, the stored android path acts as the Anbernic root
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
          // (wizard pre-fill handled by showWizard() with the path argument)
          // Render setup checklist
          const cl = d.setup_checklist || {};
          const chk = (ok, label, hint) =>
            '<div>' + (ok ? '<span style="color:#4ec9b0">&#x2611;</span>' : '<span style="color:#666">&#x2610;</span>') +
            ' <span style="color:' + (ok ? '#d4d4d4' : '#888') + '">' + label + '</span>' +
            (hint && !ok ? ' <span style="color:#555;font-size:11px">— ' + hint + '</span>' : '') + '</div>';
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
      // Auto-show wizard only on first page load if first_run (library not configured yet)
      if (d.first_run && !localStorage.getItem('wizard_dismissed')) {
        showWizard(pcPath || cfg.library_root || '', cfg.anbernic_root || '');
      }
    } catch(e) {
      if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
    }

    // Fetch Anbernic stats (if path configured)
    const abCardsEl  = document.getElementById('ov-ab-cards');
    const abDot      = document.getElementById('ov-ab-dot');
    const abEmptyMsg = document.getElementById('ov-ab-empty-msg');
    // D8-1: stale badge + scan button refs
    const abStaleBadge = document.getElementById('ov-ab-stale-badge');
    const abScanBtn    = document.getElementById('ov-ab-scan-btn');
    if (abPath && abCardsEl) {
      try {
        const ab = await apiFetch('/api/status?root=' + encodeURIComponent(abPath) + '&t=' + _t);
        const abMatchPct = ab.total_games > 0 ? Math.round(ab.matched_games / ab.total_games * 100) : 0;
        if (abDot) _txtCls(abDot, ab.total_games > 0 ? 'txt-ok' : 'txt-dim');
        // D8-1: show stale badge if scan is outdated
        if (abStaleBadge) abStaleBadge.classList.toggle('hidden', !(ab.stale));
        if (abScanBtn)    abScanBtn.classList.toggle('hidden', !((ab.stale || ab.total_games === 0)));
        // Find last scan for this Anbernic path
        const lastScans = ab.last_scans_by_root || {};
        const abLastScan = Object.entries(lastScans).find(([k]) => abPath && k.toLowerCase().startsWith(abPath.toLowerCase()))?.[1] || null;
        if (ab.total_games === 0) {
          if (abCardsEl) abCardsEl.innerHTML = `<p id="ov-ab-empty-msg" style="color:#dcdcaa;font-size:12px;padding:10px 0">&#x26A0; Ruta configurada pero sin datos escaneados. Activa el checkbox de <em>${_devName}</em> en <em>Gestión de biblioteca</em> y lanza un Scan.</p>`;
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
        // D8-7: show report available notice (only if PC status and not filtered by ab path)
      } catch(e) {
        if (abCardsEl) abCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
      }
    } else if (!abPath && abCardsEl) {
      abCardsEl.innerHTML = '<p style="color:#555;font-size:12px;padding:10px 0">Configura la ruta de la consola Android en el panel de abajo para ver sus estadísticas.</p>';
      if (abStaleBadge) abStaleBadge.classList.add('hidden');
      if (abScanBtn)    abScanBtn.classList.add('hidden');
    }

    // Recently played (27-1 hero card + 28-2 horizontal scroll)
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
        // 27-1: hero card for last played
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
        // 28-2: Netflix-style horizontal scroll (up to 6 games)
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
        // Simple list below
        if (recentEl) recentEl.innerHTML = games.map(g => {
          const title = g.canonical_title || g.original_filename;
          return `<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1e1e2e;font-size:12px;cursor:pointer" onclick="openGamePanel(${JSON.stringify(g).replace(/</g,'\\u003c')})">
            <span>${_platBadge(g.platform)} <span style="color:#d4d4d4">${_h(title)}</span></span>
            <span style="color:#555">${_relTime(g.last_played_at)}</span>
          </div>`;
        }).join('');
      } else {
        if (heroEl) heroEl.classList.add('hidden');
        if (contSection) contSection.classList.add('hidden');
        if (recentEl) recentEl.innerHTML = '<p style="color:#555;font-size:12px">Juega un rato y vuelve aquí.</p>';
      }
    } catch(_) {
      if (heroEl) heroEl.classList.add('hidden');
      if (contSection) contSection.classList.add('hidden');
      if (recentEl) recentEl.innerHTML = '<p style="color:#555;font-size:12px">—</p>';
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
              <span style="width:110px;color:#888;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(p.platform)}">${_h(p.platform)}</span>
              <div style="flex:1;background:#1e1e2e;border-radius:2px;height:14px">
                <div style="width:${pct}%;background:#569cd6;height:14px;border-radius:2px;transition:width 0.3s"></div>
              </div>
              <span style="width:40px;color:#d4d4d4;font-size:11px">${p.count}</span>
            </div>`;
          }).join('');
        } else {
          chartEl.innerHTML = '<p style="color:#555;font-size:12px">Sin datos. Escanea la biblioteca primero.</p>';
        }
      } catch(_) { /* silent */ }
    }

    // D8-7: show report available notice based on PC status
    try {
      const pcStatusForReport = await apiFetch('/api/status' + (pcPath ? '?root=' + encodeURIComponent(pcPath) + '&t=' + (_t+1) : ('?t=' + (_t+1))));
      const reportNoticeEl = document.getElementById('ov-report-notice');
      if (reportNoticeEl) {
        if (pcStatusForReport.last_report_at && pcStatusForReport.last_report_mins_ago !== null) {
          const mins = pcStatusForReport.last_report_mins_ago;
          const timeStr = mins < 60 ? ('hace ' + mins + ' min') : ('hace ' + Math.round(mins/60) + 'h');
          reportNoticeEl.classList.remove('hidden');
          reportNoticeEl.innerHTML = '<span style="color:#dcdcaa;font-size:12px">&#x1F4CA; Informe disponible — generado ' + timeStr + '</span> '
            + '<a href="/api/report/html' + (pcPath ? '?path=' + encodeURIComponent(pcPath) : '') + '" target="_blank" class="btn" style="padding:2px 8px;font-size:11px;margin-left:8px">Ver informe</a>';
        } else {
          reportNoticeEl.classList.add('hidden');
        }
      }
    } catch(_) {}

    // S35-2: Render platform grid
    if (pcPath) {
      try {
        _renderPlatformGrid(pcPath);
      } catch(_) { /* silent */ }
    }

    // S36-2: Render activity heatmap
    try {
      _renderActivityHeatmap();
    } catch(e) {
      console.error('Heatmap error:', e);
    }

    // S36-3: Render monthly analysis chart
    try {
      _renderMonthlyChart();
    } catch(e) {
      console.error('Monthly chart error:', e);
    }

    // S36-4: Load game suggestion
    try {
      _loadNewGameSuggestion();
    } catch(e) {
      console.error('Game suggestion error:', e);
    }

  } catch(e) {
    const pcCardsEl = document.getElementById('ov-pc-cards');
    if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function card(label, value, sub, onclick, colorCls, actions) {
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

// ── S35-2: Platform Grid ───────────────────────────────────────────────────────
// SVG logos for platforms
const _platformLogos = {
  'Atari 2600': '<svg viewBox="0 0 40 40"><rect fill="#d32f2f" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="20" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">A2K</text></svg>',
  'NES': '<svg viewBox="0 0 40 40"><rect fill="#4a90e2" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="18" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">NES</text></svg>',
  'SNES': '<svg viewBox="0 0 40 40"><rect fill="#9c27b0" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="16" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">SNES</text></svg>',
  'Game Boy': '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#a0a0a0" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#222" text-anchor="middle" dominant-baseline="middle">GB</text></svg>',
  'Game Boy Color': '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#90ee90" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#222" text-anchor="middle" dominant-baseline="middle">GBC</text></svg>',
  'Game Boy Advance': '<svg viewBox="0 0 40 40"><rect fill="#8b7355" width="40" height="40" rx="2"/><rect fill="#6600cc" x="4" y="4" width="32" height="32" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">GBA</text></svg>',
  'Nintendo 64': '<svg viewBox="0 0 40 40"><rect fill="#c41e3a" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">N64</text></svg>',
  'Nintendo DS': '<svg viewBox="0 0 40 40"><rect fill="#e5a35f" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">NDS</text></svg>',
  'Nintendo 3DS': '<svg viewBox="0 0 40 40"><rect fill="#ffc000" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">3DS</text></svg>',
  'Sega Genesis': '<svg viewBox="0 0 40 40"><rect fill="#0066cc" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">MD</text></svg>',
  'Sega Master System': '<svg viewBox="0 0 40 40"><rect fill="#333" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">SMS</text></svg>',
  'Game Gear': '<svg viewBox="0 0 40 40"><rect fill="#333" width="40" height="40" rx="2"/><rect fill="#ffcc00" x="5" y="5" width="30" height="30" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">GG</text></svg>',
  'PlayStation': '<svg viewBox="0 0 40 40"><rect fill="#003087" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PS1</text></svg>',
  'PlayStation 2': '<svg viewBox="0 0 40 40"><rect fill="#111" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PS2</text></svg>',
  'PlayStation Portable': '<svg viewBox="0 0 40 40"><rect fill="#003087" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">PSP</text></svg>',
  'Dreamcast': '<svg viewBox="0 0 40 40"><rect fill="#f4c300" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="12" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">DC</text></svg>',
  'Arcade': '<svg viewBox="0 0 40 40"><rect fill="#ff6600" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">ARC</text></svg>',
  'MAME': '<svg viewBox="0 0 40 40"><rect fill="#ff6600" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">MAME</text></svg>',
};

function _getPlatformLogo(platformName) {
  if (!platformName) return null;
  return _platformLogos[platformName] ||
    `<svg viewBox="0 0 40 40"><rect fill="#666" width="40" height="40" rx="2"/><text x="50%" y="50%" font-size="10" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle">${platformName.slice(0,3).toUpperCase()}</text></svg>`;
}

async function _renderPlatformGrid(pcPath) {
  const gridEl = document.getElementById('ov-platform-grid');
  if (!gridEl) return;

  try {
    const ps = await apiFetch('/api/platform-stats?root=' + encodeURIComponent(pcPath));
    if (!ps.platforms || ps.platforms.length === 0) {
      gridEl.innerHTML = '<p style="color:#555;font-size:12px">Sin datos. Escanea la biblioteca primero.</p>';
      return;
    }

    // Find max count for relative sizing
    const maxCount = Math.max(...ps.platforms.map(p => p.count));

    // Render up to 12 platforms
    gridEl.innerHTML = ps.platforms.slice(0, 12).map((p, idx) => {
      const logo = _getPlatformLogo(p.platform);
      const size = Math.max(40, Math.round(p.count / maxCount * 100));
      const platName = _h(p.platform || '?');
      const platEscaped = (p.platform || '').replace(/'/g, "\\'");
      return `<div class="platform-tile" data-idx="${idx}"
        style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:12px;background:#1e1e2e;border:1px solid #2a2a3a;border-radius:6px;cursor:pointer;transition:all 0.2s;text-align:center"
        onmouseover="this.style.background='#252535';this.style.borderColor='#3a3a5c'"
        onmouseout="this.style.background='#1e1e2e';this.style.borderColor='#2a2a3a'">
        <div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center">${logo}</div>
        <div style="font-size:11px;font-weight:600;color:#d4d4d4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%" title="${platName}">${platName}</div>
        <div style="font-size:10px;color:#888">${p.count} game${p.count !== 1 ? 's' : ''}</div>
      </div>`;
    }).join('');

    // Add click handlers
    ps.platforms.slice(0, 12).forEach((p, idx) => {
      const tile = gridEl.querySelector(`[data-idx="${idx}"]`);
      if (tile) {
        tile.addEventListener('click', () => {
          gamesState.root = pcPath;
          gamesState.status = '';
          gamesState.platform = p.platform || '';
          gamesState.filetype = '';
          platformsLoaded = false;
          showTab('games');
        });
      }
    });
  } catch(_) {
    gridEl.innerHTML = '<p style="color:#555;font-size:12px">Error al cargar plataformas.</p>';
  }
}

// ── D8-P1: Setup Wizard ───────────────────────────────────────────────────────
let _wizardPollingTimer = null;

function showWizard(prefillPcPath, prefillAndroidPath) {
  const modal = document.getElementById('wizard-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  document.getElementById('wizard-page-1').classList.remove('hidden');
  document.getElementById('wizard-page-2').classList.add('hidden');
  document.getElementById('wizard-page-3').classList.add('hidden');
  // Pre-fill paths from config if available
  const pcInp = document.getElementById('wiz-library-root');
  if (pcInp && !pcInp.value && prefillPcPath) pcInp.value = prefillPcPath;
  const andInp = document.getElementById('wiz-android-root');
  if (andInp && !andInp.value && prefillAndroidPath) andInp.value = prefillAndroidPath;
}

function closeWizard() {
  const modal = document.getElementById('wizard-modal');
  if (modal) modal.classList.add('hidden');
  localStorage.setItem('wizard_dismissed', '1');
  if (_wizardPollingTimer) { clearInterval(_wizardPollingTimer); _wizardPollingTimer = null; }
}

async function wizardAutoDetect() {
  const btn = document.getElementById('wiz-detect-btn');
  const msg = document.getElementById('wiz-detect-msg');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando\u2026'; }
  if (msg) { msg.classList.add('hidden'); }
  try {
    const d = await apiFetch('/api/wizard-detect');
    const lines = [];

    // Pre-fill PC library root if field is empty
    const pcInp = document.getElementById('wiz-library-root');
    if (pcInp && !pcInp.value && d.library_root_suggestion) {
      pcInp.value = d.library_root_suggestion;
      lines.push('\u2705 Carpeta PC detectada: <strong>' + d.library_root_suggestion + '</strong>');
    } else if (!d.library_root_suggestion) {
      lines.push('\u26A0\uFE0F No se encontr\u00F3 RetroArch en rutas habituales. Introduce la carpeta manualmente.');
    }

    // Pre-fill Android root if a device is connected
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

async function startSetup() {
  const libRoot    = (document.getElementById('wiz-library-root')?.value || '').trim();
  const androidRoot = (document.getElementById('wiz-android-root')?.value || '').trim();
  if (!libRoot) { alert('Introduce la carpeta de biblioteca (PC) primero.'); return; }
  const cleanJunk   = document.getElementById('wiz-clean-junk')?.checked || false;
  const extractZips = document.getElementById('wiz-extract-zips')?.checked !== false;
  const doMatch     = document.getElementById('wiz-match')?.checked !== false;

  // Switch to page 2
  document.getElementById('wizard-page-1').classList.add('hidden');
  document.getElementById('wizard-page-2').classList.remove('hidden');
  _renderWizSteps(null);

  try {
    await apiPost('/api/setup-run', {
      library_root:  libRoot,
      android_root:  androidRoot,
      clean_junk:    cleanJunk,
      extract_zips:  extractZips,
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

function _renderWizSteps(progress) {
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
    if (n < current) { icon = '&#x2705;'; color = '#4ec9b0'; }
    else if (n === current) { icon = '&#x23F3;'; color = '#c9bcf5'; }
    else { icon = '&nbsp;&nbsp;&nbsp;'; color = '#444'; }
    return '<div style="font-size:13px;color:' + color + ';margin-bottom:6px">' + icon + ' <span style="color:#777;font-size:11px">Paso ' + n + '/5</span>  ' + s + '</div>';
  }).join('');
  // Progress bar
  const bar = document.getElementById('wiz-prog-bar');
  if (bar) bar.style.width = pct + '%';
  const fileEl = document.getElementById('wiz-prog-file');
  if (fileEl) fileEl.textContent = progress ? (progress.current_file || '') : '';
}

async function _pollSetupProgress() {
  try {
    const s = await apiFetch('/api/setup-status');
    if (s.setup_progress) _renderWizSteps(s.setup_progress);
    if (!s.setup_running && s.setup_result) {
      if (_wizardPollingTimer) { clearInterval(_wizardPollingTimer); _wizardPollingTimer = null; }
      _showSetupResult(s.setup_result);
    }
  } catch(_) {}
}

function _showSetupResult(r) {
  document.getElementById('wizard-page-2').classList.add('hidden');
  document.getElementById('wizard-page-3').classList.remove('hidden');
  const el = document.getElementById('wiz-result-stats');
  if (!el) return;
  if (r.error) {
    el.innerHTML = '<span style="color:#f44747">Error: ' + _h(r.error) + '</span><span style="color:#888;font-size:12px;margin-left:8px">— Recarga la página o comprueba que hay ROMs escaneados.</span>';
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
  // Reload overview to refresh counts
  loadOverview();
}

function wizardGoToOrganize() {
  closeWizard();
  showTab('plan');
}

// Navigate to Games tab pre-filtered by device root, match status, and filetype
function goToGames(root, status, filetype, platform) {
  gamesState.root     = root   || null;
  gamesState.status   = status || '';
  gamesState.platform = platform || '';
  gamesState.filetype = filetype || '';
  platformsLoaded = false;
  const statusSel = document.getElementById('games-matched');
  if (statusSel) statusSel.value = status || '';
  const ftSel = document.getElementById('games-filetype');
  if (ftSel && filetype !== undefined) ftSel.value = filetype || 'all';
  showTab('games');
}


// ── Games ────────────────────────────────────────────────────────────────────
let _gamesSearchTimer = null;
function onGamesSearchChange() {
  clearTimeout(_gamesSearchTimer);
  _gamesSearchTimer = setTimeout(() => { loadGames(0); }, 300);
}
function onGamesFilterChange() {
  gamesState.platform = document.getElementById('games-platform').value;
  gamesState.status   = document.getElementById('games-matched').value;
  gamesState.filetype = document.getElementById('games-filetype').value;
  gamesState.genre    = document.getElementById('games-genre')?.value || '';
  gamesState.year     = document.getElementById('games-year')?.value || '';
  gamesState.sortBy   = document.getElementById('games-sort-by')?.value || '';
  loadGames(0);
}
let _filterOptionsLoaded = false;
async function loadFilterOptions() {
  if (_filterOptionsLoaded) return;
  try {
    const r = await apiFetch('/api/games/filter-options');
    _filterOptionsLoaded = true;
    const _populate = (id, items, emptyLabel) => {
      const sel = document.getElementById(id);
      if (!sel) return;
      const cur = sel.value;
      while (sel.options.length > 1) sel.remove(1);
      items.forEach(v => { const o = document.createElement('option'); o.value = v; o.text = v; sel.add(o); });
      if (cur) sel.value = cur;
    };
    _populate('games-genre', r.genres || [], 'Género');
    _populate('games-year',  r.years  || [], 'Año');
  } catch (_) {}
}
function toggleFavoritesFilter() {
  const btn = document.getElementById('btn-filter-favorites');
  if (!btn) return;
  gamesState.favorite = !gamesState.favorite;
  _txtCls(btn, gamesState.favorite ? 'txt-fav' : 'txt-muted');
  btn.style.borderColor = gamesState.favorite ? '#f9c74f' : '#444';
  loadGames(0);
}

async function loadGames(offset) {
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
  if (_gamesRoot)          params.set('root',      _gamesRoot);

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
        empty.innerHTML = _emptyState('🎮', 'Sin juegos aún', 'Escanea tu biblioteca y ejecuta "Match catálogos" para ver tus juegos aquí.', 'Ir a Inicio', () => showTab('overview'));
      } else {
        empty.innerHTML = _emptyState('🔎', 'Sin resultados', 'Prueba con otros filtros o borra la búsqueda.');
      }
      empty.classList.remove('hidden');
    }
    else {
      empty.classList.add('hidden');
      const _srcPath = gamesState.root || _deviceRoot() || '';
      tbody.innerHTML = rows.map(g => {
        const thumb = g.id ? `<img src="/api/asset-image?game_id=${g.id}" style="width:32px;height:32px;object-fit:contain;border-radius:2px;background:#0a0a0a" onerror="this.style.display=\'none\'">` : '';
        const statusVal = g.play_status || '';
        const statusSel = `<select style="background:#1e1e2e;border:1px solid #333;color:#d4d4d4;padding:2px 5px;border-radius:3px;font:inherit;font-size:11px;cursor:pointer" onchange="setPlayStatus(${g.id}, '${_srcPath.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}', this.value)">
          <option value=""${statusVal===''?' selected':''}>—</option>
          <option value="playing"${statusVal==='playing'?' selected':''}>&#x1F3AE; Jugando</option>
          <option value="completed"${statusVal==='completed'?' selected':''}>&#x2705; Completado</option>
          <option value="100pct"${statusVal==='100pct'?' selected':''}>&#x1F4AF; Al 100%</option>
          <option value="abandoned"${statusVal==='abandoned'?' selected':''}>&#x23F8; Abandonado</option>
        </select>`;
        const accentColor = _platHex(g.platform);
        const favActive = g.is_favorite ? ' active' : '';
        return `<tr style="cursor:pointer;border-left:2px solid ${accentColor}20" onclick="openGamePanel(${JSON.stringify(g).replace(/</g,'\\u003c').replace(/>/g,'\\u003e')})">
          <td style="padding:4px 6px;text-align:center" onclick="event.stopPropagation()"><button class="fav-star${favActive}" data-fav-id="${g.id}" onclick="toggleRowFavorite(${g.id},this)" title="${g.is_favorite?'Quitar favorito':'Marcar favorito'}">&#x2605;</button></td>
          <td style="padding:4px 6px">${thumb}</td>
          <td>${_platBadge(g.platform)}</td>
          <td title="${_h(g.canonical_title||'')}">${g.canonical_title || '<span style="color:#444">—</span>'}</td>
          <td class="mono" title="${_h(g.original_filename)}" style="color:#9cdcfe;font-size:12px">${_h(g.original_filename)}</td>
          <td style="white-space:nowrap" onclick="event.stopPropagation()">${statusSel}</td>
          <td><span style="font-size:11px;color:#888">${_h(g.region || '')}</span></td>
          <td>${g.match_confidence ? badge(g.match_confidence, g.match_confidence) : badge('none','—')}</td>
          <td style="color:#666;font-size:12px">${fmtSize(g.size_bytes)}</td>
          <td class="mono" style="color:#444;font-size:11px">${(g.sha1||'').slice(0,10)}…</td>
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

async function setPlayStatus(gameId, sourcePath, status) {
  try {
    await apiPost('/api/set-play-status', { game_id: gameId, status: status || null, source_path: sourcePath });
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

function renderPagination() {
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
      ${[50,100,200,500].map(n => `<option value="${n}"${n===limit?' selected':''}>${n} por página</option>`).join('')}
    </select>`;
}

// ── Games view toggle ────────────────────────────────────────────────────────
function setGamesView(mode) {
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
  // Re-render current data in the new view mode
  loadGames(gamesState.offset);
}

function _renderGamesGrid(games) {
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
    return `<div class="game-card" style="border-top:2px solid ${accentGc}40" onclick="openGamePanel(${JSON.stringify(g).replace(/</g,'\\u003c').replace(/>/g,'\\u003e')})">
      <div class="gc-thumb">${thumb}${statusBadge}${favBadge}</div>
      <div class="gc-body">
        <div class="gc-title" title="${title}">${title}</div>
        <div class="gc-meta">${_platBadge(g.platform)}</div>
      </div>
    </div>`;
  }).join('');
}

// ── S33-3: Save comparator ────────────────────────────────────────────────────
async function loadSaveComparison() {
  const el = document.getElementById('save-comparison-content');
  if (!el) return;
  el.innerHTML = '<p style="color:#555;font-size:12px">Cargando…</p>';
  try {
    const d = await apiFetch('/api/save-comparison');
    const saves = d.saves || [];
    if (!saves.length) {
      el.innerHTML = '<p style="color:#555;font-size:12px">No hay saves en la biblioteca.</p>';
      return;
    }
    const _fmtDate = s => s ? s.replace('T', ' ').substring(0, 16) : '<span style="color:#444">—</span>';
    const _syncBadge = s => {
      if (!s.last_sync_at) return '<span style="color:#666;font-size:10px">Nunca</span>';
      const cls = s.last_result === 'ok' ? '#4ec9b0' : '#e06c75';
      return `<span style="color:${cls};font-size:10px">${_fmtDate(s.last_sync_at)}</span>`;
    };
    let html = `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead><tr style="color:#555;border-bottom:1px solid #2a2a3a">
        <th style="text-align:left;padding:4px 6px">Plataforma</th>
        <th style="text-align:left;padding:4px 6px">Título</th>
        <th style="text-align:left;padding:4px 6px">Mod. local</th>
        <th style="text-align:left;padding:4px 6px">Último sync</th>
        <th style="text-align:left;padding:4px 6px">Dirección</th>
      </tr></thead><tbody>`;
    saves.forEach(s => {
      const stale = s.local_mtime && s.last_sync_at && s.local_mtime > s.last_sync_at;
      const rowStyle = stale ? 'background:#1a1a0a' : '';
      html += `<tr style="${rowStyle};border-bottom:1px solid #1a1a2a">
        <td style="padding:4px 6px;color:#888">${_h(s.platform)}</td>
        <td style="padding:4px 6px;color:#d4d4d4">${_h(s.title)}</td>
        <td style="padding:4px 6px;color:${stale ? '#f9c74f' : '#888'}">${_fmtDate(s.local_mtime)}</td>
        <td style="padding:4px 6px">${_syncBadge(s)}</td>
        <td style="padding:4px 6px;color:#555;font-size:10px">${_h(s.last_direction || '—')}</td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    if (saves.some(s => s.local_mtime && s.last_sync_at && s.local_mtime > s.last_sync_at)) {
      html = `<div style="font-size:11px;color:#f9c74f;margin-bottom:8px">&#x26A0; Filas en amarillo: save modificado después del último sync.</div>` + html;
    }
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

// ── S33-4: Game sync history ──────────────────────────────────────────────────
async function loadGameSyncHistory(sourcePath) {
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
        <span style="color:#555;font-size:10px;flex:1">${_h(h.created_at?.substring(0,16) || '')}</span>
        ${h.message ? `<span style="color:#666;font-size:10px">${_h(h.message.substring(0,40))}</span>` : ''}
      </div>`;
    }).join('');
  } catch(_) {}
}

async function doLibraryDiff() {
  const parityEl = document.getElementById('lib-diff-parity');
  const resultEl = document.getElementById('lib-diff-result');
  if (parityEl) parityEl.textContent = 'Comparando…';
  if (resultEl) resultEl.innerHTML   = '';
  try {
    const d = await apiFetch('/api/library-diff');
    const { only_pc, only_android, in_both, total_pc, total_android, parity } = d;

    if (parityEl) {
      if (parity) {
        parityEl.innerHTML = '<span style="color:#a6e3a1">✓ Bibliotecas sincronizadas</span>';
      } else {
        const diff = only_pc.length + only_android.length;
        parityEl.innerHTML = '<span style="color:#f38ba8">⚠ ' + diff + ' ROM' + (diff !== 1 ? 's' : '') + ' difieren</span>';
      }
    }

    if (!resultEl) return;
    const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const makeTable = (rows, loc) => {
      if (!rows.length) return '<p style="color:#888;font-size:13px;margin:6px 0 0">Ninguno.</p>';
      let t = '<table class="report-table" style="width:100%"><thead><tr><th>Plataforma</th><th>Título</th></tr></thead><tbody>';
      for (const r of rows) t += '<tr><td>' + esc(r.platform) + '</td><td>' + esc(r.title) + '</td></tr>';
      return t + '</tbody></table>';
    };

    let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:4px">';

    html += '<div><h4 style="margin:0 0 6px;color:#f38ba8">Solo en PC (' + only_pc.length + ' / ' + total_pc + ')</h4>' + makeTable(only_pc) + '</div>';
    html += '<div><h4 style="margin:0 0 6px;color:#89b4fa">Solo en Android (' + only_android.length + ' / ' + total_android + ')</h4>' + makeTable(only_android) + '</div>';
    html += '</div>';
    html += '<details style="margin-top:12px"><summary style="cursor:pointer;color:#888;font-size:13px">En ambos (' + in_both.length + ')</summary>' + makeTable(in_both) + '</details>';

    resultEl.innerHTML = html;
  } catch (e) {
    if (parityEl) parityEl.textContent = '';
    if (resultEl) resultEl.innerHTML = '<p style="color:#f38ba8">Error: ' + e.message + '</p>';
  }
}

async function doSync(dryRun) {
  const btnDry   = document.getElementById('btn-sync-dry');
  const btnApply = document.getElementById('btn-sync-apply');
  const resultEl = document.getElementById('job-result-sync');
  if (btnDry)   btnDry.disabled   = true;
  if (btnApply) btnApply.disabled = true;
  resultEl.className = 'job-result';
  if (!dryRun) _requestNotifPermission();
  try {
    const d = await apiPost('/api/sync', { dry_run: dryRun });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un sync en curso…';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    if (btnDry)   btnDry.disabled   = false;
    if (btnApply) btnApply.disabled = false;
  }
}

function _renderSyncResult(result) {
  const resultEl   = document.getElementById('job-result-sync');
  const decisionsEl = document.getElementById('sync-decisions');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    const verb = result.dry_run ? 'Sincronizaría' : 'Sincronizado';
    const hasErrors = result.errors > 0;
    resultEl.className = 'job-result visible ' + (hasErrors ? 'error-r' : 'success');
    const deltaNote = result.delta_skipped ? `  Δ ${result.delta_skipped}` : '';
    resultEl.textContent = `${verb} — ↑ ${result.uploaded}  ↓ ${result.downloaded}  ✓ ${result.up_to_date}  ⚠ ${result.conflicts}  ✗ ${result.errors}${deltaNote}`;
    if (!result.dry_run) _sendNotif('Sync completado', '↑ ' + result.uploaded + ' ↓ ' + result.downloaded + ' ✓ ' + result.up_to_date);

    if (decisionsEl) {
      const colors = { upload: '#569cd6', download: '#6a9955', conflict: '#f44747' };
      let html = '';
      const sources = result.sources || [];
      if (sources.length) {
        sources.forEach(src => {
          const srcColor = src.error ? '#f48771' : '#888';
          html += `<div style="margin-top:10px;padding:8px 10px;background:#1a1a2a;border-radius:4px;border-left:3px solid ${src.error?'#f44747':'#333'}">`;
          html += `<span style="color:#d4d4d4;font-weight:600">${src.name}</span>`;
          if (src.error) {
            html += ` <span style="color:#f48771;font-size:12px;margin-left:8px">${src.error}</span>`;
          } else {
            const srcDelta = src.delta_skipped ? `  Δ ${src.delta_skipped}` : '';
            html += ` <span style="color:#555;font-size:12px;margin-left:8px">↑ ${src.uploaded}  ↓ ${src.downloaded}  ✓ ${src.up_to_date}  ⚠ ${src.conflicts}  ✗ ${src.errors}${srcDelta}</span>`;
            if (src.decisions?.length) {
              html += src.decisions.map(d =>
                `<div style="font-size:11px;color:${colors[d.action]||'#888'};padding:1px 0 0 8px">[${d.action.toUpperCase()}] ${d.relative}</div>`
              ).join('');
            }
          }
          html += '</div>';
        });
      } else if (result.decisions?.length) {
        // Legacy single-source fallback
        html = result.decisions.map(d =>
          `<div style="font-size:12px;color:${colors[d.action]||'#888'};padding:2px 0">[${d.action.toUpperCase()}] ${d.relative}</div>`
        ).join('');
      }
      decisionsEl.innerHTML = html;
    }
    loadSync(); // Refresh sync log
  }
  const btnDry   = document.getElementById('btn-sync-dry');
  const btnApply = document.getElementById('btn-sync-apply');
  if (btnDry)   btnDry.disabled   = false;
  if (btnApply) btnApply.disabled = false;
}

// ── Convert CHD ──────────────────────────────────────────────────────────────
async function doConvertChd() {
  const pathVal    = document.getElementById('chd-path').value.trim();
  const dryRun     = document.getElementById('chd-dry-run').checked;
  const delSource  = document.getElementById('chd-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .cue/.bin'); return; }
  const btn = document.getElementById('btn-convert-chd');
  const resultEl = document.getElementById('job-result-convert-chd');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/convert-chd', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una conversión en curso…';
      btn.disabled = false;
      btn.textContent = 'Convertir a CHD';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Convertir a CHD';
  }
}

let _chdResults = [];

function _renderChdResult(result) {
  const resultEl   = document.getElementById('job-result-convert-chd');
  const btn        = document.getElementById('btn-convert-chd');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    _showJobResult('convert-chd', result);
    _chdResults = result.results || [];
    // Show filter header if there are results
    const hdr = document.getElementById('chd-results-header');
    if (hdr) hdr.classList.toggle('hidden', !(_chdResults.length));
    // Default: show errors-only if any failures exist
    const hasFails = _chdResults.some(r => !r.success && r.error);
    const cb = document.getElementById('chd-filter-errors');
    if (cb) cb.checked = hasFails;
    applyChdFilter();
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a CHD'; }
}

function applyChdFilter() {
  const resultsDiv = document.getElementById('chd-results');
  const countEl    = document.getElementById('chd-results-count');
  if (!resultsDiv) return;
  const errorsOnly = document.getElementById('chd-filter-errors')?.checked ?? false;
  const visible = errorsOnly ? _chdResults.filter(r => !r.success) : _chdResults;
  if (countEl) countEl.textContent = `${visible.length} / ${_chdResults.length} entradas`;
  if (!visible.length) {
    resultsDiv.innerHTML = errorsOnly
      ? '<p style="color:#4ec9b0;font-size:12px;margin:4px 0">Sin errores.</p>'
      : '';
    return;
  }
  // Determine if this was a dry_run from the job-result text (best-effort)
  const isDry = document.getElementById('job-result-convert-chd')?.textContent?.includes('DRY') ?? false;
  resultsDiv.innerHTML = visible.map(r => {
    if (r.success) {
      const tag = isDry ? 'PREVIEW' : 'OK';
      const bins = r.bin_count > 0 ? ` <span style="color:#555;font-size:10px">(${r.bin_count} bin)</span>` : '';
      return `<div style="font-size:12px;color:#4ec9b0;padding:2px 0">[${tag}] ${_h(r.cue)} → ${_h(r.chd)}${bins}</div>`;
    } else {
      const bins = r.bin_count > 0 ? ` <span style="color:#555;font-size:10px">(${r.bin_count} bin)</span>` : '';
      const errMsg = r.error ? `<div style="color:#f44747;font-size:11px;margin-top:2px;padding-left:8px">${_h(r.error)}</div>` : '';
      return `<div style="padding:4px 0;border-bottom:1px solid #2a1a1a"><span style="font-size:12px;color:#f44747"><strong>[FAIL]</strong> ${_h(r.cue)}${bins}</span>${errMsg}</div>`;
    }
  }).join('');
}

// ── Convert CSO/ZSO ────────────────────────────────────────────────────────────
async function doConvertCso() {
  const pathVal   = document.getElementById('cso-path').value.trim();
  const delSource = document.getElementById('cso-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .cso/.zso'); return; }
  const btn = document.getElementById('btn-convert-cso');
  const resultEl = document.getElementById('job-result-convert-cso');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/convert-cso', { source_path: pathVal, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una conversión CSO en curso…';
      btn.disabled = false;
      btn.textContent = 'Convertir a ISO';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Convertir a ISO';
  }
}

function _renderCsoResult(result) {
  const resultEl = document.getElementById('job-result-convert-cso');
  const btn = document.getElementById('btn-convert-cso');
  const resultsDiv = document.getElementById('cso-results');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    const tot = result.converted + result.failed + result.skipped;
    const summary = `Convertidos: ${result.converted} | Omitidos: ${result.skipped} | Fallidos: ${result.failed}`;
    resultEl.className = 'job-result visible ' + (result.failed > 0 ? 'warning-r' : 'success');
    resultEl.textContent = summary;
    // Render detailed results
    if (resultsDiv && result.results) {
      resultsDiv.innerHTML = result.results.map(r => {
        if (r.success) {
          return `<div style="font-size:12px;color:#4ec9b0;padding:2px 0">[OK] ${_h(r.file)}</div>`;
        } else {
          const errMsg = r.error ? `<div style="color:#f44747;font-size:11px;margin-top:2px;padding-left:8px">${_h(r.error)}</div>` : '';
          return `<div style="padding:4px 0;border-bottom:1px solid #2a1a1a"><span style="font-size:12px;color:#f44747"><strong>[FAIL]</strong> ${_h(r.file)}</span>${errMsg}</div>`;
        }
      }).join('');
    }
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a ISO'; }
}

// ── Extract ZIP ──────────────────────────────────────────────────────────────
async function doCleanupZips() {
  const pathVal = document.getElementById('zip-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  const n = (document.querySelectorAll('#zip-results div').length) || '?';
  if (!confirm(`¿Eliminar TODOS los archivos .zip de:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-zips', { source_path: pathVal });
    const el = document.getElementById('job-result-extract-zip');
    el.className = 'job-result visible success';
    el.textContent = `ZIPs eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message + '\n\nVerifica que los archivos no estén en uso por otro programa.'); }
}

async function doCleanupCueBin() {
  const pathVal = document.getElementById('chd-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  if (!confirm(`¿Eliminar los archivos .cue y .bin que ya tienen su .chd en:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-cue-bin', { source_path: pathVal });
    const el = document.getElementById('job-result-convert-chd');
    el.className = 'job-result visible success';
    el.textContent = `Archivos eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.skipped ? `  |  Sin .chd (no tocados): ${d.skipped}` : ''}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message + '\n\nVerifica que los archivos no estén en uso por otro programa.'); }
}

async function doExtractZip() {
  const pathVal   = document.getElementById('zip-path').value.trim();
  const dryRun    = document.getElementById('zip-dry-run').checked;
  const delSource = document.getElementById('zip-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .zip'); return; }
  const btn = document.getElementById('btn-extract-zip');
  const resultEl = document.getElementById('job-result-extract-zip');
  btn.disabled = true; btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  document.getElementById('zip-results').innerHTML = '';
  try {
    const d = await apiPost('/api/extract-zip', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay una extracción en curso…';
      btn.disabled = false; btn.textContent = 'Descomprimir ZIPs'; return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false; btn.textContent = 'Descomprimir ZIPs';
  }
}

// ── M3U Generator ─────────────────────────────────────────────────────────────
async function doGenerateM3U() {
  const pathVal = document.getElementById('m3u-path').value.trim();
  const dryRun  = document.getElementById('m3u-dry-run').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta de ROMs'); return; }
  const resultEl = document.getElementById('m3u-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Buscando grupos multi-disco…</p>';
  try {
    const d = await apiPost('/api/generate-m3u', { source_path: pathVal, dry_run: dryRun });
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
    const verb = dryRun ? 'Crearía' : 'Creados';
    let html = `<p style="color:#4ec9b0;margin-bottom:12px">${verb}: <strong>${d.created}</strong>  |  Ya existían: <strong>${d.skipped}</strong></p>`;
    if (d.groups.length) {
      html += '<div style="max-height:300px;overflow-y:auto">';
      html += d.groups.map(g => {
        const color = g.discs.length >= 2 ? '#4ec9b0' : '#888';
        return `<div style="font-size:12px;color:${color};padding:2px 0"><strong>${g.m3u}</strong> → ${g.discs.join(', ')}</div>`;
      }).join('');
      html += '</div>';
    } else {
      html += '<p style="color:#555;font-size:12px">No se encontraron grupos multi-disco.</p>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function autodetectM3UFolders() {
  const btn = document.getElementById('btn-m3u-autodetect');
  const wrap = document.getElementById('m3u-folder-select-wrap');
  const listEl = document.getElementById('m3u-folder-list');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando…'; }
  try {
    const d = await apiFetch('/api/disc-folders');
    const folders = d.folders || [];
    if (folders.length === 0) {
      alert('No se detectaron carpetas de plataformas de disco en library_root.');
    } else if (folders.length === 1) {
      document.getElementById('m3u-path').value = folders[0];
      if (wrap) wrap.classList.add('hidden');
    } else {
      // Show folder buttons to pick one
      listEl.innerHTML = folders.map(f => {
        const name = f.split(/[\\/]/).pop();
        return `<button class="btn" style="font-size:12px;padding:3px 10px" onclick="document.getElementById('m3u-path').value='${f.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}';document.getElementById('m3u-folder-select-wrap').classList.add('hidden')">${name}</button>`;
      }).join('');
      if (wrap) wrap.classList.remove('hidden');
    }
  } catch(e) {
    alert('Error al detectar carpetas: ' + e.message + '\n\nConsulta los logs para más detalles.');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Autodetectar carpetas'; }
  }
}

// ── Multi-disc Verifier ───────────────────────────────────────────────────────
async function doVerifyMultidisc() {
  const rawVal = document.getElementById('verify-multidisc-path').value.trim();
  if (!rawVal) { alert('Introduce al menos una carpeta de ROMs'); return; }
  const paths = rawVal.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
  const resultEl = document.getElementById('multidisc-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Verificando…</p>';
  // Aggregate results across all paths
  let totalOk = 0, totalIssues = 0;
  const allIssues = [];
  try {
    for (const pathVal of paths) {
      const d = await apiPost('/api/verify-multidisc', { source_path: pathVal });
      if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
      totalOk += d.groups_ok; totalIssues += d.groups_with_issues;
      allIssues.push(...d.issues);
    }
    const d = { groups_ok: totalOk, groups_with_issues: totalIssues, issues: allIssues };
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }

    const realIssues    = d.issues.filter(i => i.issue_type !== 'unmatched');
    const unmatchedOnly = d.issues.filter(i => i.issue_type === 'unmatched');
    const realBad = new Set(realIssues.map(i => i.base_name));
    // Groups with only "unmatched" and no real structural issues are OK structurally
    const structurallyBad = d.groups_with_issues - [...new Set(unmatchedOnly.map(i => i.base_name))].filter(n => !realBad.has(n)).length;
    const total = d.groups_ok + d.groups_with_issues;

    let html = `<p style="margin-bottom:8px">`;
    html += `<span style="color:#4ec9b0">✓ ${d.groups_ok + (d.groups_with_issues - structurallyBad)} grupos OK estructuralmente</span>`;
    if (structurallyBad > 0) html += `  <span style="color:#f44747">✗ ${structurallyBad} con problemas reales</span>`;
    if (unmatchedOnly.length > 0) html += `  <span style="color:#888">⚠ ${unmatchedOnly.length} sin match en catálogo (normal si no has hecho Match aún)</span>`;
    html += `  <span style="color:#555">(${total} grupos)</span></p>`;

    const issueLabels = { gap: 'Disco faltante', mixed_ext: 'Extensiones mezcladas', missing_file: 'Archivo no encontrado', unmatched: 'Sin match en catálogo' };
    if (realIssues.length) {
      html += `<p style="color:#f44747;font-size:12px;margin:10px 0 6px">Problemas que requieren atención:</p>`;
      html += '<div style="max-height:300px;overflow-y:auto;margin-bottom:12px">';
      html += realIssues.map(i => `<div style="font-size:12px;padding:3px 0;border-bottom:1px solid #1e1e2e">
        <span style="color:#f44747">${issueLabels[i.issue_type] || i.issue_type}</span>
        <span style="color:#888;margin:0 6px">·</span>
        ${i.platform ? `<span style="color:#569cd6;font-size:11px;background:#1a2233;padding:1px 5px;border-radius:3px;margin-right:6px">${_h(i.platform)}</span>` : ''}
        <span style="color:#d4d4d4">${_h(i.base_name)}</span>
        <span style="color:#555;margin-left:8px">${_h(i.detail)}</span>
      </div>`).join('');
      html += '</div>';
    }
    if (unmatchedOnly.length) {
      html += `<details style="font-size:12px;color:#555"><summary style="cursor:pointer;color:#888">Sin match en catálogo (${unmatchedOnly.length}) — haz Match catálogos para resolverlos</summary>`;
      html += '<div style="max-height:200px;overflow-y:auto;margin-top:6px">';
      html += unmatchedOnly.map(i => `<div style="padding:2px 0;color:#555">${i.base_name} — ${i.detail}</div>`).join('');
      html += '</div></details>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Orphaned Saves ────────────────────────────────────────────────────────────
async function doFindOrphans() {
  const pathVal = document.getElementById('orphan-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la biblioteca'); return; }
  const resultEl = document.getElementById('orphan-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Buscando…</p>';
  try {
    const d = await apiFetch('/api/orphaned-saves?path=' + encodeURIComponent(pathVal));
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
    if (d.total === 0) { resultEl.innerHTML = '<p class="empty">No se encontraron saves huérfanos.</p>'; return; }
    const totalBytes = d.orphans.reduce((s, o) => s + o.size_bytes, 0);
    let html = `<p style="color:#888;margin-bottom:8px">${d.total} save(s) huérfano(s) — ${fmtSize(totalBytes)} en total:</p>`;
    html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:12px">
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#888">
        <input type="checkbox" id="orphan-select-all" checked onchange="document.querySelectorAll('.orphan-chk').forEach(c=>c.checked=this.checked)">
        Seleccionar todos
      </label>
    </div>`;
    html += '<div style="max-height:400px;overflow-y:auto;margin-bottom:10px">';
    html += d.orphans.map(o => {
      const sugHtml = (o.suggestions && o.suggestions.length)
        ? `<div style="margin-top:4px;padding:4px 8px;background:#12121e;border-radius:3px">
            ${o.suggestions.map(s =>
              `<div style="font-size:11px;color:#888;display:flex;align-items:center;gap:6px;padding:2px 0">
                <span style="color:#569cd6">Posible match:</span>
                <span style="color:#d4d4d4">${_h(s.filename)}</span>
                <span style="color:#555">(${_h(s.platform)})</span>
                <button class="btn" style="font-size:10px;padding:1px 7px"
                  onclick="moveOrphanedSave(${JSON.stringify(o.save_path)}, ${JSON.stringify(s.source_path)}, this)">Mover aquí</button>
              </div>`
            ).join('')}
          </div>`
        : '';
      return `<div style="padding:4px 0;font-size:12px">
        <div style="display:flex;align-items:center;gap:8px">
          <input type="checkbox" class="orphan-chk" value="${o.save_path.replace(/"/g, '&quot;')}" data-size="${o.size_bytes}" checked onchange="_updateOrphanSelectAll()">
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#888" title="${o.save_path}">${o.save_path}</span>
          <span style="color:#555;flex-shrink:0">${fmtSize(o.size_bytes)}</span>
        </div>${sugHtml}
      </div>`;
    }).join('');
    html += '</div>';
    html += '<div style="display:flex;gap:8px">';
    html += '<button class="btn" onclick="selectAllOrphans()">☑️ Seleccionar todos</button>';
    html += '<button class="btn" onclick="doMoveOrphansToArchive()">📁 Mover seleccionados a _huérfanos/</button>';
    html += '<button class="btn danger" onclick="doDeleteOrphans()">🗑️ Borrar seleccionados</button>';
    html += '</div>';
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function _updateOrphanSelectAll() {
  const all = [...document.querySelectorAll('.orphan-chk')];
  const allChecked = all.every(c => c.checked);
  const noneChecked = all.every(c => !c.checked);
  const sa = document.getElementById('orphan-select-all');
  if (sa) { sa.checked = allChecked; sa.indeterminate = !allChecked && !noneChecked; }
}

async function doDeleteOrphans() {
  const checkedEls = [...document.querySelectorAll('.orphan-chk:checked')];
  const checked = checkedEls.map(c => c.value);
  if (checked.length === 0) { alert('Selecciona al menos un archivo.'); return; }
  const totalBytes = checkedEls.reduce((s, c) => s + parseInt(c.dataset.size || '0'), 0);
  if (!confirm(`¿Eliminar ${checked.length} save(s) huérfano(s)?\nEspacio a liberar: ${fmtSize(totalBytes)}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/orphaned-saves/delete', { paths: checked });
    alert(`Eliminados: ${d.deleted}  |  Fallidos: ${d.failed}  |  Liberados: ${fmtSize(d.freed_bytes)}`);
    doFindOrphans();
  } catch(e) {
    alert('Error: ' + e.message + '\n\nVerifica que los archivos no estén en uso por otro programa.');
  }
}

// B9-4: Select all orphaned saves
function selectAllOrphans() {
  document.querySelectorAll('.orphan-chk').forEach(cb => cb.checked = true);
}

// B9-4: Move orphaned saves to _huerfanos/
async function doMoveOrphansToArchive() {
  const checkedEls = [...document.querySelectorAll('.orphan-chk:checked')];
  const checked = checkedEls.map(c => c.value);
  if (checked.length === 0) { alert('Selecciona al menos un archivo.'); return; }
  const totalBytes = checkedEls.reduce((s, c) => s + parseInt(c.dataset.size || '0'), 0);
  const pathVal = document.getElementById('orphan-path').value.trim();
  if (!pathVal) { alert('Introduce la carpeta de la biblioteca.'); return; }
  if (!confirm(`¿Mover ${checked.length} save(s) huérfano(s) a _huérfanos/?\nEspacio a mover: ${fmtSize(totalBytes)}`)) return;
  try {
    const d = await apiPost('/api/orphaned-saves/move-to-archive', {
      paths: checked,
      library_root: pathVal
    });
    if (d.error) { alert('Error: ' + d.error); return; }
    const msg = `Movidos: ${d.moved}  |  Fallidos: ${d.failed}  |  Espacio movido: ${fmtSize(d.moved_bytes)}`;
    alert(msg + `\n\nCarpeta: ${d.archive_dir}`);
    doFindOrphans();
  } catch(e) {
    alert('Error: ' + e.message);
  }
}

async function moveOrphanedSave(savePath, gamePath, btn) {
  const saveFilename = savePath.split(/[\\/]/).pop();
  const gameFilename = gamePath.split(/[\\/]/).pop();
  if (!confirm(`¿Mover el save "${saveFilename}" junto al juego "${gameFilename}"?`)) return;
  btn.disabled = true;
  btn.textContent = '…';
  try {
    const d = await apiPost('/api/orphaned-saves/move', { save_path: savePath, game_path: gamePath });
    if (d.error) { showToast('Error: ' + d.error, 'err'); btn.disabled = false; btn.textContent = 'Mover aquí'; return; }
    showToast(`Save movido: ${saveFilename}`, 'ok');
    doFindOrphans();
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
    btn.disabled = false;
    btn.textContent = 'Mover aquí';
  }
}

// ── Health Check ─────────────────────────────────────────────────────────────
async function doHealthCheck() {
  const btn = document.getElementById('btn-health-check');
  if (!confirm('El Health Check re-hashea todos los ROMs. Puede tardar mucho en bibliotecas grandes.\n\n¿Continuar?')) return;
  btn.disabled = true; btn.textContent = 'Verificando…';
  document.getElementById('health-result').innerHTML = '';
  try {
    const d = await apiPost('/api/health-check', {});
    if (d.status === 'already_running') {
      btn.disabled = false; btn.textContent = 'Iniciar Health Check'; return;
    }
    startPolling();
  } catch(e) {
    btn.disabled = false; btn.textContent = 'Iniciar Health Check';
    document.getElementById('health-result').innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function _renderHealthResult(r) {
  const el = document.getElementById('health-result');
  if (!el) return;
  if (r.error) { el.innerHTML = `<p class="error-msg">${r.error}</p>`; return; }
  const total = r.ok + r.corrupted + r.missing;
  let html = `<p style="margin-bottom:12px">`;
  html += `<span style="color:#4ec9b0">✓ ${r.ok} OK</span>`;
  if (r.corrupted > 0) html += `  <span style="color:#f44747">✗ ${r.corrupted} corruptos</span>`;
  if (r.missing   > 0) html += `  <span style="color:#ce9178">⚠ ${r.missing} no encontrados</span>`;
  html += `  <span style="color:#555">(${total} ROMs verificados)</span></p>`;
  if (r.issues?.length) {
    // Platform filter dropdown
    const platforms = [...new Set(r.issues.map(i => i.platform || '').filter(Boolean))].sort();
    if (platforms.length > 1) {
      html += '<div style="margin-bottom:8px">';
      html += '<label style="font-size:12px;color:#888;margin-right:6px">Plataforma:</label>';
      html += '<select id="health-plat-filter" onchange="_filterHealthIssues()" style="font-size:12px;background:#1e1e1e;color:#ccc;border:1px solid #333;padding:2px 6px;border-radius:4px">';
      html += '<option value="">Todas</option>';
      html += platforms.map(p => `<option value="${_h(p)}">${_h(p)}</option>`).join('');
      html += '</select></div>';
    }
    html += '<div id="health-issues-list" style="max-height:400px;overflow-y:auto">';
    html += '<table style="font-size:12px;width:100%;border-collapse:collapse">';
    html += '<thead><tr style="color:#888;border-bottom:1px solid #333">';
    html += '<th style="text-align:left;padding:4px 6px">Estado</th>';
    html += '<th style="text-align:left;padding:4px 6px">Plataforma</th>';
    html += '<th style="text-align:left;padding:4px 6px">Archivo</th>';
    html += '<th style="text-align:left;padding:4px 6px">Búsqueda</th>';
    html += '</tr></thead><tbody id="health-issues-tbody">';
    html += r.issues.map(i => _healthIssueRow(i)).join('');
    html += '</tbody></table></div>';
  }
  el.innerHTML = html;
  // Store issues for filtering
  el._issues = r.issues;
}

function _healthIssueRow(i) {
  const color = i.status === 'corrupted' ? '#f44747' : '#ce9178';
  const label = i.status === 'corrupted' ? 'CORRUPTO' : 'NO ENCONTRADO';
  const name  = i.source_path.split(/[\\/]/).pop();
  const plat  = i.platform || '';
  const title = i.canonical_title || name.replace(/\.[^.]+$/, '');
  const query = title + (plat ? ' ' + plat : '') + ' No-Intro site:archive.org';
  const qEnc  = encodeURIComponent(query);
  const qHtml = _h(query);
  return `<tr data-platform="${_h(plat)}" style="border-bottom:1px solid #222">` +
    `<td style="padding:3px 6px;color:${color};white-space:nowrap">[${label}]</td>` +
    `<td style="padding:3px 6px;color:#888;white-space:nowrap">${_h(plat)}</td>` +
    `<td style="padding:3px 6px;color:${color}" title="${_h(i.source_path)}">${_h(name)}</td>` +
    `<td style="padding:3px 6px;white-space:nowrap">` +
    `<span style="font-size:11px;color:#888;margin-right:4px" title="${qHtml}">${_h(title)}</span>` +
    `<button onclick="_copyToClipboard('${query.replace(/'/g,"\\'")}');" ` +
    `style="font-size:11px;padding:1px 6px;background:#2d2d2d;border:1px solid #444;color:#ccc;border-radius:3px;cursor:pointer" title="${qHtml}">Copiar</button>` +
    `</td></tr>`;
}

function _filterHealthIssues() {
  const el = document.getElementById('health-result');
  const sel = document.getElementById('health-plat-filter');
  if (!el || !sel || !el._issues) return;
  const plat = sel.value;
  const tbody = document.getElementById('health-issues-tbody');
  if (!tbody) return;
  tbody.innerHTML = el._issues
    .filter(i => !plat || (i.platform || '') === plat)
    .map(i => _healthIssueRow(i)).join('');
}


// ── QoL-4: Platform health dashboard ─────────────────────────────────────────
function togglePlatformHealth() {
  const panel = document.getElementById('platform-health-panel');
  if (panel.classList.contains('hidden')) {
    panel.classList.remove('hidden');
    loadPlatformHealth();
  } else {
    panel.classList.add('hidden');
  }
}

async function loadPlatformHealth() {
  const tbl = document.getElementById('ph-table');
  const lbl = document.getElementById('ph-last-scan');
  if (!tbl) return;
  tbl.innerHTML = '<span style="color:#555;font-size:12px">Cargando…</span>';
  try {
    const root = _deviceRoot() || '';
    const d = await apiFetch('/api/platform-health' + (root ? '?root=' + encodeURIComponent(root) : ''));
    if (lbl) lbl.textContent = d.last_scan || '—';
    if (!d.platforms || d.platforms.length === 0) {
      tbl.innerHTML = '<span style="color:#555;font-size:12px">Sin datos. Ejecuta un scan primero.</span>';
      return;
    }
    const _bar = (pct, color) => {
      const w = Math.round(pct);
      return `<div style="display:flex;align-items:center;gap:6px">
        <div style="width:80px;height:6px;background:#1e1e2e;border-radius:3px;overflow:hidden;flex-shrink:0">
          <div style="width:${w}%;height:100%;background:${color}"></div>
        </div>
        <span style="font-size:11px;color:#888;min-width:34px">${pct.toFixed(0)}%</span>
      </div>`;
    };
    let html = `<table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead><tr style="color:#555;font-size:10px;text-transform:uppercase;letter-spacing:0.8px;border-bottom:1px solid #2a2a2a">
        <th style="text-align:left;padding:4px 8px">Plataforma</th>
        <th style="text-align:right;padding:4px 8px">ROMs</th>
        <th style="padding:4px 16px">DAT match</th>
        <th style="padding:4px 16px">Portadas</th>
      </tr></thead><tbody>`;
    for (const p of d.platforms) {
      html += `<tr style="border-bottom:1px solid #1a1a1a">
        <td style="padding:5px 8px;color:#d4d4d4">${_h(p.platform)}</td>
        <td style="text-align:right;padding:5px 8px;color:#888">${p.total_roms}</td>
        <td style="padding:5px 16px">${_bar(p.match_pct, '#4ec9b0')}</td>
        <td style="padding:5px 16px">${_bar(p.art_pct, '#c586c0')}</td>
      </tr>`;
    }
    html += '</tbody></table>';
    tbl.innerHTML = html;
  } catch(e) {
    tbl.innerHTML = `<span style="color:#f44747;font-size:12px">Error: ${_h(e.message)}</span>`;
  }
}


// ── 32-4: Timeline de operaciones ─────────────────────────────────────────────
async function loadOperationsTimeline() {
  const el = document.getElementById('operations-timeline');
  if (!el) return;
  el.innerHTML = '<p class="loading">Cargando…</p>';
  try {
    const d = await apiFetch('/api/operations-timeline?limit=100');
    const ops = d.operations || [];
    if (!ops.length) {
      el.innerHTML = '<p style="color:#555">No hay operaciones registradas todavía.</p>';
      return;
    }
    const ICONS = { rename: '✏', delete: '🗑', move: '📦', extract: '📦', copy: '📋' };
    const COLORS = { success: '#4ec9b0', error: '#f44747', skipped: '#888', ok: '#4ec9b0' };
    let html = '<div style="display:flex;flex-direction:column;gap:4px">';
    for (const op of ops) {
      const icon = ICONS[op.operation_type] || '📄';
      const color = COLORS[op.result] || '#888';
      const name = (op.source_path || '').split(/[\\/]/).pop();
      const ts = (op.created_at || '').replace('T', ' ').slice(0, 16);
      html += `<div style="display:flex;align-items:baseline;gap:8px;padding:3px 0;border-bottom:1px solid #1a1a1a">`;
      html += `<span style="width:20px;text-align:center;flex-shrink:0">${icon}</span>`;
      html += `<span style="color:${color};width:60px;flex-shrink:0;font-size:11px">${_h(op.result || '')}</span>`;
      html += `<span style="color:#888;width:80px;flex-shrink:0;font-size:10px;font-family:monospace">${ts}</span>`;
      html += `<span style="color:#888;width:70px;flex-shrink:0;font-size:11px">${_h(op.operation_type || '')}</span>`;
      html += `<span style="color:#ccc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;font-size:12px" title="${_h(op.source_path || '')}">${_h(name)}</span>`;
      if (op.message) html += `<span style="color:#555;font-size:11px;flex-shrink:0;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(op.message)}">${_h(op.message)}</span>`;
      html += `</div>`;
    }
    html += '</div>';
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── 32-5: Playlists RetroArch .lpl ───────────────────────────────────────────
async function doExportLpl() {
  const el = document.getElementById('lpl-result');
  const outputDir = document.getElementById('lpl-output-dir')?.value.trim() || '';
  if (el) { el.innerHTML = '<span class="loading">Generando…</span>'; el.classList.remove('hidden'); }
  try {
    const d = await apiPost('/api/export-lpl', outputDir ? { output_dir: outputDir } : {});
    if (d.error) {
      if (el) el.innerHTML = `<span style="color:#f44747">✗ ${_h(d.error)}</span>`;
    } else {
      if (el) el.innerHTML = `<span style="color:#4ec9b0">✓ ${d.platforms} plataformas · ${d.games} juegos → <code style="font-size:11px">${_h(d.output_dir)}</code></span>`;
    }
  } catch (e) {
    if (el) el.innerHTML = `<span style="color:#f44747">✗ ${e.message}</span>`;
  }
}

// ── S34-3: N64 converter ─────────────────────────────────────────────────────
async function doN64Scan() {
  const path = document.getElementById('n64-path')?.value.trim();
  const el = document.getElementById('n64-scan-result');
  if (!path || !el) return;
  el.innerHTML = '<span class="loading">Escaneando…</span>';
  try {
    const d = await apiFetch('/api/n64-scan?path=' + encodeURIComponent(path));
    const roms = d.roms || [];
    if (!roms.length) { el.innerHTML = '<p style="color:#555;font-size:12px">No se encontraron ROMs de N64 en esa carpeta.</p>'; return; }
    const needConv = roms.filter(r => r.needs_conversion);
    let html = `<p style="font-size:12px;color:#888;margin-bottom:8px">${roms.length} ROMs encontrados — ${needConv.length} necesitan conversión a .z64</p>`;
    if (needConv.length) {
      html += `<div style="max-height:200px;overflow-y:auto">`;
      html += needConv.map(r => `<div style="display:flex;gap:8px;align-items:center;padding:3px 0;border-bottom:1px solid #1a1a2a;font-size:12px">
        <span style="color:#f9c74f;width:36px;flex-shrink:0">${_h(r.format.toUpperCase())}</span>
        <span style="color:#d4d4d4;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_h(r.filename)}</span>
        <button class="btn" style="padding:1px 8px;font-size:11px;flex-shrink:0" onclick="doN64Convert(${JSON.stringify(r.path)})">Convertir</button>
      </div>`).join('');
      html += `</div>`;
    } else {
      html += `<p style="color:#4ec9b0;font-size:12px">&#x2713; Todos los ROMs ya están en formato .z64</p>`;
    }
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

async function doN64Convert(sourcePath) {
  try {
    const d = await apiPost('/api/convert-n64', { source_path: sourcePath });
    if (d.success) {
      showToast(`✓ Convertido: ${d.target_path.split(/[\\/]/).pop()}`, 'ok');
      doN64Scan();  // refresh list
    } else {
      showToast(`✗ ${d.error || 'Error desconocido'}`, 'err');
    }
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ── S34-5: BIOS Checker ──────────────────────────────────────────────────────
async function loadBiosStatus() {
  const el = document.getElementById('bios-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:#555;font-size:12px">Buscando…</p>';
  try {
    const d = await apiFetch('/api/bios-status');
    const bios = d.bios || [];
    if (!bios.length) { el.innerHTML = '<p style="color:#555;font-size:12px">No hay definiciones de BIOS.</p>'; return; }
    // Group by platform
    const byPlat = {};
    bios.forEach(b => { (byPlat[b.platform] = byPlat[b.platform] || []).push(b); });
    let html = '';
    Object.entries(byPlat).sort(([a],[b]) => a.localeCompare(b)).forEach(([plat, entries]) => {
      const total = entries.length, found = entries.filter(e => e.found).length;
      const clr = found === total ? '#4ec9b0' : (found > 0 ? '#f9c74f' : '#e06c75');
      html += `<div style="margin-bottom:12px">
        <div style="font-size:12px;font-weight:600;color:${clr};margin-bottom:4px">${_h(plat)} <span style="font-weight:400;color:#555">(${found}/${total})</span></div>`;
      entries.forEach(b => {
        const icon = b.found ? (b.md5_match === false ? '&#x26A0;' : '&#x2713;') : (b.required ? '&#x2717;' : '&#x25A1;');
        const clrIcon = b.found ? (b.md5_match === false ? '#f9c74f' : '#4ec9b0') : (b.required ? '#e06c75' : '#555');
        const md5note = b.found && b.md5_match === false ? ' <span style="color:#f9c74f;font-size:10px">MD5 no coincide</span>' : '';
        html += `<div style="display:flex;gap:6px;align-items:center;padding:2px 0;font-size:11px">
          <span style="color:${clrIcon};width:14px;flex-shrink:0">${icon}</span>
          <code style="color:#ce9178;flex:1">${_h(b.filename)}</code>
          <span style="color:#555">${_h(b.notes)}</span>${md5note}
        </div>`;
      });
      html += `</div>`;
    });
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

// ── B6-1/B6-6: RetroArch diagnostic ─────────────────────────────────────────
async function loadRetroArchCheck() {
  const spinner = document.getElementById('ra-check-spinner');
  const result  = document.getElementById('ra-check-result');
  const status  = document.getElementById('ra-check-status');
  const rows    = document.getElementById('ra-check-rows');
  const issues  = document.getElementById('ra-check-issues');
  const coresWrap = document.getElementById('ra-check-cores');
  const coresList = document.getElementById('ra-check-cores-list');
  if (!result) return;
  if (spinner) spinner.classList.remove('hidden');
  result.classList.add('hidden');
  try {
    const d = await apiFetch('/api/retroarch-check');
    if (spinner) spinner.classList.add('hidden');

    // status badge
    const okColor = d.ok ? '#4ec9b0' : '#e06c75';
    const okIcon  = d.ok ? '&#x2713; Todo correcto' : '&#x26A0; Hay problemas';
    status.innerHTML = `<span style="color:${okColor}">${okIcon}</span>`;

    // main rows
    const cell = (txt, mono) => mono
      ? `<td style="padding:2px 0 2px 8px"><code style="color:#ce9178;font-size:11px">${_h(txt)}</code></td>`
      : `<td style="padding:2px 0 2px 8px;color:#d4d4d4;font-size:11px">${_h(txt)}</td>`;
    const icon = ok => ok
      ? `<td style="color:#4ec9b0;font-size:11px;width:14px">&#x2713;</td>`
      : `<td style="color:#e06c75;font-size:11px;width:14px">&#x2717;</td>`;

    let html = '';
    html += `<tr>${icon(d.exe_configured)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Ruta configurada</td>${cell(d.exe_path || '\u2014', true)}</tr>`;
    if (d.exe_configured) {
      html += `<tr>${icon(d.exe_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Ejecutable existe</td>${cell(d.exe_exists ? 'S\xed' : 'No', false)}</tr>`;
      html += `<tr>${icon(d.cfg_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">retroarch.cfg</td>${cell(d.cfg_exists ? 'Encontrado' : 'No encontrado', false)}</tr>`;
      html += `<tr>${icon(d.cores_dir_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Cores</td>${cell(d.cores_dir_exists ? d.cores_count + ' cores' : 'No encontrado', false)}</tr>`;
      if (d.savefile_dir)   html += `<tr><td></td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Saves dir</td>${cell(d.savefile_dir, true)}</tr>`;
      if (d.savestate_dir)  html += `<tr><td></td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">States dir</td>${cell(d.savestate_dir, true)}</tr>`;
      if (d.esde_ra_path) {
        const matchIcon = d.esde_ra_match === true ? '&#x2713;' : (d.esde_ra_match === false ? '&#x26A0;' : '?');
        const matchColor = d.esde_ra_match === true ? '#4ec9b0' : '#f9c74f';
        html += `<tr><td style="color:${matchColor};font-size:11px">${matchIcon}</td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">ES-DE apunta a</td>${cell(d.esde_ra_path, true)}</tr>`;
      }
    }
    rows.innerHTML = html;

    // issues list
    if (d.issues && d.issues.length) {
      issues.innerHTML = d.issues.map(i =>
        `<div style="font-size:11px;color:#f9c74f;margin-bottom:3px">&#x26A0; ${_h(i)}</div>`
      ).join('');
    } else {
      issues.innerHTML = '';
    }

    // key cores list
    if (d.key_cores && Object.keys(d.key_cores).length) {
      coresWrap.classList.remove('hidden');
      coresList.innerHTML = Object.entries(d.key_cores).map(([lbl, found]) => {
        const bg = found ? '#1e3a2f' : '#2a1a1a';
        const fg = found ? '#4ec9b0' : '#666';
        const ic = found ? '&#x2713;' : '&#x2717;';
        return `<span style="background:${bg};color:${fg};font-size:10px;padding:2px 6px;border-radius:3px">${ic} ${_h(lbl)}</span>`;
      }).join('');
    } else {
      coresWrap.classList.add('hidden');
    }

    result.classList.remove('hidden');
  } catch(e) {
    if (spinner) spinner.classList.add('hidden');
    result.classList.remove('hidden');
    status.innerHTML = `<span style="color:#e06c75">Error: ${_h(e.message)}</span>`;
    rows.innerHTML = '';
    issues.innerHTML = '';
    coresWrap.classList.add('hidden');
  }
}

// ── S34-6: ES-DE Status ──────────────────────────────────────────────────────
async function loadEsdeStatus() {
  const el = document.getElementById('esde-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:#555;font-size:12px">Detectando…</p>';
  try {
    const d = await apiFetch('/api/esde-status');
    if (!d.installed) {
      el.innerHTML = `<p style="color:#e06c75;font-size:12px">&#x2717; ES-DE no detectado en las rutas conocidas.</p>
        <p style="color:#555;font-size:11px">Instala ES-DE desde <a href="https://es-de.org" target="_blank" style="color:#4ec9b0">es-de.org</a> o configura la ruta manualmente.</p>`;
      return;
    }
    el.innerHTML = `
      <div style="font-size:12px;color:#4ec9b0;margin-bottom:8px">&#x2713; ES-DE detectado</div>
      <table style="font-size:12px;border-collapse:collapse;width:100%">
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">Carpeta</td><td><code style="color:#ce9178">${_h(d.install_dir)}</code></td></tr>
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">ROMs</td><td><code style="color:#ce9178">${_h(d.roms_path || '—')}</code></td></tr>
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">Gamelists</td><td><code style="color:#ce9178">${_h(d.gamelists_dir || '—')}</code></td></tr>
      </table>
      ${d.gamelists_dir ? `<div style="margin-top:10px"><button class="btn primary" onclick="doExportGamelistsAll(${JSON.stringify(d.gamelists_dir)})" style="font-size:12px">&#x2193; Exportar todas las gamelists a ES-DE</button></div>` : ''}`;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

async function doExportGamelistsAll(gamlistsDir) {
  try {
    const d = await apiPost('/api/export-gamelists', { output_dir: gamlistsDir });
    if (d.error) showToast('✗ ' + d.error, 'err');
    else showToast(`✓ Gamelists exportadas: ${d.written || 0} archivos`, 'ok');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ES-DE gamelists dir — kept for status display only; NOT used as export output.
// For ES-DE, gamelists go in library_root/{platform}/ (alongside ROMs), not in
// ~/.emulationstation/gamelists/ — that old path caused broken <path> entries.
let _esdeGamelistsDir = '';

async function _autoFillEsdeGamelistDir() {
  // Do NOT auto-fill the export dir — library_root (the default) is correct for ES-DE.
  // Only fetch gamelists_dir for status/informational display.
  try {
    const d = await apiFetch('/api/esde-status');
    if (d.gamelists_dir) _esdeGamelistsDir = d.gamelists_dir;
  } catch(_) {}
}

async function useEsdeGamelistDir() {
  // For ES-DE: leave the field empty so the export defaults to library_root.
  // The gamelist.xml belongs alongside the ROMs, not in the ES config dir.
  const inp = document.getElementById('gamelist-output-dir');
  if (inp) { inp.value = ''; inp.placeholder = 'Vacío = library_root (correcto para ES-DE)'; }
  showToast('ES-DE: deja vacío para exportar a library_root (junto a los ROMs)', 'ok');
}

// ── Análisis de carpeta ───────────────────────────────────────────────────────
let _faUid = 0;
function _faCollapsibleList(items, renderItem, limit = 10) {
  if (!items || items.length === 0) return '';
  const uid = 'falist_' + (++_faUid);
  const visible = items.slice(0, limit);
  const hidden  = items.slice(limit);
  let html = `<div style="max-height:220px;overflow-y:auto;border:1px solid #222;border-radius:4px;padding:4px 0;margin-bottom:4px">`;
  html += '<ul style="margin:0;padding-left:20px">';
  html += visible.map(renderItem).join('');
  if (hidden.length > 0) {
    html += `</ul><ul id="${uid}_rest" style="margin:0;padding-left:20px;display:none">`;
    html += hidden.map(renderItem).join('');
  }
  html += '</ul></div>';
  if (hidden.length > 0) {
    html += `<button onclick="(function(){var r=document.getElementById('${uid}_rest'),b=document.getElementById('${uid}_btn');if(r.classList.contains('hidden')){r.classList.remove('hidden');b.textContent='▲ Mostrar menos';}else{r.classList.add('hidden');b.textContent='▼ Ver todos (${items.length})';}})()" id="${uid}_btn" style="background:none;border:none;color:#569cd6;font-size:11px;cursor:pointer;padding:2px 0">▼ Ver todos (${items.length})</button>`;
  }
  return html;
}

async function doFolderAnalysis() {
  const path = document.getElementById('folder-analysis-path').value.trim();
  const el   = document.getElementById('folder-analysis-result');
  if (!path) { el.innerHTML = '<p class="error-msg">Introduce una ruta.</p>'; return; }
  el.innerHTML = '<p class="loading">Analizando…</p>';
  try {
    const d = await apiFetch('/api/folder-analysis?path=' + encodeURIComponent(path));
    let html = '';

    // Extensions table (usually short — no limit needed)
    if (d.extensions && d.extensions.length > 0) {
      html += '<h4 style="color:#569cd6;margin-bottom:8px">Extensiones encontradas</h4>';
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Extensión</th><th>Archivos</th><th>Categoría</th></tr></thead><tbody>';
      html += d.extensions.map(e => {
        const color = e.category === 'rom' ? '#4ec9b0' : e.category === 'unknown' ? '#f44747' : '#888';
        return `<tr><td class="mono" style="color:${color}">${_h(e.ext)}</td><td>${e.count}</td><td style="color:${color}">${_h(e.category)}</td></tr>`;
      }).join('');
      html += '</tbody></table></div>';
    }

    // CUE sets with missing BIN
    if (d.cue_missing_bin && d.cue_missing_bin.length > 0) {
      html += `<h4 style="color:#f44747;margin:16px 0 6px">&#x26D4; .cue sin .bin (${d.cue_missing_bin.length})</h4>`;
      html += _faCollapsibleList(d.cue_missing_bin, f => `<li class="mono" style="color:#ce9178;font-size:12px;padding:1px 0">${_h(f)}</li>`);
    }

    // Orphan BIN (no CUE)
    if (d.bin_orphan && d.bin_orphan.length > 0) {
      html += `<h4 style="color:#ce9178;margin:16px 0 6px">&#x26A0; .bin sin .cue (${d.bin_orphan.length})</h4>`;
      html += _faCollapsibleList(d.bin_orphan, f => `<li class="mono" style="font-size:12px;padding:1px 0">${_h(f)}</li>`);
    }

    // Formats needing conversion
    if (d.needs_conversion && d.needs_conversion.length > 0) {
      html += `<h4 style="color:#dcdcaa;margin:16px 0 6px">Formatos que necesitan soporte/conversión</h4>`;
      html += _faCollapsibleList(d.needs_conversion, e => `<li style="color:#888;font-size:12px;padding:1px 0"><code>${_h(e.ext)}</code> — ${_h(e.note)}</li>`);
    }

    if (!html) html = '<p style="color:#555">No se encontraron archivos en la carpeta.</p>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${_h(e.message)}</p>`;
  }
}

// ── ROMs no identificadas (QoL-15) ──────────────────────────────────────────
async function loadUnmatchedDiagnosis() {
  const el = document.getElementById('unmatched-result');
  if (!el) return;
  el.innerHTML = '<span style="color:#555;font-size:12px">Analizando…</span>';
  try {
    const d = await apiFetch('/api/unmatched-by-platform');
    if (d.total_unmatched === 0) {
      el.innerHTML = '<span style="color:#4ec9b0;font-size:12px">✓ Todas las ROMs escaneadas tienen coincidencia en algún catálogo DAT.</span>';
      return;
    }
    const platCount = d.platforms.length;
    let html = `<div style="margin-bottom:10px;font-size:12px;color:#ce9178;font-weight:600">${d.total_unmatched} ROM${d.total_unmatched !== 1 ? 's' : ''} sin identificar en ${platCount} plataforma${platCount !== 1 ? 's' : ''}</div>`;

    if (d.loaded_dats && d.loaded_dats.length > 0) {
      const datItems = d.loaded_dats.map(n => `<li style="color:#555">${_h(n)}</li>`).join('');
      html += `<details style="margin-bottom:12px"><summary style="cursor:pointer;color:#888;font-size:11px;user-select:none">${d.loaded_dats.length} DAT${d.loaded_dats.length !== 1 ? 's' : ''} cargados — ver lista</summary><ul style="margin:6px 0 0 16px;font-size:11px;line-height:1.8;list-style:disc">${datItems}</ul></details>`;
    } else {
      html += `<p style="color:#f48771;font-size:12px;margin-bottom:10px">&#x26A0; No hay DATs cargados. Importa catálogos DAT desde <strong>Organizar → Importar catálogos DAT</strong>.</p>`;
    }

    html += `<div style="font-size:11px;color:#555;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.8px">Plataforma · ROMs sin match · Ejemplos</div>`;
    html += d.platforms.map(p => {
      const ex = (p.examples || []).slice(0, 3).map(f => `<code style="color:#ce9178;font-size:10px;background:#1a1a1a;padding:1px 4px;border-radius:2px">${_h(f)}</code>`).join(' ');
      return `<div style="display:flex;align-items:baseline;gap:10px;padding:5px 0;border-bottom:1px solid #1e1e2e;flex-wrap:wrap">
        <span style="min-width:110px;font-size:12px;color:#d4d4d4;flex-shrink:0">${_h(p.platform)}</span>
        <span style="font-size:13px;font-weight:600;color:#ce9178;min-width:32px;flex-shrink:0">${p.count}</span>
        <span style="font-size:11px;color:#666;overflow:hidden">${ex}</span>
      </div>`;
    }).join('');

    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<span style="color:#f44747;font-size:12px">Error: ${_h(e.message)}</span>`;
  }
}

// ── RetroAchievements ────────────────────────────────────────────────────────
async function doRaCheck() {
  const btn = document.getElementById('btn-ra-check');
  btn.disabled = true;
  btn.textContent = 'Comprobando…';
  document.getElementById('ra-result').innerHTML = '';
  try {
    const d = await apiPost('/api/ra-check', {});
    if (d.error) {
      document.getElementById('ra-result').innerHTML = `<p class="error-msg">${d.error}</p>`;
      btn.disabled = false; btn.textContent = 'Comprobar compatibilidad RA';
      return;
    }
    if (d.status === 'already_running') {
      document.getElementById('ra-result').innerHTML = '<p style="color:#888;font-size:12px">Ya hay una comprobación en curso…</p>';
    }
    startPolling();
  } catch(e) {
    document.getElementById('ra-result').innerHTML = `<p class="error-msg">${e.message}</p>`;
    btn.disabled = false; btn.textContent = 'Comprobar compatibilidad RA';
  }
}

function _renderRaResult(r) {
  const el = document.getElementById('ra-result');
  if (!el) return;
  if (r.error) { el.innerHTML = `<p class="error-msg">${r.error}</p>`; return; }

  window._lastRaResult = r;

  // Populate platform filter dropdown
  const filterSel = document.getElementById('ra-platform-filter');
  if (filterSel) {
    const platforms = new Set();
    (r.alternatives || []).forEach(a => { if (a.platform) platforms.add(a.platform); });
    (r.no_support_entries || []).forEach(e => { if (e.platform) platforms.add(e.platform); });
    const prev = filterSel.value;
    filterSel.innerHTML = '<option value="">Todas las plataformas</option>';
    [...platforms].sort().forEach(p => {
      const opt = document.createElement('option');
      opt.value = p; opt.textContent = p;
      if (p === prev) opt.selected = true;
      filterSel.appendChild(opt);
    });
    const filterRow = document.getElementById('ra-filter-row');
    if (filterRow) filterRow.classList.toggle('hidden', !(platforms.size > 0));
  }

  const selectedPlatform = filterSel?.value || '';
  const filteredAlts = selectedPlatform
    ? (r.alternatives || []).filter(a => a.platform === selectedPlatform)
    : (r.alternatives || []);
  const filteredNoSupport = selectedPlatform
    ? (r.no_support_entries || []).filter(e => e.platform === selectedPlatform)
    : (r.no_support_entries || []);

  const hasAlternatives = filteredAlts.length > 0 || r.no_support_alternative > 0;
  const csvLink = r.no_support_alternative > 0
    ? `<a href="/api/ra-check.csv" download class="btn" style="margin-left:12px;font-size:12px">&#x2193; CSV (${r.no_support_alternative} juegos)</a>`
    : '';

  let html = `<div style="margin-bottom:12px;display:flex;align-items:center;flex-wrap:wrap;gap:8px">`;
  html += `<span style="color:#4ec9b0">✓ ${r.supported} con logros</span>`;
  if (r.no_support_alternative > 0)
    html += `  <span style="color:#ce9178">⚠ ${r.no_support_alternative} sin logros (alternativa disponible)</span>`;
  if (r.no_support > 0)
    html += `  <span style="color:#555">✗ ${r.no_support} sin soporte RA</span>`;
  if (r.no_md5 > 0)
    html += `  <span style="color:#555">? ${r.no_md5} sin MD5</span>`;
  if (r.platform_unknown > 0)
    html += `  <span style="color:#555">— ${r.platform_unknown} plataforma no soportada</span>`;
  html += `  <span style="color:#333">(${r.total} total)</span>`;
  html += csvLink;
  if (selectedPlatform) html += `  <span style="color:#569cd6;font-size:11px">· filtrando: ${selectedPlatform}</span>`;
  html += `</div>`;

  if (filteredNoSupport.length > 0) {
    html += `<div style="margin:12px 0;padding:10px 14px;background:#1a1a1a;border:1px solid #3a2020;border-radius:6px;display:flex;align-items:center;gap:12px;flex-wrap:wrap">`;
    html += `<span style="color:#ce5555;font-size:13px">✗ ${filteredNoSupport.length} juegos${selectedPlatform ? ' de ' + selectedPlatform : ''} sin ningún soporte de RetroAchievements</span>`;
    html += `<button class="btn danger" style="font-size:12px;padding:4px 12px" onclick="discardRaNoSupport(${filteredNoSupport.length})">`;
    html += `Mover a descartados (${filteredNoSupport.length})</button>`;
    html += `<span style="font-size:11px;color:#555">Se moverán a <code>_descartados/</code> junto a su ROM</span>`;
    html += `</div>`;
  }

  if (filteredAlts.length) {
    const totalPages = Math.ceil(filteredAlts.length / _RA_PAGE_SIZE);
    const page = Math.min(_raPage, totalPages - 1);
    const pageAlts = filteredAlts.slice(page * _RA_PAGE_SIZE, (page + 1) * _RA_PAGE_SIZE);

    html += `<div style="margin-bottom:8px;color:#ce9178;font-size:12px">`;
    html += `Estos juegos tienen una versión RA-compatible disponible:`;
    html += `</div>`;
    html += '<div style="overflow-x:auto;border:1px solid var(--border);border-radius:6px"><table style="width:100%;border-collapse:collapse"><thead><tr style="background:var(--bg-deep);">';
    html += '<th style="min-width:100px;text-align:left;padding:8px 12px">Plataforma</th>';
    html += '<th style="min-width:200px;text-align:left;padding:8px 12px">Tu archivo</th>';
    html += '<th style="min-width:200px;text-align:left;padding:8px 12px">Título RA</th>';
    html += '<th style="min-width:80px;text-align:right;padding:8px 12px">Logros</th>';
    html += '<th style="min-width:80px;text-align:right;padding:8px 12px">Puntos</th>';
    html += '<th style="min-width:140px;text-align:center;padding:8px 12px">Descargar</th>';
    html += '</tr></thead><tbody>';
    html += pageAlts.map(a => {
      return `<tr style="border-bottom:1px solid var(--border)">
      <td style="padding:8px 12px;color:var(--fg-2)">${a.platform}</td>
      <td style="padding:8px 12px;color:#ce9178;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${a.filename}">${a.filename}</td>
      <td style="padding:8px 12px"><a href="https://retroachievements.org/game/${a.ra_id}" target="_blank" style="color:#4ec9b0">${a.ra_title}</a></td>
      <td style="padding:8px 12px;text-align:right;color:#ce9178">${a.ra_achievements}</td>
      <td style="padding:8px 12px;text-align:right;color:#555">${a.ra_points}</td>
      <td style="padding:8px 12px;text-align:center;gap:4px;display:flex;justify-content:center">
        <button class="btn" style="font-size:10px;padding:2px 7px" onclick="_openArchiveOrg('${a.ra_title.replace(/'/g, "\\'")}', '${a.platform}')" title="Abrir en Archive.org">🔗</button>
        <button class="btn" style="font-size:10px;padding:2px 7px" onclick="_copyArchiveOrgLink('${a.ra_title.replace(/'/g, "\\'")}', '${a.platform}')" title="Copiar link de Archive.org">📋</button>
      </td>
    </tr>`;
    }).join('');
    html += '</tbody></table></div>';

    if (totalPages > 1) {
      html += `<div style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12px">`;
      html += `<button class="btn" style="padding:2px 10px" ${page <= 0 ? 'disabled' : `onclick="_raGoToPage(${page - 1})"`}>&#8592;</button>`;
      html += `<span style="color:#888">Pág. ${page + 1} de ${totalPages} (${filteredAlts.length} total)</span>`;
      html += `<button class="btn" style="padding:2px 10px" ${page >= totalPages - 1 ? 'disabled' : `onclick="_raGoToPage(${page + 1})"`}>&#8594;</button>`;
      html += `</div>`;
    }
  }

  el.innerHTML = html;
}

let _raPage = 0;
const _RA_PAGE_SIZE = 25;
function filterRaByPlatform() {
  _raPage = 0;
  if (window._lastRaResult) _renderRaResult(window._lastRaResult);
}
function _raGoToPage(n) { _raPage = n; if (window._lastRaResult) _renderRaResult(window._lastRaResult); }
function _copyText(text) {
  navigator.clipboard?.writeText(text).then(() => showToast('Copiado', 'ok')).catch(() => {});
}
function _googleQuery(raTitle, platform) {
  return `"${raTitle}" download`;
}
function _archiveOrgUrl(raTitle, platform) {
  const query = encodeURIComponent(`"${raTitle}" download`);
  return `https://archive.org/search.php?query=${query}`;
}
function _openArchiveOrg(raTitle, platform) {
  const url = _archiveOrgUrl(raTitle, platform);
  window.open(url, '_blank');
}
function _copyArchiveOrgLink(raTitle, platform) {
  const url = _archiveOrgUrl(raTitle, platform);
  _copyToClipboard(url);
}

async function discardRaNoSupport(count) {
  if (!confirm(`¿Mover ${count} juegos sin soporte RA a la carpeta _descartados/? Esta acción es reversible (los archivos no se eliminan permanentemente).`)) return;
  try {
    const d = await apiPost('/api/ra-check/discard-no-support', {});
    if (d.error) { showToast(d.error, true); return; }
    let msg = `✓ ${d.discarded} juego${d.discarded !== 1 ? 's' : ''} movido${d.discarded !== 1 ? 's' : ''} a _descartados/`;
    if (d.failed) msg += ` — ${d.failed} errores`;
    showToast(msg, d.failed > 0);
    // Refresh the RA result to remove the discard button
    const el = document.getElementById('ra-result');
    if (el && d.discarded > 0) {
      const note = document.createElement('p');
      note.style.cssText = 'color:#4ec9b0;font-size:12px;margin-top:8px';
      note.textContent = msg + '. Ejecuta un nuevo scan para actualizar la biblioteca.';
      el.querySelector('div')?.after(note);
      el.querySelector('button.danger')?.closest('div')?.remove();
    }
  } catch(e) { showToast('Error al descartar juegos: ' + e.message, true); }
}

// ── Scraper ──────────────────────────────────────────────────────────────────
async function loadScraperSummary() {
  const el = document.getElementById('scraper-summary');
  if (!el) return;
  try {
    const d = await apiFetch('/api/scrape-summary?t=' + Date.now());
    if (!d.platforms || d.platforms.length === 0) {
      el.innerHTML = '<p class="empty">No hay datos. Ejecuta un scan primero.</p>';
      return;
    }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Total ROMs</th><th>Scrapeados</th><th>Pendientes</th></tr></thead><tbody>';
    html += d.platforms.map(p => {
      const pct = p.total > 0 ? Math.round(p.scraped / p.total * 100) : 0;
      const color = p.missing === 0 ? '#4ec9b0' : p.scraped > 0 ? '#ce9178' : '#555';
      return `<tr>
        <td>${p.platform}</td>
        <td style="text-align:right">${p.total}</td>
        <td style="text-align:right;color:${color}">${p.scraped} (${pct}%)</td>
        <td style="text-align:right;color:${p.missing > 0 ? '#f44747' : '#555'}">${p.missing || '—'}</td>
      </tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function loadSsQuota() {
  const label = document.getElementById('ss-quota-label');
  const bar   = document.getElementById('ss-quota-bar');
  const fill  = document.getElementById('ss-quota-fill');
  if (!label) return;
  try {
    const d = await apiFetch('/api/ss-quota');
    const today = parseInt(d.requests_today) || 0;
    const max   = parseInt(d.max_requests_per_day) || 0;
    const hasDev = d.has_dev_account;
    if (!today && !max) {
      label.textContent = hasDev
        ? 'Cuenta dev detectada (~3 req/s). Realiza un scraping para ver cuota.'
        : 'Realiza un scraping para ver la cuota.';
      _txtCls(label, hasDev ? 'txt-ok' : 'txt-dim');
      if (bar) bar.classList.add('hidden');
      return;
    }
    const pct = max > 0 ? Math.min(100, Math.round(today / max * 100)) : 0;
    const color = pct > 90 ? '#f44747' : pct > 70 ? '#ce9178' : '#4ec9b0';
    label.textContent = `${today.toLocaleString()} / ${max.toLocaleString()} peticiones hoy (${pct}%)${hasDev ? ' · Cuenta dev ✓' : ''}`;
    label.style.color = color;
    if (bar) { bar.classList.remove('hidden'); }
    if (fill) { fill.style.background = color; fill.style.width = pct + '%'; }
  } catch(e) {
    if (label) { label.textContent = 'No disponible'; _txtCls(label, 'txt-dim'); }
  }
}

async function loadScrapePlatforms() {
  const sel = document.getElementById('scrape-platform');
  if (!sel) return;
  try {
    const d = await apiFetch('/api/games/filter-options');
    const current = sel.value;
    // Keep "all" option, rebuild the rest
    sel.innerHTML = '<option value="">Todas las plataformas</option>';
    (d.platforms || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      sel.appendChild(opt);
    });
    if (current) sel.value = current;
  } catch (_) {}
}

async function doScrape() {
  const btn = document.getElementById('btn-scrape');
  const resultEl = document.getElementById('job-result-scrape');
  btn.disabled = true;
  btn.textContent = 'Scraping…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/scrape', {
      platform: document.getElementById('scrape-platform').value || null,
      limit:    parseInt(document.getElementById('scrape-limit').value) || 0,
      images:   document.getElementById('scrape-images').checked,
    });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un scraping en curso…';
      btn.disabled = false;
      btn.textContent = 'Iniciar scraping';
      return;
    }
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      btn.disabled = false;
      btn.textContent = 'Iniciar scraping';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Iniciar scraping';
  }
}

async function doExportGamelists() {
  const resultEl = document.getElementById('gamelist-result');
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/export-gamelists', {
      output_dir: document.getElementById('gamelist-output-dir').value.trim() || null,
      platform:   document.getElementById('gamelist-platform').value.trim() || null,
    });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    resultEl.className = 'job-result visible success';
    if (d.written.length === 0) {
      resultEl.textContent = 'No hay metadatos scrapeados para exportar.';
    } else {
      const esNote = d.es_detected ? '\n✔ EmulationStation detectado — gamelist.xml también escrito en ~/.emulationstation/gamelists/' : '';
      resultEl.textContent = d.written.map(w => `${w.platform}: ${w.entries} entradas → ${w.path}`).join('\n') + esNote;
      resultEl.style.whiteSpace = 'pre';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

async function doJunkScan() {
  const path = document.getElementById('junk-path')?.value.trim();
  if (!path) { alert('Introduce una ruta.'); return; }
  const el  = document.getElementById('junk-result');
  const btn = document.getElementById('btn-junk-scan');
  el.innerHTML = '<p class="loading">Escaneando…</p>';
  btn.disabled = true;
  try {
    const d = await apiFetch('/api/junk-scan?path=' + encodeURIComponent(path));
    if (d.error) { el.innerHTML = `<p class="error-msg">${_h(d.error)}</p>`; return; }
    if (!d.categories || d.categories.length === 0) {
      el.innerHTML = '<p style="color:#4ec9b0">No se encontraron archivos basura. ✓</p>';
      return;
    }
    let html = `<p style="color:#888;margin-bottom:12px;font-size:12px">
      <strong style="color:#f44747">${d.total_junk_files}</strong> archivos basura detectados —
      <strong style="color:#f44747">${fmtSize(d.total_junk_bytes)}</strong> en total
      &nbsp;·&nbsp; <label style="color:#888"><input type="checkbox" id="junk-select-all" onchange="junkSelectAll(this.checked)"> Seleccionar todos</label>
    </p>`;
    d.categories.forEach(cat => {
      const catId = 'junk-cat-' + cat.category.replace(/\\W+/g, '_');
      html += '<div style="margin-bottom:10px">'
        + '<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#1a1a2e;border-radius:4px;cursor:pointer" onclick="junkToggleCat(\'' + catId + '\')">'
        + '<input type="checkbox" class="junk-cat-cb" data-cat="' + catId + '" onchange="junkCatCheck(this,\'' + catId + '\')" onclick="event.stopPropagation()">'
        + '<span style="flex:1;color:#d4d4d4;font-size:12px"><strong>' + _h(cat.category) + '</strong> — ' + cat.count + ' archivos — ' + fmtSize(cat.total_bytes) + '</span>'
        + '<span style="color:#555;font-size:11px">▼</span>'
        + '</div>'
        + '<div id="' + catId + '" style="display:none;padding:4px 0 4px 20px">'
        + cat.files.map(f =>
            '<div style="display:flex;align-items:center;gap:8px;padding:2px 0;font-size:11px">'
            + '<input type="checkbox" class="junk-file-cb junk-cb-' + catId + '" data-path="' + f.full_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;') + '">'
            + '<span style="flex:1;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + _h(f.path) + '">' + _h(f.path) + '</span>'
            + '<span style="color:#555;flex-shrink:0">' + fmtSize(f.size_bytes) + '</span>'
            + '</div>'
          ).join('')
        + (cat.count > 50 ? '<p style="color:#555;font-size:11px">… y ' + (cat.count - 50) + ' más no mostrados</p>' : '')
        + '</div></div>';
    });
    html += '<div style="margin-top:16px;display:flex;gap:8px">'
      + '<button class="btn" onclick="doJunkDelete(true)" style="color:#dcdcaa">Dry-run (previsualizar)</button>'
      + '<button class="btn danger" onclick="doJunkDelete(false)">Eliminar seleccionados</button>'
      + '</div>'
      + '<div id="junk-delete-result" style="margin-top:10px"></div>';
    el.innerHTML = html;
    localStorage.setItem('tool_path_junk', path);
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${_h(e.message)}</p>`;
  } finally {
    btn.disabled = false;
  }
}

function junkToggleCat(catId) {
  const el = document.getElementById(catId);
  if (el) el.classList.toggle('hidden', !(el.classList.contains('hidden')));
}

function junkSelectAll(checked) {
  document.querySelectorAll('.junk-file-cb').forEach(cb => cb.checked = checked);
  document.querySelectorAll('.junk-cat-cb').forEach(cb => cb.checked = checked);
}

function junkCatCheck(catCb, catId) {
  document.querySelectorAll('.junk-cb-' + catId).forEach(cb => cb.checked = catCb.checked);
}

async function doJunkDelete(dryRun) {
  const selected = Array.from(document.querySelectorAll('.junk-file-cb:checked')).map(cb => cb.dataset.path);
  if (selected.length === 0) { alert('Selecciona al menos un archivo.'); return; }
  if (!dryRun && !confirm('¿Eliminar ' + selected.length + ' archivo(s) del disco?\\n\\nEsta operación no se puede deshacer.')) return;
  const resEl = document.getElementById('junk-delete-result');
  try {
    const d = await apiPost('/api/junk-delete', { paths: selected, dry_run: dryRun });
    const verb = dryRun ? 'Eliminaría' : 'Eliminados';
    resEl.className = 'job-result visible success';
    resEl.textContent = verb + ': ' + d.deleted + ' archivos — ' + fmtSize(d.freed_bytes) + ' liberados'
      + (d.failed > 0 ? ' | Fallidos: ' + d.failed : '');
  } catch(e) {
    resEl.className = 'job-result visible error-r';
    resEl.textContent = 'Error: ' + e.message;
  }
}

// ── Library Structure ──────────────────────────────────────────────────────────
async function createLibraryStructure() {
  const resultEl = document.getElementById('job-result-structure');
  resultEl.className = 'job-result';
  const alsoAndroid = document.getElementById('struct-also-android')?.checked || false;
  try {
    const d = await apiPost('/api/create-library-structure', { also_android: alsoAndroid });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    resultEl.className = 'job-result visible success';
    resultEl.innerHTML = `✓ PC: ${d.created.length} carpeta${d.created.length !== 1 ? 's' : ''} creada${d.created.length !== 1 ? 's' : ''} en <code>${d.root}</code>`;
    if (d.skipped.length > 0) resultEl.innerHTML += `<br><span style="font-size:11px;color:#555">${d.skipped.length} ya existían</span>`;
    if (d.android && d.android.root) {
      if (d.android.error) {
        resultEl.innerHTML += `<br><span style="color:#dcdcaa;font-size:11px">⚠ Android: ${d.android.error}</span>`;
      } else {
        resultEl.innerHTML += `<br><span style="color:#4ec9b0;font-size:11px">✓ Android: ${d.android.created.length} carpetas creadas en <code>${d.android.root}</code></span>`;
      }
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message + '\n\nVerifica que library_root esté configurado en Ajustes.';
  }
}

async function organizeLibrary(dryRun) {
  const resultEl = document.getElementById('job-result-structure');
  resultEl.className = 'job-result';
  if (!dryRun) {
    if (!confirm('¿Organizar la biblioteca?\n\n• ROMs → carpetas de plataforma\n• Saves → saves/\n• BIOS conocidas → bios/\n\nLas rutas en la base de datos se actualizarán. Haz una copia de seguridad si es tu primera vez.')) return;
  }
  try {
    const d = await apiPost('/api/organize-library', { dry_run: dryRun });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    const verb = dryRun ? 'Se moverían' : 'Movidos';
    const total = (d.moves_roms || 0) + (d.moves_saves || 0) + (d.moves_bios || 0);
    resultEl.className = 'job-result visible ' + (d.errors?.length ? 'error-r' : 'success');
    resultEl.innerHTML = `${verb}: <strong>${total}</strong> archivos total` +
      `<span style="color:#555;font-size:11px;margin-left:10px">ROMs: ${d.moves_roms || 0} · Saves: ${d.moves_saves || 0} · BIOS: ${d.moves_bios || 0}</span>` +
      (d.errors?.length ? `<br><span style="color:#f48771;font-size:11px">${d.errors.length} errores: ${d.errors.slice(0,3).join('; ')}</span>` : '');
    if (dryRun && d.preview?.length) {
      const rows = d.preview.slice(0, 12).map(m => {
        const tag = m.platform ? `<span style="color:#4ec9b0">${m.platform}</span>` : (m.target?.includes('/bios/') ? '<span style="color:#dcdcaa">bios</span>' : '<span style="color:#9cdcfe">save</span>');
        return `<div style="font-size:11px;color:#888;padding:1px 0"><span style="color:#ce9178">${m.filename || m.source?.split(/[\\/]/).pop()}</span> → ${tag}</div>`;
      }).join('');
      resultEl.innerHTML += '<div style="margin-top:8px">' + rows + (total > 12 ? `<div style="color:#555;font-size:11px">... y ${total - 12} más</div>` : '') + '</div>';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Library Doctor ────────────────────────────────────────────────────────────
async function doLibraryDoctor() {
  const el = document.getElementById('library-doctor-result');
  el.innerHTML = '<p style="color:#555;font-size:12px">Analizando…</p>';
  try {
    const d = await apiFetch('/api/library-doctor');
    if (d.error) { el.innerHTML = `<p class="error-msg">${_h(d.error)}</p>`; return; }
    if (d.total === 0) {
      el.innerHTML = '<p style="color:#4ec9b0;font-size:12px">&#x2713; Biblioteca sana — no se encontraron problemas.</p>';
      return;
    }
    const sev = { error: '#f44747', warning: '#ce9178', info: '#555' };
    const icon = { misplaced_rom: '&#x1F4C2;', incomplete_cue: '&#x274C;', empty_dir: '&#x1F4C1;' };
    const label = { misplaced_rom: 'ROM mal ubicado', incomplete_cue: 'Set CUE incompleto', empty_dir: 'Carpeta vacía' };
    let html = `<div style="margin-bottom:10px;display:flex;gap:12px;flex-wrap:wrap;font-size:12px">`;
    for (const [type, count] of Object.entries(d.by_type || {})) {
      html += `<span style="color:${sev[{misplaced_rom:'warning',incomplete_cue:'error',empty_dir:'info'}[type]||'info']}">${icon[type]||'·'} ${count} ${label[type]||type}</span>`;
    }
    html += `</div>`;
    html += '<div style="max-height:420px;overflow-y:auto">';
    html += '<table style="font-size:11px;width:100%;border-collapse:collapse"><thead><tr>';
    html += '<th style="text-align:left;padding:3px 6px;color:#555;border-bottom:1px solid #222">Tipo</th>';
    html += '<th style="text-align:left;padding:3px 6px;color:#555;border-bottom:1px solid #222">Archivo</th>';
    html += '<th style="text-align:left;padding:3px 6px;color:#555;border-bottom:1px solid #222">Acción sugerida</th>';
    html += '<th style="padding:3px 6px;border-bottom:1px solid #222"></th>';
    html += '</tr></thead><tbody>';
    // Store issues for action handlers (B7-7)
    window._doctorIssues = d.issues;
    for (let _di = 0; _di < d.issues.length; _di++) {
      const iss = d.issues[_di];
      const c = sev[iss.severity] || '#888';
      let actionBtn = '';
      if (iss.type === 'misplaced_rom') {
        actionBtn = `<button class="btn" style="font-size:10px;padding:2px 6px;min-height:unset" onclick="doctorMoveRom(${_di})">Mover</button>`;
      } else if (iss.type === 'empty_dir') {
        actionBtn = `<button class="btn danger" style="font-size:10px;padding:2px 6px;min-height:unset" onclick="doctorDeleteDir(${_di})">Eliminar</button>`;
      }
      html += `<tr id="doctor-row-${_di}" style="border-bottom:1px solid #1a1a1a">`;
      html += `<td style="padding:3px 6px;color:${c};white-space:nowrap">${icon[iss.type]||''} ${label[iss.type]||iss.type}</td>`;
      html += `<td style="padding:3px 6px;color:#ce9178;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(iss.path)}">${_h(iss.file)}</td>`;
      html += `<td style="padding:3px 6px;color:#555">${_h(iss.action||'')}${iss.missing_bins ? ' (' + iss.missing_bins.map(_h).join(', ') + ')' : ''}</td>`;
      html += `<td style="padding:3px 6px">${actionBtn}</td>`;
      html += `</tr>`;
    }
    html += '</tbody></table></div>';
    if (d.total > 200) html += `<p style="color:#555;font-size:11px;margin-top:6px">… y ${d.total - 200} más</p>`;
    el.innerHTML = html;
    // Mostrar/ocultar botón "Resolver todos"
    const hasActionable = d.issues.some(iss =>
      iss.type === 'misplaced_rom' || iss.type === 'empty_dir'
    );
    const resolveBtn = document.getElementById('btn-doctor-resolve-all');
    if (resolveBtn) resolveBtn.classList.toggle('hidden', !(hasActionable));
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${_h(e.message)}</p>`;
  }
}

// B7-7: Doctor action handlers
async function doctorMoveRom(idx) {
  const iss = (window._doctorIssues || [])[idx];
  if (!iss) return;
  const row = document.getElementById('doctor-row-' + idx);
  try {
    const d = await apiPost('/api/doctor-move-rom', { path: iss.path, expected_dir: iss.expected_dir });
    if (d.error) { showToast('Error: ' + d.error, 'err'); return; }
    showToast('Movido a ' + (iss.expected_dir || '').split(/[\\/]/).pop() + '/', 'ok');
    if (row) row.style.opacity = '0.3';
    const btn = row?.querySelector('button');
    if (btn) btn.disabled = true;
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

async function doctorDeleteDir(idx) {
  const iss = (window._doctorIssues || [])[idx];
  if (!iss) return;
  const row = document.getElementById('doctor-row-' + idx);
  try {
    const d = await apiPost('/api/doctor-delete-dir', { path: iss.path });
    if (d.error) { showToast('Error: ' + d.error, 'err'); return; }
    showToast('Carpeta eliminada: ' + iss.file, 'ok');
    if (row) row.style.opacity = '0.3';
    const btn = row?.querySelector('button');
    if (btn) btn.disabled = true;
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// B9-1: Doctor "Resolver todos"
async function doctorResolveAll() {
  const issues = window._doctorIssues || [];
  const actionable = issues.filter(iss =>
    iss.type === 'misplaced_rom' || iss.type === 'empty_dir'
  );
  if (!actionable.length) return;

  const btn = document.getElementById('btn-doctor-resolve-all');
  if (btn) { btn.disabled = true; btn.textContent = 'Resolviendo…'; }

  let ok = 0, errors = 0;
  for (let i = 0; i < issues.length; i++) {
    const iss = issues[i];
    const row = document.getElementById('doctor-row-' + i);
    if (iss.type === 'misplaced_rom') {
      try {
        const d = await apiPost('/api/doctor-move-rom', {
          path: iss.path, expected_dir: iss.expected_dir
        });
        if (d.error) { errors++; }
        else { ok++; if (row) row.style.opacity = '0.3'; }
      } catch { errors++; }
    } else if (iss.type === 'empty_dir') {
      try {
        const d = await apiPost('/api/doctor-delete-dir', { path: iss.path });
        if (d.error) { errors++; }
        else { ok++; if (row) row.style.opacity = '0.3'; }
      } catch { errors++; }
    }
  }

  if (btn) { btn.disabled = false; btn.textContent = '✔ Resolver todos'; }
  const msg = errors
    ? `Resueltos ${ok} issues. ${errors} con errores.`
    : `${ok} issues resueltos correctamente.`;
  showToast(msg, errors ? 'warn' : 'ok');
}

// ── Library Report ───────────────────────────────────────────────────────────
let _reportData = null;

function showReportTab(name) {
  document.querySelectorAll('.rpt-tab').forEach(t => t.classList.add('hidden'));
  document.querySelectorAll('.rpt-tab-btn').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById('rpt-tab-' + name);
  const btn = document.getElementById('rpt-tab-btn-' + name);
  if (tab) tab.classList.remove('hidden');
  if (btn) btn.classList.add('active');
}

async function generateReport() {
  const pathInput = document.getElementById('report-path');
  const path = pathInput?.value.trim() || '';
  const loadingEl  = document.getElementById('report-loading');
  const contentEl  = document.getElementById('report-content');
  const exportBtn  = document.getElementById('btn-export-report');

  if (loadingEl) loadingEl.classList.remove('hidden');
  if (contentEl) contentEl.classList.add('hidden');
  if (exportBtn) exportBtn.classList.add('hidden');

  try {
    const params = path ? '?path=' + encodeURIComponent(path) : '';
    _reportData = await apiFetch('/api/library-report' + params);

    // Warn if the filesystem path is not accessible (e.g. SD card disconnected)
    const notAccessibleBanner = document.getElementById('report-not-accessible');
    if (notAccessibleBanner) {
      if (_reportData.path_accessible === false) {
        notAccessibleBanner.classList.remove('hidden');
        notAccessibleBanner.textContent = '\u26A0 La ruta "' + (_reportData.source_path || path) + '" no est\xe1 accesible desde este PC. Los datos del informe provienen de la base de datos local (sin escaneo de disco).';
      } else {
        notAccessibleBanner.classList.add('hidden');
      }
    }

    // Inject RA data from last RA check if the report doesn't include it
    if (!_reportData.retroachievements && window._lastRaResult && !window._lastRaResult.error) {
      _reportData.retroachievements = window._lastRaResult;
    }

    _renderReportZips(_reportData);
    _renderReportPlaylists(_reportData);
    _renderReportMultidisc(_reportData);
    _renderReportOrphans(_reportData);
    _renderReportRa(_reportData);
    _renderReportChd(_reportData);

    if (contentEl) contentEl.classList.remove('hidden');
    if (exportBtn) exportBtn.classList.remove('hidden');
    showReportTab('zips');
  } catch(e) {
    const el = document.getElementById('rpt-tab-zips');
    if (el) el.innerHTML = `<p class="error-msg">${e.message}</p>`;
    if (contentEl) contentEl.classList.remove('hidden');
    showReportTab('zips');
  } finally {
    if (loadingEl) loadingEl.classList.add('hidden');
  }
}

function _rptStat(cls, text) {
  return `<span class="rpt-stat ${cls}">${text}</span>`;
}

function _renderReportZips(d) {
  const el = document.getElementById('rpt-tab-zips');
  if (!el) return;
  const z = d.zips;
  const normal    = z.files.filter(f => !f.is_disc_set);
  const discSets  = z.files.filter(f => f.is_disc_set);
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-info', z.total + ' ZIPs encontrados')}
    ${discSets.length ? _rptStat('rpt-warn', discSets.length + ' sets multi-disco (usar CHD)') : ''}
    ${normal.length   ? _rptStat('rpt-ok',   normal.length + ' ROMs comprimidos pendientes') : _rptStat('rpt-ok', 'Sin ZIPs pendientes')}
  </div>`;
  if (normal.length) {
    const totalBytes = normal.reduce((s, f) => s + f.size_bytes, 0);
    html += `<p style="color:#888;font-size:12px;margin-bottom:8px">Espacio total: ${fmtSize(totalBytes)}</p>`;
    html += '<div style="max-height:350px;overflow-y:auto;font-size:12px">';
    html += normal.map(f => `<div style="padding:2px 0;color:#d4d4d4">${f.path} <span style="color:#555">(${fmtSize(f.size_bytes)})</span></div>`).join('');
    html += '</div>';
  }
  if (discSets.length) {
    html += `<p style="color:#ce9178;font-size:11px;margin-top:12px;margin-bottom:4px">Sets multi-disco (omitidos por el extractor — usar conversor CHD):</p>`;
    html += '<div style="max-height:200px;overflow-y:auto;font-size:12px">';
    html += discSets.map(f => `<div style="padding:2px 0;color:#555">${f.path}</div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html || '<p class="empty">No hay archivos ZIP en la carpeta.</p>';
}

function _renderReportPlaylists(d) {
  const el = document.getElementById('rpt-tab-playlists');
  if (!el) return;
  const p = d.playlists;
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-info',  p.total_groups + ' grupos multi-disco')}
    ${_rptStat('rpt-ok',    p.with_m3u    + ' con playlist M3U')}
    ${p.without_m3u ? _rptStat('rpt-warn', p.without_m3u + ' sin playlist') : ''}
  </div>`;
  if (!p.groups.length) { el.innerHTML = '<p class="empty">No hay juegos multi-disco.</p>'; return; }
  html += '<div style="max-height:450px;overflow-y:auto">';
  html += p.groups.map(g => {
    const tag = g.m3u_exists
      ? `<span style="color:#4ec9b0;font-size:11px">✓ M3U</span>`
      : `<span style="color:#ce9178;font-size:11px">⚠ Sin M3U</span>`;
    return `<div style="padding:5px 0;border-bottom:1px solid #1e1e2e">
      <div style="display:flex;align-items:center;gap:8px">
        ${tag}
        <span style="color:#d4d4d4;font-size:13px">${g.base_name}</span>
        <span style="color:#555;font-size:11px">${g.disc_count} discos</span>
      </div>
      <div style="color:#555;font-size:11px;margin-top:2px;padding-left:4px">${g.discs.join(' · ')}</div>
    </div>`;
  }).join('');
  html += '</div>';
  el.innerHTML = html;
}

function _renderReportMultidisc(d) {
  const el = document.getElementById('rpt-tab-multidisc');
  if (!el) return;
  const m = d.multidisc;
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-ok',  m.groups_ok + ' sets completos')}
    ${m.groups_with_issues ? _rptStat('rpt-bad', m.groups_with_issues + ' sets con problemas') : ''}
  </div>`;
  if (!m.issues.length) {
    html += '<p style="color:#4ec9b0;font-size:12px">Todos los sets multi-disco están completos.</p>';
  } else {
    const typeLabels = { gap: 'Discos faltantes', mixed_ext: 'Extensiones mezcladas', missing_file: 'Archivo no encontrado', unmatched: 'Sin match en catálogo' };
    html += '<div style="max-height:450px;overflow-y:auto">';
    const grouped = {};
    m.issues.forEach(i => { (grouped[i.base_name] = grouped[i.base_name] || []).push(i); });
    html += Object.entries(grouped).map(([name, issues]) => `
      <div style="padding:8px 0;border-bottom:1px solid #1e1e2e">
        <div style="color:#ce9178;font-size:13px;margin-bottom:4px">${name}</div>
        ${issues.map(i => `<div style="font-size:12px;color:#888;padding:1px 0">
          <span style="color:#f44747">${typeLabels[i.issue_type] || i.issue_type}:</span> ${i.detail}
        </div>`).join('')}
      </div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

function _renderReportOrphans(d) {
  const el = document.getElementById('rpt-tab-orphans');
  if (!el) return;
  const o = d.orphans;
  let html = `<div style="margin-bottom:12px">
    ${o.total ? _rptStat('rpt-warn', o.total + ' saves huérfanos') : _rptStat('rpt-ok', 'Sin saves huérfanos')}
    ${o.total ? _rptStat('rpt-info', fmtSize(o.total_bytes) + ' recuperables') : ''}
  </div>`;
  if (!o.saves.length) { el.innerHTML = html + '<p style="color:#4ec9b0;font-size:12px">No hay saves huérfanos.</p>'; return; }
  html += '<div style="max-height:400px;overflow-y:auto;font-size:12px">';
  html += o.saves.map(s => {
    const name = s.path.split(/[\\/]/).pop();
    return `<div style="padding:2px 0;color:#888">${name} <span style="color:#555">(${fmtSize(s.size_bytes)})</span> <span style="color:#444;font-size:10px">${s.path}</span></div>`;
  }).join('');
  html += '</div>';
  el.innerHTML = html;
}

let _rptRaPage = 0;
function _rptRaGoToPage(n) { _rptRaPage = n; if (_reportData) _renderReportRa(_reportData); }
function filterRptRaByPlatform() { _rptRaPage = 0; if (_reportData) _renderReportRa(_reportData); }

function _renderReportRa(d) {
  const el = document.getElementById('rpt-tab-ra');
  if (!el) return;
  const ra = d.retroachievements;
  if (!ra) {
    el.innerHTML = `<p style="color:#555;font-size:12px">Sin datos RA — ejecuta el <em>Check RetroAchievements</em> primero y vuelve a generar el informe.</p>`;
    return;
  }
  if (ra.note) { el.innerHTML = `<p style="color:#555;font-size:12px">${ra.note}</p>`; return; }
  if (ra.error) { el.innerHTML = `<p class="error-msg">${ra.error}</p>`; return; }

  // Normalize field names (RA check uses 'filename', report may use 'our_filename')
  const alts = (ra.alternatives || []).map(a => ({
    platform: a.platform || '',
    filename: a.filename || a.our_filename || '',
    ra_title: a.ra_title || '',
    ra_id: a.ra_id || 0,
    ra_achievements: a.ra_achievements || 0,
    ra_points: a.ra_points || 0,
  }));

  // Platform filter
  const platforms = [...new Set(alts.map(a => a.platform).filter(Boolean))].sort();
  const filterId = 'rpt-ra-plat-filter';
  const prevPlat = el.querySelector('#' + filterId)?.value || '';

  let html = `<div style="margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">`;
  html += `${_rptStat('rpt-ok', ra.supported + ' con logros')}`;
  if (ra.no_support_alternative) html += _rptStat('rpt-warn', ra.no_support_alternative + ' sin logros (alt. disponible)');
  if (ra.no_support) html += _rptStat('rpt-info', ra.no_support + ' sin soporte RA');
  if (ra.no_md5) html += _rptStat('rpt-info', ra.no_md5 + ' sin MD5');
  html += `</div>`;

  if (platforms.length > 0) {
    html += `<div style="margin-bottom:10px;display:flex;align-items:center;gap:8px">`;
    html += `<label style="font-size:12px;color:#888">Plataforma:</label>`;
    html += `<select id="${filterId}" onchange="filterRptRaByPlatform()" style="font-size:12px;padding:2px 6px;background:#1e1e2e;color:#d4d4d4;border:1px solid #333;border-radius:4px">`;
    html += `<option value="">Todas</option>`;
    platforms.forEach(p => {
      html += `<option value="${p}"${p === prevPlat ? ' selected' : ''}>${p}</option>`;
    });
    html += `</select>`;
    html += `</div>`;
  }

  const selectedPlat = prevPlat;
  const filtered = selectedPlat ? alts.filter(a => a.platform === selectedPlat) : alts;

  if (filtered.length) {
    const totalPages = Math.ceil(filtered.length / _RA_PAGE_SIZE);
    const page = Math.min(_rptRaPage, totalPages - 1);
    const pageAlts = filtered.slice(page * _RA_PAGE_SIZE, (page + 1) * _RA_PAGE_SIZE);

    html += `<p style="color:#888;font-size:12px;margin-bottom:8px">Juegos con versión alternativa compatible con RA:</p>`;
    html += '<div style="overflow-x:auto;border:1px solid var(--border);border-radius:6px"><table style="width:100%;border-collapse:collapse"><thead><tr style="background:var(--bg-deep);">';
    html += '<th style="min-width:100px;text-align:left;padding:8px 12px">Plataforma</th>';
    html += '<th style="min-width:200px;text-align:left;padding:8px 12px">Tu archivo</th>';
    html += '<th style="min-width:200px;text-align:left;padding:8px 12px">Título RA</th>';
    html += '<th style="min-width:80px;text-align:right;padding:8px 12px">Logros</th>';
    html += '<th style="min-width:80px;text-align:right;padding:8px 12px">Puntos</th>';
    html += '<th style="min-width:140px;text-align:center;padding:8px 12px">Descargar</th>';
    html += '</tr></thead><tbody>';
    html += pageAlts.map(a => {
      return `<tr style="border-bottom:1px solid var(--border)">
      <td style="padding:8px 12px;color:var(--fg-2)">${a.platform}</td>
      <td style="padding:8px 12px;color:#ce9178;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${a.filename}">${a.filename}</td>
      <td style="padding:8px 12px"><a href="https://retroachievements.org/game/${a.ra_id}" target="_blank" style="color:#4ec9b0">${a.ra_title}</a></td>
      <td style="padding:8px 12px;text-align:right;color:#ce9178">${a.ra_achievements}</td>
      <td style="padding:8px 12px;text-align:right;color:#555">${a.ra_points}</td>
      <td style="padding:8px 12px;text-align:center;gap:4px;display:flex;justify-content:center">
        <button class="btn" style="font-size:10px;padding:2px 7px" onclick="_openArchiveOrg('${a.ra_title.replace(/'/g, "\\'")}', '${a.platform}')" title="Abrir en Archive.org">🔗</button>
        <button class="btn" style="font-size:10px;padding:2px 7px" onclick="_copyArchiveOrgLink('${a.ra_title.replace(/'/g, "\\'")}', '${a.platform}')" title="Copiar link de Archive.org">📋</button>
      </td>
    </tr>`;
    }).join('');
    html += '</tbody></table></div>';

    if (totalPages > 1) {
      html += `<div style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12px">`;
      html += `<button class="btn" style="padding:2px 10px" ${page <= 0 ? 'disabled' : `onclick="_rptRaGoToPage(${page - 1})"`}>&#8592;</button>`;
      html += `<span style="color:#888">Pág. ${page + 1} de ${totalPages} (${filtered.length} total)</span>`;
      html += `<button class="btn" style="padding:2px 10px" ${page >= totalPages - 1 ? 'disabled' : `onclick="_rptRaGoToPage(${page + 1})"`}>&#8594;</button>`;
      html += `</div>`;
    }

    if (ra.no_support_alternative > 0) {
      html += `<p style="margin-top:10px"><a href="/api/ra-check.csv" download class="btn" style="font-size:12px">&#x2193; CSV completo (${ra.no_support_alternative} juegos)</a></p>`;
    }
  } else if (alts.length === 0) {
    html += `<p style="color:#4ec9b0;font-size:12px">Todos los juegos escaneados son compatibles con RA.</p>`;
  }

  el.innerHTML = html;
}

function _renderReportChd(d) {
  const el = document.getElementById('rpt-tab-chd');
  if (!el) return;
  const chd = d.chd;
  if (chd?.note) { el.innerHTML = `<p style="color:#555;font-size:12px">${chd.note}</p>`; return; }
  if (chd?.error) { el.innerHTML = `<p class="error-msg">${chd.error}</p>`; return; }
  const ok   = (chd.results || []).filter(r => r.success);
  const fail = (chd.results || []).filter(r => !r.success && r.error);
  const skip = (chd.results || []).filter(r => !r.success && !r.error);
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-ok',   ok.length   + ' convertidos')}
    ${fail.length ? _rptStat('rpt-bad', fail.length + ' fallidos') : ''}
    ${skip.length ? _rptStat('rpt-info', skip.length + ' omitidos') : ''}
    ${chd.dry_run ? '<span style="color:#569cd6;font-size:11px">[DRY RUN]</span>' : ''}
  </div>`;
  if (fail.length) {
    html += '<p style="color:#f44747;font-size:12px;margin-bottom:8px">Fallos de conversión:</p>';
    html += '<div style="max-height:350px;overflow-y:auto">';
    html += fail.map(r => `<div style="padding:3px 0;border-bottom:1px solid #1e1e2e">
      <strong style="color:#d4d4d4;font-size:12px">${r.cue}</strong>
      <em style="display:block;color:#f44747;font-size:11px;margin-top:2px">${r.error}</em>
    </div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

function exportReportHtml() {
  if (!_reportData) return;
  const d = _reportData;
  const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const lines = [
    `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Informe Biblioteca — ${ts}</title>`,
    `<style>body{font-family:monospace;background:#0f0f0f;color:#d4d4d4;padding:20px;font-size:13px}`,
    `h1{color:#4ec9b0}h2{color:#888;border-bottom:1px solid #333;padding-bottom:4px}`,
    `.ok{color:#4ec9b0}.warn{color:#ce9178}.bad{color:#f44747}.dim{color:#555}</style></head><body>`,
    `<h1>Informe de biblioteca</h1><p class="dim">Generado: ${ts} | Ruta: ${d.source_path}</p>`,
    `<h2>ZIPs (${d.zips.total})</h2>`,
    d.zips.files.filter(f => !f.is_disc_set).map(f => `<div>${f.path} <span class="dim">(${fmtSize(f.size_bytes)})</span></div>`).join('') || '<p class="ok">Sin ZIPs pendientes</p>',
    `<h2>Playlists M3U</h2>`,
    d.playlists.groups.map(g => `<div>${g.m3u_exists ? '<span class="ok">✓</span>' : '<span class="warn">⚠</span>'} ${g.base_name} (${g.disc_count} discos)</div>`).join('') || '<p class="ok">Sin grupos multi-disco</p>',
    `<h2>Sets multi-disco — problemas (${d.multidisc.groups_with_issues})</h2>`,
    d.multidisc.issues.map(i => `<div class="bad">${i.base_name}: ${i.detail}</div>`).join('') || '<p class="ok">Todos los sets completos</p>',
    `<h2>Saves huérfanos (${d.orphans.total}) — ${fmtSize(d.orphans.total_bytes)}</h2>`,
    d.orphans.saves.map(s => `<div class="warn">${s.path}</div>`).join('') || '<p class="ok">Sin saves huérfanos</p>',
    // B7-8: RA section in HTML report
    (() => {
      const ra = d.ra;
      if (!ra || ra.note || ra.error) return '';
      const alts = (ra.alternatives || []);
      if (!alts.length) return '<h2>RetroAchievements</h2><p class="ok">Todos los juegos son compatibles con RA.</p>';
      const rows = alts.map(a => `<tr><td>${a.platform||''}</td><td>${a.filename||''}</td><td><a href="https://retroachievements.org/game/${a.ra_id}" style="color:#4ec9b0">${a.ra_title||''}</a></td><td style="text-align:right;color:#ce9178">${a.ra_achievements||0}</td><td style="text-align:right">${a.ra_points||0}</td></tr>`).join('');
      return `<h2>RetroAchievements — ${alts.length} con alternativa</h2><div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;font-size:12px"><thead><tr style="color:#555"><th style="text-align:left;padding:3px 6px">Plataforma</th><th style="text-align:left;padding:3px 6px">Tu archivo</th><th style="text-align:left;padding:3px 6px">Título RA</th><th style="padding:3px 6px">Logros</th><th style="padding:3px 6px">Puntos</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    })(),
    `</body></html>`,
  ];
  const blob = new Blob([lines.join('\n')], {type: 'text/html;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `informe-biblioteca-${ts.replace(/[: ]/g,'-')}.html`;
  a.click();
}

// ── Clipboard helpers ──────────────────────────────────────────────────────────
// B9-3: Copy to clipboard with fallback for HTTP contexts
function _copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
      .then(() => showToast('Copiado al portapapeles', 'ok'))
      .catch(() => _copyToClipboardFallback(text));
  } else {
    _copyToClipboardFallback(text);
  }
}

function _copyToClipboardFallback(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  ta.style.pointerEvents = 'none';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {
    document.execCommand('copy');
    showToast('Copiado al portapapeles', 'ok');
  } catch(e) {
    showToast('No se pudo copiar', 'error');
  }
  document.body.removeChild(ta);
}

// ── TV Mode (S36-1) ────────────────────────────────────────────────────────────
async function enterTvMode() {
  _tvActive = true;
  showTab('tv');
  try { await document.documentElement.requestFullscreen(); } catch(_) {}
  await loadTvGrid('', 0);
}

function exitTvMode() {
  _tvActive = false;
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {});
  }
  showTab('collection');
}

async function loadTvGrid(platform, offset) {
  try {
    const params = new URLSearchParams({
      limit: _TV_LIMIT,
      offset: offset,
      sort_by: 'canonical_title',
    });
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
  } catch(e) {
    console.error('loadTvGrid failed:', e);
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

    const coverUrl = `/api/asset-image?game_id=${g.id}`;
    tile.innerHTML = `
      <div class="tv-cover skeleton">
        <img src="${coverUrl}" alt="${g.canonical_title || ''}"
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

  // Calculate columns based on tile width (180px + 16px gap)
  _tvCols = Math.max(1, Math.round(gridEl.offsetWidth / 196));

  if (_tvGames.length > 0) {
    _tvMoveFocus(0);
  }
}

function _tvMoveFocus(idx) {
  document.querySelector('.tv-tile.tv-focused')?.classList.remove('tv-focused');
  _tvFocusIdx = Math.max(0, Math.min(idx, _tvGames.length - 1));
  const tile = document.querySelector(`.tv-tile[data-tv-idx="${_tvFocusIdx}"]`);
  if (tile) {
    tile.classList.add('tv-focused');
    tile.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  if (_tvGames[_tvFocusIdx]) {
    _updateTvInfoBar(_tvGames[_tvFocusIdx]);
  }
}

function _updateTvInfoBar(g) {
  document.getElementById('tv-info-title').textContent = g.canonical_title || '';
  document.getElementById('tv-info-platform').textContent = g.platform || '';
  const statusEl = document.getElementById('tv-info-status');
  if (statusEl) {
    statusEl.textContent = g.play_status ? `${g.play_status}` : '';
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
_initColPicker();
loadOverview();

// ── S24 init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // S25: Check PIN status on load (shows logout button in header if needed)
  loadAuthStatus();
  loadLocalUrl();
  _checkAndroidUserAgent();  // S40: show Android setup panel if on Android
  startAutoSyncPolling();

  // 24-1: Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;

    // TV mode controls (S36-1)
    if (_tvActive) {
      if (e.key === 'ArrowRight') { e.preventDefault(); _tvMoveFocus(_tvFocusIdx + 1); return; }
      if (e.key === 'ArrowLeft')  { e.preventDefault(); _tvMoveFocus(_tvFocusIdx - 1); return; }
      if (e.key === 'ArrowDown')  { e.preventDefault(); _tvMoveFocus(_tvFocusIdx + _tvCols); return; }
      if (e.key === 'ArrowUp')    { e.preventDefault(); _tvMoveFocus(_tvFocusIdx - _tvCols); return; }
      if (e.key === 'Enter')      { e.preventDefault(); openGamePanel(_tvGames[_tvFocusIdx]); return; }
      if (e.key === 'Escape')     { e.preventDefault(); exitTvMode(); return; }
    }

    if (e.key === 'Escape') {
      if (document.getElementById('game-panel')?.classList.contains('open')) { closeGamePanel(); return; }
      _closeConfirm();
      closeWizard?.();
      return;
    }
    // Don't trigger nav shortcuts when a modal is open
    const confirmOpen = !document.getElementById('confirm-modal')?.classList.contains('hidden');
    const wizardOpen  = !document.getElementById('wizard-modal')?.classList.contains('hidden');
    if (confirmOpen || wizardOpen) return;
    const k = e.key.toLowerCase();
    if (k === 't') { e.preventDefault(); enterTvMode(); return; }
    if (k === 's') { e.preventDefault(); showTab('sync'); }
    if (k === 'g') { e.preventDefault(); showTab('games'); }
    if (k === 'r') {
      e.preventDefault();
      const t = document.querySelector('.nav-item.active')?.id?.replace('nav-', '');
      if (t) showTab(t);
    }
  });
});

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || '';
  _applyTheme(current === 'dark' ? 'light' : 'dark');
}
