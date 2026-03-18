"use strict";

// Pagination state for Games tab
let gamesState = { offset: 0, limit: 100, total: 0, platform: '', status: '', root: null };
let _gamesViewMode = localStorage.getItem('games_view_mode') || 'list'; // 'list' | 'grid'
let platformsLoaded = false;

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
  const show = (id, vis) => { const el = document.getElementById(id); if (el) el.style.display = vis ? '' : 'none'; };
  show('gcol-region', prefs.region);
  show('gcol-match',  prefs.match);
  show('gcol-size',   prefs.size);
  show('gcol-sha1',   prefs.sha1);
  // Update row cells (col index: 0=platform,1=title,2=filename,3=region,4=match,5=size,6=sha1)
  const COL = { region: 3, match: 4, size: 5, sha1: 6 };
  document.querySelectorAll('#games-tbody tr').forEach(tr => {
    Object.entries(COL).forEach(([key, idx]) => {
      const td = tr.cells[idx];
      if (td) td.style.display = prefs[key] ? '' : 'none';
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
  picker.style.display = picker.style.display === 'none' ? '' : 'none';
  if (picker.style.display !== 'none') {
    // Close when clicking outside
    const close = (e) => { if (!picker.contains(e.target)) { picker.style.display = 'none'; document.removeEventListener('click', close); }};
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
let _devName = 'Consola Android';  // display name for the Android device — updated from config

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
  const activeTab = document.querySelector('nav button.active')?.id?.replace('nav-','');
  if (activeTab) {
    if (activeTab === 'games')      loadGames(0);
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
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById('tab-' + name);
  tab.classList.add('active', 'fading-in');
  tab.addEventListener('animationend', () => tab.classList.remove('fading-in'), { once: true });
  const navBtn = document.getElementById('nav-' + name);
  if (navBtn) navBtn.classList.add('active');
  else if (event?.currentTarget) event.currentTarget.classList.add('active');
  if (name === 'overview')   loadOverview();
  if (name === 'games')      { loadGames(0); _refreshTagFilter(); }
  if (name === 'plan')       loadPlan();
  if (name === 'duplicates') loadDuplicates();
  if (name === 'assets')     loadAssets();
  if (name === 'sync')       { loadSync(); loadManualBackups(); }
  if (name === 'cable')      loadCableSync();
  if (name === 'scraper')    loadScraperSummary();
  if (name === 'settings')   { loadSettings(); loadCatalogStatus(); loadSsQuota(); loadAuthStatus(); loadLocalUrl(); }
  if (name === 'tools')      { loadTools(); _initToolsContext(); }
  if (name === 'inbox')      loadInbox();
}

// ── Guide toggle (update arrow icon) ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
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
  if (!val.trim()) { results.style.display = 'none'; return; }
  _globalSearchTimer = setTimeout(async () => {
    try {
      const d = await apiFetch('/api/games?search=' + encodeURIComponent(val) + '&limit=8');
      if (!d.games || d.games.length === 0) { results.style.display = 'none'; return; }
      results.style.display = '';
      results.innerHTML = d.games.map(g => {
        const title = _h(g.canonical_title || g.original_filename);
        const gj = JSON.stringify(g).replace(/</g,'\\u003c');
        return `<div class="sr-item" onclick="document.getElementById('global-search').value='';document.getElementById('global-search-results').style.display='none';openGamePanel(${gj})">
          <img src="/api/asset-image?game_id=${g.id}" width="28" height="28" style="border-radius:3px;object-fit:cover" onerror="this.style.display='none'">
          <div><div style="color:#d4d4d4">${title}</div><div style="font-size:11px;color:#555">${_h(g.platform||'')}</div></div>
        </div>`;
      }).join('');
    } catch(e) { results.style.display = 'none'; }
  }, 200);
}
// Close global search results on outside click
document.addEventListener('click', e => {
  const wrap = document.getElementById('global-search-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const r = document.getElementById('global-search-results');
    if (r) r.style.display = 'none';
  }
});

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
  btn.style.color = isFav ? '#f9c74f' : '#555';
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
    ['Publisher',  g.publisher? _h(g.publisher): '<span style="color:#444">—</span>'],
    ['Nota',       g.rating   ? _h(g.rating)   : '<span style="color:#444">—</span>'],
    ['Tamaño',     fmtSize(g.size_bytes)],
    ['SHA1',       `<span style="color:#444;font-family:Consolas,monospace;font-size:11px">${(g.sha1||'').slice(0,10)}…</span>`],
  ];
  document.getElementById('gp-meta').innerHTML = rows.filter(([,v])=>v).map(([k,v])=>`<span class="gk">${k}</span><span class="gv">${v}</span>`).join('');
  const desc = document.getElementById('gp-desc');
  if (g.description) { desc.textContent = g.description; desc.style.display = ''; }
  else { desc.style.display = 'none'; }
  const sel = document.getElementById('gp-status-sel');
  if (sel) sel.value = g.play_status || '';
  // S30: populate notes
  const notesEl = document.getElementById('gp-notes');
  if (notesEl) {
    notesEl.value = g.notes || '';
    notesEl.style.color = g.notes ? '#d4d4d4' : '#555';
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
  document.getElementById('gp-stateshot-wrap').style.display = 'none';
  apiFetch('/api/stateshot?id=' + g.id).then(r => {
    if (r.found && r.data) {
      const img = document.getElementById('gp-stateshot');
      img.src = 'data:image/png;base64,' + r.data;
      document.getElementById('gp-stateshot-wrap').style.display = '';
    }
  }).catch(() => {});
  // S30: reset meta editor state
  const _editWrap = document.getElementById('gp-meta-edit-wrap');
  if (_editWrap) _editWrap.style.display = 'none';
  const _editToggle = document.getElementById('gp-meta-edit-toggle');
  if (_editToggle) _editToggle.style.color = '#444';
  const _scrapePreview = document.getElementById('gp-scrape-preview');
  if (_scrapePreview) _scrapePreview.style.display = 'none';
  const _gmeResult = document.getElementById('gme-result');
  if (_gmeResult) _gmeResult.textContent = '';
  // Backup history — load async
  const bkWrap = document.getElementById('gp-backups-wrap');
  if (bkWrap) {
    bkWrap.style.display = 'none';
    document.getElementById('gp-backups-list').innerHTML = '';
    apiFetch('/api/save-backups?id=' + g.id).then(r => {
      if (r.backups?.length) {
        loadSaveBackupsResult(r.backups, g.id);
        bkWrap.style.display = '';
      }
    }).catch(() => {});
  }
  // Launch button — show if retroarch configured
  const launchBtn = document.getElementById('gp-launch-btn');
  if (launchBtn) launchBtn.style.display = '';
  // Open
  document.getElementById('game-panel-overlay').classList.add('open');
  document.getElementById('game-panel').classList.add('open');
  // Load full scraped details async
  if (g.id && !g.description && !g.year) {
    apiFetch('/api/game?id=' + g.id).then(full => {
      if (full.id === _gpGameId) {
        _gpFillMeta(full);
        _gpGameId = full.id;
      }
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
  const open = wrap.style.display !== 'none';
  wrap.style.display = open ? 'none' : '';
  if (btn) btn.style.color = open ? '#444' : '#4ec9b0';
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
    if (res) { res.style.color = '#4ec9b0'; res.textContent = '✓ Guardado'; setTimeout(() => { if (res) res.textContent = ''; }, 2000); }
    // Refresh display
    if (title) document.getElementById('gp-title').textContent = title;
    apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
  } catch(e) {
    if (res) { res.style.color = '#f44747'; res.textContent = 'Error: ' + e.message; }
  }
}
async function gpScrapeSingle() {
  if (!_gpGameId) return;
  const previewEl = document.getElementById('gp-scrape-preview');
  const res = document.getElementById('gme-result');
  if (previewEl) { previewEl.style.display = ''; previewEl.innerHTML = '<span style="color:#555">Consultando ScreenScraper…</span>'; }
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
      <button onclick="document.getElementById('gp-scrape-preview').style.display='none'" style="margin-left:6px;background:none;border:1px solid #444;color:#888;padding:3px 10px;border-radius:4px;font:inherit;font-size:11px;cursor:pointer">Cancelar</button>`;
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
      if (previewEl) previewEl.style.display = 'none';
      if (res) { res.style.color = '#4ec9b0'; res.textContent = '✓ Metadatos actualizados'; setTimeout(() => { if(res) res.textContent = ''; }, 2500); }
      apiFetch('/api/game?id=' + _gpGameId).then(full => { if (full.id === _gpGameId) _gpFillMeta(full); }).catch(() => {});
    } else {
      if (res) { res.style.color = '#f44747'; res.textContent = r.error || 'Error'; }
    }
  } catch(e) {
    if (res) { res.style.color = '#f44747'; res.textContent = 'Error: ' + e.message; }
  }
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

// 24-4: confirm modal
let _confirmOkHandler = null;
function _showConfirm(title, bodyHtml, okLabel, onConfirm) {
  const modal = document.getElementById('confirm-modal');
  if (!modal) return;
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-body').innerHTML = bodyHtml;
  const okBtn = document.getElementById('confirm-ok');
  if (okBtn) okBtn.textContent = okLabel || 'Confirmar';
  _confirmOkHandler = onConfirm;
  modal.style.display = 'flex';
}
function _closeConfirm() {
  const modal = document.getElementById('confirm-modal');
  if (modal) modal.style.display = 'none';
  _confirmOkHandler = null;
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
          setupBanner.style.display = '';
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
          setupBanner.style.display = 'none';
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
        if (abDot) abDot.style.color = ab.total_games > 0 ? '#4ec9b0' : '#555';
        // D8-1: show stale badge if scan is outdated
        if (abStaleBadge) abStaleBadge.style.display = ab.stale ? '' : 'none';
        if (abScanBtn)    abScanBtn.style.display    = (ab.stale || ab.total_games === 0) ? '' : 'none';
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
      if (abStaleBadge) abStaleBadge.style.display = 'none';
      if (abScanBtn)    abScanBtn.style.display    = 'none';
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
          heroEl.style.display = '';
          heroEl.innerHTML = `<div class="hero-game" style="border-left-color:${_platHex(last.platform)};cursor:pointer" onclick="openGamePanel(${JSON.stringify(last).replace(/</g,'\\u003c')})">
            <img src="/api/asset-image?game_id=${last.id}" onerror="this.style.display='none'" alt="">
            <div class="hg-body">
              <div class="hg-label">Continuar jugando</div>
              <div class="hg-title">${_h(last.canonical_title || last.original_filename)}</div>
              <div class="hg-meta">${_platBadge(last.platform)} · ${_relTime(last.last_played_at)}</div>
            </div>
          </div>`;
        }
        // 28-2: Netflix-style horizontal scroll (up to 6 games)
        if (contScroll && contSection) {
          contSection.style.display = '';
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
        if (heroEl) heroEl.style.display = 'none';
        if (contSection) contSection.style.display = 'none';
        if (recentEl) recentEl.innerHTML = '<p style="color:#555;font-size:12px">Juega un rato y vuelve aquí.</p>';
      }
    } catch(_) {
      if (heroEl) heroEl.style.display = 'none';
      if (contSection) contSection.style.display = 'none';
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
          reportNoticeEl.style.display = '';
          reportNoticeEl.innerHTML = '<span style="color:#dcdcaa;font-size:12px">&#x1F4CA; Informe disponible — generado ' + timeStr + '</span> '
            + '<a href="/api/report/html' + (pcPath ? '?path=' + encodeURIComponent(pcPath) : '') + '" target="_blank" class="btn" style="padding:2px 8px;font-size:11px;margin-left:8px">Ver informe</a>';
        } else {
          reportNoticeEl.style.display = 'none';
        }
      }
    } catch(_) {}

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

// ── D8-P1: Setup Wizard ───────────────────────────────────────────────────────
let _wizardPollingTimer = null;

function showWizard(prefillPcPath, prefillAndroidPath) {
  const modal = document.getElementById('wizard-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  document.getElementById('wizard-page-1').style.display = '';
  document.getElementById('wizard-page-2').style.display = 'none';
  document.getElementById('wizard-page-3').style.display = 'none';
  // Pre-fill paths from config if available
  const pcInp = document.getElementById('wiz-library-root');
  if (pcInp && !pcInp.value && prefillPcPath) pcInp.value = prefillPcPath;
  const andInp = document.getElementById('wiz-android-root');
  if (andInp && !andInp.value && prefillAndroidPath) andInp.value = prefillAndroidPath;
}

function closeWizard() {
  const modal = document.getElementById('wizard-modal');
  if (modal) modal.style.display = 'none';
  localStorage.setItem('wizard_dismissed', '1');
  if (_wizardPollingTimer) { clearInterval(_wizardPollingTimer); _wizardPollingTimer = null; }
}

async function wizardAutoDetect() {
  const btn = document.getElementById('wiz-detect-btn');
  const msg = document.getElementById('wiz-detect-msg');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando\u2026'; }
  if (msg) { msg.style.display = 'none'; }
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
      msg.style.display = '';
    }
  } catch(e) {
    if (msg) { msg.innerHTML = '\u274C Error al detectar: ' + e.message; msg.style.display = ''; }
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
  document.getElementById('wizard-page-1').style.display = 'none';
  document.getElementById('wizard-page-2').style.display = '';
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
    document.getElementById('wizard-page-2').style.display = 'none';
    document.getElementById('wizard-page-1').style.display = '';
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
  document.getElementById('wizard-page-2').style.display = 'none';
  document.getElementById('wizard-page-3').style.display = '';
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
function goToGames(root, status, filetype) {
  gamesState.root   = root   || null;
  gamesState.status = status || '';
  gamesState.platform = '';
  gamesState.filetype = filetype || '';
  platformsLoaded = false;
  const statusSel = document.getElementById('games-matched');
  if (statusSel) statusSel.value = status || '';
  const ftSel = document.getElementById('games-filetype');
  if (ftSel && filetype !== undefined) ftSel.value = filetype || 'all';
  showTab('games');
}

// ── Job polling ───────────────────────────────────────────────────────────────
function startPolling() {
  if (_pollingTimer) return;
  _pollingTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      _applyJobStatus(s);
      if (!s.scan_running && !s.match_running && !s.sync_running && !s.convert_chd_running && !s.scrape_running && !s.extract_zip_running && !s.health_check_running && !s.ra_check_running && !s.cable_sync_running && !s.apply_running && !s.inbox_running && !s.setup_running && !s.backup_now_running) {
        clearInterval(_pollingTimer);
        _pollingTimer = null;
      }
    } catch(_) {}
  }, 2000);
}

function _applyJobStatus(s) {
  const btnScan  = document.getElementById('btn-scan');
  const btnMatch = document.getElementById('btn-match');

  if (btnScan) {
    if (s.scan_running) {
      btnScan.disabled = false;
      btnScan.textContent = 'Detener scan';
      btnScan.onclick = () => stopJob('scan');
      btnScan.classList.add('danger');
    } else {
      btnScan.disabled = false;
      btnScan.textContent = 'Scan';
      btnScan.onclick = doScan;
      btnScan.classList.remove('danger');
    }
  }
  const scanProgWrap = document.getElementById('scan-progress-wrap');
  if (scanProgWrap) {
    if (s.scan_running && s.scan_progress) {
      const p = s.scan_progress;
      scanProgWrap.style.display = '';
      const counts = document.getElementById('scan-progress-counts');
      const file   = document.getElementById('scan-progress-file');
      if (counts) counts.textContent = `${p.files_seen || 0} archivos — ${p.roms_detected || 0} ROMs`;
      if (file)   file.textContent   = p.current_file || p.current_path || '';
    } else {
      scanProgWrap.style.display = 'none';
    }
  }
  if (btnMatch) {
    if (s.match_running) {
      btnMatch.disabled = false;
      btnMatch.textContent = 'Cancelar match';
      btnMatch.onclick = () => stopJob('match');
      btnMatch.classList.add('danger');
    } else {
      btnMatch.disabled = false;
      btnMatch.textContent = 'Match catálogos';
      btnMatch.onclick = doMatch;
      btnMatch.classList.remove('danger');
    }
  }

  const btnSyncDry   = document.getElementById('btn-sync-dry');
  const btnSyncApply = document.getElementById('btn-sync-apply');
  const btnChd       = document.getElementById('btn-convert-chd');

  if (btnSyncDry)   btnSyncDry.disabled   = s.sync_running;
  if (btnSyncApply) btnSyncApply.disabled = s.sync_running;
  if (btnChd) {
    if (s.convert_chd_running) {
      btnChd.disabled = false;
      btnChd.textContent = 'Cancelar';
      btnChd.onclick = () => stopJob('convert_chd');
      btnChd.classList.add('danger');
    } else {
      btnChd.textContent = 'Convertir a CHD';
      btnChd.onclick = doConvertChd;
      btnChd.classList.remove('danger');
    }
  }

  if (!s.scan_running && s.scan_result) {
    const ts = s.scan_result.result_ts || JSON.stringify(s.scan_result);
    if (_shownResultTs.scan !== ts) {
      _shownResultTs.scan = ts;
      _showJobResult('scan', s.scan_result);
      loadOverview();
    }
  }
  if (!s.match_running && s.match_result) {
    const ts = s.match_result.result_ts || JSON.stringify(s.match_result);
    if (_shownResultTs.match !== ts) {
      _shownResultTs.match = ts;
      _showJobResult('match', s.match_result);
      loadOverview();
    }
  }
  if (!s.sync_running && s.sync_result) {
    _renderSyncResult(s.sync_result);
  }
  // CHD progress bar
  const chdWrap = document.getElementById('chd-progress-wrap');
  if (s.convert_chd_running && s.chd_progress && s.chd_progress.total > 0) {
    const p = s.chd_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (chdWrap) chdWrap.style.display = '';
    const bar = document.getElementById('chd-progress-bar');
    const lbl = document.getElementById('chd-progress-label');
    const file = document.getElementById('chd-progress-file');
    if (bar) bar.style.width = pct + '%';
    if (lbl) lbl.textContent = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.convert_chd_running) {
    if (chdWrap) chdWrap.style.display = 'none';
  }
  if (!s.convert_chd_running && s.convert_chd_result) {
    _renderChdResult(s.convert_chd_result);
  }
  // Scrape progress bar
  const scrapeWrap = document.getElementById('scrape-progress-wrap');
  const btnScrape  = document.getElementById('btn-scrape');
  if (s.scrape_running && s.scrape_progress && s.scrape_progress.total > 0) {
    const p = s.scrape_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (scrapeWrap) scrapeWrap.style.display = '';
    const bar   = document.getElementById('scrape-progress-bar');
    const lbl   = document.getElementById('scrape-progress-label');
    const found = document.getElementById('scrape-progress-found');
    const file  = document.getElementById('scrape-progress-file');
    if (bar)   bar.style.width  = pct + '%';
    if (lbl)   lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (found) found.textContent = p.found > 0 ? `✓ ${p.found} encontrados` : '';
    if (file)  file.textContent  = p.current_game;
    if (btnScrape) {
      btnScrape.disabled = false;
      btnScrape.textContent = 'Cancelar';
      btnScrape.onclick = () => stopJob('scrape');
      btnScrape.classList.add('danger');
    }
  } else if (!s.scrape_running) {
    if (scrapeWrap) scrapeWrap.style.display = 'none';
    if (btnScrape) {
      btnScrape.textContent = 'Iniciar scraping';
      btnScrape.onclick = doScrape;
      btnScrape.classList.remove('danger');
    }
  }
  if (!s.scrape_running && s.scrape_result) {
    const el = document.getElementById('job-result-scrape');
    const btn = document.getElementById('btn-scrape');
    if (el) {
      if (s.scrape_result.error) {
        el.className = 'job-result visible error-r';
        el.textContent = 'Error: ' + s.scrape_result.error;
      } else {
        el.className = 'job-result visible success';
        el.textContent = `Completado — Encontrados: ${s.scrape_result.found}  |  No encontrados: ${s.scrape_result.skipped}  (de ${s.scrape_result.total})`;
      }
    }
    if (btn) { btn.disabled = false; btn.textContent = 'Iniciar scraping'; btn.onclick = doScrape; btn.classList.remove('danger'); }
    loadScraperSummary();
  }

  // ZIP progress
  const zipWrap = document.getElementById('zip-progress-wrap');
  const btnZip  = document.getElementById('btn-extract-zip');
  if (s.extract_zip_running && s.zip_progress && s.zip_progress.total > 0) {
    const p = s.zip_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (zipWrap) zipWrap.style.display = '';
    const bar  = document.getElementById('zip-progress-bar');
    const lbl  = document.getElementById('zip-progress-label');
    const file = document.getElementById('zip-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.extract_zip_running) {
    if (zipWrap) zipWrap.style.display = 'none';
  }
  if (btnZip) {
    if (s.extract_zip_running) {
      btnZip.disabled = false;
      btnZip.textContent = 'Cancelar';
      btnZip.onclick = () => stopJob('extract_zip');
      btnZip.classList.add('danger');
    } else {
      btnZip.textContent = 'Descomprimir ZIPs';
      btnZip.onclick = doExtractZip;
      btnZip.classList.remove('danger');
    }
  }
  if (!s.extract_zip_running && s.extract_zip_result) {
    const el = document.getElementById('job-result-extract-zip');
    const r  = s.extract_zip_result;
    if (el) {
      if (r.error) {
        el.className = 'job-result visible error-r';
        el.textContent = 'Error: ' + r.error;
      } else {
        const verb = r.dry_run ? 'Extraería' : 'Extraídos';
        const discMsg = r.disc_sets > 0 ? `  |  Sets multi-disco (omitidos): ${r.disc_sets}` : '';
        el.className = 'job-result visible success';
        const scanBtn = (!r.dry_run && r.extracted > 0) ? ` <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:8px" onclick="quickScanPC()">Escanear ahora</button>` : '';
        el.innerHTML = `${verb}: ${r.extracted}  |  Omitidos: ${r.skipped}  |  Fallidos: ${r.failed}${discMsg}${scanBtn}`;
      }
      const div = document.getElementById('zip-results');
      if (div && r.results?.length) {
        div.innerHTML = r.results.map(x => {
          const isDisc = x.is_disc_set;
          const color = x.success ? '#4ec9b0' : (isDisc ? '#569cd6' : (x.skipped_reason ? '#888' : '#f44747'));
          const tag   = x.success ? (r.dry_run ? 'PREVIEW' : 'OK') : (isDisc ? 'DISC' : (x.skipped_reason ? 'SKIP' : 'FAIL'));
          const msg   = x.skipped_reason || x.error || (x.extracted.length ? '→ ' + x.extracted.join(', ') : '');
          return `<div style="font-size:12px;color:${color};padding:2px 0">[${tag}] ${x.zip}${msg ? ' — ' + msg : ''}</div>`;
        }).join('');
      }
    }
    if (btnZip) { btnZip.disabled = false; btnZip.textContent = 'Descomprimir ZIPs'; }
    // D8-P1: auto-scan after ZIP extraction
    if (!s.extract_zip_running && s.extract_zip_result && !s.extract_zip_result.dry_run && s.extract_zip_result.extracted > 0) {
      const _zipR = s.extract_zip_result;
      const _zipTs = _zipR.result_ts || JSON.stringify(_zipR);
      if (!window._autoScanAfterZipTs || window._autoScanAfterZipTs !== _zipTs) {
        window._autoScanAfterZipTs = _zipTs;
        setTimeout(() => {
          showToast('ZIPs extraidos. Lanzando escaneo automatico...', 'ok');
          quickScanPC();
        }, 1500);
      }
    }
  }

  // Health check progress
  const healthWrap = document.getElementById('health-progress-wrap');
  const btnHealth  = document.getElementById('btn-health-check');
  if (s.health_check_running && s.health_progress && s.health_progress.total > 0) {
    const p = s.health_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (healthWrap) healthWrap.style.display = '';
    const bar  = document.getElementById('health-progress-bar');
    const lbl  = document.getElementById('health-progress-label');
    const file = document.getElementById('health-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.health_check_running) {
    if (healthWrap) healthWrap.style.display = 'none';
  }
  if (btnHealth) {
    if (s.health_check_running) {
      btnHealth.disabled = false;
      btnHealth.textContent = 'Cancelar';
      btnHealth.onclick = () => stopJob('health_check');
      btnHealth.classList.add('danger');
    } else {
      btnHealth.textContent = 'Iniciar Health Check';
      btnHealth.onclick = doHealthCheck;
      btnHealth.classList.remove('danger');
    }
  }
  if (!s.health_check_running && s.health_check_result) {
    _renderHealthResult(s.health_check_result);
    if (btnHealth) { btnHealth.disabled = false; btnHealth.textContent = 'Iniciar Health Check'; btnHealth.onclick = doHealthCheck; btnHealth.classList.remove('danger'); }
  }

  // RA check progress
  const raWrap  = document.getElementById('ra-progress-wrap');
  const btnRa   = document.getElementById('btn-ra-check');
  if (s.ra_check_running && s.ra_progress && s.ra_progress.total > 0) {
    const p = s.ra_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (raWrap) raWrap.style.display = '';
    const bar  = document.getElementById('ra-progress-bar');
    const lbl  = document.getElementById('ra-progress-label');
    const file = document.getElementById('ra-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.ra_check_running) {
    if (raWrap) raWrap.style.display = 'none';
  }
  if (btnRa) {
    if (s.ra_check_running) {
      btnRa.disabled = false;
      btnRa.textContent = 'Cancelar';
      btnRa.onclick = () => stopJob('ra_check');
      btnRa.classList.add('danger');
    } else {
      btnRa.textContent = 'Comprobar compatibilidad RA';
      btnRa.onclick = doRaCheck;
      btnRa.classList.remove('danger');
    }
  }
  if (!s.ra_check_running && s.ra_check_result) {
    _renderRaResult(s.ra_check_result);
    if (btnRa) { btnRa.disabled = false; btnRa.textContent = 'Comprobar compatibilidad RA'; btnRa.onclick = doRaCheck; btnRa.classList.remove('danger'); }
  }

  // Cable sync
  const btnCable = document.getElementById('btn-cable-sync');
  const cableWrap = document.getElementById('cable-progress-wrap');
  if (s.cable_sync_running && s.cable_progress) {
    const p = s.cable_progress;
    if (cableWrap) cableWrap.style.display = '';
    const lbl  = document.getElementById('cable-progress-label');
    const file = document.getElementById('cable-progress-file');
    const bar  = document.getElementById('cable-progress-bar');
    const bytesCopied = p.bytes_copied || 0;
    const bytesTotal  = p.bytes_total  || 0;
    const speedBps    = p.speed_bps    || 0;
    const pct = bytesTotal > 0 ? Math.min(100, Math.round(bytesCopied / bytesTotal * 100)) : null;
    const etaSec = (speedBps > 0 && bytesTotal > bytesCopied) ? Math.round((bytesTotal - bytesCopied) / speedBps) : null;
    const etaStr = etaSec !== null ? (etaSec < 60 ? `${etaSec}s` : `${Math.round(etaSec/60)}min`) : '';
    const speedStr = speedBps > 0 ? `${(speedBps / 1048576).toFixed(1)} MB/s` : '';
    const lblText = bytesTotal > 0
        ? `${fmtSize(bytesCopied)} / ${fmtSize(bytesTotal)} (${p.copied || 0} archivos)${speedStr ? ' — ' + speedStr : ''}${etaStr ? ' — ETA: ' + etaStr : ''}`
        : `Copiados: ${p.copied || 0}`;
    if (lbl)  lbl.textContent  = lblText;
    if (file) file.textContent = p.current_file || '';
    if (bar) {
        if (pct !== null) {
            bar.style.width = pct + '%';
        } else {
            bar.style.width = (((p.copied || 0) * 7) % 80 + 10) + '%';
        }
    }
    // Mutate button to Cancelar
    if (btnCable) {
        btnCable.disabled = false;
        btnCable.textContent = 'Cancelar';
        btnCable.onclick = () => stopJob('cable_sync');
        btnCable.classList.add('danger');
    }
  } else if (!s.cable_sync_running) {
    if (cableWrap) cableWrap.style.display = 'none';
    if (btnCable) {
        btnCable.textContent = 'Iniciar sincronización';
        btnCable.onclick = doCableSync;
        btnCable.classList.remove('danger');
    }
  }
  if (!s.cable_sync_running && s.cable_sync_result) {
    _renderCableSyncResult(s.cable_sync_result);
  }
  // Backup now
  const btnBkNow = document.getElementById('btn-backup-now');
  if (s.backup_now_running) {
    if (btnBkNow) { btnBkNow.disabled = true; btnBkNow.textContent = 'Haciendo backup…'; }
  } else {
    if (btnBkNow) { btnBkNow.disabled = false; btnBkNow.textContent = 'Hacer backup ahora'; }
  }
  if (!s.backup_now_running && s.backup_now_result) {
    const ts = s.backup_now_result.result_ts || JSON.stringify(s.backup_now_result);
    if (_shownResultTs.backup_now !== ts) {
      _shownResultTs.backup_now = ts;
      const el = document.getElementById('job-result-backup-now');
      const r  = s.backup_now_result;
      if (el) {
        if (r.error) { el.className = 'job-result visible error-r'; el.textContent = 'Error: ' + r.error; }
        else { const sz = r.size > 1048576 ? (r.size/1048576).toFixed(1)+' MB' : (r.size/1024).toFixed(1)+' KB'; el.className = 'job-result visible success'; el.textContent = `Backup completado — ZIP: ${sz}`; }
      }
      loadManualBackups();
    }
  }
  // Inbox progress
  _applyInboxProgress(s);
}

function _showJobResult(type, result) {
  const el = document.getElementById('job-result-' + type);
  if (!el) return;
  if (result.error) {
    el.className = 'job-result visible error-r';
    el.textContent = 'Error: ' + result.error;
  } else if (type === 'scan') {
    el.className = 'job-result visible success';
    const prunedMsg = result.pruned > 0 ? `  |  Eliminados de BD: ${result.pruned}` : '';
    const srcMsg = result.source === 'adb' ? ` [ADB — ${result.android_path}]` : '';
    // If ADB scan, store the android path so the Overview Anbernic column filters by it
    if (result.source === 'adb' && result.android_path) {
      localStorage.setItem('anbernic_adb_path', result.android_path);
      // Also pre-fill the ov-ab-path field so stats show immediately
      const abInput = document.getElementById('ov-ab-path');
      if (abInput && !abInput.value) abInput.value = result.android_path;
    }
    el.textContent = `Scan completado${srcMsg} — ROMs: ${result.roms_detected}  |  Ya escaneados: ${result.roms_skipped}  |  Saves: ${result.saves_detected}  |  Errores: ${result.errors}${prunedMsg}`;
    showToast(`Scan completado — ${result.roms_detected} ROMs${result.errors ? ', ' + result.errors + ' errores' : ''}`, result.errors ? 'err' : 'ok');
  } else if (type === 'match') {
    el.className = 'job-result visible success';
    el.textContent = `Match completado — SHA1: ${result.matched_high}  |  Nombre: ${result.matched_low}  |  Sin match: ${result.unmatched}  (de ${result.total} ROMs)`;
  } else if (type === 'convert-chd') {
    el.className = 'job-result visible success';
    const verb = result.dry_run ? 'Convertiría' : 'Convertidos';
    el.textContent = `${verb}: ${result.converted}  |  Omitidos: ${result.skipped}  |  Fallidos: ${result.failed}`;
  }
}

// ── ADB scan helpers ──────────────────────────────────────────────────────────
function _onScanAdbChange() {
  const cb  = document.getElementById('scan-include-adb');
  const box = document.getElementById('scan-adb-options');
  if (box) box.style.display = cb?.checked ? '' : 'none';
}

async function detectAdbDevicesForScan() {
  const sel    = document.getElementById('scan-adb-device');
  const status = document.getElementById('scan-adb-status');
  if (status) { status.style.color = '#555'; status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) { if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + d.error; } return; }
    if (!d.devices?.length) {
      if (status) { status.style.color = '#ce9178'; status.textContent = `No se encontraron dispositivos — conecta la ${_devName} y activa Depuración USB`; }
      return;
    }
    if (sel) {
      sel.innerHTML = d.devices.map(dev =>
        `<option value="${dev.serial}" ${!dev.ready ? 'disabled' : ''}>${dev.display}${!dev.ready ? ' [NO LISTO]' : ''}</option>`
      ).join('');
      const ready = d.devices.find(dv => dv.ready);
      if (ready) sel.value = ready.serial;
    }
    const readyCount = d.devices.filter(dv => dv.ready).length;
    if (status) {
      status.style.color = readyCount ? '#4ec9b0' : '#ce9178';
      status.textContent = readyCount ? `✓ ${readyCount} dispositivo(s) listo(s)` : `⚠ Acepta el diálogo de depuración USB en la ${_devName}`;
    }
  } catch(e) { if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + e.message; } }
}

// ── Scan action ───────────────────────────────────────────────────────────────
async function doScan() {
  const includePc  = document.getElementById('scan-include-pc')?.checked;
  const includeAb  = document.getElementById('scan-include-ab')?.checked;
  const includeAdb = document.getElementById('scan-include-adb')?.checked;
  const pcPath = document.getElementById('ov-pc-path')?.value.trim() || '';
  const abPath = document.getElementById('ov-ab-path')?.value.trim() || '';
  const sourcePaths = [];
  if (includePc && pcPath) sourcePaths.push(pcPath);
  if (includeAb && abPath) sourcePaths.push(abPath);

  // ADB scan runs separately
  if (includeAdb) {
    const serial      = document.getElementById('scan-adb-device')?.value.trim();
    const androidPath = document.getElementById('scan-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    const resultEl = document.getElementById('job-result-scan');
    const btn      = document.getElementById('btn-scan');
    btn.disabled = true; btn.textContent = 'Escaneando ADB…';
    resultEl.className = 'job-result';
    try {
      const d = await apiPost('/api/adb-scan', { adb_serial: serial, android_path: androidPath });
      if (d.status === 'already_running') {
        resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay un scan en curso…';
        btn.disabled = false; btn.textContent = 'Scan'; return;
      }
      // Also run FS scan if any FS paths selected
      if (sourcePaths.length > 0) {
        await apiPost('/api/scan', { source_paths: sourcePaths, quick: document.getElementById('scan-quick')?.checked || false });
      }
      startPolling();
    } catch(e) {
      btn.disabled = false; btn.textContent = 'Scan';
      resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message;
    }
    return;
  }

  if (sourcePaths.length === 0) {
    alert('Configura al menos una ruta en el panel "Rutas" y activa el checkbox correspondiente.');
    return;
  }
  const btn = document.getElementById('btn-scan');
  btn.disabled = true;
  btn.textContent = 'Escaneando…';
  const resultEl = document.getElementById('job-result-scan');
  resultEl.className = 'job-result';

  try {
    const quick = document.getElementById('scan-quick')?.checked || false;
    const d = await apiPost('/api/scan', { source_paths: sourcePaths, quick });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un scan en curso…';
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Scan';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// Quick scan of the PC library root — triggered from Cable Sync / ZIP result buttons
async function quickScanPC() {
  const cfg = await apiFetch('/api/config').catch(() => ({}));
  const pcPath = document.getElementById('ov-pc-path')?.value.trim() || cfg.library_root || '';
  if (!pcPath) { alert('Configura la ruta del PC en Overview primero.'); return; }
  try {
    const d = await apiPost('/api/scan', { source_paths: [pcPath], quick: false });
    if (d.status === 'already_running') { showToast('Scan ya en curso…', 'ok'); return; }
    showToast('Scan iniciado — espera a que termine', 'ok');
    showTab('overview');
    startPolling();
  } catch(e) {
    alert('Error al lanzar scan: ' + e.message + '\n\nConsulta los logs para más detalles.');
  }
}

// D8-1: Quick scan of the Android device library root
async function quickScanAndroid() {
  const abPath = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '';
  if (!abPath) { alert('Configura la ruta de la consola Android en Overview primero.'); return; }
  try {
    const d = await apiPost('/api/scan', { source_paths: [abPath], quick: false });
    if (d.status === 'already_running') { showToast('Scan ya en curso…', 'ok'); return; }
    showToast('Scan de consola Android iniciado…', 'ok');
    showTab('overview');
    startPolling();
  } catch(e) {
    alert('Error al lanzar scan: ' + e.message + '\n\nConsulta los logs para más detalles.');
  }
}

// ── Fix platforms action ─────────────────────────────────────────────────────
async function doFixPlatforms() {
  const btn = document.getElementById('btn-fix-platforms');
  const resultEl = document.getElementById('job-result-fix-platforms');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/fix-platforms', {});
    resultEl.className = 'job-result visible success';
    resultEl.textContent = `Plataformas actualizadas: ${d.updated} juegos`;
    loadOverview();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Fix plataformas';
  }
}

// ── Match action ──────────────────────────────────────────────────────────────
async function doMatch() {
  const btn = document.getElementById('btn-match');
  btn.disabled = true;
  btn.textContent = 'Matching…';
  const resultEl = document.getElementById('job-result-match');
  resultEl.className = 'job-result';

  try {
    const d = await apiPost('/api/match', {});
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un match en curso…';
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Match catálogos';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
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
  loadGames(0);
}
function toggleFavoritesFilter() {
  const btn = document.getElementById('btn-filter-favorites');
  if (!btn) return;
  gamesState.favorite = !gamesState.favorite;
  btn.style.color = gamesState.favorite ? '#f9c74f' : '#888';
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
  if (_listV) _listV.style.display = _gamesViewMode === 'list' ? '' : 'none';
  if (_gridV) _gridV.style.display = _gamesViewMode === 'grid' ? '' : 'none';
  if (_btnL)  _btnL.classList.toggle('active', _gamesViewMode === 'list');
  if (_btnG)  _btnG.classList.toggle('active', _gamesViewMode === 'grid');

  // Show active root filter if set
  const rootBanner = document.getElementById('games-root-banner');
  if (rootBanner) {
    if (gamesState.root) {
      rootBanner.style.display = 'flex';
      rootBanner.innerHTML = `<span style="color:#888;font-size:12px">Filtrando por: <code style="color:#ce9178">${gamesState.root}</code></span> <button class="btn" style="padding:2px 8px;font-size:11px" onclick="gamesState.root=null;document.getElementById('games-root-banner').style.display='none';loadGames(0)">&#x2715; Quitar filtro</button>`;
    } else {
      rootBanner.style.display = 'none';
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
      empty.style.display = '';
    }
    else {
      empty.style.display = 'none';
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
  if (listView) listView.style.display = mode === 'list' ? '' : 'none';
  if (gridView) gridView.style.display = mode === 'grid' ? '' : 'none';
  if (btnList)  btnList.classList.toggle('active', mode === 'list');
  if (btnGrid)  btnGrid.classList.toggle('active', mode === 'grid');
  // Re-render current data in the new view mode
  loadGames(gamesState.offset);
}

function _renderGamesGrid(games) {
  const grid = document.getElementById('games-grid');
  if (!grid) return;
  if (games.length === 0) { grid.innerHTML = ''; return; }
  grid.innerHTML = games.map(g => {
    const thumb = g.id
      ? `<img src="/api/asset-image?game_id=${g.id}" alt="" onerror="this.parentElement.innerHTML='<span class=gc-no-art>&#x1F3AE;</span>'">`
      : `<span class="gc-no-art">&#x1F3AE;</span>`;
    const title = _h(g.canonical_title || g.original_filename || '—');
    const accentGc = _platHex(g.platform);
    return `<div class="game-card" style="border-top:2px solid ${accentGc}30" onclick="openGamePanel(${JSON.stringify(g).replace(/</g,'\\u003c').replace(/>/g,'\\u003e')})">
      <div class="gc-thumb">${thumb}</div>
      <div class="gc-body">
        <div class="gc-title" title="${title}">${title}</div>
        <div class="gc-plat">${_platBadge(g.platform)}</div>
      </div>
    </div>`;
  }).join('');
}

// ── Plan ─────────────────────────────────────────────────────────────────────
function _chk(id, def = '1') {
  const el = document.getElementById(id);
  return el ? (el.checked ? '1' : '0') : def;
}

function toggleShaLength() {
  const label = document.getElementById('sha-length-label');
  if (label) label.style.display = document.getElementById('fmt-sha').checked ? '' : 'none';
}

function _planQueryString() {
  const shaLength = document.getElementById('fmt-sha-length')?.value || '8';
  return `?include_region=${_chk('fmt-region')}&include_revision=${_chk('fmt-revision')}` +
         `&include_platform=${_chk('fmt-platform', '0')}&include_sha=${_chk('fmt-sha', '0')}` +
         `&sha_length=${shaLength}`;
}

async function loadPlan() {
  const el = document.getElementById('plan-content');
  el.innerHTML = '<p class="loading">Cargando…</p>';
  try {
    const root = _deviceRoot();
    const rootParam = root ? `&source_root=${encodeURIComponent(root)}` : '';
    // D8-2: device filter dropdown
    const deviceFilterSel = document.getElementById('plan-device-filter');
    const _planDeviceFilter = deviceFilterSel ? deviceFilterSel.value : '';
    const [d, cfg] = await Promise.all([apiFetch('/api/plan' + _planQueryString() + rootParam), apiFetch('/api/config')]);
    const planBar = document.getElementById('plan-context-bar');
    if (planBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        const r = cfg.library_root || '(no configurado)';
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${r}</span> &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      } else if (_activeDevice === 'anbernic') {
        const r = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">${_devName} — ${r}</span> &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      } else {
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> (PC + ${_devName}) &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      }
      planBar.innerHTML = barHtml;
      planBar.style.display = '';
    }

    // Update preview bar
    const previewEl  = document.getElementById('fmt-preview');
    const previewTxt = document.getElementById('fmt-preview-text');
    const firstPending = d.pending?.[0] || d.already_correct_example;
    if (previewEl && previewTxt && d.pending.length > 0) {
      previewTxt.textContent = d.pending[0].target_name;
      previewEl.style.display = '';
    } else if (previewEl) {
      previewEl.style.display = 'none';
    }

    // ── C2: Summary bar ──────────────────────────────────────────────────────
    const summaryBar = document.getElementById('plan-summary-bar');
    if (summaryBar) {
      const pendingN   = d.pending.length;
      const conflictsN = d.conflicts.length;
      const unmatchedN = d.unmatched_count || 0;
      const correctN   = d.already_correct || 0;
      const parts = [];
      if (pendingN > 0)   parts.push(`<span style="color:#4ec9b0;font-weight:600">${pendingN}</span> <span style="color:#888">listos para renombrar</span>`);
      if (correctN > 0)   parts.push(`<span style="color:#555">${correctN} ya correctos</span>`);
      if (conflictsN > 0) parts.push(`<span style="color:#f44747;font-weight:600">${conflictsN}</span> <span style="color:#888">conflictos</span>`);
      if (unmatchedN > 0) parts.push(`<span style="color:#888">${unmatchedN} sin match en catálogo</span>`);
      summaryBar.innerHTML = parts.join('<span style="color:#333;margin:0 4px">·</span>');
      summaryBar.style.display = parts.length ? 'flex' : 'none';
    }

    // D8-2: apply device filter to pending list
    const pendingFiltered = _planDeviceFilter
      ? (d.pending || []).filter(op => op.device === _planDeviceFilter)
      : (d.pending || []);

    // ── C3: Update action buttons with counts ─────────────────────────────────
    const btnApply    = document.getElementById('btn-apply');
    const btnResolve  = document.getElementById('btn-resolve-conflicts');
    const btnResolveRa = document.getElementById('btn-resolve-ra-conflicts');
    if (btnApply) {
      const n = pendingFiltered.length;
      btnApply.textContent = n > 0 ? `Renombrar ${n} archivo${n !== 1 ? 's' : ''}` : 'Nada que renombrar';
      btnApply.disabled = n === 0;
    }
    if (btnResolve) {
      const collisions = (d.conflicts || []).filter(c => c.reason === 'collision').length;
      if (collisions > 0) {
        btnResolve.textContent = `Resolver ${collisions} colisión${collisions !== 1 ? 'es' : ''}`;
        btnResolve.style.display = '';
      } else {
        btnResolve.style.display = 'none';
      }
    }
    // D8-3: show RA resolver if there are disk conflicts
    if (btnResolveRa) {
      const diskConflictCount = (d.conflicts || []).filter(c => c.reason === 'disk').length;
      btnResolveRa.style.display = diskConflictCount > 0 ? '' : 'none';
      if (diskConflictCount > 0) btnResolveRa.textContent = 'Resolver con RA (' + diskConflictCount + ')';
    }

    if (d.total === 0) {
      if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        el.innerHTML = `<p class="empty">No hay ROMs de esta ruta en la base de datos.<br><span style="color:#888;font-size:12px">Ruta ${_devName}: <code>${ab}</code><br>Escanea la consola primero (Overview → Escanear → consola Android por ADB).</span></p>`;
      } else {
        el.innerHTML = '<p class="empty">Sin juegos con match. Ejecuta <strong>Match catálogos</strong> primero desde la pestaña Inicio.</p>';
      }
      return;
    }

    let html = '';
    if (pendingFiltered.length) {
      const savesNote = d.total_saves_affected > 0 ? ` <span style="color:#dcdcaa;font-size:11px">· ${d.total_saves_affected} save(s) se renombrarán también</span>` : '';
      const filterNote = _planDeviceFilter ? ` <span style="color:#888;font-size:11px">[filtro: ${_planDeviceFilter === 'pc' ? 'PC' : 'Consola Android'}]</span>` : '';
      html += `<h3 style="color:#569cd6;margin-bottom:12px">Listos para renombrar — ${pendingFiltered.length}${savesNote}${filterNote}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Platform</th><th>Dispositivo</th><th>From</th><th>To</th><th style="text-align:center">Saves</th></tr></thead><tbody>';
      html += pendingFiltered.map(op => {
        const devLabel = op.device === 'pc'
          ? '<span style="color:#4ec9b0;font-size:10px">PC</span>'
          : '<span style="color:#ce9178;font-size:10px">Android</span>';
        return `<tr>
          <td>${op.platform||'<span style="color:#555">Unknown</span>'}</td>
          <td>${devLabel}</td>
          <td title="${_h(op.source)}">${_h(op.source_name)}</td>
          <td style="color:#4ec9b0" title="${_h(op.target)}">${_h(op.target_name)}</td>
          <td style="text-align:center;color:${op.companion_saves > 0 ? '#dcdcaa' : '#555'}">${op.companion_saves > 0 ? op.companion_saves : '—'}</td>
        </tr>`;
      }).join('');
      html += '</tbody></table></div>';
    }
    if (d.conflicts.length) {
      const collisions = d.conflicts.filter(c => c.reason === 'collision');
      const diskConflicts = d.conflicts.filter(c => c.reason === 'disk');
      const unknown = d.conflicts.filter(c => !c.reason || (c.reason !== 'collision' && c.reason !== 'disk'));

      html += `<h3 style="color:#f44747;margin:20px 0 8px">Conflictos — ${d.conflicts.length}</h3>`;

      if (collisions.length) {
        html += `<div style="background:#1a1218;border:1px solid #3a2030;border-left:3px solid #ce9178;border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:#ce9178;font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26A0; Colisión de plan (${collisions.length}) — dos ROMs quieren el mismo nombre canónico`;
        html += `</div>`;
        html += `<div style="color:#888;font-size:11px;margin-bottom:10px">`;
        html += `Causa habitual: tienes múltiples versiones del mismo juego (regional, revisión) y la opción <strong>Región</strong> o <strong>Revisión</strong> está desactivada en el formato. Actívalas para que cada versión obtenga un nombre único.<br>`;
        html += `O usa <button class="btn" style="padding:2px 10px;font-size:11px;margin:0 4px" onclick="applyKeepBoth()">Resolver automáticamente (añadir sufijo _1 _2)</button> para aplicar ambas con nombres distintos.`;
        html += `</div>`;
        html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Nombre bloqueado</th></tr></thead><tbody>';
        html += collisions.map(op => `<tr>
          <td class="mono" style="color:#9cdcfe">${_h(op.source_name)}</td>
          <td class="mono" style="color:#ce9178">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div></div>';
      }

      if (diskConflicts.length) {
        html += `<div style="background:#1a1212;border:1px solid #3a2020;border-left:3px solid #f44747;border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:#f44747;font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26D4; Conflicto de disco (${diskConflicts.length}) — el nombre de destino ya está ocupado por un archivo diferente`;
        html += `</div>`;
        html += `<div style="color:#888;font-size:11px;margin-bottom:10px">`;
        html += `<strong style="color:#d4d4d4">¿Por qué no aparecen en la pestaña Duplicados?</strong><br>`;
        html += `La pestaña <em>Duplicados</em> solo muestra archivos con el <strong>mismo contenido exacto</strong> (mismo hash SHA1). `;
        html += `Estos conflictos son distintos: el archivo que quieres renombrar y el que ya ocupa el nombre de destino son ROMs <em>diferentes</em> (distinto contenido), `;
        html += `pero el catálogo les asigna el mismo nombre canónico — por ejemplo, <code>Super Mario Bros (E)</code> y <code>Super Mario Bros (Europe)</code> son el mismo juego con nombres distintos.<br><br>`;
        html += `<strong style="color:#d4d4d4">Qué hacer:</strong> Decide cuál de los dos quieres conservar. `;
        html += `Puedes ir a la pestaña <a href="#" style="color:#569cd6" onclick="event.preventDefault();showTab(\'duplicates\')">Duplicados →</a> para verificar si alguno es idéntico por hash. `;
        html += `Si son versiones distintas y quieres conservar ambas, activa la opción <strong>Región</strong> o <strong>Revisión</strong> en el formato (arriba) para que cada una obtenga un nombre único.`;
        html += `</div>`;
        html += `<div style="margin-bottom:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">`;
        html += `<button class="btn" style="font-size:12px;padding:4px 12px" title="Activa Región y Revisión en las opciones de formato y recalcula el plan para que cada versión obtenga un nombre único" onclick="document.getElementById('fmt-region').checked=true;document.getElementById('fmt-revision').checked=true;loadPlan()">&#x21BB; Recalcular con Región + Revisión</button>`;
        html += `<span style="color:#555;font-size:11px">Resuelve la mayoría de conflictos de disco añadiendo la región o versión al nombre</span>`;
        html += `</div>`;
        html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Destino bloqueado</th></tr></thead><tbody>';
        html += diskConflicts.map(op => `<tr>
          <td class="mono" style="color:#9cdcfe">${_h(op.source_name)}</td>
          <td class="mono" style="color:#f44747">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div></div>';
      }

      if (unknown.length) {
        html += '<div style="overflow-x:auto"><table><thead><tr><th>From</th><th>To (blocked)</th></tr></thead><tbody>';
        html += unknown.map(op => `<tr>
          <td class="mono">${_h(op.source_name)}</td>
          <td class="mono" style="color:#f44747">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div>';
      }
    }
    if (d.already_correct > 0) {
      html += `<p style="color:#555;margin-top:16px">${d.already_correct} archivo(s) ya tienen el nombre correcto.</p>`;
    }
    if (d.unmatched_count > 0) {
      html += `<details style="margin-top:20px;border:1px solid #333;border-radius:6px;padding:10px 14px;background:#161620">`;
      html += `<summary style="cursor:pointer;color:#888;font-size:13px;user-select:none">`;
      html += `${d.unmatched_count} ROM${d.unmatched_count !== 1 ? 's' : ''} sin match en catálogo (no se renombrarán) `;
      html += `— <a href="#" style="color:#569cd6;font-size:12px" onclick="event.preventDefault();goToGames(null,'unmatched')">Ver en Games →</a>`;
      html += `</summary>`;
      const _reasonLabels = {
        'no_sha1':       { text: 'sin hashear', color: '#888',    tip: 'Ejecuta un scan completo (sin Quick mode) para calcular el hash' },
        'no_dat':        { text: 'sin catálogo DAT', color: '#dcdcaa', tip: 'No se ha cargado ningún DAT para esta plataforma — haz Match catálogos primero' },
        'hash_not_found':{ text: 'hash no en DAT', color: '#ce9178', tip: 'El hash del archivo no está en ningún DAT cargado — puede ser una versión no reconocida' },
      };
      html += `<div style="margin-top:10px;overflow-x:auto"><table><thead><tr><th>Platform</th><th>Filename</th><th>Razón</th></tr></thead><tbody>`;
      html += d.unmatched.map(g => {
        const r = _reasonLabels[g.unmatched_reason] || { text: g.unmatched_reason || '?', color: '#555', tip: '' };
        const badge = `<span style="font-size:10px;color:${r.color};background:#1e1e2e;padding:1px 6px;border-radius:3px" title="${_h(r.tip)}">${_h(r.text)}</span>`;
        return `<tr>
          <td>${_platBadge(g.platform)}</td>
          <td class="mono" style="color:#9cdcfe;font-size:12px">${_h(g.original_filename)}</td>
          <td>${badge}</td>
        </tr>`;
      }).join('');
      html += `</tbody></table></div></details>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Apply action ──────────────────────────────────────────────────────────────
async function applyKeepBoth() {
  const btnR = document.getElementById('btn-resolve-conflicts');
  const n = parseInt(btnR?.textContent?.match(/\d+/)?.[0] || '0');
  if (!confirm(`¿Resolver ${n} colisión${n !== 1 ? 'es' : ''} añadiendo sufijo _1 _2? Los archivos en conflicto recibirán nombres únicos.`)) return;

  const applyBody = {
    keep_both: true,
    format_opts: {
      include_region:   document.getElementById('fmt-region').checked,
      include_revision: document.getElementById('fmt-revision').checked,
      include_platform: document.getElementById('fmt-platform').checked,
      include_sha:      document.getElementById('fmt-sha').checked,
      sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
    }
  };
  const applyRoot = _deviceRoot();
  if (applyRoot) applyBody.source_root = applyRoot;

  if (btnR) { btnR.disabled = true; btnR.textContent = 'Resolviendo…'; }
  const btn = document.getElementById('btn-apply');
  if (btn) btn.disabled = true;

  const wrap = document.getElementById('apply-progress-wrap');
  const bar  = document.getElementById('apply-progress-bar');
  const lbl  = document.getElementById('apply-progress-label');
  const pct  = document.getElementById('apply-progress-pct');
  if (wrap) wrap.style.display = '';

  try {
    await apiPost('/api/apply', applyBody);
    let done = false;
    while (!done) {
      await new Promise(r => setTimeout(r, 500));
      const s = await apiFetch('/api/job-status');
      if (s.apply_running && s.apply_progress) {
        const p = s.apply_progress;
        const fraction = p.total > 0 ? p.current / p.total : 0;
        if (bar) bar.style.width = Math.round(fraction * 100) + '%';
        if (pct) pct.textContent = Math.round(fraction * 100) + '%';
        if (lbl) lbl.textContent = p.current_file ? `Resolviendo: ${p.current_file}` : 'Resolviendo…';
      }
      if (!s.apply_running && s.apply_result) {
        done = true;
        const r = s.apply_result;
        if (!r.error) showToast(`Resueltos: ${r.renamed} renombrados, ${r.conflicts} conflictos restantes`, r.conflicts > 0 ? 'info' : 'ok');
      }
    }
    await loadPlan();
    loadOverview();
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  } finally {
    setTimeout(() => { if (wrap) wrap.style.display = 'none'; if (bar) bar.style.width = '0%'; }, 2000);
    if (btn) btn.disabled = false;
  }
}

async function doApply() {
  const btn = document.getElementById('btn-apply');
  const total = parseInt(btn?.textContent?.match(/\d+/)?.[0] || '0');
  if (!total) return;
  if (!confirm(`¿Renombrar ${total} archivo${total !== 1 ? 's' : ''} en disco? Los saves compañeros se moverán automáticamente. La operación es reversible.`)) return;

  const applyBody = {
    format_opts: {
      include_region:   document.getElementById('fmt-region').checked,
      include_revision: document.getElementById('fmt-revision').checked,
      include_platform: document.getElementById('fmt-platform').checked,
      include_sha:      document.getElementById('fmt-sha').checked,
      sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
    }
  };
  const applyRoot = _deviceRoot();
  if (applyRoot) applyBody.source_root = applyRoot;

  // Disable buttons while running
  if (btn) { btn.disabled = true; btn.textContent = 'Renombrando…'; }
  const btnR = document.getElementById('btn-resolve-conflicts');
  if (btnR) btnR.disabled = true;

  const wrap = document.getElementById('apply-progress-wrap');
  const bar  = document.getElementById('apply-progress-bar');
  const lbl  = document.getElementById('apply-progress-label');
  const pct  = document.getElementById('apply-progress-pct');
  if (wrap) wrap.style.display = '';

  try {
    await apiPost('/api/apply', applyBody);

    // Poll for completion
    const _shownApplyTs = _job_results_apply_ts || null;
    let done = false;
    while (!done) {
      await new Promise(r => setTimeout(r, 500));
      const s = await apiFetch('/api/job-status');
      if (s.apply_running && s.apply_progress) {
        const p = s.apply_progress;
        const fraction = p.total > 0 ? p.current / p.total : 0;
        const pctVal = Math.round(fraction * 100);
        if (bar) bar.style.width = pctVal + '%';
        if (pct) pct.textContent = pctVal + '%';
        if (lbl) lbl.textContent = p.current_file ? `Renombrando: ${p.current_file}` : 'Renombrando…';
      }
      if (!s.apply_running && s.apply_result) {
        done = true;
        const r = s.apply_result;
        if (r.error) {
          showToast('Error: ' + r.error, 'err');
        } else {
          const savesInfo   = r.saves_renamed > 0 ? ` · ${r.saves_renamed} saves` : '';
          const failedInfo  = r.failed > 0 ? ` · ${r.failed} fallidos` : '';
          const conflictInfo = r.conflicts > 0 ? ` · ${r.conflicts} conflictos restantes` : '';
          showToast(`✓ ${r.renamed} renombrados${savesInfo}${failedInfo}${conflictInfo}`,
            r.failed > 0 || r.conflicts > 0 ? 'info' : 'ok');
          if (bar) bar.style.width = '100%';
          if (pct) pct.textContent = '100%';
          if (lbl) lbl.textContent = 'Completado';
          // D8-2: show error details if any
          const errDetails = r.error_details || r.skip_details || [];
          const errPanel = document.getElementById('apply-error-details');
          const errList  = document.getElementById('apply-error-list');
          const errCount = document.getElementById('apply-error-count');
          if (errDetails.length > 0 && errPanel && errList && errCount) {
            errCount.textContent = errDetails.length + ' archivo(s) con errores o no encontrados:';
            errList.innerHTML = errDetails.map(e => '<div style="padding:1px 0">&#x25B8; ' + _h(e) + '</div>').join('');
            errPanel.style.display = '';
          } else if (errPanel) {
            errPanel.style.display = 'none';
          }
        }
      }
    }

    await loadPlan();
    loadOverview();
  } catch(e) {
    showToast('Error al aplicar: ' + e.message, 'err');
  } finally {
    setTimeout(() => { if (wrap) wrap.style.display = 'none'; if (bar) bar.style.width = '0%'; }, 2000);
    if (btnR) btnR.disabled = false;
  }
}
let _job_results_apply_ts = null;

// ── Duplicates ────────────────────────────────────────────────────────────────
async function loadDuplicates() {
  const el = document.getElementById('dup-content');
  try {
    const cfg = await apiFetch('/api/config');
    const root = _deviceRoot();
    let url;
    if (root) {
      url = `/api/duplicates?source_root=${encodeURIComponent(root)}`;
    } else {
      // Sistema completo: always send pc_root so the server can exclude intentional cross-device copies
      const pcPath = document.getElementById('ov-pc-path')?.value.trim() || cfg.library_root || '';
      const abPath = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '';
      url = '/api/duplicates';
      const params = new URLSearchParams();
      if (pcPath) params.set('pc_root', pcPath);
      if (abPath) params.set('ab_root', abPath);
      if (params.toString()) url += '?' + params.toString();
    }
    const d = await apiFetch(url);
    const dupBar = document.getElementById('dup-context-bar');
    if (dupBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${cfg.library_root || '(no configurado)'}</span> &nbsp;·&nbsp; <span style="color:#555">Duplicado = mismo SHA1 exacto</span>`;
      } else if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">${_devName} — ${ab}</span> &nbsp;·&nbsp; <span style="color:#555">Duplicado = mismo SHA1 exacto</span>`;
      } else {
        const parts = [`PC: <span style="color:#4ec9b0">${cfg.library_root || '(no configurado)'}</span>`];
        const ab = localStorage.getItem('anbernic_path');
        if (ab) parts.push(`${_devName}: <span style="color:#ce9178">${ab}</span>`);
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> → ${parts.join(' &nbsp;+&nbsp; ')} &nbsp;·&nbsp; <span style="color:#555">Duplicados <em>dentro</em> del mismo dispositivo — las copias PC↔${_devName} se excluyen</span>`;
      }
      dupBar.innerHTML = barHtml;
      dupBar.style.display = '';
    }
    if (d.groups.length === 0) {
      if (_activeDevice === 'anbernic') {
        el.innerHTML = _emptyState('✅', `Sin duplicados en ${_devName}`, `Los duplicados cruzados entre PC y ${_devName} solo aparecen en modo <strong>Sistema completo</strong>.`);
      } else {
        el.innerHTML = _emptyState('✅', 'Sin duplicados', 'Los duplicados son ROMs con el mismo contenido exacto (SHA1 idéntico).<br>Si acabas de añadir juegos, ejecuta un Scan y luego un Match.', 'Ir a Inicio', () => showTab('overview'));
      }
      return;
    }
    let html = `<p style="color:#888;margin-bottom:16px">${d.groups.length} grupo${d.groups.length !== 1 ? 's' : ''} — ${d.total_files} archivos — ~${fmtSize(d.wasted_bytes)} ocupados de más</p>`;
    html += d.groups.map(g => `
      <div class="dup-group" id="dup-${g.sha1}">
        <div class="title" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
          <span>${g.canonical_title || '(unmatched)'}
            <span style="color:#555;font-size:11px;margin-left:8px">${g.platform||'Unknown'} · SHA1: ${g.sha1.slice(0,12)}…</span>
          </span>
          <button class="btn" style="padding:2px 10px;font-size:11px;color:#888;border-color:#444" title="No aparecerá más como duplicado (copia intencional entre dispositivos)" onclick="markAsIntentionalCopy('${g.sha1}')">Copia intencional ✓</button>
        </div>
        ${g.entries.map((e, i) => `
          <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
            ${i === 0
              ? '<span class="badge ok" style="min-width:44px;text-align:center">keep</span>'
              : `<button class="btn danger" style="padding:2px 10px;font-size:11px" data-id="${e.id}" data-path="${e.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" onclick="deleteDuplicate(this)">Eliminar</button>`}
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${e.source_path}">${e.source_path}</span>
            <span style="color:#555;flex-shrink:0">${fmtSize(e.size_bytes)}</span>
          </div>`).join('')}
      </div>`).join('');
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function deleteAllDuplicates() {
  const rows = document.querySelectorAll('#tab-duplicates .btn.danger');
  const count = rows.length;
  if (count === 0) { showToast('No hay duplicados para eliminar.', false); return; }
  _showConfirm(
    'Eliminar todos los duplicados',
    `Se eliminarán <strong>${count} archivo${count !== 1 ? 's' : ''}</strong> del disco.<br>Se conservará una copia de cada juego.<br><br><span style="color:#f44747">Esta operación no se puede deshacer.</span>`,
    'Eliminar todos',
    async () => {
      const btn = document.getElementById('btn-delete-all-dups');
      if (btn) { btn.disabled = true; btn.textContent = 'Eliminando…'; }
      try {
        const d = await apiPost('/api/duplicates/delete-all', {});
        await loadDuplicates();
        loadOverview();
        showToast(`Eliminados: ${d.deleted} · Espacio liberado: ${fmtSize(d.freed_bytes)}`, false);
      } catch(e) {
        showToast('Error: ' + e.message, true);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Eliminar todos los duplicados'; }
      }
    }
  );
}

async function deleteDuplicate(btn) {
  const gameId = parseInt(btn.dataset.id);
  const sourcePath = btn.dataset.path;
  const filename = sourcePath.split(/[\\/]/).pop();
  _showConfirm(
    'Eliminar archivo duplicado',
    `¿Eliminar <strong>${_h(filename)}</strong> del disco?<br><br><span style="color:#f44747">Esta operación no se puede deshacer.</span>`,
    'Eliminar',
    async () => {
      btn.disabled = true;
      btn.textContent = 'Eliminando…';
      try {
        await apiPost('/api/duplicates/delete', { game_id: gameId, source_path: sourcePath });
        const row = document.getElementById('dup-entry-' + gameId);
        if (row) {
          const group = row.closest('.dup-group');
          row.remove();
          if (group && !group.querySelector('.btn.danger')) group.remove();
        }
        loadOverview();
      } catch(e) {
        btn.disabled = false;
        btn.textContent = 'Eliminar';
        showToast('Error al eliminar: ' + e.message, true);
      }
    }
  );
}

async function markAsIntentionalCopy(sha1) {
  _showConfirm(
    'Marcar como copia intencional',
    '¿Marcar este grupo como copia intencional PC↔consola?<br><br>No aparecerá más en la lista de duplicados.',
    'Confirmar',
    async () => {
      try {
        await apiPost('/api/duplicates/exclude', { sha1 });
        const el = document.getElementById('dup-' + sha1);
        if (el) el.remove();
        showToast('Grupo excluido de duplicados', 'ok');
      } catch(e) {
        showToast('Error: ' + e.message, true);
      }
    }
  );
}

// ── RA Duplicates ─────────────────────────────────────────────────────────────
async function loadRaDuplicates() {
  const el = document.getElementById('ra-dup-content');
  const btn = document.getElementById('btn-ra-dups');
  const batchBtn = document.getElementById('btn-ra-dups-discard-all');
  el.innerHTML = '<p style="color:#555;font-size:12px">Cargando…</p>';
  if (btn) btn.disabled = true;
  if (batchBtn) batchBtn.style.display = 'none';
  try {
    const d = await apiFetch('/api/ra-duplicates');
    if (d.note) {
      el.innerHTML = `<p style="color:#888;font-size:12px">${d.note}</p>`;
      return;
    }
    if (d.total_groups === 0) {
      el.innerHTML = '<p style="color:#4ec9b0;font-size:13px">No se encontraron versiones candidatas a eliminar. ✓</p>';
      return;
    }
    // D8-4: show batch delete button when there are groups
    if (batchBtn) batchBtn.style.display = '';
    let html = `<p style="color:#888;font-size:12px;margin-bottom:12px">
      <strong style="color:#e0e0e0">${d.total_groups}</strong> grupos encontrados —
      <strong style="color:#f44747">${fmtSize(d.wasted_bytes)}</strong> recuperables eliminando versiones sin logros.
    </p>`;
    for (const g of d.groups) {
      html += `<div style="border:1px solid #2a2a3e;border-radius:4px;margin-bottom:10px;overflow:hidden">
        <div style="background:#252537;padding:7px 12px;display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:13px;font-weight:600;color:#c9bcf5">${_h(g.normalized_title)}</span>
          <span style="font-size:11px;color:#888">${_h(g.platform)} — ${fmtSize(g.wasted_bytes)} recuperables</span>
        </div>
        <table style="width:100%;font-size:12px">
          <thead><tr>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Archivo</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Tamaño</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Logros RA</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Recomendación</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Acción</th>
          </tr></thead>
          <tbody>`;
      for (const e of g.entries) {
        const raLabel = e.ra_supported
          ? `<span style="color:#4ec9b0">✓ ${e.ra_achievements} logros</span>`
          : `<span style="color:#f44747">✗ Sin logros</span>`;
        const rec = e.ra_supported
          ? '<span style="color:#4ec9b0">Conservar</span>'
          : '<span style="color:#f44747">Candidata a eliminar</span>';
        const rowBg = e.ra_supported ? '' : 'style="background:#1a1015"';
        const delBtn = e.ra_supported ? '' :
          `<button class="btn danger" style="font-size:11px;padding:2px 8px"
            onclick="deleteRaDuplicate(${e.id}, ${JSON.stringify(e.source_path)}, this)">Eliminar</button>`;
        html += `<tr ${rowBg}>
          <td style="padding:5px 10px;word-break:break-all">${_h(e.filename)}</td>
          <td style="padding:5px 10px">${fmtSize(e.size_bytes)}</td>
          <td style="padding:5px 10px">${raLabel}</td>
          <td style="padding:5px 10px">${rec}</td>
          <td style="padding:5px 10px">${delBtn}</td>
        </tr>`;
      }
      html += '</tbody></table></div>';
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function deleteRaDuplicate(gameId, sourcePath, btn) {
  const filename = sourcePath.split(/[\\/]/).pop();
  if (!confirm(`¿Eliminar la versión sin logros RA?\n\n${filename}\n\nSe moverá a _descartados/. Esta acción es difícil de deshacer.`)) return;
  btn.disabled = true;
  btn.textContent = '…';
  try {
    // D8-4: use dedicated discard endpoint
    await apiPost('/api/ra-duplicates/discard', { path: sourcePath });
    const row = btn.closest('tr');
    if (row) row.remove();
    showToast(`Eliminado: ${filename}`, 'ok');
    loadOverview();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Eliminar';
    showToast('Error: ' + e.message, 'err');
  }
}

// D8-3: Resolve plan conflicts keeping RA winner
async function doResolveRaConflicts() {
  const btn = document.getElementById('btn-resolve-ra-conflicts');
  if (btn) { btn.disabled = true; btn.textContent = 'Resolviendo…'; }
  try {
    const d = await apiPost('/api/apply-ra-conflicts', {});
    if (d.error) {
      showToast('Error: ' + d.error, 'err');
    } else {
      let msg;
      if (d.no_cache) {
        msg = 'Sin datos RA en caché — ejecuta primero la comprobación de RetroAchievements en la pestaña Tools';
      } else if (d.resolved === 0 && d.skipped_no_ra > 0) {
        msg = d.skipped_no_ra + ' conflictos sin datos RA suficientes para decidir — ejecuta la comprobación RA primero';
      } else {
        msg = 'RA resuelto: ' + d.resolved + ' conflictos' + (d.skipped_no_ra > 0 ? ' · ' + d.skipped_no_ra + ' sin datos RA' : '');
      }
      showToast(msg, d.resolved > 0 ? 'ok' : 'info');
      await loadPlan();
      loadOverview();
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// D8-4: Discard all RA duplicates without RA support
async function discardAllRaDuplicates() {
  if (!confirm('¿Eliminar TODOS los archivos sin logros RA de todos los grupos de versión?\n\nSe moverán a una carpeta _descartados/ junto a cada archivo. Esta acción no se puede deshacer fácilmente.')) return;
  const btn = document.getElementById('btn-ra-dups-discard-all');
  if (btn) { btn.disabled = true; btn.textContent = 'Eliminando…'; }
  try {
    const d = await apiPost('/api/ra-duplicates/discard-all', {});
    if (d.error) {
      showToast('Error: ' + d.error, 'err');
    } else if (d.discarded === 0 && d.failed === 0) {
      showToast(d.note || 'Sin archivos que eliminar — ejecuta primero la comprobación RA en Tools para cargar el caché.', 'info');
    } else {
      showToast('Eliminados: ' + d.discarded + (d.failed > 0 ? ' · Fallidos: ' + d.failed : ''), d.failed > 0 ? 'info' : 'ok');
      await loadRaDuplicates();
      loadOverview();
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Eliminar todos sin logros'; }
  }
}

// D8-5: Tools context selector
function setToolsContext(ctx) {
  localStorage.setItem('tools_context', ctx);
  const btnPc  = document.getElementById('tools-ctx-pc');
  const btnAb  = document.getElementById('tools-ctx-android');
  const lbl    = document.getElementById('tools-ctx-path-label');
  if (btnPc)  btnPc.classList.toggle('active',  ctx === 'pc');
  if (btnAb)  btnAb.classList.toggle('active',  ctx === 'android');

  apiFetch('/api/config').then(cfg => {
    let rootPath = '';
    if (ctx === 'pc') {
      rootPath = cfg.library_root || '';
    } else {
      rootPath = localStorage.getItem('anbernic_path') || localStorage.getItem('cable_ab_path') || '';
    }
    if (lbl) lbl.textContent = rootPath ? '— ' + rootPath : '(sin ruta configurada)';
    // Fill all tool path inputs
    const toolInputIds = ['zip-path', 'chd-path', 'orphan-path', 'folder-analysis-path', 'junk-path', 'health-path'];
    for (const id of toolInputIds) {
      const el = document.getElementById(id);
      if (el && rootPath) { el.value = rootPath; el.dispatchEvent(new Event('input')); }
    }
  }).catch(() => {});
}

async function _initToolsContext() {
  const ctx = localStorage.getItem('tools_context') || 'pc';
  setToolsContext(ctx);
}

// ── Sync ──────────────────────────────────────────────────────────────────────
async function loadSync() {
  const el = document.getElementById('sync-content');
  try {
    const [sl, cfg] = await Promise.all([apiFetch('/api/sync-log'), apiFetch('/api/config')]);
    let html = '';
    const sources = cfg.sync_sources || [];
    const syncBar = document.getElementById('sync-context-bar');
    if (syncBar) {
      if (sources.length) {
        const names = sources.map(s => `<span style="color:#4ec9b0">${s.name}</span>`).join(' &nbsp;·&nbsp; ');
        syncBar.innerHTML = `Fuentes configuradas: ${names}`;
      } else {
        syncBar.innerHTML = `<span style="color:#f48771">Sin fuentes de sync — configura <code>[[sync.sources]]</code> en config.toml</span>`;
      }
      syncBar.style.display = '';
    }
    if (!sources.length) {
      html += `<p class="error-msg" style="margin-bottom:16px">No hay fuentes de sync configuradas. Edita <code>config.toml</code> y añade entradas <code>[[sync.sources]]</code>.</p>`;
    }
    if (sl.entries.length === 0) {
      html += '<p class="empty">Aún no hay registros de sincronización. Pulsa <strong>Sincronizar</strong> para empezar.</p>';
      el.innerHTML = html;
      return;
    }
    html += `<p style="color:#666;margin-bottom:12px">${sl.entries.length} evento${sl.entries.length !== 1 ? 's' : ''}</p>`;
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Fecha</th><th>Dirección</th><th>Resultado</th><th>Ruta local</th><th>Ruta remota</th><th>Mensaje</th>';
    html += '</tr></thead><tbody>';
    html += sl.entries.map(e => {
      const dirBadge = badge(e.direction, e.direction);
      const resBadge = badge(e.result, e.result);
      const msg  = e.message ? `<span style="color:#888">${e.message}</span>` : '';
      const date = e.created_at ? e.created_at.replace('T', ' ') : '';
      return `<tr><td>${date}</td><td>${dirBadge}</td><td>${resBadge}</td><td title="${e.local_path}">${e.local_path.split(/[\\/]/).pop()}</td><td title="${e.remote_path}">${e.remote_path}</td><td>${msg}</td></tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Assets ───────────────────────────────────────────────────────────────────
async function loadAssets() {
  const el = document.getElementById('assets-content');
  el.innerHTML = '<p class="loading">Cargando…</p>';
  const filter = document.getElementById('assets-filter')?.value || 'all';
  try {
    const _assetsRoot = _deviceRoot();
    const assetsUrl = _assetsRoot ? `/api/assets?root=${encodeURIComponent(_assetsRoot)}` : '/api/assets';
    const [d, cfg] = await Promise.all([apiFetch(assetsUrl), apiFetch('/api/config')]);
    const assetsBar = document.getElementById('assets-context-bar');
    if (assetsBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${cfg.library_root || '(no configurado)'}</span> &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      } else if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">${_devName} — ${ab}</span> &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      } else {
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> (PC + ${_devName}) &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      }
      assetsBar.innerHTML = barHtml;
      assetsBar.style.display = '';
    }
    let stats = d.stats;
    if (filter === 'orphans') stats = stats.filter(s => s.orphan_assets > 0);
    if (filter === 'missing') stats = stats.filter(s => s.rom_count > 0 && s.image_count === 0 && s.video_count === 0);
    if (stats.length === 0) { el.innerHTML = '<p class="empty">Sin datos de assets todavía. Ejecuta un Scan para indexar la biblioteca.</p>'; return; }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>ROMs</th><th>Imágenes</th><th>Vídeos</th><th>XML</th><th>Huérfanos</th>';
    html += '</tr></thead><tbody>';
    html += stats.map(s => `<tr>
      <td>${s.platform}</td>
      <td style="text-align:right">${s.rom_count}</td>
      <td style="text-align:right;color:${s.image_count ? '#4ec9b0' : '#555'}">${s.image_count}</td>
      <td style="text-align:right;color:${s.video_count ? '#4ec9b0' : '#555'}">${s.video_count}</td>
      <td style="text-align:right;color:${s.xml_count ? '#4ec9b0' : '#555'}">${s.xml_count}</td>
      <td style="text-align:right;color:${s.orphan_assets ? '#f44747' : '#555'}">${s.orphan_assets || '—'}</td>
    </tr>`).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Sync actions ─────────────────────────────────────────────────────────────
// ── Catalog DAT management ─────────────────────────────────────────────────────
async function loadCatalogStatus() {
  const el = document.getElementById('catalog-status');
  if (!el) return;
  try {
    const d = await apiFetch('/api/catalog-status');
    const ni = d.nointro.length, rd = d.redump.length;
    const niE = (d.total_nointro_entries || 0).toLocaleString();
    const rdE = (d.total_redump_entries || 0).toLocaleString();
    let html = '';
    if (ni === 0 && rd === 0) {
      html = '<span style="color:#dcdcaa">\u26A0 No hay cat\u00e1logos DAT cargados.</span> El cruce de hashes no estar\u00e1 disponible hasta que importes archivos DAT.';
    } else {
      html = `\u2705 <strong style="color:#4ec9b0">${ni}</strong> No-Intro (${niE} entradas) &middot; <strong style="color:#4ec9b0">${rd}</strong> Redump (${rdE} entradas)`;
    }
    html += `<br><span style="color:#555;font-size:10px">No-Intro: <code>${d.nointro_dir}</code><br>Redump: <code>${d.redump_dir}</code></span>`;
    el.innerHTML = html;
  } catch(e) {
    el.textContent = 'Error al cargar estado de cat\u00e1logos.';
  }
}

async function importDats() {
  const folder = (document.getElementById('import-dats-folder')?.value || '').trim();
  if (!folder) { alert('Introduce la carpeta con los archivos DAT.'); return; }
  const res = document.getElementById('import-dats-result');
  if (res) { res.textContent = 'Importando\u2026'; res.style.color = '#888'; }
  try {
    const d = await apiPost('/api/import-dats', { source_folder: folder });
    if (d.error) {
      if (res) { res.textContent = '\u274C ' + d.error; res.style.color = '#f44747'; }
      return;
    }
    const ni = d.imported.filter(x => x.catalog === 'nointro').length;
    const rd = d.imported.filter(x => x.catalog === 'redump').length;
    const msg = d.total > 0
      ? `\u2705 ${d.total} archivo(s) importados: ${ni} No-Intro, ${rd} Redump.` + (d.errors.length ? ` (${d.errors.length} errores)` : '')
      : '\u26A0 No se encontraron archivos DAT reconocidos en esa carpeta.';
    if (res) { res.innerHTML = msg; res.style.color = d.total > 0 ? '#4ec9b0' : '#dcdcaa'; }
    loadCatalogStatus();
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; res.style.color = '#f44747'; }
  }
}

// ── Rclone setup wizard ────────────────────────────────────────────────────────
function toggleRcloneSetup() {
  const panel = document.getElementById('rclone-setup-panel');
  if (!panel) return;
  const showing = panel.style.display !== 'none';
  panel.style.display = showing ? 'none' : '';
  if (!showing) loadRcloneStatus();
}

async function loadRcloneStatus() {
  const info = document.getElementById('rclone-status-info');
  const remPanel = document.getElementById('rclone-remotes-panel');
  if (info) info.textContent = 'Comprobando rclone\u2026';
  if (remPanel) remPanel.style.display = 'none';
  try {
    const d = await apiFetch('/api/rclone-status');
    if (!d.installed) {
      if (info) info.innerHTML = '\u274C rclone no encontrado en <code>' + d.binary + '</code>.<br>'
        + 'Desc\u00e1rgalo de <strong style="color:#d4d4d4">rclone.org/downloads</strong> y ponlo en PATH, '
        + 'o indica la ruta en <code>config.toml</code> bajo <code>[sync]</code> como <code>rclone = "C:/tools/rclone.exe"</code>.';
      return;
    }
    let statusHtml = '\u2705 ' + d.version;
    if (d.remotes.length === 0) {
      statusHtml += '<br>\u26A0 Sin remotes configurados. Ejecuta <code>rclone config</code> en un terminal para a\u00f1adir uno (Dropbox, Google Drive, OneDrive\u2026).';
    } else {
      statusHtml += ` &middot; ${d.remotes.length} remote(s): <strong style="color:#d4d4d4">${d.remotes.join('  ')}</strong>`;
    }
    if (info) info.innerHTML = statusHtml;
    if (d.remotes.length) {
      const sel = document.getElementById('rclone-remote-select');
      if (sel) {
        sel.innerHTML = d.remotes.map(r => `<option value="${r}">${r}</option>`).join('');
        // Pre-select current remote
        const currentFull = document.getElementById('cfg-rclone-remote')?.value || '';
        if (currentFull) {
          const currentRemote = currentFull.split('/')[0] + ':';
          const currentPath = '/' + currentFull.slice(currentRemote.length).replace(/^\/+/, '');
          for (const opt of sel.options) if (opt.value === currentRemote) opt.selected = true;
          const pathInp = document.getElementById('rclone-path-input');
          if (pathInp && !pathInp.value) pathInp.value = currentPath;
        }
      }
      if (remPanel) remPanel.style.display = '';
    }
  } catch(e) {
    if (info) info.textContent = '\u274C Error: ' + e.message;
  }
}

async function applyRcloneRemote() {
  const remote = document.getElementById('rclone-remote-select')?.value || '';
  const pathVal = (document.getElementById('rclone-path-input')?.value || '').trim().replace(/^\/+/, '');
  const res = document.getElementById('rclone-apply-result');
  if (!remote) { if (res) { res.textContent = 'Selecciona un remote.'; res.style.color = '#dcdcaa'; } return; }
  const fullRemote = remote + pathVal;
  try {
    await apiPost('/api/config', { 'sync.remote': fullRemote });
    if (res) { res.innerHTML = '\u2705 Guardado: <code>' + fullRemote + '</code>'; res.style.color = '#4ec9b0'; }
    const cfgInp = document.getElementById('cfg-rclone-remote');
    if (cfgInp) cfgInp.value = fullRemote;
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; res.style.color = '#f44747'; }
  }
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
    resultEl.textContent = `${verb} — ↑ ${result.uploaded}  ↓ ${result.downloaded}  ✓ ${result.up_to_date}  ⚠ ${result.conflicts}  ✗ ${result.errors}`;
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
            html += ` <span style="color:#555;font-size:12px;margin-left:8px">↑ ${src.uploaded}  ↓ ${src.downloaded}  ✓ ${src.up_to_date}  ⚠ ${src.conflicts}  ✗ ${src.errors}</span>`;
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

function _renderChdResult(result) {
  const resultEl   = document.getElementById('job-result-convert-chd');
  const resultsDiv = document.getElementById('chd-results');
  const btn        = document.getElementById('btn-convert-chd');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    _showJobResult('convert-chd', result);
    if (resultsDiv && result.results?.length) {
      resultsDiv.innerHTML = result.results.map(r => {
        if (r.success) {
          const tag = result.dry_run ? 'PREVIEW' : 'OK';
          return `<div style="font-size:12px;color:#4ec9b0;padding:2px 0">[${tag}] ${r.cue} → ${r.chd}</div>`;
        } else {
          const errMsg = r.error ? `<span style="color:#f44747;margin-left:6px;font-style:italic">${r.error}</span>` : '';
          return `<div style="font-size:12px;color:#f44747;padding:4px 0;border-bottom:1px solid #2a1a1a"><strong>[FAIL]</strong> ${r.cue}${errMsg}</div>`;
        }
      }).join('');
    }
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a CHD'; }
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
      if (wrap) wrap.style.display = 'none';
    } else {
      // Show folder buttons to pick one
      listEl.innerHTML = folders.map(f => {
        const name = f.split(/[\\/]/).pop();
        return `<button class="btn" style="font-size:12px;padding:3px 10px" onclick="document.getElementById('m3u-path').value='${f.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}';document.getElementById('m3u-folder-select-wrap').style.display='none'">${name}</button>`;
      }).join('');
      if (wrap) wrap.style.display = '';
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
    html += '<button class="btn danger" onclick="doDeleteOrphans()">Borrar seleccionados</button>';
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
    html += '<div style="max-height:400px;overflow-y:auto">';
    html += r.issues.map(i => {
      const color = i.status === 'corrupted' ? '#f44747' : '#ce9178';
      const label = i.status === 'corrupted' ? 'CORRUPTO' : 'NO ENCONTRADO';
      const name  = i.source_path.split(/[\\/]/).pop();
      return `<div style="font-size:12px;color:${color};padding:2px 0" title="${i.source_path}">[${label}] ${name}</div>`;
    }).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

// ── Análisis de carpeta ───────────────────────────────────────────────────────
async function doFolderAnalysis() {
  const path = document.getElementById('folder-analysis-path').value.trim();
  const el   = document.getElementById('folder-analysis-result');
  if (!path) { el.innerHTML = '<p class="error-msg">Introduce una ruta.</p>'; return; }
  el.innerHTML = '<p class="loading">Analizando…</p>';
  try {
    const d = await apiFetch('/api/folder-analysis?path=' + encodeURIComponent(path));
    let html = '';

    // Extensions table
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
      html += `<h4 style="color:#f44747;margin:16px 0 8px">&#x26D4; .cue sin .bin (${d.cue_missing_bin.length})</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.cue_missing_bin.map(f => `<li class="mono" style="color:#ce9178;font-size:12px">${_h(f)}</li>`).join('');
      html += '</ul>';
    }

    // Orphan BIN (no CUE)
    if (d.bin_orphan && d.bin_orphan.length > 0) {
      html += `<h4 style="color:#ce9178;margin:16px 0 8px">&#x26A0; .bin sin .cue (${d.bin_orphan.length})</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.bin_orphan.map(f => `<li class="mono" style="font-size:12px">${_h(f)}</li>`).join('');
      html += '</ul>';
    }

    // Formats needing conversion
    if (d.needs_conversion && d.needs_conversion.length > 0) {
      html += `<h4 style="color:#dcdcaa;margin:16px 0 8px">Formatos que necesitan soporte/conversión</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.needs_conversion.map(e => `<li style="color:#888;font-size:12px"><code>${_h(e.ext)}</code> — ${_h(e.note)}</li>`).join('');
      html += '</ul>';
    }

    if (!html) html = '<p style="color:#555">No se encontraron archivos en la carpeta.</p>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${_h(e.message)}</p>`;
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
    if (filterRow) filterRow.style.display = platforms.size > 0 ? '' : 'none';
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
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Tu archivo</th><th>Título RA</th><th>Logros</th><th>Puntos</th><th>Buscar</th>';
    html += '</tr></thead><tbody>';
    html += pageAlts.map(a => {
      const q = _googleQuery(a.ra_title, a.platform);
      return `<tr>
      <td>${a.platform}</td>
      <td title="${a.filename}" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a.filename}</td>
      <td><a href="https://retroachievements.org/game/${a.ra_id}" target="_blank" style="color:#4ec9b0">${a.ra_title}</a></td>
      <td style="text-align:right;color:#ce9178">${a.ra_achievements}</td>
      <td style="text-align:right;color:#555">${a.ra_points}</td>
      <td style="white-space:nowrap"><button class="btn" style="font-size:10px;padding:2px 7px" onclick="_copyText(${JSON.stringify(q)})">📋 Copiar</button></td>
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
  return `"${raTitle}" ${platform} No-Intro site:archive.org`;
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
    const d = await apiFetch('/api/scrape-summary');
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
      label.style.color = hasDev ? '#4ec9b0' : '#555';
      if (bar) bar.style.display = 'none';
      return;
    }
    const pct = max > 0 ? Math.min(100, Math.round(today / max * 100)) : 0;
    const color = pct > 90 ? '#f44747' : pct > 70 ? '#ce9178' : '#4ec9b0';
    label.textContent = `${today.toLocaleString()} / ${max.toLocaleString()} peticiones hoy (${pct}%)${hasDev ? ' · Cuenta dev ✓' : ''}`;
    label.style.color = color;
    if (bar) { bar.style.display = 'block'; }
    if (fill) { fill.style.background = color; fill.style.width = pct + '%'; }
  } catch(e) {
    if (label) { label.textContent = 'No disponible'; label.style.color = '#555'; }
  }
}

async function doScrape() {
  const btn = document.getElementById('btn-scrape');
  const resultEl = document.getElementById('job-result-scrape');
  btn.disabled = true;
  btn.textContent = 'Scraping…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/scrape', {
      platform: document.getElementById('scrape-platform').value.trim() || null,
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
      resultEl.textContent = d.written.map(w => `${w.platform}: ${w.entries} entradas → ${w.path}`).join('\n');
      resultEl.style.whiteSpace = 'pre';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Settings ──────────────────────────────────────────────────────────────────
function _onDevicePresetChange() {
  const sel    = document.getElementById('cfg-device-preset');
  const custom = document.getElementById('cfg-device-name-custom');
  if (custom) custom.style.display = sel?.value === 'custom' ? 'block' : 'none';
}

async function loadSettings() {
  try {
    const cfg = await apiFetch('/api/config');
    document.getElementById('cfg-library-root').value  = cfg.library_root  || '';
    const anbEl = document.getElementById('cfg-anbernic-root');
    if (anbEl) anbEl.value = cfg.anbernic_root || '';
    // Device name preset
    const dn = cfg.device_name || 'Consola Android';
    const presetEl = document.getElementById('cfg-device-preset');
    const customEl = document.getElementById('cfg-device-name-custom');
    if (presetEl) {
      const knownPresets = ['Consola Android', 'Steam Deck'];
      if (knownPresets.includes(dn)) {
        presetEl.value = dn;
        if (customEl) customEl.style.display = 'none';
      } else {
        presetEl.value = 'custom';
        if (customEl) { customEl.style.display = 'block'; customEl.value = dn; }
      }
    }
    document.getElementById('cfg-rclone-remote').value = cfg.rclone_remote || '';
    const whEl = document.getElementById('cfg-web-host');
    if (whEl) whEl.value = cfg.web_host || '127.0.0.1';
    document.getElementById('cfg-ss-user').value       = cfg.screenscraper_user || '';
    document.getElementById('cfg-ss-pass').value       = cfg.screenscraper_pass || '';
    const ssDevId  = document.getElementById('cfg-ss-devid');
    const ssDevPass = document.getElementById('cfg-ss-devpass');
    if (ssDevId)   ssDevId.value   = cfg.screenscraper_dev_id   || '';
    if (ssDevPass) ssDevPass.value = cfg.screenscraper_dev_pass  || '';
    document.getElementById('cfg-chdman').value        = cfg.chdman || 'chdman';
    document.getElementById('cfg-adb').value           = cfg.adb || 'adb';
    const raPathEl = document.getElementById('cfg-retroarch-path');
    if (raPathEl) raPathEl.value = cfg.retroarch_path || '';
    const bkEnabledEl = document.getElementById('cfg-backup-enabled');
    const bkKeepNEl   = document.getElementById('cfg-backup-keep-n');
    if (bkEnabledEl) bkEnabledEl.checked = cfg.backup_saves_enabled !== false;
    if (bkKeepNEl)   bkKeepNEl.value     = cfg.backup_saves_keep_n ?? 5;
    document.getElementById('cfg-ra-api-key').value   = cfg.ra_api_key || '';
    // Show config warnings
    const banner = document.getElementById('cfg-warnings-banner');
    if (banner) {
      const warns = (cfg.warnings || []);
      if (warns.length === 0) {
        banner.style.display = 'none';
      } else {
        const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        const items = warns.map(w => {
          const icon = w.level === 'warning' ? '⚠' : 'ℹ';
          const color = w.level === 'warning' ? '#f9e2af' : '#89b4fa';
          return `<div style="color:${color};font-size:12px;margin:2px 0">${icon} ${esc(w.message)}</div>`;
        }).join('');
        banner.innerHTML = items;
        banner.style.display = 'block';
      }
    }
    // Show two-DB info
    const dbInfo = document.getElementById('settings-db-info');
    if (dbInfo && cfg.pc_db_path) {
      const fmtSize = (n) => n == null ? '?' : n < 1024*1024 ? (n/1024).toFixed(0)+'KB' : (n/1024/1024).toFixed(1)+'MB';
      dbInfo.innerHTML =
        '<div style="display:grid;grid-template-columns:auto 1fr auto;gap:4px 12px;align-items:center">' +
        '<span style="color:#4ec9b0">&#x25CF;</span><span style="font-family:monospace;color:#d4d4d4">library_pc.db</span><span style="color:#888">' + fmtSize(cfg.pc_db_size) + '</span>' +
        '<span style="color:#ce9178">&#x25CF;</span><span style="font-family:monospace;color:#d4d4d4">library_android.db</span><span style="color:#888">' + fmtSize(cfg.android_db_size) + '</span>' +
        '</div>';
    }
  } catch(e) { /* silent */ }
}

async function migrateSplitDb() {
  const el = document.getElementById('migrate-db-result');
  if (!el) return;
  el.style.color = '#888'; el.textContent = 'Migrando…';
  try {
    const r = await apiPost('/api/migrate-split-db', {});
    if (r.error) { el.style.color = '#f44747'; el.textContent = '✗ ' + r.error; return; }
    el.style.color = '#4ec9b0';
    el.textContent = '✓ Migrados: ' + r.migrated_games + ' juegos  |  Errores: ' + (r.errors?.length || 0);
    if (r.errors && r.errors.length > 0) {
      el.textContent += '  [' + r.errors.slice(0,3).join('; ') + ']';
    }
  } catch(e) { el.style.color = '#f44747'; el.textContent = '✗ ' + e.message; }
}

async function testChdman() {
  const el = document.getElementById('chdman-test-result');
  el.style.color = '#888'; el.textContent = 'Probando…';
  // Save current chdman value first if changed
  const val = document.getElementById('cfg-chdman').value.trim();
  if (val) await apiPost('/api/config', { 'tools.chdman': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/test-chdman');
    if (d.ok) {
      el.style.color = '#4ec9b0';
      el.textContent = '✓ ' + (d.version || 'OK') + '  (' + d.path + ')';
      // Update CHD panel status too
      const st = document.getElementById('chdman-status');
      if (st) { st.style.color = '#4ec9b0'; st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
    } else {
      el.style.color = '#f44747'; el.textContent = '✗ ' + d.error;
      const st = document.getElementById('chdman-status');
      if (st) { st.style.color = '#f44747'; st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
    }
  } catch(e) { el.style.color = '#f44747'; el.textContent = '✗ ' + e.message; }
}

async function testAdbBinary() {
  const el = document.getElementById('adb-test-result');
  el.style.color = '#888'; el.textContent = 'Probando…';
  const val = document.getElementById('cfg-adb').value.trim();
  if (val) await apiPost('/api/config', { 'tools.adb': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      el.style.color = '#f44747'; el.textContent = '✗ ' + d.error;
    } else {
      el.style.color = '#4ec9b0';
      el.textContent = `✓ adb accesible — ${d.devices?.length ?? 0} dispositivo(s) detectado(s)  (${d.adb_path})`;
    }
  } catch(e) { el.style.color = '#f44747'; el.textContent = '✗ ' + e.message; }
}

async function loadTools() {
  try {
    const [cfg, discData] = await Promise.all([
      apiFetch('/api/config'),
      apiFetch('/api/disc-folders').catch(() => ({ folders: [], library_root: null })),
    ]);
    const root = cfg.library_root || '';
    // Auto-fill simple tools with library_root
    if (root) {
      _setIfEmpty('zip-path',               root);
      _setIfEmpty('orphan-path',            root);
      _setIfEmpty('verify-multidisc-path',  discData.folders.length ? discData.folders.join('\n') : root);
      _setIfEmpty('m3u-path',               discData.folders.length ? discData.folders[0] : root);
      _setIfEmpty('chd-path',               discData.folders.length ? discData.folders[0] : root);
      _setIfEmpty('report-path',            root);
    }
    // Show multi-disc hint
    if (discData.folders.length > 1) {
      const hint = document.getElementById('multidisc-folder-hint');
      if (hint) {
        hint.textContent = `Detectadas ${discData.folders.length} carpetas de plataformas de disco: ${discData.folders.map(f => f.split(/[\\/]/).pop()).join(', ')}`;
        hint.style.display = '';
      }
    }
    // Test chdman silently and update status
    try {
      const d = await apiFetch('/api/test-chdman');
      const st = document.getElementById('chdman-status');
      if (st) {
        if (d.ok) { st.style.color = '#4ec9b0'; st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
        else      { st.style.color = '#f44747'; st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
      }
    } catch(_) {}
    // Show RA API key status
    const raStatus = document.getElementById('ra-api-key-status');
    if (raStatus) {
      if (cfg.ra_api_key) {
        raStatus.style.color = '#4ec9b0';
        raStatus.textContent = '✓ API key configurada';
      } else {
        raStatus.style.color = '#f44747';
        raStatus.innerHTML = '✗ API key no configurada — <a href="#" onclick="showTab(\'settings\');return false" style="color:#569cd6">ir a Settings</a>';
      }
    }
    // Restore persisted tool paths (Fix E)
    _initToolPath('zip-path',              'tool_path_zip');
    _initToolPath('orphan-path',           'tool_path_orphan');
    _initToolPath('chd-path',              'tool_path_chd');
    _initToolPath('m3u-path',              'tool_path_m3u');
    _initToolPath('report-path',           'tool_path_report');
    _initToolPath('folder-analysis-path',  'tool_path_folder_analysis');
    _initToolPath('junk-path',             'tool_path_junk');
  } catch(e) { /* silent */ }
}

function _setIfEmpty(id, value) {
  const el = document.getElementById(id);
  if (el && !el.value.trim() && value) { el.value = value; return true; }
  return false;
}

// ── Batch run (Fix 11) ────────────────────────────────────────────────────────
async function doBatchRun() {
  const cfg = await apiFetch('/api/config');
  const root = cfg.library_root;
  if (!root) { alert('Configura library_root en Settings primero.'); return; }

  const jobs = [];
  if (document.getElementById('batch-scan')?.checked) jobs.push({
    name: 'Escanear biblioteca', runningKey: 'scan_running',
    start: () => apiPost('/api/scan', { source_paths: [root], quick: false }),
  });
  if (document.getElementById('batch-match')?.checked) jobs.push({
    name: 'Identificar ROMs (DAT)', runningKey: 'match_running',
    start: () => apiPost('/api/match', {}),
  });
  if (document.getElementById('batch-zip')?.checked) jobs.push({
    name: 'Descomprimir ZIPs', runningKey: 'extract_zip_running',
    start: () => apiPost('/api/extract-zip', { source_path: root, dry_run: false, delete_source: false }),
  });
  if (document.getElementById('batch-chd')?.checked) jobs.push({
    name: 'Convertir a CHD', runningKey: 'convert_chd_running',
    start: () => apiPost('/api/convert-chd', { source_path: root, dry_run: false }),
  });
  if (document.getElementById('batch-health')?.checked) jobs.push({
    name: 'Health Check', runningKey: 'health_check_running',
    start: () => apiPost('/api/health-check', {}),
  });
  if (document.getElementById('batch-ra')?.checked) jobs.push({
    name: 'RetroAchievements', runningKey: 'ra_check_running',
    start: () => apiPost('/api/ra-check', {}),
  });
  if (jobs.length === 0) { alert('Selecciona al menos una herramienta.'); return; }

  const btn = document.getElementById('btn-batch-run');
  const statusEl = document.getElementById('batch-status');
  btn.disabled = true;
  let allOk = true;

  for (const job of jobs) {
    statusEl.innerHTML = `<span style="color:#888">⟳ ${_h(job.name)}…</span>`;
    try {
      const d = await job.start();
      if (d.status === 'already_running') {
        statusEl.innerHTML = `<span style="color:#dcdcaa">⚠ ${_h(job.name)} ya está en curso — esperando…</span>`;
      } else if (d.error) {
        statusEl.innerHTML = `<span style="color:#f44747">Error en ${_h(job.name)}: ${_h(d.error)}</span>`;
        allOk = false; break;
      }
      // Poll until job finishes
      await new Promise((resolve, reject) => {
        const t = setInterval(async () => {
          try {
            const s = await apiFetch('/api/job-status');
            if (!s[job.runningKey]) { clearInterval(t); resolve(); }
          } catch(e) { clearInterval(t); reject(e); }
        }, 2000);
      });
      statusEl.innerHTML = `<span style="color:#4ec9b0">✓ ${_h(job.name)} completado.</span>`;
      startPolling();
    } catch(e) {
      statusEl.innerHTML = `<span style="color:#f44747">Error en ${_h(job.name)}: ${_h(e.message)}</span>`;
      allOk = false; break;
    }
  }

  btn.disabled = false;
  if (allOk) {
    statusEl.innerHTML = `<span style="color:#4ec9b0">✓ Todas las operaciones completadas sobre ${_h(root)}.</span>`;
    loadOverview();
  }
}

// ── Tool path persistence (Fix E) ────────────────────────────────────────────
function _initToolPath(inputId, storageKey) {
  const el = document.getElementById(inputId);
  if (!el) return;
  const saved = localStorage.getItem(storageKey);
  if (saved && !el.value.trim()) el.value = saved;
  el.addEventListener('input', () => localStorage.setItem(storageKey, el.value));
}

async function fillToolPath(inputId) {
  try {
    const cfg = await apiFetch('/api/config');
    const el = document.getElementById(inputId);
    if (el && cfg.library_root) { el.value = cfg.library_root; el.dispatchEvent(new Event('input')); }
  } catch(e) { /* silent */ }
}

// ── S25: PIN + URL helpers ────────────────────────────────────────────────────
async function loadAuthStatus() {
  const statusEl = document.getElementById('pin-status');
  const clearBtn = document.getElementById('btn-clear-pin');
  const logoutBtn = document.getElementById('btn-logout');
  try {
    const d = await apiFetch('/api/auth/status');
    if (statusEl) {
      if (d.pin_configured) {
        statusEl.innerHTML = '<span style="color:#4ec9b0">&#x2713; PIN activado</span> — se pedirá al abrir la app desde otra IP.';
        if (clearBtn) clearBtn.style.display = '';
        if (logoutBtn) logoutBtn.style.display = '';
      } else {
        statusEl.textContent = 'Sin PIN. La interfaz es accesible sin contraseña.';
        if (clearBtn) clearBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'none';
      }
    }
  } catch(e) {
    if (statusEl) statusEl.textContent = '—';
  }
}

async function doLogout() {
  try {
    await apiPost('/api/auth/logout', {});
    location.href = '/login';
  } catch(e) { showToast('Error al cerrar sesión', 'err'); }
}

async function setPin() {
  const input = document.getElementById('pin-input');
  const pin = input?.value.trim();
  if (!pin || pin.length < 4) { showToast('El PIN debe tener al menos 4 dígitos', 'err'); return; }
  try {
    const d = await apiPost('/api/set-pin', { pin });
    if (d.ok) { showToast('PIN activado', 'ok'); input.value = ''; loadAuthStatus(); }
    else showToast(d.error || 'Error', 'err');
  } catch(e) { showToast(e.message, 'err'); }
}

async function clearPin() {
  _showConfirm('Desactivar PIN', 'La interfaz quedará accesible sin contraseña desde cualquier IP en la red.', async () => {
    try {
      const d = await apiPost('/api/clear-pin', {});
      if (d.ok) { showToast('PIN desactivado', 'ok'); loadAuthStatus(); }
      else showToast(d.error || 'Error', 'err');
    } catch(e) { showToast(e.message, 'err'); }
  });
}

async function loadLocalUrl() {
  const el = document.getElementById('local-url-display');
  try {
    const d = await apiFetch('/api/local-url');
    if (el) el.textContent = d.url;
  } catch(e) {
    if (el) el.textContent = '—';
  }
}

function copyLocalUrl() {
  const url = document.getElementById('local-url-display')?.textContent;
  if (!url || url === 'cargando…' || url === '—') return;
  navigator.clipboard?.writeText(url).then(() => showToast('URL copiada', 'ok')).catch(() => {});
}

async function saveSettings() {
  const resultEl = document.getElementById('settings-result');
  resultEl.className = 'job-result';
  const updates = {};
  const lr = document.getElementById('cfg-library-root').value.trim();
  const ar = (document.getElementById('cfg-anbernic-root')?.value || '').trim();
  const presetEl = document.getElementById('cfg-device-preset');
  const customEl = document.getElementById('cfg-device-name-custom');
  const dn = presetEl ? (presetEl.value === 'custom' ? (customEl?.value.trim() || '') : presetEl.value) : '';
  const rr = document.getElementById('cfg-rclone-remote').value.trim();
  const su = document.getElementById('cfg-ss-user').value.trim();
  const sp = document.getElementById('cfg-ss-pass').value;
  const ch = document.getElementById('cfg-chdman').value.trim();
  const ab = document.getElementById('cfg-adb').value.trim();
  const ra = document.getElementById('cfg-ra-api-key').value.trim();
  if (lr) updates['library.library_root']        = lr;
  if (ar) updates['library.anbernic_root']        = ar;
  if (dn) updates['android.device_name']          = dn;
  if (rr) updates['sync.remote']                 = rr;
  updates['web.host'] = document.getElementById('cfg-web-host')?.value || '127.0.0.1';
  const sd = document.getElementById('cfg-ss-devid')?.value.trim()   || '';
  const sdp = document.getElementById('cfg-ss-devpass')?.value        || '';
  if (su)  updates['screenscraper.user']        = su;
  if (sp)  updates['screenscraper.pass']        = sp;
  if (sd)  updates['screenscraper.dev_id']      = sd;
  if (sdp) updates['screenscraper.dev_pass']    = sdp;
  if (ch) updates['tools.chdman']                 = ch;
  if (ab) updates['tools.adb']                    = ab;
  if (ra) updates['retroachievements.api_key']    = ra;
  const raPath = document.getElementById('cfg-retroarch-path')?.value.trim();
  if (raPath) updates['launchers.retroarch'] = raPath;
  const bkEnabledEl = document.getElementById('cfg-backup-enabled');
  const bkKeepNEl   = document.getElementById('cfg-backup-keep-n');
  if (bkEnabledEl) updates['backup.saves_enabled'] = bkEnabledEl.checked;
  if (bkKeepNEl && bkKeepNEl.value) updates['backup.saves_keep_n'] = parseInt(bkKeepNEl.value, 10);
  if (Object.keys(updates).length === 0) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Nada que guardar — rellena al menos un campo.';
    return;
  }
  try {
    const d = await apiPost('/api/config', updates);
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
    } else {
      resultEl.className = 'job-result visible success';
      resultEl.textContent = 'Guardado: ' + d.saved.join(', ') + '.';
      // Apply device name immediately without page reload
      if (dn) _applyDeviceName(dn);
      // 24-3: per-field checkmarks
      const _CFG_CHECK = {
        'library.library_root':       'cfg-check-library-root',
        'library.anbernic_root':      'cfg-check-anbernic-root',
        'sync.remote':                'cfg-check-rclone-remote',
        'screenscraper.user':         'cfg-check-ss-user',
        'screenscraper.pass':         'cfg-check-ss-pass',
        'screenscraper.dev_id':       'cfg-check-ss-devid',
        'screenscraper.dev_pass':     'cfg-check-ss-devpass',
        'tools.chdman':               'cfg-check-chdman',
        'tools.adb':                  'cfg-check-adb',
        'retroachievements.api_key':  'cfg-check-ra-api-key',
      };
      d.saved.forEach(key => {
        const id = _CFG_CHECK[key];
        if (!id) return;
        const span = document.getElementById(id);
        if (!span) return;
        span.classList.add('visible');
        setTimeout(() => span.classList.remove('visible'), 3000);
      });
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

async function saveOvPaths() {
  const pcPath = document.getElementById('ov-pc-path').value.trim();
  const abPath = document.getElementById('ov-ab-path').value.trim();
  const resultEl = document.getElementById('ov-paths-result');
  const updates = {};
  if (pcPath) updates['library.library_root'] = pcPath;
  if (abPath) updates['library.anbernic_root'] = abPath;
  if (Object.keys(updates).length > 0) {
    try {
      const d = await apiPost('/api/config', updates);
      if (d.error) {
        resultEl.className = 'job-result visible error-r';
        resultEl.textContent = 'Error: ' + d.error;
        return;
      }
    } catch(e) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + e.message;
      return;
    }
  }
  // Update UI elements that depend on abPath
  const abCb    = document.getElementById('scan-include-ab');
  const devAb   = document.getElementById('dev-anbernic');
  const abLabel = document.getElementById('scan-ab-label');
  const abLbl   = document.getElementById('ov-ab-path-label');
  if (abCb)    { abCb.disabled = !abPath; if (abPath && !abCb.checked) abCb.checked = true; }
  if (devAb)   devAb.disabled = !abPath;
  if (abLabel) abLabel.textContent = abPath || '(configura la ruta arriba)';
  if (abLbl)   abLbl.textContent = abPath ? '— ' + abPath : '';
  // Reload Anbernic stats in Overview if path changed
  if (abPath) loadOverview();

  resultEl.className = 'job-result visible ok-r';
  resultEl.textContent = 'Rutas guardadas.';
  setTimeout(() => { resultEl.className = 'job-result'; }, 3000);
}

// ── Cable Sync ────────────────────────────────────────────────────────────────

function _isAdbMode() {
  return document.querySelector('input[name="cable-ab-mode"]:checked')?.value === 'adb';
}

function _onCableModeChange() {
  const adb = _isAdbMode();
  const fsEl  = document.getElementById('cable-fs-section');
  const adbEl = document.getElementById('cable-adb-section');
  if (fsEl)  fsEl.style.display  = adb ? 'none' : '';
  if (adbEl) adbEl.style.display = adb ? '' : 'none';
}

function _onCableDryRunChange() {
  const cb = document.getElementById('cable-dry-run');
  const warn = document.getElementById('cable-dry-run-warning');
  if (warn) warn.style.display = cb?.checked ? 'none' : '';
}

function _onCableDirectionChange() {
  const dir = document.querySelector('input[name="cable-direction"]:checked')?.value;
  const row = document.getElementById('cable-sha1-row');
  if (row) row.style.display = (dir === 'anbernic_to_pc') ? '' : 'none';
}

async function testCablePath(which) {
  const inputId  = which === 'pc' ? 'cable-pc-path' : 'cable-ab-path';
  const statusId = which === 'pc' ? 'cable-pc-path-status' : 'cable-ab-path-status';
  const path = document.getElementById(inputId)?.value.trim();
  const statusEl = document.getElementById(statusId);
  if (!path) { if (statusEl) { statusEl.style.color = '#888'; statusEl.textContent = 'Introduce una ruta primero.'; } return; }
  if (statusEl) { statusEl.style.color = '#555'; statusEl.textContent = 'Verificando…'; }
  try {
    const d = await apiFetch('/api/test-path?path=' + encodeURIComponent(path));
    if (d.accessible) {
      statusEl.style.color = '#4ec9b0';
      statusEl.textContent = `✓ Accesible — ${d.entries} entradas en la carpeta`;
    } else {
      statusEl.style.color = '#f44747';
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { statusEl.style.color = '#f44747'; statusEl.textContent = '✗ ' + e.message; }
  }
}

async function detectDrives() {
  const listEl = document.getElementById('cable-drives-list');
  if (!listEl) return;
  listEl.style.display = '';
  listEl.textContent = 'Buscando…';
  try {
    const d = await apiFetch('/api/list-drives');
    if (!d.drives?.length) { listEl.textContent = 'No se encontraron unidades.'; return; }
    listEl.innerHTML = d.drives.map(dr => {
      const label = dr.label ? ` — ${dr.label}` : '';
      const size  = dr.total_bytes > 0 ? ` (${fmtSize(dr.free_bytes)} libres de ${fmtSize(dr.total_bytes)})` : '';
      return `<div style="display:flex;align-items:center;gap:8px;padding:2px 0">
        <code style="color:#ce9178;min-width:36px">${dr.letter}</code>
        <span style="color:#888">${label}${size}</span>
        <button class="btn" style="padding:1px 8px;font-size:11px;margin-left:auto" onclick="document.getElementById('cable-ab-path').value='${dr.letter.replace(/\\/g, '\\\\')}';testCablePath('ab');document.getElementById('cable-drives-list').style.display='none'">Usar</button>
      </div>`;
    }).join('');
  } catch(e) {
    listEl.textContent = 'Error: ' + e.message;
  }
}

async function detectAdbDevices() {
  const sel    = document.getElementById('cable-adb-device');
  const status = document.getElementById('cable-adb-status');
  const pathStatus = document.getElementById('cable-adb-path-status');
  if (status) { status.style.color = '#555'; status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + d.error; }
      return;
    }
    if (!d.devices?.length) {
      if (status) { status.style.color = '#ce9178'; status.textContent = 'No se encontraron dispositivos. ¿Cable conectado? ¿Depuración USB activada?'; }
      return;
    }
    if (sel) {
      sel.innerHTML = d.devices.map(dev =>
        `<option value="${dev.serial}" ${!dev.ready ? 'disabled' : ''}>
          ${dev.display}${!dev.ready ? ' — NO LISTO' : ''}
        </option>`
      ).join('');
    }
    const ready = d.devices.filter(dv => dv.ready);
    if (status) {
      status.style.color = ready.length ? '#4ec9b0' : '#ce9178';
      status.textContent = ready.length
        ? `✓ ${ready.length} dispositivo(s) listo(s)`
        : '⚠ Dispositivo detectado pero no listo — acepta el diálogo de depuración USB en la pantalla';
    }
    // Auto-test the Android path if a ready device is selected
    if (ready.length) {
      sel.value = ready[0].serial;
      testAdbPath();
    }
  } catch(e) {
    if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + e.message; }
  }
}

async function testAdbPath() {
  const serial  = document.getElementById('cable-adb-device')?.value.trim();
  const ap      = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
  const statusEl = document.getElementById('cable-adb-path-status');
  if (!serial) { if (statusEl) { statusEl.style.color = '#888'; statusEl.textContent = 'Selecciona un dispositivo primero.'; } return; }
  if (statusEl) { statusEl.style.color = '#555'; statusEl.textContent = 'Verificando ruta en el dispositivo…'; }
  try {
    const d = await apiFetch(`/api/test-adb-path?serial=${encodeURIComponent(serial)}&path=${encodeURIComponent(ap)}`);
    if (d.accessible) {
      statusEl.style.color = '#4ec9b0';
      statusEl.textContent = `✓ Ruta accesible — ${d.entries} entradas`;
    } else {
      statusEl.style.color = '#f44747';
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { statusEl.style.color = '#f44747'; statusEl.textContent = '✗ ' + e.message; }
  }
}

async function loadCableSync() {
  try {
    const cfg = await apiFetch('/api/config');
    const ovPc = document.getElementById('ov-pc-path')?.value.trim();
    const ovAb = document.getElementById('ov-ab-path')?.value.trim();
    const storedPc = localStorage.getItem('cable_pc_path') || '';
    const storedAb = localStorage.getItem('anbernic_path') || '';
    // Fill both fs and adb pc-path inputs
    _setIfEmpty('cable-pc-path',     ovPc || cfg.library_root || storedPc || '');
    _setIfEmpty('cable-adb-pc-path', ovPc || cfg.library_root || storedPc || '');
    _setIfEmpty('cable-ab-path', ovAb || cfg.anbernic_root || storedAb || '');
    if (document.getElementById('cable-pc-path')?.value) testCablePath('pc');
    if (document.getElementById('cable-ab-path')?.value) testCablePath('ab');
  } catch(_) {}
}

async function loadCableSyncPreview() {
  const adb = _isAdbMode();
  const pcPath = (adb
    ? document.getElementById('cable-adb-pc-path')
    : document.getElementById('cable-pc-path'))?.value.trim();
  const abPath = adb ? null : document.getElementById('cable-ab-path')?.value.trim();
  const direction = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const mode = adb ? 'adb' : 'sd';
  const previewEl = document.getElementById('cable-preview-result');
  if (!previewEl) return;
  previewEl.className = 'cable-preview visible';
  previewEl.innerHTML = '<span style="color:#555">Calculando…</span>';
  try {
    const params = new URLSearchParams({ mode, direction });
    if (pcPath)  params.set('pc_path',  pcPath);
    if (abPath)  params.set('ab_path',  abPath);
    const d = await apiFetch('/api/cable-sync-preview?' + params);
    const pcN  = d.pc_saves !== null && d.pc_saves !== undefined ? `<span class="cp-num">${d.pc_saves}</span>` : `<span class="cp-null">?</span>`;
    const abN  = d.android_saves !== null && d.android_saves !== undefined ? `<span class="cp-num">${d.android_saves}</span>` : `<span class="cp-null">${d.android_message || 'no accesible'}</span>`;
    const cpN  = d.to_copy !== null && d.to_copy !== undefined ? `<span class="cp-num">${d.to_copy}</span>` : `<span class="cp-null">—</span>`;
    previewEl.innerHTML =
      `<span class="cp-stat">PC: ${pcN} saves</span>` +
      `<span style="color:#444;margin-right:12px">·</span>` +
      `<span class="cp-stat">Consola: ${abN} saves</span>` +
      `<span style="color:#444;margin-right:12px">·</span>` +
      `<span class="cp-stat">Se copiarán ≈ ${cpN} archivos</span>`;
  } catch(e) {
    previewEl.innerHTML = `<span style="color:#f44747">Error: ${e.message}</span>`;
  }
}

async function doCableSync() {
  const adb = _isAdbMode();
  const pcPath = (adb
    ? document.getElementById('cable-adb-pc-path')
    : document.getElementById('cable-pc-path'))?.value.trim();
  if (!pcPath) { alert('Introduce la ruta del PC (library_root).'); return; }

  const wantSaves = document.getElementById('cable-what-saves').checked;
  const wantRoms  = document.getElementById('cable-what-roms').checked;
  if (!wantSaves && !wantRoms) { alert('Selecciona al menos qué sincronizar: saves o ROMs.'); return; }

  const what = [];
  if (wantSaves) what.push('saves');
  if (wantRoms)  what.push('roms');

  const direction    = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const dryRun       = document.getElementById('cable-dry-run').checked;
  const skipExisting = document.getElementById('cable-skip-existing')?.checked ?? true;
  const safeMode     = document.getElementById('cable-safe-mode')?.checked ?? true;
  const skipSha1Dups = direction === 'anbernic_to_pc' && (document.getElementById('cable-skip-sha1')?.checked ?? false);

  let body;
  if (adb) {
    const serial      = document.getElementById('cable-adb-device')?.value.trim();
    const androidPath = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    body = { pc_path: pcPath, use_adb: true, adb_serial: serial, android_path: androidPath,
             what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode };
  } else {
    const abPath = document.getElementById('cable-ab-path')?.value.trim();
    if (!abPath) { alert('Introduce la ruta de la tarjeta SD / consola Android.'); return; }
    // Persist paths for next session
    localStorage.setItem('anbernic_path', abPath);
    if (pcPath) localStorage.setItem('cable_pc_path', pcPath);
    body = { pc_path: pcPath, anbernic_path: abPath, what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode };
  }

  const btn      = document.getElementById('btn-cable-sync');
  const resultEl = document.getElementById('cable-result');
  btn.disabled = true;
  btn.textContent = 'Sincronizando…';
  resultEl.className = 'job-result';
  document.getElementById('cable-details-wrap').style.display = 'none';
  delete window._lastCableSyncResult;
  if (!dryRun) _requestNotifPermission();

  try {
    const d = await apiPost('/api/cable-sync', body);
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una sincronización en curso…';
      btn.disabled = false;
      btn.textContent = 'Iniciar sincronización';
      return;
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Iniciar sincronización';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

function _renderCableSyncResult(r) {
  const resultEl = document.getElementById('cable-result');
  const detailsWrap = document.getElementById('cable-details-wrap');
  const detailsList = document.getElementById('cable-details-list');
  if (!resultEl) return;

  // Guard: only render once per result
  const key = JSON.stringify({c: r.copied, e: r.errors, d: r.direction});
  if (window._lastCableSyncResult === key) return;
  window._lastCableSyncResult = key;

  if (r.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + r.error;
    return;
  }

  const verb   = r.dry_run ? 'Copiaría' : 'Copiados';
  const dirMap = { pc_to_anbernic: `PC → ${_devName}`, anbernic_to_pc: `${_devName} → PC`, newest: 'Más reciente gana', pc_to_device: `PC → ${_devName}`, device_to_pc: `${_devName} → PC` };
  const dirStr = dirMap[r.direction] || r.direction;
  const dryTag = r.dry_run ? ' [DRY RUN — nada fue copiado]' : '';
  const sha1Msg     = r.sha1_skipped > 0 ? `  |  Dups SHA1: ${r.sha1_skipped}` : '';
  const existsCount = r.details ? r.details.filter(d => d.file === 'EXISTS').length : 0;
  const existsMsg   = existsCount > 0 ? `  |  Ya existen: ${existsCount}` : '';
  const safeMsg     = r.safe_mode_skipped_overwrites > 0
    ? `  |  <span title="Modo seguro: archivos existentes no sobreescritos" style="color:#f4c842">&#x26A0; Modo seguro: ${r.safe_mode_skipped_overwrites} no sobreescritos</span>` : '';

  const needsScan = !r.dry_run && r.copied > 0 && (r.direction === 'anbernic_to_pc' || r.direction === 'newest');
  // D8-6: file count display
  const pcCount = r.pc_file_count > 0 ? r.pc_file_count : null;
  const abCount = r.ab_file_count > 0 ? r.ab_file_count : null;
  const countMsg = (pcCount && abCount && !r.dry_run && !r.use_adb)
    ? `  |  PC: ${pcCount} archivos  Consola: ${abCount} archivos`
    : '';
  const countDiff = pcCount && abCount && Math.abs(pcCount - abCount) > Math.max(pcCount, abCount) * 0.05;
  const diffWarn = countDiff ? ' <span style="color:#dcdcaa;font-size:11px">&#x26A0; Los conteos difieren — puede haber archivos que no se sincronizaron</span>' : '';
  resultEl.className = 'job-result visible success';
  if (!r.dry_run) _sendNotif('Cable Sync completado', r.copied + ' archivos copiados');
  resultEl.innerHTML = `${verb}: <strong>${r.copied}</strong> archivo(s) (${fmtSize(r.copied_bytes)})  |  Omitidos: ${r.skipped}  |  Errores: <strong style="${r.errors > 0 ? 'color:#f44747' : ''}">${r.errors}</strong>${existsMsg}${sha1Msg}${safeMsg}${countMsg}${diffWarn}  —  ${dirStr}${dryTag}`
    + (needsScan ? `<br><span style="color:#dcdcaa;font-size:11px">&#x26A0; Archivos copiados al PC — indexa la BD: <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:6px" onclick="quickScanPC()">Escanear ahora</button></span>` : '')
    + (!r.dry_run && r.copied > 0 && r.direction === 'newest'
        ? '<br><span style="color:#569cd6;font-size:11px">Para actualizar conteos en Overview: <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:6px" onclick="quickScanPC()">Escanear PC</button> <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:4px" onclick="quickScanAndroid()">Escanear consola</button></span>'
        : '');

  if (r.details && r.details.length > 0) {
    // Separate error entries from normal entries
    const errEntries = r.details.filter(d => d.file && d.file.startsWith('ERROR'));
    const okEntries  = r.details.filter(d => !d.file || !d.file.startsWith('ERROR'));

    let detailHtml = '';
    if (errEntries.length > 0) {
      detailHtml += `<div style="background:#2a1010;border:1px solid #f44747;border-radius:4px;padding:8px 12px;margin-bottom:8px">`
        + `<div style="color:#f44747;font-weight:bold;margin-bottom:6px;font-size:12px">&#x2717; ${errEntries.length} archivo(s) fallaron al copiarse:</div>`
        + errEntries.map(d => `<div style="padding:1px 0;color:#f99;font-size:11px">&#x25B8; ${_h(d.path)}</div>`).join('')
        + `</div>`;
    }
    detailHtml += okEntries.map(d => {
      const isDup    = d.file === 'DUP';
      const isExists = d.file === 'EXISTS';
      const isSafe   = d.file === 'SAFE';
      const tagColor = isDup ? '#569cd6' : isExists ? '#444' : isSafe ? '#f4c842' : '#4ec9b0';
      return `<div style="padding:2px 0;color:#888"><span style="color:${tagColor};margin-right:8px">${_h(d.file)}</span>${_h(d.path)}</div>`;
    }).join('');

    detailsList.innerHTML = detailHtml;
    detailsWrap.style.display = '';
  }
}

// ── Cable Sync log viewer ─────────────────────────────────────────────────────
function toggleCableSyncLog() {
  const wrap = document.getElementById('cable-log-wrap');
  if (!wrap) return;
  const visible = wrap.style.display !== 'none';
  wrap.style.display = visible ? 'none' : '';
  if (!visible) loadCableSyncLog();
}

async function loadCableSyncLog() {
  const el = document.getElementById('cable-log-content');
  if (!el) return;
  el.textContent = 'Cargando…';
  try {
    const d = await apiFetch('/api/cable-sync-log');
    el.textContent = d.log || '(Log vacío — aún no se ha ejecutado Cable Sync)';
    el.scrollTop = el.scrollHeight;
  } catch(e) {
    el.textContent = 'Error: ' + e.message;
  }
}

// ── Junk file cleaner (Fix F) ────────────────────────────────────────────────
async function exportPegasus() {
  const el = document.getElementById('pegasus-result');
  if (el) { el.textContent = 'Exportando...'; el.style.display = 'block'; el.className = 'job-result visible'; }
  try {
    const d = await apiPost('/api/export-pegasus', {});
    if (d.error) { if (el) { el.textContent = '\u2717 ' + d.error; el.className = 'job-result visible error-r'; } return; }
    if (el) { el.textContent = `\u2713 ${d.games} juegos en ${d.platforms} plataformas exportados`; el.className = 'job-result visible success'; }
    showToast('Pegasus exportado: ' + d.games + ' juegos', 'ok');
  } catch(e) { if (el) { el.textContent = '\u2717 ' + e.message; el.className = 'job-result visible error-r'; } }
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
  if (el) el.style.display = el.style.display === 'none' ? '' : 'none';
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

// ── Library Report ───────────────────────────────────────────────────────────
let _reportData = null;

function showReportTab(name) {
  document.querySelectorAll('.rpt-tab').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.rpt-tab-btn').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById('rpt-tab-' + name);
  const btn = document.getElementById('rpt-tab-btn-' + name);
  if (tab) tab.style.display = '';
  if (btn) btn.classList.add('active');
}

async function generateReport() {
  const pathInput = document.getElementById('report-path');
  const path = pathInput?.value.trim() || '';
  const loadingEl  = document.getElementById('report-loading');
  const contentEl  = document.getElementById('report-content');
  const exportBtn  = document.getElementById('btn-export-report');

  if (loadingEl) loadingEl.style.display = '';
  if (contentEl) contentEl.style.display = 'none';
  if (exportBtn) exportBtn.style.display = 'none';

  try {
    const params = path ? '?path=' + encodeURIComponent(path) : '';
    _reportData = await apiFetch('/api/library-report' + params);

    // Warn if the filesystem path is not accessible (e.g. SD card disconnected)
    const notAccessibleBanner = document.getElementById('report-not-accessible');
    if (notAccessibleBanner) {
      if (_reportData.path_accessible === false) {
        notAccessibleBanner.style.display = '';
        notAccessibleBanner.textContent = '\u26A0 La ruta "' + (_reportData.source_path || path) + '" no est\xe1 accesible desde este PC. Los datos del informe provienen de la base de datos local (sin escaneo de disco).';
      } else {
        notAccessibleBanner.style.display = 'none';
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

    if (contentEl) contentEl.style.display = '';
    if (exportBtn) exportBtn.style.display = '';
    showReportTab('zips');
  } catch(e) {
    const el = document.getElementById('rpt-tab-zips');
    if (el) el.innerHTML = `<p class="error-msg">${e.message}</p>`;
    if (contentEl) contentEl.style.display = '';
    showReportTab('zips');
  } finally {
    if (loadingEl) loadingEl.style.display = 'none';
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
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Tu archivo</th><th>Título RA</th><th>Logros</th><th>Puntos</th><th>Buscar</th>';
    html += '</tr></thead><tbody>';
    html += pageAlts.map(a => {
      const q = _googleQuery(a.ra_title, a.platform);
      return `<tr>
      <td>${a.platform}</td>
      <td title="${a.filename}" style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a.filename}</td>
      <td><a href="https://retroachievements.org/game/${a.ra_id}" target="_blank" style="color:#4ec9b0">${a.ra_title}</a></td>
      <td style="text-align:right;color:#ce9178">${a.ra_achievements}</td>
      <td style="text-align:right;color:#555">${a.ra_points}</td>
      <td style="white-space:nowrap"><button class="btn" style="font-size:10px;padding:2px 7px" onclick="_copyText(${JSON.stringify(q)})">📋 Copiar</button></td>
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
    `</body></html>`,
  ];
  const blob = new Blob([lines.join('\n')], {type: 'text/html;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `informe-biblioteca-${ts.replace(/[: ]/g,'-')}.html`;
  a.click();
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(msg, type='ok', duration=3000) {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity='0'; t.style.transition='opacity .3s'; setTimeout(() => t.remove(), 320); }, duration);
}

// ── Auto-sync UI ─────────────────────────────────────────────────────────────
let _autoSyncTimer = null;
let _autoSyncEnabled = true;

function _updateAutoSyncBanner(data, sdStatus) {
  const banner  = document.getElementById('auto-sync-banner');
  const icon    = document.getElementById('auto-sync-banner-icon');
  const text    = document.getElementById('auto-sync-banner-text');
  if (!banner || !icon || !text) return;

  const enabled = data.enabled;
  const s       = data.status || {};
  const state   = s.state || 'waiting';
  const sdState = sdStatus ? (sdStatus.state || 'waiting') : 'waiting';

  _autoSyncEnabled = enabled;
  _updateAutoSyncToggleUI(enabled);

  // Status text in the card
  const statusEl = document.getElementById('auto-sync-status-text');
  if (statusEl) {
    if (!enabled) {
      statusEl.textContent = 'Sync automatico desactivado';
      statusEl.style.color = '#ce9178';
    } else if (state === 'syncing') {
      const dev = s.last_device || '';
      statusEl.textContent = 'Sincronizando' + (dev ? ' con ' + dev : '') + '...';
      statusEl.style.color = '#4ec9b0';
    } else if (state === 'idle' && s.last_sync_at) {
      statusEl.textContent = 'Ultimo sync: ' + s.last_sync_at + (s.last_error ? ' | Error: ' + s.last_error : '');
      statusEl.style.color = s.last_error ? '#ce9178' : '#4ec9b0';
    } else {
      statusEl.textContent = 'Esperando conexion...';
      statusEl.style.color = '#888';
    }
  }

  // Banner
  if (!enabled) {
    banner.style.display = 'flex';
    banner.style.background = '#2a2a12';
    banner.style.borderBottomColor = '#4a4a1a';
    icon.textContent = 'Sync automatico desactivado';
    icon.style.color = '#ce9178';
    text.textContent = 'Activa el sync automatico en la pestana Cable Sync.';
    text.style.color = '#888';
  } else if (state === 'syncing' || sdState === 'syncing') {
    const dev = state === 'syncing' ? (s.last_device || 'consola') : 'tarjeta SD';
    banner.style.display = 'flex';
    banner.style.background = '#0d1f16';
    banner.style.borderBottomColor = '#1a4a2a';
    icon.textContent = sdState === 'syncing' ? 'Sincronizando saves (tarjeta SD)...' : ('Sincronizando saves con ' + dev + '...');
    icon.style.color = '#4ec9b0';
    text.textContent = '';
  } else if (state === 'idle' && s.last_sync_at) {
    banner.style.display = 'flex';
    banner.style.background = '#0d1a12';
    banner.style.borderBottomColor = '#1a3a22';
    const lastErr = s.last_error ? ' (' + s.last_error + ')' : '';
    icon.textContent = 'Ultimo sync automatico: ' + s.last_sync_at + lastErr;
    icon.style.color = s.last_error ? '#ce9178' : '#4ec9b0';
    text.textContent = '';
  } else if (sdState === 'watching') {
    banner.style.display = 'flex';
    banner.style.background = '#0d1520';
    banner.style.borderBottomColor = '#1a2a3a';
    icon.textContent = 'Tarjeta SD detectada — sincronizacion automatica activa';
    icon.style.color = '#4ec9b0';
    text.textContent = '';
  } else {
    banner.style.display = 'none';
  }

  // 24-5: always update the compact header indicator
  const hdr = document.getElementById('header-last-sync');
  if (hdr) {
    const lastAt = s.last_sync_at;
    if (lastAt) {
      hdr.textContent = `Sync ${_relTime(lastAt)}`;
      hdr.className = s.last_error ? 'sync-err' : 'sync-ok';
      hdr.title = `Última sync: ${lastAt}` + (s.last_error ? ` · Error: ${s.last_error}` : '');
    } else if (enabled) {
      hdr.textContent = 'Sync en espera';
      hdr.className = '';
      hdr.title = 'Sin sincronizaciones aún';
    } else {
      hdr.textContent = '';
      hdr.className = '';
    }
  }
}

function _updateAutoSyncToggleUI(enabled) {
  const wrap  = document.getElementById('auto-sync-toggle-wrap');
  const knob  = document.getElementById('auto-sync-toggle-knob');
  const label = document.getElementById('auto-sync-toggle-label');
  if (!wrap) return;
  if (enabled) {
    wrap.style.background = '#4ec9b0';
    if (knob) knob.style.left = '21px';
    if (label) { label.textContent = 'Activado'; label.style.color = '#4ec9b0'; }
  } else {
    wrap.style.background = '#444';
    if (knob) knob.style.left = '3px';
    if (label) { label.textContent = 'Desactivado'; label.style.color = '#888'; }
  }
}

async function toggleAutoSync() {
  try {
    const d = await apiPost('/api/auto-sync-toggle', {});
    _autoSyncEnabled = d.enabled;
    _updateAutoSyncToggleUI(d.enabled);
    const statusEl = document.getElementById('auto-sync-status-text');
    if (statusEl) {
      statusEl.textContent = d.enabled ? 'Esperando conexion...' : 'Sync automatico desactivado';
      statusEl.style.color = d.enabled ? '#888' : '#ce9178';
    }
    showToast(d.enabled ? 'Sync automatico activado' : 'Sync automatico desactivado', d.enabled ? 'ok' : 'info');
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  }
}

async function saveAutoSyncSettings() {
  const dir       = document.getElementById('auto-sync-direction')?.value || 'newest';
  const conflict  = document.getElementById('auto-sync-conflict')?.value  || 'newest';
  const androidP  = document.getElementById('auto-sync-android-path')?.value.trim() || '/storage/emulated/0/RetroArch';
  const resultEl  = document.getElementById('auto-sync-save-result');
  try {
    const d = await apiPost('/api/auto-sync-save', {
      'sync.auto_sync_direction':   dir,
      'sync.conflict_policy':       conflict,
      'sync.auto_sync_android_path': androidP,
      'sync.auto_sync_enabled':     _autoSyncEnabled,
    });
    if (d.error) {
      if (resultEl) { resultEl.style.display=''; resultEl.style.color='#f44747'; resultEl.textContent = 'Error: ' + d.error; }
    } else {
      if (resultEl) { resultEl.style.display=''; resultEl.style.color='#4ec9b0'; resultEl.textContent = 'Guardado'; setTimeout(() => { if (resultEl) resultEl.style.display='none'; }, 2500); }
      showToast('Ajustes de auto-sync guardados', 'ok');
    }
  } catch(e) {
    if (resultEl) { resultEl.style.display=''; resultEl.style.color='#f44747'; resultEl.textContent = 'Error: ' + e.message; }
  }
}

async function _pollAutoSync() {
  try {
    const [d, sdStatus] = await Promise.all([
      apiFetch('/api/auto-sync-status'),
      apiFetch('/api/sd-sync-status').catch(() => null),
    ]);
    _updateAutoSyncBanner(d, sdStatus);
    // Populate fields on first load
    const dirEl = document.getElementById('auto-sync-direction');
    const confEl = document.getElementById('auto-sync-conflict');
    const pathEl = document.getElementById('auto-sync-android-path');
    if (dirEl && !dirEl.dataset.loaded && d.config) {
      dirEl.value = d.config.direction || 'newest';
      if (confEl) confEl.value = d.config.conflict_policy || 'newest';
      if (pathEl) pathEl.value = d.config.android_path || '/storage/emulated/0/RetroArch';
      dirEl.dataset.loaded = '1';
    }
  } catch(_) { /* silent */ }
}

function startAutoSyncPolling() {
  if (_autoSyncTimer) return;
  _pollAutoSync();
  _autoSyncTimer = setInterval(_pollAutoSync, 5000);
}

// ── Inbox (Pilar 2) ──────────────────────────────────────────────────────────

function loadInbox() {
  // Pre-fill from config via /api/config
  apiFetch('/api/config').then(cfg => {
    const pathEl   = document.getElementById('inbox-path');
    const targetEl = document.getElementById('inbox-target');
    const delEl    = document.getElementById('inbox-delete-source');
    const autoEl   = document.getElementById('inbox-auto-process');
    if (pathEl   && cfg.inbox_path)         pathEl.value    = cfg.inbox_path;
    if (targetEl && cfg.inbox_target_root)  targetEl.value  = cfg.inbox_target_root;
    if (delEl    && cfg.inbox_delete_source !== undefined) delEl.checked  = cfg.inbox_delete_source;
    if (autoEl   && cfg.inbox_auto_process  !== undefined) autoEl.checked = cfg.inbox_auto_process;
    // Restore from localStorage as override
    const savedPath = localStorage.getItem('inbox_path');
    if (savedPath && pathEl && !pathEl.value) pathEl.value = savedPath;
    // Show watcher info
    _pollInboxWatcher();
  }).catch(() => {});
}

function fillInboxTarget() {
  apiFetch('/api/config').then(cfg => {
    const el = document.getElementById('inbox-target');
    if (el && cfg.library_root) el.value = cfg.library_root;
  }).catch(() => {});
}

async function scanInbox() {
  const pathEl = document.getElementById('inbox-path');
  const inboxPath = pathEl ? pathEl.value.trim() : '';
  if (!inboxPath) { showToast('Introduce la carpeta Inbox primero', 'err'); return; }
  localStorage.setItem('inbox_path', inboxPath);
  const btn = document.getElementById('btn-inbox-scan');
  if (btn) { btn.disabled = true; btn.textContent = 'Analizando…'; }
  const summaryEl   = document.getElementById('inbox-summary');
  const summaryText = document.getElementById('inbox-summary-text');
  const filesWrap   = document.getElementById('inbox-files-wrap');
  const tbody       = document.getElementById('inbox-files-tbody');
  try {
    const d = await apiFetch('/api/inbox-scan?path=' + encodeURIComponent(inboxPath));
    if (d.error) { showToast('Error: ' + d.error, 'err'); return; }
    // Summary
    const platStr = Object.entries(d.by_platform || {}).map(([k,v]) => k + ' x' + v).join(' · ');
    if (summaryText) summaryText.innerHTML =
      '<strong style="color:#d4d4d4">' + d.total + ' archivos</strong>' +
      (d.zips > 0 ? ' · <span style="color:#dcdcaa">' + d.zips + ' ZIPs</span>' : '') +
      (d.unrecognized > 0 ? ' · <span style="color:#f14c4c">' + d.unrecognized + ' no reconocidos</span>' : '') +
      (platStr ? ' &nbsp;|&nbsp; ' + platStr : '');
    if (summaryEl) summaryEl.style.display = '';
    // Table
    if (tbody) {
      tbody.innerHTML = (d.files || []).map(f => {
        const typeColor = f.type === 'zip' ? '#dcdcaa' : f.type === 'disc_image' ? '#4ec9b0' : f.type === 'rom' ? '#9cdcfe' : '#555';
        const platBadge = f.platform_guess ? '<span class="badge">' + f.platform_guess + '</span>' : '<span style="color:#555">—</span>';
        const extract   = f.needs_extraction ? '<span style="color:#dcdcaa">extraer ZIP</span>' : '';
        return '<tr style="border-bottom:1px solid #1e1e2e">' +
          '<td style="padding:4px 8px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + f.name + '">' + _h(f.name) + '</td>' +
          '<td style="padding:4px 8px;color:' + typeColor + '">' + f.type + '</td>' +
          '<td style="padding:4px 8px">' + platBadge + '</td>' +
          '<td style="padding:4px 8px;text-align:right;color:#888">' + fmtSize(f.size_bytes) + '</td>' +
          '<td style="padding:4px 8px">' + extract + '</td>' +
          '</tr>';
      }).join('');
    }
    if (filesWrap) filesWrap.style.display = d.total > 0 ? '' : 'none';
    if (d.total === 0) showToast('La carpeta Inbox está vacía', 'ok');
  } catch(e) {
    showToast('Error al analizar: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Analizar carpeta'; }
  }
}

async function runInbox() {
  const pathEl   = document.getElementById('inbox-path');
  const targetEl = document.getElementById('inbox-target');
  const delEl    = document.getElementById('inbox-delete-source');
  const inboxPath = pathEl ? pathEl.value.trim() : '';
  if (!inboxPath) { showToast('Introduce la carpeta Inbox primero', 'err'); return; }
  const targetPath   = targetEl ? targetEl.value.trim() : '';
  const deleteSource = delEl ? delEl.checked : false;
  const btn = document.getElementById('btn-inbox-run');
  if (btn) { btn.disabled = true; btn.textContent = 'Organizando…'; }
  const resultEl = document.getElementById('inbox-result');
  if (resultEl) { resultEl.className = 'job-result'; resultEl.textContent = ''; }
  try {
    const d = await apiPost('/api/inbox-run', { path: inboxPath, target_root: targetPath, delete_source: deleteSource });
    if (d.status === 'already_running') {
      showToast('Ya hay un proceso Inbox en curso…', 'ok');
      startPolling();
      return;
    }
    if (d.error) { showToast('Error: ' + d.error, 'err'); return; }
    showToast('Pipeline Inbox iniciado', 'ok');
    startPolling();
  } catch(e) {
    showToast('Error al lanzar: ' + e.message, 'err');
    if (btn) { btn.disabled = false; btn.textContent = 'Organizar todo'; }
  }
}

function _applyInboxProgress(s) {
  const wrap    = document.getElementById('inbox-progress-wrap');
  const stepEl  = document.getElementById('inbox-progress-step');
  const cntEl   = document.getElementById('inbox-progress-counts');
  const barEl   = document.getElementById('inbox-progress-bar');
  const fileEl  = document.getElementById('inbox-progress-file');
  const btn     = document.getElementById('btn-inbox-run');

  const _STEP_LABELS = {
    'extracting':  'Paso 1/6: Extrayendo ZIPs',
    'scanning':    'Paso 2/6: Escaneando archivos',
    'matching':    'Paso 3/6: Cotejando catálogos',
    'planning':    'Paso 4/6: Planificando renames',
    'renaming':    'Paso 5/6: Renombrando',
    'organizing':  'Paso 6/6: Organizando por plataforma',
    'done':        'Completado',
  };

  if (s.inbox_running && s.inbox_progress) {
    if (wrap) wrap.style.display = '';
    const p = s.inbox_progress;
    if (stepEl) stepEl.textContent = _STEP_LABELS[p.step] || p.step || 'Procesando…';
    const pct = (p.total > 0) ? Math.round((p.processed / p.total) * 100) : 0;
    if (barEl) barEl.style.width = pct + '%';
    if (cntEl) cntEl.textContent = p.total > 0 ? p.processed + ' / ' + p.total + ' (' + pct + '%)' : '';
    if (fileEl) fileEl.textContent = p.current_file || '';
    if (btn) { btn.disabled = true; btn.textContent = 'Organizando…'; }
  } else if (!s.inbox_running) {
    if (wrap) wrap.style.display = 'none';
    if (btn) { btn.disabled = false; btn.textContent = 'Organizar todo'; }
    if (s.inbox_result) {
      const ts = s.inbox_result.result_ts || JSON.stringify(s.inbox_result);
      if (_shownResultTs.inbox !== ts) {
        _shownResultTs.inbox = ts;
        _renderInboxResult(s.inbox_result);
      }
    }
  }
}

function _renderInboxResult(r) {
  const el = document.getElementById('inbox-result');
  if (!el) return;
  if (r.error) {
    el.className = 'job-result visible error-r';
    el.textContent = 'Error: ' + r.error;
    return;
  }
  el.className = 'job-result visible';
  let html = '<strong style="color:#4ec9b0">Pipeline completado</strong><br>';
  html += 'ZIPs extraidos: <strong>' + (r.zips_extracted || 0) + '</strong> &nbsp;';
  html += 'ROMs escaneados: <strong>' + (r.roms_scanned || 0) + '</strong> &nbsp;';
  html += 'Cotejados: <strong>' + (r.matched || 0) + '</strong> &nbsp;';
  html += 'Renombrados: <strong>' + (r.renamed || 0) + '</strong> &nbsp;';
  html += 'Organizados: <strong>' + (r.organized || 0) + '</strong>';
  if (r.target_root) html += '<br><span style="color:#555;font-size:11px">Destino: ' + r.target_root + '</span>';
  if ((r.rename_errors || []).length > 0) {
    html += '<details style="margin-top:8px"><summary style="color:#dcdcaa;cursor:pointer">' + r.rename_errors.length + ' errores de rename</summary><ul style="margin:4px 0;padding-left:16px;font-size:11px;color:#888">';
    r.rename_errors.forEach(e => { html += '<li>' + _h(e) + '</li>'; });
    html += '</ul></details>';
  }
  if ((r.organize_errors || []).length > 0) {
    html += '<details style="margin-top:4px"><summary style="color:#dcdcaa;cursor:pointer">' + r.organize_errors.length + ' errores al organizar</summary><ul style="margin:4px 0;padding-left:16px;font-size:11px;color:#888">';
    r.organize_errors.forEach(e => { html += '<li>' + _h(e) + '</li>'; });
    html += '</ul></details>';
  }
  el.innerHTML = html;
  showToast('Inbox: ' + (r.organized || 0) + ' juegos organizados', 'ok');
}

async function saveInboxSettings() {
  const pathEl   = document.getElementById('inbox-path');
  const targetEl = document.getElementById('inbox-target');
  const delEl    = document.getElementById('inbox-delete-source');
  const autoEl   = document.getElementById('inbox-auto-process');
  const updates = {};
  if (pathEl)   updates['inbox.path']          = pathEl.value.trim();
  if (targetEl) updates['inbox.target_root']   = targetEl.value.trim();
  if (delEl)    updates['inbox.delete_source'] = delEl.checked;
  if (autoEl)   updates['inbox.auto_process']  = autoEl.checked;
  try {
    await apiPost('/api/config', updates);
    showToast('Ajustes de Inbox guardados', 'ok');
  } catch(e) {
    showToast('Error al guardar: ' + e.message, 'err');
  }
}

async function _pollInboxWatcher() {
  try {
    const d = await apiFetch('/api/inbox-watcher-status');
    const el = document.getElementById('inbox-watcher-info');
    const txt = document.getElementById('inbox-watcher-text');
    if (!el || !txt) return;
    if (d.watching) {
      el.style.display = '';
      const pending = d.pending_files || 0;
      const lastCheck = d.last_check ? d.last_check.replace('T',' ').slice(0,16) : '—';
      txt.innerHTML = 'Daemon activo · Ultimo chequeo: ' + lastCheck +
        (pending > 0 ? ' · <span style="color:#dcdcaa">' + pending + ' archivos pendientes</span>' : ' · sin archivos pendientes');
    } else {
      el.style.display = 'none';
    }
  } catch(_) {}
}

// ── Init ─────────────────────────────────────────────────────────────────────
_initColPicker();
loadOverview();
startAutoSyncPolling();

// ── S24 init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // S25: Check PIN status on load (shows logout button in header if needed)
  loadAuthStatus();
  loadLocalUrl();

  // 24-4: Confirm modal OK button
  const confirmOkBtn = document.getElementById('confirm-ok');
  if (confirmOkBtn) confirmOkBtn.addEventListener('click', () => {
    if (_confirmOkHandler) _confirmOkHandler();
    _closeConfirm();
  });

  // 24-1: Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
    if (e.key === 'Escape') {
      if (document.getElementById('game-panel')?.classList.contains('open')) { closeGamePanel(); return; }
      _closeConfirm();
      closeWizard?.();
      return;
    }
    // Don't trigger nav shortcuts when a modal is open
    const confirmOpen = document.getElementById('confirm-modal')?.style.display !== 'none';
    const wizardOpen  = document.getElementById('wizard-modal')?.style.display  !== 'none';
    if (confirmOpen || wizardOpen) return;
    const k = e.key.toLowerCase();
    if (k === 's') { e.preventDefault(); showTab('sync'); }
    if (k === 'g') { e.preventDefault(); showTab('games'); }
    if (k === 'r') {
      e.preventDefault();
      const t = document.querySelector('nav button.active')?.id?.replace('nav-', '');
      if (t) showTab(t);
    }
  });
});
