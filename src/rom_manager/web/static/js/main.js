// js/main.js — Retro Vault module entry point
// Loaded as type="module" (deferred) before app.js.
// Sets up window globals so inline onclick handlers and app.js can call these functions.

import { AppState, getActiveDevice, getDevName, setActiveDevice, setDevName, getDeviceConnected, getDeviceConnectReason, startDeviceStatusPolling, stopDeviceStatusPolling } from './state.js';
import { showToast } from './components/toast.js';
import { _showConfirm, _closeConfirm } from './components/modal.js';
import {
  _onDevicePresetChange,
  loadSettings, migrateSplitDb, testChdman, testMaxcso, testAdbBinary,
  loadLogViewer, downloadLog, loadTools, _setIfEmpty,
  doBatchRun, _initToolPath, fillToolPath,
  loadAuthStatus, doLogout, setPin, clearPin,
  loadLocalUrl, copyLocalUrl, renderQR,
  saveSettings, testNotification, saveOvPaths,
  doMigrateSavesStructure,
  browseFolder, browseFile, detectRetroArch,
  loadTrashStatus, emptyTrash,
} from './tabs/config.js';
import {
  _onScanAdbChange, detectAdbDevicesForScan,
  doScan, quickScanPC, quickScanAndroid,
  doFixPlatforms, doMatch,
  loadCatalogStatus, importArcadeCatalog, importDats, loadDatCatalogList, downloadDats,
} from './tabs/scan.js';
import {
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  exportWishlist,
  loadCollectionStatsV2, toggleColStats,
  toggleDiff, loadLibraryDiff, syncSelected, syncConflict, deleteSelectedStorage,
  _diffToggleAll, _syncAllSide,
  toggleDiskUsage, loadDiskUsage,
  toggleCompleteness,
  toggleOverrides, loadOverrides,
  openOverrideEditor, closeOverrideEditor, saveOverrideEditor,
  copyOverride,
} from './tabs/collection.js';
import {
  setToolsContext, _initToolsContext,
} from './tabs/duplicates.js';
import {
  _chk, toggleShaLength, _planQueryString,
  loadPlan, applyKeepBoth, doApply, doUndoLastApply, _discardCollisionEntry,
} from './tabs/organize.js';
import {
  loadReviewQueue, applyReviewGroup, chooseReviewEntry,
  markReviewGroupIntentional, applyAllReviewRecommendations, doResolveRaConflicts,
} from './tabs/review_copies.js';
import {
  startPolling, _applyJobStatus, _showJobResult,
} from './jobs.js';
import {
  doExportGamelistsAll,
  loadScraperSummary,
  loadSsQuota,
  loadSsCredsStatus,
  loadScrapePlatforms,
  doScrape,
  doExportGamelists,
} from './tabs/scraper.js';
import {
  updateInboxBadge,
  _initInboxBadge,
  inboxDragOver,
  inboxDragLeave,
  inboxDrop,
  loadInbox,
  fillInboxTarget,
  scanInbox,
  runInbox,
  _applyInboxProgress,
  _renderInboxResult,
  loadInboxConflicts,
  resolveInboxConflict,
  saveInboxSettings, autoSaveInboxToggle,
  _pollInboxWatcher,
} from './tabs/inbox.js';
import {
  gamesState,
  applyColVisibility, _initColPicker, toggleColPicker,
  goToGames, onGamesSearchChange, onGamesFilterChange,
  loadFilterOptions, toggleFavoritesFilter, _refreshTagFilter, toggleRowFavorite,
  markFilteredForAnbernic, setInitialFilter,
  _platHex, _platBadge, fmtSize,
  loadGames, setPlayStatus, renderPagination, setGamesView, _renderGamesGrid,
  _gpSetFavStar,
  gpShowPlaytimeInfo, gpRefreshPlaytime,
  openGamePanel, closeGamePanel,
  gpSetStatus, gpToggleFavorite,
  gpAddTag, gpRemoveTag,
  gpSetRating,
  gpLaunch, gpOpenFolder,
  loadSaveBackupsResult, restoreBackup,
  gpNotesInput, gpToggleMetaEdit, gpSaveMetaFields,
  gpScrapeSingle, gpApplyScrape, gpCopyAssetToEsde,
  loadGameSyncHistory,
  enterTvMode, exitTvMode, loadTvGrid, _tvMoveFocus,
  _tvActive, _tvFocusIdx, _tvCols, _tvGames,
  loadRecommendations, dismissRecommendations, loadGameScreenshots, loadGameStatshots,
} from './tabs/games.js';
import {
  loadEsdeStatus, loadBiosStatus, loadRetroArchCheck, generateEsSystems,
  doRaCheck, _renderRaResult, _updateRaProgress, filterRaByPlatform, clearRaFilter, _raGoToPage, _raSelectAlternative, discardRaNoSupport,
  _copyText, _googleQuery, _archiveOrgUrl, _openArchiveOrg, _copyArchiveOrgLink,
  doHealthCheck, _renderHealthResult, _filterHealthIssues, loadOperationsTimeline, _clearHealthFilter,
  doJunkScan, _renderJunkResult, junkToggleCat, junkSelectAll, junkRevealCat, junkCatCheck, junkDelete, zipRouteApply,
  doFindOrphans, doDeleteOrphans, doMoveOrphansToArchive, moveOrphanedSave,
  doLibraryDoctor, doctorMoveRom, doctorDeleteDir, doctorResolveAll, doFolderAnalysis,
  loadUnmatchedDiagnosis, downloadMissingDats,
  generateReport, showReportTab, _renderReportZips, _renderReportPlaylists, _renderReportMultidisc, _renderReportOrphans, _renderReportRA, _renderReportChd, exportReportHtml,
} from './tabs/esde.js';
import {
  _relTime, _emptyState, card, _getPlatformLogo,
  _loadNewGameSuggestion, openGameSuggestionPanel, _renderMonthlyChart,
  loadOverview, _renderPlatformGrid, loadCollectionCompleteness,
  showWizard, closeWizard, wizardAutoDetect, startSetup,
  _renderWizSteps, _pollSetupProgress, _showSetupResult, wizardGoToOrganize, loadActivityHeatmap,
} from './tabs/overview.js';
import {
  doConvertChd, applyChdFilter, _renderChdResult,
  doConvertCso, _renderCsoResult,
  doCleanupZips, doCleanupCueBin, doExtractZip,
  doGenerateM3U, autodetectM3UFolders,
  doVerifyMultidisc, generateM3uFromVerify,
  doExportLpl,
  doN64Scan, doN64Convert,
  createLibraryStructure, organizeLibrary,
  doVerifyChd, _renderVerifyChdResult, applyVerifyChdFilter,
  loadPatchList, selectPatch, clearPatchSelection, applySelectedPatch, loadPatchLog,
  _initToolsImports,
} from './tabs/tools.js';
import {
  loadSync,
  loadAssets,
  showOrphanAssets,
  loadSystemStatus,
  detectCloudFolder,
  useCloudFolder,
  loadAutostart,
  toggleAutostart,
  shutdownServer,
  _checkAndroidUserAgent,
  loadAnbernicTab,
  copyAnbernicCmd,
  copyAnbernicUrl,
  tvCheckStatus, tvCheckServer, tvToggleSetup, tvCopySetupCmd, tvStartSync, tvShowResult, tvReset, tvSkipToFull,
  loadRcloneStatus,
  openRcloneConfig,
  testRcloneRemote,
  applyRcloneRemote,
  applyRcloneSavesStates,
  backupNow,
  loadManualBackups,
  _isAdbMode,
  _onCableModeChange,
  _onCableDryRunChange,
  _onCableWhatRomsChange,
  _onCableDirectionChange,
  testCablePath,
  detectDrives,
  detectAdbDevices,
  detectAndroidRaConfigDir,
  testAdbPath,
  loadCableSync,
  loadCableSyncPreview,
  doCableSync,
  doQuickSync,
  _renderCableSyncResult,
  toggleCableSyncLog,
  loadCableSyncLog,
  runSyncDoctor,
  exportPegasus,
  _updateAutoSyncBanner,
  _updateAutoSyncToggleUI,
  toggleAutoSync,
  saveAutoSyncSettings,
  saveConflictPolicy,
  startAutoSyncPolling,
  _onTreeDiffSourceChange,
  _loadTreeDiffDevices,
  doTreeDiff,
  _renderTreeDiff,
  loadSaveComparison,
  doLibraryDiff,
  doSaveFragmentation,
  doSync,
  _renderSyncResult,
  promptSyncNow,
  loadCloudAuthStatus,
  startCloudAuth,
  cancelCloudAuth,
  disconnectCloud,
  useRemoteForSync,
  openCloudSetup,
} from './tabs/sync.js';
import { openFlowWizard, closeFlowWizard } from './flow_wizard.js';

// Expose all migrated functions on window for:
// - Inline onclick="xxx()" handlers in index.html
// - Legacy app.js callers (e.g. DOMContentLoaded calling loadAuthStatus)
Object.assign(window, {
  // flow_wizard.js — run-all wizard
  openFlowWizard, closeFlowWizard,
  // games.js — games tab, game panel, TV mode
  gamesState,
  applyColVisibility, _initColPicker, toggleColPicker,
  goToGames, onGamesSearchChange, onGamesFilterChange,
  loadFilterOptions, toggleFavoritesFilter, _refreshTagFilter, toggleRowFavorite,
  markFilteredForAnbernic, setInitialFilter,
  _platHex, _platBadge, fmtSize,
  loadGames, setPlayStatus, renderPagination, setGamesView, _renderGamesGrid,
  _gpSetFavStar,
  gpShowPlaytimeInfo, gpRefreshPlaytime,
  openGamePanel, closeGamePanel,
  gpSetStatus, gpToggleFavorite,
  gpAddTag, gpRemoveTag,
  gpSetRating,
  gpLaunch, gpOpenFolder,
  loadSaveBackupsResult, restoreBackup,
  gpNotesInput, gpToggleMetaEdit, gpSaveMetaFields,
  gpScrapeSingle, gpApplyScrape, gpCopyAssetToEsde,
  loadGameSyncHistory,
  enterTvMode, exitTvMode, loadTvGrid, _tvMoveFocus,
  loadRecommendations, dismissRecommendations, loadGameScreenshots, loadGameStatshots,
  // esde.js — ES-DE status, BIOS checker, RetroArch diagnostic, RA compatibility, health check, junk/orphans/doctor
  loadEsdeStatus, loadBiosStatus, loadRetroArchCheck, generateEsSystems,
  doRaCheck, _renderRaResult, _updateRaProgress, filterRaByPlatform, clearRaFilter, _raGoToPage, _raSelectAlternative, discardRaNoSupport,
  _copyText, _googleQuery, _archiveOrgUrl, _openArchiveOrg, _copyArchiveOrgLink,
  doHealthCheck, _renderHealthResult, _filterHealthIssues, loadOperationsTimeline, _clearHealthFilter,
  doJunkScan, _renderJunkResult, junkToggleCat, junkSelectAll, junkRevealCat, junkCatCheck, junkDelete, zipRouteApply,
  doFindOrphans, doDeleteOrphans, doMoveOrphansToArchive, moveOrphanedSave,
  doLibraryDoctor, doctorMoveRom, doctorDeleteDir, doctorResolveAll, doFolderAnalysis,
  loadUnmatchedDiagnosis, downloadMissingDats,
  generateReport, showReportTab, _renderReportZips, _renderReportPlaylists, _renderReportMultidisc, _renderReportOrphans, _renderReportRA, _renderReportChd, exportReportHtml,
  // overview.js — overview tab, heatmap, charts, wizard
  _relTime, _emptyState, card, _getPlatformLogo,
  _loadNewGameSuggestion, openGameSuggestionPanel, _renderMonthlyChart,
  loadOverview, _renderPlatformGrid, loadCollectionCompleteness,
  showWizard, closeWizard, wizardAutoDetect, startSetup,
  _renderWizSteps, _pollSetupProgress, _showSetupResult, wizardGoToOrganize, loadActivityHeatmap,
  // tools.js — tool conversions
  doConvertChd, applyChdFilter, _renderChdResult,
  doConvertCso, _renderCsoResult,
  doCleanupZips, doCleanupCueBin, doExtractZip,
  doGenerateM3U, autodetectM3UFolders,
  doVerifyMultidisc, generateM3uFromVerify,
  doExportLpl,
  doN64Scan, doN64Convert,
  createLibraryStructure, organizeLibrary,
  doVerifyChd, _renderVerifyChdResult, applyVerifyChdFilter,
  loadPatchList, selectPatch, clearPatchSelection, applySelectedPatch, loadPatchLog,
  // state.js — shared device context
  AppState, getActiveDevice, getDevName, setActiveDevice, setDevName,
  getDeviceConnected, getDeviceConnectReason,
  startDeviceStatusPolling, stopDeviceStatusPolling,
  showToast,
  _showConfirm, _closeConfirm,
  _h,  // HTML escape helper for collection.js, organize.js
  // Global UI control (2l migration)
  _applyDeviceName, setDevice, _deviceRoot, showTab, toggleSidebar,
  initTheme, setTheme, _applyTheme, toggleTheme, onGlobalSearch,
  _requestNotifPermission, _sendNotif,
  stopJob, openHtmlReport, openHtmlReportAndroid,
  _copyToClipboard, _copyToClipboardFallback,
  _onDevicePresetChange,
  loadSettings, migrateSplitDb, testChdman, testMaxcso, testAdbBinary,
  loadLogViewer, downloadLog, loadTools, _setIfEmpty,
  doBatchRun, _initToolPath, fillToolPath,
  loadAuthStatus, doLogout, setPin, clearPin,
  loadLocalUrl, copyLocalUrl, renderQR,
  saveSettings, testNotification, saveOvPaths,
  doMigrateSavesStructure,
  browseFolder, browseFile, detectRetroArch,
  loadTrashStatus, emptyTrash,
  _onScanAdbChange, detectAdbDevicesForScan,
  doScan, quickScanPC, quickScanAndroid,
  doFixPlatforms, doMatch,
  loadCatalogStatus, importArcadeCatalog, importDats, loadDatCatalogList, downloadDats,
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  exportWishlist,
  loadCollectionStatsV2, toggleColStats,
  toggleDiff, loadLibraryDiff, syncSelected, syncConflict, deleteSelectedStorage,
  _diffToggleAll, _syncAllSide,
  toggleDiskUsage, loadDiskUsage,
  toggleCompleteness,
  toggleOverrides, loadOverrides,
  openOverrideEditor, closeOverrideEditor, saveOverrideEditor,
  copyOverride,
  setToolsContext, _initToolsContext,
  _chk, toggleShaLength, _planQueryString,
  loadPlan, applyKeepBoth, doApply, doUndoLastApply, _discardCollisionEntry,
  loadReviewQueue, applyReviewGroup, chooseReviewEntry,
  markReviewGroupIntentional, applyAllReviewRecommendations, doResolveRaConflicts,
  startPolling, _applyJobStatus, _showJobResult,
  // scraper.js
  doExportGamelistsAll,
  loadScraperSummary,
  loadSsQuota,
  loadSsCredsStatus,
  loadScrapePlatforms,
  doScrape,
  doExportGamelists,
  // inbox.js
  updateInboxBadge,
  _initInboxBadge,
  inboxDragOver,
  inboxDragLeave,
  inboxDrop,
  loadInbox,
  fillInboxTarget,
  scanInbox,
  runInbox,
  _applyInboxProgress,
  _renderInboxResult,
  loadInboxConflicts,
  resolveInboxConflict,
  saveInboxSettings, autoSaveInboxToggle,
  _pollInboxWatcher,
  // sync.js
  loadSync,
  loadAssets,
  showOrphanAssets,
  loadSystemStatus,
  detectCloudFolder,
  useCloudFolder,
  loadAutostart,
  toggleAutostart,
  shutdownServer,
  _checkAndroidUserAgent,
  loadAnbernicTab,
  copyAnbernicCmd,
  copyAnbernicUrl,
  tvCheckStatus, tvCheckServer, tvToggleSetup, tvCopySetupCmd, tvStartSync, tvShowResult, tvReset, tvSkipToFull,
  loadRcloneStatus,
  openRcloneConfig,
  testRcloneRemote,
  applyRcloneRemote,
  applyRcloneSavesStates,
  backupNow,
  loadManualBackups,
  _isAdbMode,
  _onCableModeChange,
  _onCableDryRunChange,
  _onCableWhatRomsChange,
  _onCableDirectionChange,
  testCablePath,
  detectDrives,
  detectAdbDevices,
  detectAndroidRaConfigDir,
  testAdbPath,
  loadCableSync,
  loadCableSyncPreview,
  doCableSync,
  doQuickSync,
  _renderCableSyncResult,
  toggleCableSyncLog,
  loadCableSyncLog,
  runSyncDoctor,
  exportPegasus,
  _updateAutoSyncBanner,
  _updateAutoSyncToggleUI,
  toggleAutoSync,
  saveAutoSyncSettings,
  saveConflictPolicy,
  startAutoSyncPolling,
  _onTreeDiffSourceChange,
  _loadTreeDiffDevices,
  doTreeDiff,
  _renderTreeDiff,
  loadSaveComparison,
  doLibraryDiff,
  doSaveFragmentation,
  doSync,
  _renderSyncResult,
  promptSyncNow,
  // SYNC-SETUP: Cloud auth wizard
  loadCloudAuthStatus,
  startCloudAuth,
  cancelCloudAuth,
  disconnectCloud,
  useRemoteForSync,
  openCloudSetup,
  // PHASE6-3b: app update download/apply
  downloadAppUpdate,
  applyAppUpdate,
});

// Initialize tools.js with main.js functions (late imports to avoid circular deps)
_initToolsImports(startPolling, _showJobResult);

// ── HTML escape helper (used by collection.js, organize.js) ──────────────────
function _h(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Global UI functions (2l migration) ────────────────────────────────────────

/** Update every UI element that shows the device name. Called once after config loads. */
export function _applyDeviceName(name) {
  setDevName(name);
  // Simple text replacements
  const simple = {
    'dev-anbernic':        name,
    'ov-ab-column-title':  name,
    'ov-ab-path-label-text': name,
    'scan-ab-device-name': name,
    'scan-adb-device-name': name,
    'cable-mode-label':    name,
  };
  for (const [id, text] of Object.entries(simple)) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }
  // Direction labels include arrow
  const toEl   = document.getElementById('cable-dir-to-dev');
  const fromEl = document.getElementById('cable-dir-from-dev');
  if (toEl)   toEl.textContent   = `PC → ${name}`;
  if (fromEl) fromEl.textContent = `${name} → PC`;
  // Tooltip on ADB row
  const adbRow = document.getElementById('scan-adb-row');
  if (adbRow) adbRow.title = `Escanea la ${name} por USB sin sacar la SD card — requiere ADB configurado en Settings`;
}

export function setDevice(d) {
  setActiveDevice(d);
  ['pc','anbernic'].forEach(id => {
    const b = document.getElementById('dev-' + id);
    if (b) b.classList.toggle('active', id === d);
  });
  // Reload current active tab
  const activeTab = document.querySelector('.nav-item.active')?.id?.replace('nav-','');
  if (activeTab) {
    if (activeTab === 'games')      { loadFilterOptions(); loadGames(0); }
    if (activeTab === 'plan')       { loadPlan(); loadReviewQueue(); }
    if (activeTab === 'assets')     loadAssets();
  }
}

export function _deviceRoot() {
  const d = getActiveDevice();
  if (d === 'pc')       return document.getElementById('ov-pc-path')?.value.trim() || null;
  if (d === 'anbernic') return document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || null;
  return null;
}

const _TAB_DESC = {
  overview:   ['Inicio',        'Estado general de tu biblioteca y acciones rápidas'],
  games:      ['Juegos',        'Explora, filtra y valora los juegos de tu biblioteca'],
  plan:       ['Organizar',     'Revisa renombres pendientes y resuelve copias duplicadas'],
  assets:     ['Assets',        'Gestiona carátulas, vídeos y otros recursos'],
  collection: ['Colección',     'Galería personal con historial de juego y logros'],
  sync:       ['Cloud Sync',    'Sincroniza saves con la nube via rclone'],
  cable:      ['Cable Sync',    'Sync de saves por USB con la consola Android'],
  anbernic:   ['Anbernic',      'Estado y configuración de tu consola Android'],
  tools:      ['Herramientas',  'Convierte, verifica y repara ROMs'],
  formats:    ['Formatos',      'Convierte formatos de disco: CHD, CSO, ZIP y m3u'],
  scraper:    ['Scraper',       'Descarga metadatos y carátulas de ScreenScraper'],
  inbox:      ['Inbox',         'Procesa automáticamente ROMs recién añadidas'],
  settings:   ['Ajustes',       'Configura rutas, catálogos DAT, sync y servidor'],
};

function _updateTabDesc(name) {
  const [label, desc] = _TAB_DESC[name] || [name, ''];
  const nameEl = document.getElementById('tab-desc-name');
  const descEl = document.getElementById('tab-desc-text');
  if (nameEl) nameEl.textContent = label;
  if (descEl) descEl.textContent = desc ? ` — ${desc}` : '';
}

export function showTab(name) {
  _updateTabDesc(name);
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
  if (name === 'overview')   { loadOverview(); loadCatalogStatus(); loadActivityHeatmap(); }
  if (name === 'games')      { loadFilterOptions(); loadGames(0); _refreshTagFilter(); loadRecommendations(); }
  if (name === 'plan')       { loadPlan(); loadReviewQueue(); }
  if (name === 'assets')     loadAssets();
  // CLOUD-UX-11: estado de saves y backups son lecturas locales baratas — se
  // cargan solos al abrir; el botón ↻ queda para refrescar.
  if (name === 'sync')       { loadSync(); loadManualBackups(); loadSaveComparison(); loadCloudAuthStatus(); }
  if (name === 'cable')      loadCableSync();
  if (name === 'collection') loadCollectionStatsV2();
  if (name === 'scraper')    { loadScraperSummary(); loadScrapePlatforms(); loadSsQuota(); loadSsCredsStatus(); }
  if (name === 'settings')   { loadSettings(); loadCatalogStatus(); loadDatCatalogList(); loadSsQuota(); loadAuthStatus(); loadLocalUrl(); loadSystemStatus(); loadAutostart(); loadTrashStatus(); }
  if (name === 'anbernic')   { loadAnbernicTab(); }
  if (name === 'formats')    { loadTools(); _initToolsContext(); }
  if (name === 'tools')      { loadTools(); _initToolsContext(); loadPatchLog(); loadPatchList(); }
  if (name === 'inbox')      loadInbox();
  if (name === 'tv')         { /* enterTvMode() handles TV tab load */ }
}

export function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (!sidebar) return;
  const collapsed = sidebar.classList.toggle('collapsed');
  localStorage.setItem('sidebar_collapsed', collapsed ? '1' : '0');
}

// ── Theme management ──────────────────────────────────────────────────────────

export function initTheme() {
  const saved = localStorage.getItem('rv_theme') || 'dark';
  _applyTheme(saved);
}

export function setTheme(theme) {
  theme = (theme === 'light') ? 'light' : 'dark';
  _applyTheme(theme);
  const icon = theme === 'light' ? '☀️' : '🌙';
  const name = theme === 'light' ? 'Modo claro' : 'Modo oscuro';
  showToast(`${icon} ${name} activado`, 'ok');
}

export function _applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : '');
  localStorage.setItem('rv_theme', theme);
  const darkRadio = document.getElementById('theme-dark');
  const lightRadio = document.getElementById('theme-light');
  if (darkRadio) darkRadio.checked = (theme === 'dark');
  if (lightRadio) lightRadio.checked = (theme === 'light');
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || '';
  _applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ── Global search ────────────────────────────────────────────────────────────

let _globalSearchTimer = null;
export function onGlobalSearch(val) {
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
        const gj = _h(JSON.stringify(g));
        return `<div class="sr-item" onclick="document.getElementById('global-search').value='';document.getElementById('global-search-results').classList.add('hidden');openGamePanel(${gj})">
          <img src="/api/asset-image?game_id=${g.id}" width="28" height="28" style="border-radius:3px;object-fit:cover" onerror="this.classList.add('hidden')">
          <div><div style="color:var(--c-text)">${title}</div><div style="font-size:11px;color:var(--c-dim)">${_h(g.platform||'')}</div></div>
        </div>`;
      }).join('');
    } catch(e) { results.classList.add('hidden'); }
  }, 200);
}

// Global search result dropdown click handler
document.addEventListener('click', e => {
  const wrap = document.getElementById('global-search-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const r = document.getElementById('global-search-results');
    if (r) r.classList.add('hidden');
  }
});

// ── Desktop notifications ─────────────────────────────────────────────────────

export function _requestNotifPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

export function _sendNotif(title, body) {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'granted') {
    new Notification(title, { body, icon: '' });
  }
}

// ── Job and report utilities ──────────────────────────────────────────────────

export async function stopJob(name) {
  try {
    await apiPost('/api/stop-job', { job: name });
  } catch(_) {}
}

export function openHtmlReport(customPath) {
  const path = customPath !== undefined ? customPath : (document.getElementById('report-path')?.value.trim() || '');
  const url = '/api/report/html' + (path ? '?path=' + encodeURIComponent(path) : '');
  window.open(url, '_blank');
}

export async function openHtmlReportAndroid() {
  const cfg = await apiFetch('/api/config').catch(() => ({}));
  const abPath = document.getElementById('ov-ab-path')?.value.trim()
    || cfg.anbernic_root || localStorage.getItem('anbernic_path') || '';
  if (!abPath) {
    alert('Configura la ruta de la consola Android en la sección Overview primero.');
    return;
  }
  openHtmlReport(abPath);
}

// ── Clipboard helpers ─────────────────────────────────────────────────────────

export function _copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
      .then(() => showToast('Copiado al portapapeles', 'ok'))
      .catch(() => _copyToClipboardFallback(text));
  } else {
    _copyToClipboardFallback(text);
  }
}

export function _copyToClipboardFallback(text) {
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

// ── PHASE6-3b: download + apply app update ─────────────────────────────────────

let _updatePollTimer = null;

export async function downloadAppUpdate() {
  const dlBtn = document.getElementById('update-banner-download-btn');
  const prog  = document.getElementById('update-banner-progress');
  try {
    const r = await apiPost('/api/update/download', {});
    if (r.status === 'error') { showToast(r.error, 'error'); return; }
    if (dlBtn) dlBtn.classList.add('hidden');
    if (prog) { prog.classList.remove('hidden'); prog.textContent = 'Descargando…'; }
    _updatePollTimer = setInterval(_pollUpdateStatus, 1000);
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

async function _pollUpdateStatus() {
  const prog    = document.getElementById('update-banner-progress');
  const applyBtn = document.getElementById('update-banner-apply-btn');
  try {
    const s = await apiFetch('/api/update/status');
    if (s.running && prog) {
      const mb = (n) => (n / (1024 * 1024)).toFixed(1);
      prog.textContent = s.bytes_total
        ? `Descargando… ${mb(s.bytes_done)}/${mb(s.bytes_total)} MB`
        : `Descargando… ${mb(s.bytes_done)} MB`;
    }
    if (s.done) {
      clearInterval(_updatePollTimer);
      _updatePollTimer = null;
      if (s.error) {
        if (prog) prog.classList.add('hidden');
        showToast('Error al descargar la actualización: ' + s.error, 'error');
      } else {
        if (prog) prog.textContent = 'Descarga completa';
        if (applyBtn) applyBtn.classList.remove('hidden');
      }
    }
  } catch (_) { /* red caída momentáneamente — el siguiente tick reintenta */ }
}

export async function applyAppUpdate() {
  if (!confirm('Retro Vault se cerrará y se abrirá el instalador. ¿Continuar?')) return;
  try {
    const r = await apiPost('/api/update/apply', {});
    if (r.status === 'error') { showToast(r.error, 'error'); return; }
    document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace;color:var(--c-dim);font-size:14px">Abriendo el instalador… cierra esta pestaña.</div>';
  } catch (_) { /* conexión cortada por el shutdown — es lo esperado */ }
}

// ── Application initialization ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Theme initialization from localStorage
  initTheme();

  // Restore sidebar collapsed state
  if (localStorage.getItem('sidebar_collapsed') === '1')
    document.getElementById('app-sidebar')?.classList.add('collapsed');

  // Initialize inbox badge + polling
  _initInboxBadge();

  // PHASE6-3a: check for app update (non-blocking, GitHub may not respond yet)
  setTimeout(async () => {
    try {
      const v = await apiFetch('/api/version');
      if (v.update_available) {
        const banner = document.getElementById('update-banner');
        const text   = document.getElementById('update-banner-text');
        const link   = document.getElementById('update-banner-link');
        const dlBtn  = document.getElementById('update-banner-download-btn');
        if (text) text.textContent = `⬆ Nueva versión disponible: ${v.latest} (actual: ${v.current})`;
        if (link && v.release_url) link.href = v.release_url;
        // PHASE6-3b: only the packaged .exe can apply an update automatically
        if (dlBtn) dlBtn.classList.toggle('hidden', !v.frozen);
        if (banner) banner.classList.remove('hidden');
      }
    } catch (_) { /* sin red o servidor sin versión — ignorar silenciosamente */ }
  }, 3000);

  // Guide toggle setup
  const guide = document.getElementById('ov-guide');
  if (guide) {
    const updateArrow = () => {
      const arrow = document.getElementById('ov-guide-arrow');
      if (arrow) arrow.innerHTML = guide.open ? '&#x25BC;' : '&#x25B6;';
      localStorage.setItem('guide_closed', guide.open ? '0' : '1');
    };
    guide.addEventListener('toggle', updateArrow);
    if (localStorage.getItem('guide_closed') === '1') guide.removeAttribute('open');
    updateArrow();
  }

  // Seed description bar for the default active tab
  _updateTabDesc('overview');

  // Load auth status and config on startup
  loadAuthStatus();
  loadLocalUrl();
  _checkAndroidUserAgent();
  startAutoSyncPolling();

  // Start device connectivity polling (UX-1/2-3)
  startDeviceStatusPolling();

  // TV mode keyboard handler — uses live module bindings from games.js
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;

    // Escape key always works
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

    // TV mode navigation
    if (_tvActive) {
      if (e.key === 'ArrowRight') { e.preventDefault(); _tvMoveFocus(_tvFocusIdx + 1); return; }
      if (e.key === 'ArrowLeft')  { e.preventDefault(); _tvMoveFocus(_tvFocusIdx - 1); return; }
      if (e.key === 'ArrowDown')  { e.preventDefault(); _tvMoveFocus(_tvFocusIdx + _tvCols); return; }
      if (e.key === 'ArrowUp')    { e.preventDefault(); _tvMoveFocus(_tvFocusIdx - _tvCols); return; }
      if (e.key === 'Enter')      { e.preventDefault(); openGamePanel(_tvGames[_tvFocusIdx]); return; }
      if (e.key === 'Escape')     { e.preventDefault(); exitTvMode(); return; }
    }

    // Ctrl+K / Cmd+K — focus global search
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      document.getElementById('global-search')?.focus();
      return;
    }

    // Global shortcuts
    const k = e.key.toLowerCase();
    if (k === 't') { e.preventDefault(); enterTvMode(); return; }
    if (k === 's') { e.preventDefault(); showTab('sync'); return; }
    if (k === 'g') { e.preventDefault(); showTab('games'); return; }
    if (k === 'r') {
      e.preventDefault();
      const t = document.querySelector('.nav-item.active')?.id?.replace('nav-', '');
      if (t) showTab(t);
    }
  });

  // Global search — debounce 300ms → jump to Games tab
  let _globalSearchTimer = null;
  const _globalSearchEl = document.getElementById('global-search');
  if (_globalSearchEl) {
    _globalSearchEl.addEventListener('input', () => {
      clearTimeout(_globalSearchTimer);
      _globalSearchTimer = setTimeout(() => {
        const val = _globalSearchEl.value.trim();
        gamesState.search = val;
        const searchEl = document.getElementById('games-search');
        if (searchEl) searchEl.value = val;
        showTab('games');
        loadGames(0);
      }, 300);
    });
    _globalSearchEl.addEventListener('keydown', e => {
      if (e.key === 'Escape') { _globalSearchEl.value = ''; _globalSearchEl.blur(); }
    });
  }
});
