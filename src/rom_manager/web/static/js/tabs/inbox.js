// js/tabs/inbox.js — Inbox pipeline, badge, drag & drop, watcher
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Module-level state ────────────────────────────────────────────────────────
let _lastInboxResultTs = null;
let _lastTriggerTs = 0;

// ── Badge (32-1) ──────────────────────────────────────────────────────────────
function updateInboxBadge() {
  apiFetch('/api/inbox-count').then(d => {
    const badge = document.getElementById('inbox-nav-badge');
    if (!badge) return;
    if (d.count > 0) {
      badge.textContent = d.count;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }).catch(() => {});
}

async function _checkAutoTrigger() {
  try {
    const d = await apiFetch('/api/inbox-watcher-status');
    if (d.trigger_ts && d.trigger_ts > _lastTriggerTs) {
      _lastTriggerTs = d.trigger_ts;
      const n = d.pending_files || 0;
      showToast(`Inbox: ${n} archivo(s) detectado(s), organizando automáticamente…`, 'ok');
      if (window.startPolling) window.startPolling();
    }
  } catch (_) {}
}

function _initInboxBadge() {
  updateInboxBadge();
  _checkAutoTrigger();
  setInterval(() => { updateInboxBadge(); _checkAutoTrigger(); }, 30000);
}

// ── Drag & drop (32-3) ────────────────────────────────────────────────────────
function inboxDragOver(e) {
  e.preventDefault();
  const zone = document.getElementById('inbox-dropzone');
  if (zone) { zone.style.borderColor = '#569cd6'; zone.style.color = '#569cd6'; }
}

function inboxDragLeave(e) {
  const zone = document.getElementById('inbox-dropzone');
  if (zone) { zone.style.borderColor = '#333'; zone.style.color = '#555'; }
}

async function inboxDrop(e) {
  e.preventDefault();
  inboxDragLeave(e);
  const files = Array.from(e.dataTransfer.files);
  if (!files.length) return;
  const resultEl = document.getElementById('inbox-drop-result');
  if (resultEl) resultEl.textContent = `Subiendo ${files.length} archivo(s)…`;

  let saved = 0, errors = [];
  for (const file of files) {
    const fd = new FormData();
    fd.append('file', file, file.name);
    try {
      const resp = await fetch('/api/inbox-upload', { method: 'POST', body: fd });
      const d = await resp.json();
      saved += d.count || 0;
      if (d.errors?.length) errors.push(...d.errors);
    } catch (err) {
      errors.push(`${file.name}: ${err.message}`);
    }
  }
  if (resultEl) {
    if (errors.length) {
      resultEl.innerHTML = `<span style="color:#f44747">✗ ${errors.join('; ')}</span>`;
    } else {
      resultEl.innerHTML = `<span style="color:#4ec9b0">✓ ${saved} archivo(s) copiado(s) al Inbox</span>`;
    }
  }
  updateInboxBadge();
}

// ── Inbox main ────────────────────────────────────────────────────────────────
function loadInbox() {
  apiFetch('/api/config').then(cfg => {
    const pathEl   = document.getElementById('inbox-path');
    const targetEl = document.getElementById('inbox-target');
    const delEl    = document.getElementById('inbox-delete-source');
    const autoEl   = document.getElementById('inbox-auto-process');
    if (pathEl   && cfg.inbox_path)         pathEl.value   = cfg.inbox_path;
    if (targetEl && cfg.inbox_target_root)  targetEl.value = cfg.inbox_target_root;
    if (delEl    && cfg.inbox_delete_source !== undefined) delEl.checked = cfg.inbox_delete_source;
    if (autoEl   && cfg.inbox_auto_process  !== undefined) autoEl.checked = cfg.inbox_auto_process;
    const savedPath = localStorage.getItem('inbox_path');
    if (savedPath && pathEl && !pathEl.value) pathEl.value = savedPath;
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
    const platStr = Object.entries(d.by_platform || {}).map(([k,v]) => k + ' x' + v).join(' · ');
    if (summaryText) summaryText.innerHTML =
      '<strong style="color:#d4d4d4">' + d.total + ' archivos</strong>' +
      (d.zips > 0 ? ' · <span style="color:#dcdcaa">' + d.zips + ' ZIPs</span>' : '') +
      (d.unrecognized > 0 ? ' · <span style="color:#f14c4c">' + d.unrecognized + ' no reconocidos</span>' : '') +
      (platStr ? ' &nbsp;|&nbsp; ' + platStr : '');
    if (summaryEl) summaryEl.classList.remove('hidden');
    if (tbody) {
      const sortedFiles = [...(d.files || [])].sort((a, b) => {
        const pa = a.platform_guess || '\xff';
        const pb = b.platform_guess || '\xff';
        if (pa !== pb) return pa < pb ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
      tbody.innerHTML = sortedFiles.map(f => {
        const typeColor = f.type === 'zip' ? '#dcdcaa' : f.type === 'disc_image' ? '#4ec9b0' : f.type === 'rom' ? '#9cdcfe' : '#555';
        const platBadge = f.platform_guess ? '<span class="badge">' + f.platform_guess + '</span>' : '<span style="color:#555">—</span>';
        const extract   = f.needs_extraction ? '<span style="color:#dcdcaa">extraer ZIP</span>' : '';
        return '<tr style="border-bottom:1px solid #1e1e2e">' +
          '<td style="padding:4px 8px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + window._h(f.name) + '">' + window._h(f.name) + '</td>' +
          '<td style="padding:4px 8px;color:' + typeColor + '">' + f.type + '</td>' +
          '<td style="padding:4px 8px">' + platBadge + '</td>' +
          '<td style="padding:4px 8px;text-align:right;color:#888">' + window.fmtSize(f.size_bytes) + '</td>' +
          '<td style="padding:4px 8px">' + extract + '</td>' +
          '</tr>';
      }).join('');
    }
    if (filesWrap) filesWrap.classList.toggle('hidden', !(d.total > 0));
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
      window.startPolling();
      return;
    }
    if (d.error) { showToast('Error: ' + d.error, 'err'); return; }
    showToast('Pipeline Inbox iniciado', 'ok');
    window.startPolling();
  } catch(e) {
    showToast('Error al lanzar: ' + e.message, 'err');
    if (btn) { btn.disabled = false; btn.textContent = 'Organizar todo'; }
  }
}

function _applyInboxProgress(s) {
  const wrap   = document.getElementById('inbox-progress-wrap');
  const stepEl = document.getElementById('inbox-progress-step');
  const cntEl  = document.getElementById('inbox-progress-counts');
  const barEl  = document.getElementById('inbox-progress-bar');
  const fileEl = document.getElementById('inbox-progress-file');
  const btn    = document.getElementById('btn-inbox-run');

  const _STEP_LABELS = {
    'extracting': 'Paso 1/6: Extrayendo ZIPs',
    'scanning':   'Paso 2/6: Escaneando archivos',
    'matching':   'Paso 3/6: Cotejando catálogos',
    'planning':   'Paso 4/6: Planificando renames',
    'renaming':   'Paso 5/6: Renombrando',
    'organizing': 'Paso 6/6: Organizando por plataforma',
    'done':       'Completado',
  };

  if (s.inbox_running && s.inbox_progress) {
    if (wrap) wrap.classList.remove('hidden');
    const p = s.inbox_progress;
    if (stepEl) stepEl.textContent = _STEP_LABELS[p.step] || p.step || 'Procesando…';
    const pct = (p.total > 0) ? Math.round((p.processed / p.total) * 100) : 0;
    if (barEl) barEl.style.width = pct + '%';
    if (cntEl) cntEl.textContent = p.total > 0 ? p.processed + ' / ' + p.total + ' (' + pct + '%)' : '';
    if (fileEl) fileEl.textContent = p.current_file || '';
    if (btn) { btn.disabled = true; btn.textContent = 'Organizando…'; }
  } else if (!s.inbox_running) {
    if (wrap) wrap.classList.add('hidden');
    if (btn) { btn.disabled = false; btn.textContent = 'Organizar todo'; }
    if (s.inbox_result) {
      const ts = s.inbox_result.result_ts || JSON.stringify(s.inbox_result);
      if (_lastInboxResultTs !== ts) {
        _lastInboxResultTs = ts;
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
  const archived = r.zips_archived || 0;
  const zipNote  = archived > 0 ? ` <span style="color:#888;font-size:11px">(${archived} movidos a _processed/)</span>` : '';
  html += 'ZIPs extraidos: <strong>' + (r.zips_extracted || 0) + '</strong>' + zipNote + ' &nbsp;';
  html += 'ROMs escaneados: <strong>' + (r.roms_scanned || 0) + '</strong> &nbsp;';
  html += 'Cotejados: <strong>' + (r.matched || 0) + '</strong> &nbsp;';
  html += 'Renombrados: <strong>' + (r.renamed || 0) + '</strong> &nbsp;';
  html += 'Organizados: <strong>' + (r.organized || 0) + '</strong>';
  if (r.target_root) html += '<br><span style="color:#555;font-size:11px">Destino: ' + r.target_root + '</span>';
  if ((r.rename_errors || []).length > 0) {
    html += '<details style="margin-top:8px"><summary style="color:#dcdcaa;cursor:pointer">' + r.rename_errors.length + ' errores de rename</summary><ul style="margin:4px 0;padding-left:16px;font-size:11px;color:#888">';
    r.rename_errors.forEach(e => { html += '<li>' + window._h(e) + '</li>'; });
    html += '</ul></details>';
  }
  if ((r.organize_errors || []).length > 0) {
    html += '<details style="margin-top:4px"><summary style="color:#dcdcaa;cursor:pointer">' + r.organize_errors.length + ' errores al organizar</summary><ul style="margin:4px 0;padding-left:16px;font-size:11px;color:#888">';
    r.organize_errors.forEach(e => { html += '<li>' + window._h(e) + '</li>'; });
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
    const el  = document.getElementById('inbox-watcher-info');
    const txt = document.getElementById('inbox-watcher-text');
    if (!el || !txt) return;
    if (d.watching) {
      el.classList.remove('hidden');
      const pending   = d.pending_files || 0;
      const lastCheck = d.last_check ? d.last_check.replace('T', ' ').slice(0, 16) : '—';
      txt.innerHTML = 'Daemon activo · Ultimo chequeo: ' + lastCheck +
        (pending > 0 ? ' · <span style="color:#dcdcaa">' + pending + ' archivos pendientes</span>' : ' · sin archivos pendientes');
    } else {
      el.classList.add('hidden');
    }
  } catch(_) {}
}

export {
  // Badge
  updateInboxBadge,
  _initInboxBadge,
  // Drag & drop
  inboxDragOver,
  inboxDragLeave,
  inboxDrop,
  // Main inbox
  loadInbox,
  fillInboxTarget,
  scanInbox,
  runInbox,
  _applyInboxProgress,
  _renderInboxResult,
  saveInboxSettings,
  _pollInboxWatcher,
};
