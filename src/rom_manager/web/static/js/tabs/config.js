// js/tabs/config.js — Settings tab
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { _showConfirm } from '../components/modal.js';

// Local helpers (small utils duplicated from app.js, removed when app.js is deleted)
const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};
const fmtSize = (n) => n == null ? '?' : n < 1024 * 1024 ? (n / 1024).toFixed(0) + 'KB' : (n / 1024 / 1024).toFixed(1) + 'MB';

// ── Settings ──────────────────────────────────────────────────────────────────
function _onDevicePresetChange() {
  const sel    = document.getElementById('cfg-device-preset');
  const custom = document.getElementById('cfg-device-name-custom');
  if (custom) custom.classList.toggle('hidden', sel?.value !== 'custom');
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
        if (customEl) customEl.classList.add('hidden');
      } else {
        presetEl.value = 'custom';
        if (customEl) { customEl.classList.remove('hidden'); customEl.value = dn; }
      }
    }
    document.getElementById('cfg-rclone-remote').value = cfg.rclone_remote || '';
    const savesRemEl  = document.getElementById('cfg-saves-remote');
    const statesRemEl = document.getElementById('cfg-states-remote');
    if (savesRemEl)  savesRemEl.value  = cfg.saves_remote  || '';
    if (statesRemEl) statesRemEl.value = cfg.states_remote || '';
    const whEl = document.getElementById('cfg-web-host');
    if (whEl) whEl.value = cfg.web_host || '127.0.0.1';
    document.getElementById('cfg-ss-user').value       = cfg.screenscraper_user || '';
    const _ssPassEl = document.getElementById('cfg-ss-pass');
    if (_ssPassEl) { _ssPassEl.value = ''; _ssPassEl.placeholder = cfg.screenscraper_pass_set ? '••••••••' : ''; }
    const ssDevId  = document.getElementById('cfg-ss-devid');
    const ssDevPass = document.getElementById('cfg-ss-devpass');
    if (ssDevId)   ssDevId.value   = cfg.screenscraper_dev_id   || '';
    if (ssDevPass) { ssDevPass.value = ''; ssDevPass.placeholder = cfg.screenscraper_dev_pass_set ? '••••••••' : ''; }
    document.getElementById('cfg-chdman').value        = cfg.chdman || 'chdman';
    document.getElementById('cfg-adb').value           = cfg.adb || 'adb';
    const raPathEl = document.getElementById('cfg-retroarch-path');
    if (raPathEl) raPathEl.value = cfg.retroarch_path || '';
    if (cfg.retroarch_path) _loadCoresStatus();
    const esdePathEl = document.getElementById('cfg-esde-path');
    if (esdePathEl) esdePathEl.value = cfg.esde_path || '';
    const esdeHint = document.getElementById('esde-library-root-hint');
    if (esdeHint) esdeHint.textContent = cfg.library_root || '(configura library_root primero)';
    const bkEnabledEl = document.getElementById('cfg-backup-enabled');
    const bkKeepNEl   = document.getElementById('cfg-backup-keep-n');
    if (bkEnabledEl) bkEnabledEl.checked = cfg.backup_saves_enabled !== false;
    if (bkKeepNEl)   bkKeepNEl.value     = cfg.backup_saves_keep_n ?? 5;
    const notifyEl = document.getElementById('cfg-notify-desktop');
    if (notifyEl) notifyEl.checked = cfg.notify_desktop !== false;
    const _raKeyEl = document.getElementById('cfg-ra-api-key');
    if (_raKeyEl) { _raKeyEl.value = ''; _raKeyEl.placeholder = cfg.ra_api_key_set ? '••••••••' : ''; }
    const raUserEl = document.getElementById('cfg-ra-username');
    if (raUserEl) raUserEl.value = cfg.ra_username || '';
    // Show config warnings
    const banner = document.getElementById('cfg-warnings-banner');
    if (banner) {
      const warns = (cfg.warnings || []);
      if (warns.length === 0) {
        banner.classList.add('hidden');
      } else {
        const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        const items = warns.map(w => {
          const icon = w.level === 'warning' ? '⚠' : 'ℹ';
          const color = w.level === 'warning' ? '#f9e2af' : '#89b4fa';
          return `<div style="color:${color};font-size:12px;margin:2px 0">${icon} ${esc(w.message)}</div>`;
        }).join('');
        banner.innerHTML = items;
        banner.classList.remove('hidden');
      }
    }
    // Show two-DB info
    const dbInfo = document.getElementById('settings-db-info');
    if (dbInfo && cfg.pc_db_path) {
      const fmtSize = (n) => n == null ? '?' : n < 1024*1024 ? (n/1024).toFixed(0)+'KB' : (n/1024/1024).toFixed(1)+'MB';
      dbInfo.innerHTML =
        '<div style="display:grid;grid-template-columns:auto 1fr auto;gap:4px 12px;align-items:center">' +
        '<span style="color:var(--c-teal)">&#x25CF;</span><span style="font-family:monospace;color:var(--c-text)">library_pc.db</span><span style="color:var(--c-muted)">' + fmtSize(cfg.pc_db_size) + '</span>' +
        '<span style="color:var(--c-orange)">&#x25CF;</span><span style="font-family:monospace;color:var(--c-text)">library_android.db</span><span style="color:var(--c-muted)">' + fmtSize(cfg.android_db_size) + '</span>' +
        '</div>';
    }
  } catch(e) { /* silent */ }
}

async function migrateSplitDb() {
  const el = document.getElementById('migrate-db-result');
  if (!el) return;
  _txtCls(el, 'txt-muted'); el.textContent = 'Migrando…';
  try {
    const r = await apiPost('/api/migrate-split-db', {});
    if (r.error) { _txtCls(el, 'txt-err'); el.textContent = '✗ ' + r.error; return; }
    _txtCls(el, 'txt-ok');
    el.textContent = '✓ Migrados: ' + r.migrated_games + ' juegos  |  Errores: ' + (r.errors?.length || 0);
    if (r.errors && r.errors.length > 0) {
      el.textContent += '  [' + r.errors.slice(0,3).join('; ') + ']';
    }
  } catch(e) { _txtCls(el, 'txt-err'); el.textContent = '✗ ' + e.message; }
}

async function testChdman() {
  const el = document.getElementById('chdman-test-result');
  _txtCls(el, 'txt-muted'); el.textContent = 'Probando…';
  // Save current chdman value first if changed
  const val = document.getElementById('cfg-chdman').value.trim();
  if (val) await apiPost('/api/config', { 'tools.chdman': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/test-chdman');
    if (d.ok) {
      _txtCls(el, 'txt-ok');
      el.textContent = '✓ ' + (d.version || 'OK') + '  (' + d.path + ')';
      // Update CHD panel status too
      const st = document.getElementById('chdman-status');
      if (st) { _txtCls(st, 'txt-ok'); st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
    } else {
      _txtCls(el, 'txt-err'); el.textContent = '✗ ' + d.error;
      const st = document.getElementById('chdman-status');
      if (st) { _txtCls(st, 'txt-err'); st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
    }
  } catch(e) { _txtCls(el, 'txt-err'); el.textContent = '✗ ' + e.message; }
}

async function testMaxcso() {
  const st = document.getElementById('maxcso-status');
  if (!st) return;
  _txtCls(st, 'txt-muted'); st.textContent = 'Verificando…';
  try {
    const d = await apiFetch('/api/test-maxcso');
    if (d.ok) {
      _txtCls(st, 'txt-ok');
      st.textContent = '✓ ' + (d.version || 'maxcso disponible');
    } else {
      _txtCls(st, 'txt-err');
      st.textContent = '✗ maxcso no encontrado — coloca maxcso.exe en tools/';
    }
  } catch(e) {
    _txtCls(st, 'txt-err');
    st.textContent = '✗ Error: ' + e.message;
  }
}

async function testAdbBinary() {
  const el = document.getElementById('adb-test-result');
  _txtCls(el, 'txt-muted'); el.textContent = 'Probando…';
  const val = document.getElementById('cfg-adb').value.trim();
  if (val) await apiPost('/api/config', { 'tools.adb': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      _txtCls(el, 'txt-err'); el.textContent = '✗ ' + d.error;
    } else {
      _txtCls(el, 'txt-ok');
      el.textContent = `✓ adb accesible — ${d.devices?.length ?? 0} dispositivo(s) detectado(s)  (${d.adb_path})`;
    }
  } catch(e) { _txtCls(el, 'txt-err'); el.textContent = '✗ ' + e.message; }
}

// B7-9: Log viewer
let _logData = {};
async function loadLogViewer() {
  const sel = document.getElementById('log-select');
  const pre = document.getElementById('log-content');
  const meta = document.getElementById('log-meta');
  if (!sel || !pre) return;
  pre.textContent = 'Cargando…';
  pre.classList.remove('hidden');
  try {
    const d = await apiFetch('/api/logs?lines=300');
    _logData = d.logs || {};
    const key = sel.value;
    const log = _logData[key] || {};
    if (log.error) {
      pre.textContent = 'Error: ' + log.error;
    } else if (!log.lines?.length) {
      pre.textContent = '(Log vacío o no encontrado)';
    } else {
      pre.textContent = log.lines.join('\n');
      pre.scrollTop = pre.scrollHeight;
    }
    if (meta && log.size_bytes !== undefined) {
      meta.textContent = `${log.total_lines || 0} líneas · ${fmtSize(log.size_bytes)} · ${log.path || ''}`;
    }
  } catch(e) {
    if (pre) pre.textContent = 'Error: ' + e.message;
  }
}

function downloadLog() {
  const sel = document.getElementById('log-select');
  if (!sel) return;
  const key = sel.value;
  const log = _logData[key];
  if (!log?.lines?.length) { showToast('Carga el log primero', 'err'); return; }
  const blob = new Blob([log.lines.join('\n')], {type: 'text/plain;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = key + '.log';
  a.click();
}

async function loadTools() {
  try {
    const [cfg, discData] = await Promise.all([
      apiFetch('/api/config'),
      apiFetch('/api/disc-folders').catch(() => ({ folders: [], library_root: null })),
    ]);
    // Health check schedule info
    apiFetch('/api/health-schedule').then(sched => {
      const el = document.getElementById('health-schedule-info');
      if (!el) return;
      const fmt = iso => iso ? new Date(iso).toLocaleDateString('es-ES', {day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}) : '—';
      const lastOk = sched.last_ok != null ? `${sched.last_ok} OK` : '';
      const lastBad = (sched.last_corrupted || 0) + (sched.last_missing || 0);
      const statusPart = lastOk ? ` · ${lastOk}${lastBad ? `, ${lastBad} problemas` : ''}` : '';
      const overdueTxt = sched.overdue ? ' <span style="color:var(--accent-ora)">⚠ programado</span>' : '';
      el.innerHTML = `&#xfa0;ltimo: <strong>${fmt(sched.last_run_at)}</strong>${statusPart} &nbsp;·&nbsp; Pr&#xf3;ximo: <strong>${fmt(sched.next_run_at)}</strong>${overdueTxt}`;
    }).catch(() => {
      const el = document.getElementById('health-schedule-info');
      if (el) el.textContent = '';
    });
    const root = cfg.library_root || '';
    // Auto-fill simple tools with library_root
    if (root) {
      _setIfEmpty('zip-path',               root);
      _setIfEmpty('orphan-path',            root);
      _setIfEmpty('verify-multidisc-path',  discData.folders.length ? discData.folders.join('\n') : root);
      _setIfEmpty('m3u-path',               discData.folders.length ? discData.folders[0] : root);
      _setIfEmpty('chd-path',               discData.folders.length ? discData.folders[0] : root);
      _setIfEmpty('cso-path',               root);
      _setIfEmpty('report-path',            root);
    }
    // Show multi-disc hint
    if (discData.folders.length > 1) {
      const hint = document.getElementById('multidisc-folder-hint');
      if (hint) {
        hint.textContent = `Detectadas ${discData.folders.length} carpetas de plataformas de disco: ${discData.folders.map(f => f.split(/[\\/]/).pop()).join(', ')}`;
        hint.classList.remove('hidden');
      }
    }
    // Test chdman silently and update status
    try {
      const d = await apiFetch('/api/test-chdman');
      const st = document.getElementById('chdman-status');
      if (st) {
        if (d.ok) { _txtCls(st, 'txt-ok'); st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
        else      { _txtCls(st, 'txt-err'); st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
      }
    } catch(_) {}
    // Test maxcso silently and update status
    try {
      const d = await apiFetch('/api/test-maxcso');
      const st = document.getElementById('maxcso-status');
      if (st) {
        if (d.ok) { _txtCls(st, 'txt-ok'); st.textContent = '✓ ' + (d.version || 'maxcso disponible'); }
        else      { _txtCls(st, 'txt-err'); st.textContent = '✗ maxcso no encontrado — coloca maxcso.exe en tools/'; }
      }
    } catch(_) {}
    // Show RA API key status
    const raStatus = document.getElementById('ra-api-key-status');
    if (raStatus) {
      if (cfg.ra_api_key_set) {
        _txtCls(raStatus, 'txt-ok');
        raStatus.textContent = '✓ API key configurada';
      } else {
        _txtCls(raStatus, 'txt-err');
        raStatus.innerHTML = '✗ API key no configurada — <a href="#" onclick="showTab(\'settings\');return false" style="color:var(--c-blue)">ir a Settings</a>';
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

  // Resolve root from context selector (PC vs Android) — B2
  const ctx = localStorage.getItem('tools_context') || 'pc';
  const root = ctx === 'android'
    ? (localStorage.getItem('anbernic_path') || localStorage.getItem('cable_ab_path') || cfg.library_root)
    : cfg.library_root;

  if (!root) { alert('Configura library_root en Settings primero.'); return; }
  if (ctx === 'android' && !localStorage.getItem('anbernic_path') && !localStorage.getItem('cable_ab_path')) {
    alert('Contexto Android: configura la ruta de la consola en Settings o conecta el cable.');
    return;
  }

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
  if (document.getElementById('batch-scraper')?.checked) jobs.push({
    name: 'Scraper (ScreenScraper)', runningKey: 'scrape_running',
    start: () => apiPost('/api/scrape', { platform: null, limit: 0, images: true }),
  });
  if (jobs.length === 0) { alert('Selecciona al menos una herramienta.'); return; }

  const btn = document.getElementById('btn-batch-run');
  const statusEl = document.getElementById('batch-status');
  btn.disabled = true;
  let allOk = true;

  for (const job of jobs) {
    statusEl.innerHTML = `<span style="color:var(--c-muted)">⟳ ${window._h(job.name)}…</span>`;
    try {
      const d = await job.start();
      if (d.status === 'already_running') {
        statusEl.innerHTML = `<span style="color:var(--c-yellow)">⚠ ${window._h(job.name)} ya está en curso — esperando…</span>`;
      } else if (d.error) {
        statusEl.innerHTML = `<span style="color:var(--c-red)">Error en ${window._h(job.name)}: ${window._h(d.error)}</span>`;
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
      statusEl.innerHTML = `<span style="color:var(--c-teal)">✓ ${window._h(job.name)} completado.</span>`;
      window.startPolling();
    } catch(e) {
      statusEl.innerHTML = `<span style="color:var(--c-red)">Error en ${window._h(job.name)}: ${window._h(e.message)}</span>`;
      allOk = false; break;
    }
  }

  btn.disabled = false;
  if (allOk) {
    statusEl.innerHTML = `<span style="color:var(--c-teal)">✓ Todas las operaciones completadas sobre ${window._h(root)}.</span>`;
    window.loadOverview();
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
        statusEl.innerHTML = '<span style="color:var(--c-teal)">&#x2713; PIN activado</span> — se pedirá al abrir la app desde otra IP.';
        if (clearBtn) clearBtn.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');
      } else {
        statusEl.textContent = 'Sin PIN. La interfaz es accesible sin contraseña.';
        if (clearBtn) clearBtn.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
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
    const urlVal = (d.ip && d.ip !== '127.0.0.1') ? `${d.ip}:${d.port}` : '';
    if (el) el.textContent = urlVal || '— (no detectada)';
    if (urlVal) {
      renderQR('http://' + urlVal, 'qr-canvas');
      const noUrlEl = document.getElementById('qr-no-url');
      if (noUrlEl) noUrlEl.classList.add('hidden');
      const canvasEl = document.getElementById('qr-canvas');
      if (canvasEl) canvasEl.classList.remove('hidden');
    } else {
      const noUrlEl = document.getElementById('qr-no-url');
      if (noUrlEl) noUrlEl.classList.remove('hidden');
      const canvasEl = document.getElementById('qr-canvas');
      if (canvasEl) canvasEl.classList.add('hidden');
    }
  } catch(e) {
    if (el) el.textContent = '—';
    const noUrlEl = document.getElementById('qr-no-url');
    if (noUrlEl) noUrlEl.classList.remove('hidden');
    const canvasEl = document.getElementById('qr-canvas');
    if (canvasEl) canvasEl.classList.add('hidden');
  }
}

function copyLocalUrl() {
  const url = document.getElementById('local-url-display')?.textContent;
  if (!url || url === 'cargando…' || url === '—') return;
  navigator.clipboard?.writeText(url).then(() => showToast('URL copiada', 'ok')).catch(() => {});
}

// ── QR Code Generator (pure JS, ~80 lines) ──────────────────────────────
function renderQR(text, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const size = 140;
  const moduleSize = 2; // Adjust for finer/coarser QR

  // Generate QR data (simple version 2 QR code)
  const data = _encodeQRData(text);
  const matrix = _generateQRMatrix(data);

  // Clear canvas
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, size, size);

  // Draw QR modules
  ctx.fillStyle = '#000';
  const qrSize = matrix.length;
  const scale = size / qrSize;
  for (let y = 0; y < qrSize; y++) {
    for (let x = 0; x < qrSize; x++) {
      if (matrix[y][x]) {
        ctx.fillRect(x * scale, y * scale, scale, scale);
      }
    }
  }
}

function _encodeQRData(text) {
  // Encode text as QR byte data
  const codes = [];
  for (let i = 0; i < text.length; i++) {
    codes.push(text.charCodeAt(i));
  }
  return codes;
}

function _generateQRMatrix(codes) {
  const version = 2;
  const qrSize = 25; // v2 = 25x25
  const matrix = Array(qrSize).fill(0).map(() => Array(qrSize).fill(0));

  // Position detection patterns (3 corners)
  const pattern = [[1,1,1,1,1,1,1],[1,0,0,0,0,0,1],[1,0,1,1,1,0,1],[1,0,1,1,1,0,1],[1,0,1,1,1,0,1],[1,0,0,0,0,0,1],[1,1,1,1,1,1,1]];
  const placePat = (x, y) => {
    for (let i = 0; i < 7; i++) for (let j = 0; j < 7; j++) if (x+i < qrSize && y+j < qrSize) matrix[y+j][x+i] = pattern[j][i];
  };
  placePat(0, 0); placePat(qrSize-7, 0); placePat(0, qrSize-7);

  // Timing patterns
  for (let i = 8; i < qrSize - 8; i++) {
    matrix[6][i] = i % 2;
    matrix[i][6] = i % 2;
  }

  // Data area (simplified: just fill with encoded data)
  let x = qrSize - 1, y = qrSize - 1, bitIdx = 0, byteIdx = 0;
  let bit = 0;

  while (x > 0) {
    for (let i = 0; i < 2; i++) {
      if (matrix[y][x] === 0) {
        if (byteIdx < codes.length) {
          bit = (codes[byteIdx] >> (7 - (bitIdx % 8))) & 1;
          matrix[y][x] = bit;
          bitIdx++;
          if (bitIdx % 8 === 0) byteIdx++;
        } else {
          matrix[y][x] = (Math.random() > 0.5) ? 1 : 0; // Padding
        }
      }
      x--;
    }
    if (x > 0) x--;
    y = y % 2 === 0 ? y - 1 : y + 1;
  }

  return matrix;
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
  const savesR  = document.getElementById('cfg-saves-remote')?.value.trim()  || '';
  const statesR = document.getElementById('cfg-states-remote')?.value.trim() || '';
  if (savesR)  updates['sync.saves_remote']  = savesR;
  if (statesR) updates['sync.states_remote'] = statesR;
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
  const raUser = document.getElementById('cfg-ra-username')?.value.trim();
  if (raUser) updates['retroachievements.username'] = raUser;
  const raPath = document.getElementById('cfg-retroarch-path')?.value.trim();
  if (raPath) updates['launchers.retroarch'] = raPath;
  const esdePath = document.getElementById('cfg-esde-path')?.value.trim();
  if (esdePath !== undefined) updates['launchers.esde'] = esdePath;
  const bkEnabledEl = document.getElementById('cfg-backup-enabled');
  const bkKeepNEl   = document.getElementById('cfg-backup-keep-n');
  if (bkEnabledEl) updates['backup.saves_enabled'] = bkEnabledEl.checked;
  if (bkKeepNEl && bkKeepNEl.value) updates['backup.saves_keep_n'] = parseInt(bkKeepNEl.value, 10);
  const notifyDesktopEl = document.getElementById('cfg-notify-desktop');
  if (notifyDesktopEl) updates['notifications.desktop'] = notifyDesktopEl.checked;
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
      if (dn) window._applyDeviceName(dn);
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

async function testNotification() {
  const resultEl = document.getElementById('notify-test-result');
  if (resultEl) resultEl.textContent = 'Enviando…';
  try {
    const d = await apiPost('/api/notify-test', {});
    if (resultEl) resultEl.textContent = d.ok ? '✓ Notificación enviada' : ('Error: ' + (d.error || 'desconocido'));
  } catch(e) {
    if (resultEl) resultEl.textContent = 'Error: ' + e.message;
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
  if (abPath) window.loadOverview();

  resultEl.className = 'job-result visible ok-r';
  resultEl.textContent = 'Rutas guardadas.';
  setTimeout(() => { resultEl.className = 'job-result'; }, 3000);
}

async function doMigrateSavesStructure(dryRun) {
  const res = document.getElementById('migrate-saves-result');
  const dryBtn   = document.getElementById('btn-migrate-saves-dry');
  const applyBtn = document.getElementById('btn-migrate-saves-apply');
  if (res) { res.textContent = dryRun ? 'Analizando\u2026' : 'Migrando\u2026'; res.style.color = '#888'; }
  if (dryBtn)   dryBtn.disabled = true;
  if (applyBtn) applyBtn.disabled = true;
  try {
    const d = await apiPost('/api/migrate-saves-structure', { dry_run: dryRun });
    if (d.error) {
      if (res) { res.textContent = '\u274C ' + d.error; res.style.color = 'var(--c-red)'; }
      return;
    }
    const action = dryRun ? 'Mover\xeda' : 'Movidos';
    let msg = `${action}: ${d.moves_saves} saves + ${d.moves_states} savestates`;
    if (d.errors?.length) msg += ` \u2014 ${d.errors.length} error(es)`;
    if (dryRun && d.preview?.length) {
      msg += '<br><small style="color:var(--c-dim)">' + d.preview.slice(0, 5).map(p => p.source.split(/[\\/]/).pop()).join(', ') + (d.preview.length > 5 ? '\u2026' : '') + '</small>';
    }
    if (res) { res.innerHTML = (dryRun ? '\u2139\uFE0F ' : '\u2705 ') + msg; res.style.color = dryRun ? 'var(--c-yellow)' : 'var(--c-teal)'; }
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; res.style.color = 'var(--c-red)'; }
  } finally {
    if (dryBtn)   dryBtn.disabled = false;
    if (applyBtn) applyBtn.disabled = false;
  }
}

// ── Public exports ────────────────────────────────────────────────────────────
// ── Folder picker ─────────────────────────────────────────────────────────────

/**
 * Open the native OS folder picker and fill *inputId* with the selected path.
 * Uses GET /api/browse-folder (backend: tkinter.filedialog).
 */
async function _loadCoresStatus() {
  const el = document.getElementById('ra-cores-status');
  if (!el) return;
  try {
    const d = await apiFetch('/api/retroarch-check');
    if (!d.exe_configured || !d.exe_exists) { el.innerHTML = ''; return; }
    if (!d.cores_dir_exists) {
      el.innerHTML = '<span style="color:var(--c-amber)">⚠ Carpeta cores/ no encontrada — instala cores desde RetroArch → Online Updater</span>';
      return;
    }
    const missing = Object.entries(d.key_cores || {}).filter(([, ok]) => !ok).map(([lbl]) => lbl);
    let html = `<span style="color:var(--c-teal)">✓ ${d.cores_count} cores instalados</span>`;
    if (missing.length) {
      html += `&nbsp;·&nbsp;<span style="color:var(--c-amber)">Sin instalar: ${missing.map(l => window._h(l)).join(', ')}</span>`;
    }
    el.innerHTML = html;
  } catch(_) { el.innerHTML = ''; }
}

async function detectRetroArch() {
  const resultEl = document.getElementById('ra-detect-result');
  const btn = document.querySelector('[data-action="detect-retroarch"]');
  if (resultEl) { resultEl.textContent = 'Buscando…'; resultEl.style.color = '#888'; }
  if (btn) btn.disabled = true;
  try {
    const d = await apiFetch('/api/detect-retroarch');
    if (d.found) {
      const input = document.getElementById('cfg-retroarch-path');
      if (input) input.value = d.retroarch_path;
      let msg = '✓ Encontrado: ' + d.retroarch_path;
      if (d.library_root) {
        const lrInput = document.getElementById('cfg-library-root');
        if (lrInput && !lrInput.value.trim()) {
          lrInput.value = d.library_root;
          msg += '  ·  Biblioteca: ' + d.library_root;
        }
      }
      if (resultEl) { resultEl.textContent = msg; resultEl.style.color = 'var(--c-teal)'; }
    } else {
      if (resultEl) { resultEl.textContent = '✗ No encontrado — introduce la ruta manualmente.'; resultEl.style.color = 'var(--c-red)'; }
    }
  } catch (e) {
    if (resultEl) { resultEl.textContent = '✗ Error: ' + e.message; resultEl.style.color = 'var(--c-red)'; }
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function browseFolder(inputId, title) {
  const input = document.getElementById(inputId);
  const btn   = document.querySelector(`button[data-browse="${inputId}"]`);
  if (btn) { btn.disabled = true; btn.textContent = '…'; }

  try {
    const initialDir = input?.value.trim() || '';
    const params = new URLSearchParams({ title: title || 'Seleccionar carpeta' });
    if (initialDir) params.set('initial_dir', initialDir);

    const d = await apiFetch('/api/browse-folder?' + params.toString());
    if (d.ok && d.path) {
      if (input) input.value = d.path;
      // Trigger a change event so auto-save listeners can react
      input?.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (!d.cancelled) {
      showToast(d.error || 'No se pudo abrir el selector de carpeta', 'err');
    }
  } catch (e) {
    showToast('Error al abrir el selector: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Examinar'; }
  }
}

export {
  _onDevicePresetChange,
  loadSettings, migrateSplitDb, testChdman, testMaxcso, testAdbBinary,
  loadLogViewer, downloadLog, loadTools, _setIfEmpty,
  doBatchRun, _initToolPath, fillToolPath,
  loadAuthStatus, doLogout, setPin, clearPin,
  loadLocalUrl, copyLocalUrl, renderQR,
  saveSettings, testNotification, saveOvPaths,
  doMigrateSavesStructure,
  browseFolder, detectRetroArch,
};
