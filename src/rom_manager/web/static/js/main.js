// js/main.js — Retro Vault module entry point
// Loaded as type="module" (deferred) before app.js.
// Sets up window globals so inline onclick handlers and app.js can call these functions.

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
} from './tabs/config.js';
import {
  _onScanAdbChange, detectAdbDevicesForScan,
  doScan, quickScanPC, quickScanAndroid,
  doFixPlatforms, doMatch,
  loadCatalogStatus, importArcadeCatalog, importDats,
} from './tabs/scan.js';
import {
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  loadCollection, colSetPlatform, colSearch, colLoadMore,
  exportCollection, exportWishlist,
  loadCollectionStatsV2, toggleColStats,
} from './tabs/collection.js';
import {
  loadDuplicates, deleteAllDuplicates, deleteDuplicate,
  resolveDuplicateRA, markAsIntentionalCopy,
  loadRaDuplicates, deleteRaDuplicate,
  doResolveRaConflicts, discardAllRaDuplicates,
  setToolsContext, _initToolsContext,
  filterDuplicatesByPlatform, _renderDupContent,
} from './tabs/duplicates.js';
import {
  _chk, toggleShaLength, _planQueryString,
  loadPlan, applyKeepBoth, doApply,
} from './tabs/organize.js';
import {
  startPolling, _applyJobStatus, _showJobResult,
} from './jobs.js';

// Expose all migrated functions on window for:
// - Inline onclick="xxx()" handlers in index.html
// - Legacy app.js callers (e.g. DOMContentLoaded calling loadAuthStatus)
Object.assign(window, {
  showToast,
  _showConfirm, _closeConfirm,
  _onDevicePresetChange,
  loadSettings, migrateSplitDb, testChdman, testMaxcso, testAdbBinary,
  loadLogViewer, downloadLog, loadTools, _setIfEmpty,
  doBatchRun, _initToolPath, fillToolPath,
  loadAuthStatus, doLogout, setPin, clearPin,
  loadLocalUrl, copyLocalUrl, renderQR,
  saveSettings, testNotification, saveOvPaths,
  _onScanAdbChange, detectAdbDevicesForScan,
  doScan, quickScanPC, quickScanAndroid,
  doFixPlatforms, doMatch,
  loadCatalogStatus, importArcadeCatalog, importDats,
  loadCollectionStats, loadMissingRoms, filterMissingByPlatform,
  toggleWishlist,
  loadCollection, colSetPlatform, colSearch, colLoadMore,
  exportCollection, exportWishlist,
  loadCollectionStatsV2, toggleColStats,
  loadDuplicates, deleteAllDuplicates, deleteDuplicate,
  resolveDuplicateRA, markAsIntentionalCopy,
  loadRaDuplicates, deleteRaDuplicate,
  doResolveRaConflicts, discardAllRaDuplicates,
  setToolsContext, _initToolsContext,
  filterDuplicatesByPlatform, _renderDupContent,
  _chk, toggleShaLength, _planQueryString,
  loadPlan, applyKeepBoth, doApply,
  startPolling, _applyJobStatus, _showJobResult,
});
