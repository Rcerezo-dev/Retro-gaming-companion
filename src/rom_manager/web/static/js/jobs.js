// js/jobs.js — Job polling and status application
// Extracted from app.js during Phase 2 migration.

import { apiFetch } from './api.js';
import { showToast } from './components/toast.js';

// ── Job polling ───────────────────────────────────────────────────────────────
let _pollingTimer = null;
const _shownResultTs = {};

function startPolling() {
  if (_pollingTimer) return;
  _pollingTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      _applyJobStatus(s);
      if (!s.scan_running && !s.match_running && !s.sync_running && !s.convert_chd_running && !s.scrape_running && !s.extract_zip_running && !s.health_check_running && !s.ra_check_running && !s.cable_sync_running && !s.apply_running && !s.inbox_running && !s.setup_running && !s.backup_now_running && !s.tree_diff_running) {
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
      btnScan.onclick = () => window.stopJob('scan');
      btnScan.classList.add('danger');
    } else {
      btnScan.disabled = false;
      btnScan.textContent = 'Scan';
      btnScan.onclick = window.doScan;
      btnScan.classList.remove('danger');
    }
  }
  const scanProgWrap = document.getElementById('scan-progress-wrap');
  if (scanProgWrap) {
    if (s.scan_running && s.scan_progress) {
      const p = s.scan_progress;
      scanProgWrap.classList.remove('hidden');
      const counts = document.getElementById('scan-progress-counts');
      const file   = document.getElementById('scan-progress-file');
      if (counts) counts.textContent = `${p.files_seen || 0} archivos — ${p.roms_detected || 0} ROMs`;
      if (file)   file.textContent   = p.current_file || p.current_path || '';
    } else {
      scanProgWrap.classList.add('hidden');
    }
  }
  if (btnMatch) {
    if (s.match_running) {
      btnMatch.disabled = false;
      btnMatch.textContent = 'Cancelar match';
      btnMatch.onclick = () => window.stopJob('match');
      btnMatch.classList.add('danger');
    } else {
      btnMatch.disabled = false;
      btnMatch.textContent = 'Match catálogos';
      btnMatch.onclick = window.doMatch;
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
      btnChd.onclick = () => window.stopJob('convert_chd');
      btnChd.classList.add('danger');
    } else {
      btnChd.textContent = 'Convertir a CHD';
      btnChd.onclick = window.doConvertChd;
      btnChd.classList.remove('danger');
    }
  }

  if (!s.scan_running && s.scan_result) {
    const ts = s.scan_result.result_ts || JSON.stringify(s.scan_result);
    if (_shownResultTs.scan !== ts) {
      _shownResultTs.scan = ts;
      _showJobResult('scan', s.scan_result);
      window.loadOverview();
    }
  }
  if (!s.match_running && s.match_result) {
    const ts = s.match_result.result_ts || JSON.stringify(s.match_result);
    if (_shownResultTs.match !== ts) {
      _shownResultTs.match = ts;
      _showJobResult('match', s.match_result);
      window.loadOverview();
    }
  }
  if (!s.sync_running && s.sync_result) {
    window._renderSyncResult(s.sync_result);
  }
  // CHD progress bar
  const chdWrap = document.getElementById('chd-progress-wrap');
  if (s.convert_chd_running && s.chd_progress && s.chd_progress.total > 0) {
    const p = s.chd_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (chdWrap) chdWrap.classList.remove('hidden');
    const bar = document.getElementById('chd-progress-bar');
    const lbl = document.getElementById('chd-progress-label');
    const file = document.getElementById('chd-progress-file');
    if (bar) bar.style.width = pct + '%';
    if (lbl) lbl.textContent = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.convert_chd_running) {
    if (chdWrap) chdWrap.classList.add('hidden');
  }
  if (!s.convert_chd_running && s.convert_chd_result) {
    window._renderChdResult(s.convert_chd_result);
  }
  // CSO progress bar
  const btnCso = document.getElementById('btn-convert-cso');
  if (btnCso) {
    if (s.convert_cso_running) {
      btnCso.disabled = false;
      btnCso.textContent = 'Cancelar';
      btnCso.onclick = () => window.stopJob('convert_cso');
      btnCso.classList.add('danger');
    } else {
      btnCso.textContent = 'Convertir a ISO';
      btnCso.onclick = window.doConvertCso;
      btnCso.classList.remove('danger');
    }
  }
  const csoWrap = document.getElementById('cso-progress-wrap');
  if (s.convert_cso_running && s.cso_progress && s.cso_progress.total > 0) {
    const p = s.cso_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (csoWrap) csoWrap.classList.remove('hidden');
    const bar = document.getElementById('cso-progress-bar');
    const lbl = document.getElementById('cso-progress-label');
    const file = document.getElementById('cso-progress-file');
    if (bar) bar.style.width = pct + '%';
    if (lbl) lbl.textContent = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.convert_cso_running) {
    if (csoWrap) csoWrap.classList.add('hidden');
  }
  if (!s.convert_cso_running && s.convert_cso_result) {
    window._renderCsoResult(s.convert_cso_result);
  }
  // Scrape progress bar
  const scrapeWrap = document.getElementById('scrape-progress-wrap');
  const btnScrape  = document.getElementById('btn-scrape');
  if (s.scrape_running && s.scrape_progress && s.scrape_progress.total > 0) {
    const p = s.scrape_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (scrapeWrap) scrapeWrap.classList.remove('hidden');
    const bar   = document.getElementById('scrape-progress-bar');
    const lbl   = document.getElementById('scrape-progress-label');
    const found = document.getElementById('scrape-progress-found');
    const file  = document.getElementById('scrape-progress-file');
    if (bar)   bar.style.width  = pct + '%';
    if (lbl)   lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    const netErr = p.network_errors > 0 ? `  ⚠ ${p.network_errors} errores de red (reintentando)` : '';
    if (found) found.textContent = (p.found > 0 ? `✓ ${p.found} encontrados` : '') + netErr;
    if (file)  file.textContent  = p.current_game;
    // Refresh platform % table every ~10s while scraping
    if (!window._scrapeSummaryTick) window._scrapeSummaryTick = 0;
    window._scrapeSummaryTick++;
    if (window._scrapeSummaryTick % 5 === 0) window.loadScraperSummary();
    if (btnScrape) {
      btnScrape.disabled = false;
      btnScrape.textContent = 'Cancelar';
      btnScrape.onclick = () => window.stopJob('scrape');
      btnScrape.classList.add('danger');
    }
  } else if (!s.scrape_running) {
    if (scrapeWrap) scrapeWrap.classList.add('hidden');
    if (btnScrape) {
      btnScrape.textContent = 'Iniciar scraping';
      btnScrape.onclick = window.doScrape;
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
        const r = s.scrape_result;
        let msg = `Completado — Encontrados: ${r.found}  |  Sin resultado: ${r.skipped}  (de ${r.total})`;
        if (r.images_filled > 0) msg += `  |  Portadas añadidas: ${r.images_filled}`;
        if (r.network_errors > 0) msg += `  |  ⚠ Errores de red: ${r.network_errors}`;
        if (r.cancelled) msg += '  |  (cancelado)';
        el.textContent = msg;
      }
    }
    if (btn) { btn.disabled = false; btn.textContent = 'Iniciar scraping'; btn.onclick = window.doScrape; btn.classList.remove('danger'); }
    window.loadScraperSummary();
  }

  // ZIP progress
  const zipWrap = document.getElementById('zip-progress-wrap');
  const btnZip  = document.getElementById('btn-extract-zip');
  if (s.extract_zip_running && s.zip_progress && s.zip_progress.total > 0) {
    const p = s.zip_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (zipWrap) zipWrap.classList.remove('hidden');
    const bar  = document.getElementById('zip-progress-bar');
    const lbl  = document.getElementById('zip-progress-label');
    const file = document.getElementById('zip-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.extract_zip_running) {
    if (zipWrap) zipWrap.classList.add('hidden');
  }
  if (btnZip) {
    if (s.extract_zip_running) {
      btnZip.disabled = false;
      btnZip.textContent = 'Cancelar';
      btnZip.onclick = () => window.stopJob('extract_zip');
      btnZip.classList.add('danger');
    } else {
      btnZip.textContent = 'Descomprimir ZIPs';
      btnZip.onclick = window.doExtractZip;
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
          window.quickScanPC();
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
    if (healthWrap) healthWrap.classList.remove('hidden');
    const bar  = document.getElementById('health-progress-bar');
    const lbl  = document.getElementById('health-progress-label');
    const file = document.getElementById('health-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.health_check_running) {
    if (healthWrap) healthWrap.classList.add('hidden');
  }
  if (btnHealth) {
    if (s.health_check_running) {
      btnHealth.disabled = false;
      btnHealth.textContent = 'Cancelar';
      btnHealth.onclick = () => window.stopJob('health_check');
      btnHealth.classList.add('danger');
    } else {
      btnHealth.textContent = 'Iniciar Health Check';
      btnHealth.onclick = window.doHealthCheck;
      btnHealth.classList.remove('danger');
    }
  }
  if (!s.health_check_running && s.health_check_result) {
    window._renderHealthResult(s.health_check_result);
    if (btnHealth) { btnHealth.disabled = false; btnHealth.textContent = 'Iniciar Health Check'; btnHealth.onclick = window.doHealthCheck; btnHealth.classList.remove('danger'); }
  }

  // RA check progress
  const raWrap  = document.getElementById('ra-progress-wrap');
  const btnRa   = document.getElementById('btn-ra-check');
  if (s.ra_check_running && s.ra_progress && s.ra_progress.total > 0) {
    const p = s.ra_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (raWrap) raWrap.classList.remove('hidden');
    const bar  = document.getElementById('ra-progress-bar');
    const lbl  = document.getElementById('ra-progress-label');
    const file = document.getElementById('ra-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.ra_check_running) {
    if (raWrap) raWrap.classList.add('hidden');
  }
  if (btnRa) {
    if (s.ra_check_running) {
      btnRa.disabled = false;
      btnRa.textContent = 'Cancelar';
      btnRa.onclick = () => window.stopJob('ra_check');
      btnRa.classList.add('danger');
    } else {
      btnRa.textContent = 'Comprobar compatibilidad RA';
      btnRa.onclick = window.doRaCheck;
      btnRa.classList.remove('danger');
    }
  }
  if (!s.ra_check_running && s.ra_check_result) {
    window._renderRaResult(s.ra_check_result);
    if (btnRa) { btnRa.disabled = false; btnRa.textContent = 'Comprobar compatibilidad RA'; btnRa.onclick = window.doRaCheck; btnRa.classList.remove('danger'); }
  }

  // Cable sync
  const btnCable = document.getElementById('btn-cable-sync');
  const cableWrap = document.getElementById('cable-progress-wrap');
  if (s.cable_sync_running && s.cable_progress) {
    const p = s.cable_progress;
    if (cableWrap) cableWrap.classList.remove('hidden');
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
        ? `${window.fmtSize(bytesCopied)} / ${window.fmtSize(bytesTotal)} (${p.copied || 0} archivos)${speedStr ? ' — ' + speedStr : ''}${etaStr ? ' — ETA: ' + etaStr : ''}`
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
        btnCable.onclick = () => window.stopJob('cable_sync');
        btnCable.classList.add('danger');
    }
  } else if (!s.cable_sync_running) {
    if (cableWrap) cableWrap.classList.add('hidden');
    if (btnCable) {
        btnCable.textContent = 'Iniciar sincronización';
        btnCable.onclick = window.doCableSync;
        btnCable.classList.remove('danger');
    }
  }
  if (!s.cable_sync_running && s.cable_sync_result) {
    window._renderCableSyncResult(s.cable_sync_result);
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
      window.loadManualBackups();
    }
  }
  // Tree diff
  const btnTreeDiff = document.getElementById('btn-tree-diff');
  if (s.tree_diff_running) {
    if (btnTreeDiff) { btnTreeDiff.disabled = true; btnTreeDiff.textContent = 'Comparando\u2026'; }
  } else {
    if (btnTreeDiff) { btnTreeDiff.disabled = false; btnTreeDiff.textContent = 'Comparar \u00e1rboles'; }
  }
  if (!s.tree_diff_running && s.tree_diff_result) {
    const ts = s.tree_diff_result.result_ts || JSON.stringify(s.tree_diff_result);
    if (_shownResultTs.tree_diff !== ts) {
      _shownResultTs.tree_diff = ts;
      window._renderTreeDiff(s.tree_diff_result);
    }
  }
  // Inbox progress
  window._applyInboxProgress(s);
  // UI-2: inbox pending badge in dashboard bar
  const inboxBadge = document.getElementById('ov-inbox-badge');
  if (inboxBadge) {
    const pending = s.inbox_pending_files || 0;
    inboxBadge.classList.toggle('hidden', !(pending > 0));
    inboxBadge.textContent   = pending;
  }
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

// ── Public exports ────────────────────────────────────────────────────────────
export { startPolling, _applyJobStatus, _showJobResult };
