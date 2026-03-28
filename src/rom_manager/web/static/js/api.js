/**
 * api.js — Retro Vault centralized API client
 *
 * ES Module (Phase 0 infrastructure). No callers yet — app.js still uses its
 * own inline apiFetch/apiPost. This file will replace them during Phase 2.
 *
 * Usage (future):
 *   import { api } from '/static/js/api.js';
 *   const status = await api.jobStatus();
 *   await api.startScan({ root: '/roms' });
 */

// ── Base helpers ──────────────────────────────────────────────────────────────

async function _get(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function _post(url, body = {}) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ── API surface ───────────────────────────────────────────────────────────────

// Named exports for direct use in migrated modules
export const apiFetch = _get;
export const apiPost  = _post;

export const api = {

  // ── System / config ────────────────────────────────────────────────────────
  config:            ()       => _get('/api/config'),
  saveConfig:        (body)   => _post('/api/config', body),
  systemStatus:      ()       => _get('/api/system-status'),
  listDrives:        ()       => _get('/api/list-drives'),
  localUrl:          ()       => _get('/api/local-url'),
  logs:              (n = 300)=> _get(`/api/logs?lines=${n}`),
  testChdman:        ()       => _get('/api/test-chdman'),
  testMaxcso:        ()       => _get('/api/test-maxcso'),
  openFolder:        (body)   => _post('/api/open-folder', body),
  notifyTest:        (body)   => _post('/api/notify-test', body),

  // ── Auth ───────────────────────────────────────────────────────────────────
  authStatus:        ()       => _get('/api/auth/status'),
  setPin:            (body)   => _post('/api/set-pin', body),
  clearPin:          ()       => _post('/api/clear-pin'),
  logout:            ()       => _post('/api/auth/logout'),

  // ── Wizard ─────────────────────────────────────────────────────────────────
  wizardDetect:      ()       => _get('/api/wizard-detect'),
  setupStatus:       ()       => _get('/api/setup-status'),
  setupRun:          (body)   => _post('/api/setup-run', body),

  // ── Jobs ───────────────────────────────────────────────────────────────────
  jobStatus:         ()       => _get('/api/job-status'),
  stopJob:           (body)   => _post('/api/stop-job', body),

  // ── Scan ───────────────────────────────────────────────────────────────────
  scan:              (body)   => _post('/api/scan', body),
  match:             (body)   => _post('/api/match', body),
  importDats:        (body)   => _post('/api/import-dats', body),
  importArcadeCatalog: (body) => _post('/api/import-arcade-catalog', body),
  catalogStatus:     ()       => _get('/api/catalog-status'),

  // ── Collection ─────────────────────────────────────────────────────────────
  collectionStats:   ()       => _get('/api/collection-stats'),
  missing:           ()       => _get('/api/missing'),
  libraryDiff:       ()       => _get('/api/library-diff'),
  operationsTimeline: (n=100) => _get(`/api/operations-timeline?limit=${n}`),
  fixPlatforms:      (body)   => _post('/api/fix-platforms', body),
  migrateSplitDb:    (body)   => _post('/api/migrate-split-db', body),

  // ── Games ──────────────────────────────────────────────────────────────────
  games:             (params) => _get('/api/games?' + new URLSearchParams(params)),
  gamesFilterOptions:()       => _get('/api/games/filter-options'),
  setMetadata:       (body)   => _post('/api/set-metadata', body),
  setPlayStatus:     (body)   => _post('/api/set-play-status', body),
  toggleFavorite:    (body)   => _post('/api/toggle-favorite', body),
  tag:               (body)   => _post('/api/tag', body),
  tags:              ()       => _get('/api/tags'),
  launch:            (body)   => _post('/api/launch', body),
  wishlist:          (body)   => _post('/api/wishlist', body),

  // ── Organize / rename ──────────────────────────────────────────────────────
  apply:             (body)   => _post('/api/apply', body),
  organizeLibrary:   (body)   => _post('/api/organize-library', body),
  generateM3u:       (body)   => _post('/api/generate-m3u', body),
  cleanupCueBin:     (body)   => _post('/api/cleanup-cue-bin', body),
  cleanupZips:       (body)   => _post('/api/cleanup-zips', body),
  verifyMultidisc:   (body)   => _post('/api/verify-multidisc', body),
  discFolders:       ()       => _get('/api/disc-folders'),

  // ── Duplicates ─────────────────────────────────────────────────────────────
  deleteDuplicate:   (body)   => _post('/api/duplicates/delete', body),
  deleteAllDuplicates: (body) => _post('/api/duplicates/delete-all', body),
  excludeDuplicate:  (body)   => _post('/api/duplicates/exclude', body),
  raDuplicates:      ()       => _get('/api/ra-duplicates'),
  discardRaDuplicate:(body)   => _post('/api/ra-duplicates/discard', body),
  discardAllRaDuplicates: ()  => _post('/api/ra-duplicates/discard-all'),
  resolveRaDuplicate:(body)   => _post('/api/resolve-duplicate-ra', body),
  applyRaConflicts:  (body)   => _post('/api/apply-ra-conflicts', body),

  // ── Converters ────────────────────────────────────────────────────────────
  convertChd:        (body)   => _post('/api/convert-chd', body),
  convertCso:        (body)   => _post('/api/convert-cso', body),
  convertN64:        (body)   => _post('/api/convert-n64', body),

  // ── Inbox ──────────────────────────────────────────────────────────────────
  inboxCount:        ()       => _get('/api/inbox-count'),
  inboxWatcherStatus:()       => _get('/api/inbox-watcher-status'),
  inboxRun:          (body)   => _post('/api/inbox-run', body),

  // ── Health / orphans ──────────────────────────────────────────────────────
  healthCheck:       (body)   => _post('/api/health-check', body),
  healthSchedule:    ()       => _get('/api/health-schedule'),
  libraryDoctor:     ()       => _get('/api/library-doctor'),
  doctorDeleteDir:   (body)   => _post('/api/doctor-delete-dir', body),
  doctorMoveRom:     (body)   => _post('/api/doctor-move-rom', body),
  junkDelete:        (body)   => _post('/api/junk-delete', body),
  deleteOrphanedSaves:    (b) => _post('/api/orphaned-saves/delete', b),
  moveOrphanedSaves:      (b) => _post('/api/orphaned-saves/move', b),
  archiveOrphanedSaves:   (b) => _post('/api/orphaned-saves/move-to-archive', b),

  // ── Sync / cloud ──────────────────────────────────────────────────────────
  sync:              (body)   => _post('/api/sync', body),
  rcloneStatus:      ()       => _get('/api/rclone-status'),
  detectCloudFolder: ()       => _get('/api/detect-cloud-folder'),
  syncLog:           ()       => _get('/api/sync-log'),
  autoSyncToggle:    (body)   => _post('/api/auto-sync-toggle', body),
  autoSyncStatus:    ()       => _get('/api/auto-sync-status'),
  autoSyncSave:      (body)   => _post('/api/auto-sync-save', body),
  saveComparison:    ()       => _get('/api/save-comparison'),
  backupNow:         ()       => _post('/api/backup-now'),
  restoreBackup:     (body)   => _post('/api/restore-backup', body),
  manualBackups:     ()       => _get('/api/manual-backups'),
  sdSyncStatus:      ()       => _get('/api/sd-sync-status'),

  // ── Cable sync / ADB ──────────────────────────────────────────────────────
  cableSync:         (body)   => _post('/api/cable-sync', body),
  cableSyncLog:      ()       => _get('/api/cable-sync-log'),
  adbDevices:        ()       => _get('/api/adb-devices'),
  adbScan:           (body)   => _post('/api/adb-scan', body),
  autostartStatus:   ()       => _get('/api/autostart-status'),

  // ── Scraper ───────────────────────────────────────────────────────────────
  scrape:            (body)   => _post('/api/scrape', body),
  scrapeSingle:      (body)   => _post('/api/scrape-single', body),
  ssQuota:           ()       => _get('/api/ss-quota'),
  biosStatus:        ()       => _get('/api/bios-status'),

  // ── RetroAchievements ─────────────────────────────────────────────────────
  raCheck:           (body)   => _post('/api/ra-check', body),
  raDiscardNoSupport:()       => _post('/api/ra-check/discard-no-support'),
  retroarchCheck:    ()       => _get('/api/retroarch-check'),

  // ── ES-DE / Gamelists ─────────────────────────────────────────────────────
  esdeStatus:        ()       => _get('/api/esde-status'),
  exportGamelists:   (body)   => _post('/api/export-gamelists', body),
  exportPegasus:     (body)   => _post('/api/export-pegasus', body),
  exportLpl:         (body)   => _post('/api/export-lpl', body),
  createLibraryStructure: (b) => _post('/api/create-library-structure', b),
  copyAssetsToEsde:  ()       => _get('/api/copy-assets-to-esde'),
};
