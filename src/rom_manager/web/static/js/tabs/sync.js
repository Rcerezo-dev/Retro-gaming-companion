// js/tabs/sync.js — Cloud Sync, Cable Sync, Auto-sync, Rclone, Android setup
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Module-level state ────────────────────────────────────────────────────────
let _androidSetupUrl = '';
let _anbernicBaseUrl = '';
let _autoSyncTimer = null;
let _autoSyncEnabled = true;

// ── Sync ──────────────────────────────────────────────────────────────────────
async function loadSync() {
  const el = document.getElementById('sync-content');
  // QoL-14: offline badge for rclone
  apiFetch('/api/system-status').then(st => {
    const banner = document.getElementById('sync-offline-banner');
    if (banner) banner.classList.toggle('hidden', st.rclone?.ok);
  }).catch(() => {});
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
      syncBar.classList.remove('hidden');
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
      assetsBar.classList.remove('hidden');
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

// ── System status ─────────────────────────────────────────────────────────────
async function loadSystemStatus() {
  const el = document.getElementById('system-status-grid');
  if (!el) return;
  try {
    const d = await apiFetch('/api/system-status');
    const row = (label, ok, detail) => {
      const icon = ok ? '<span style="color:#4ec9b0">✓</span>' : '<span style="color:#f44747">✗</span>';
      const det = detail ? `<span style="color:#555;margin-left:4px">${_h(detail)}</span>` : '';
      return `<div>${icon} <strong>${label}</strong>${det}</div>`;
    };
    const rcloneDetail = d.rclone.ok
      ? (d.rclone.remotes.length ? d.rclone.remotes.join(', ') : 'instalado, sin remotes')
      : 'no encontrado';
    const catDetail = d.catalogs.ok
      ? `${d.catalogs.nointro} No-Intro, ${d.catalogs.redump} Redump`
      : 'ningún catálogo importado — ve a Catálogos DAT';
    el.innerHTML =
      row('chdman',   d.chdman.ok,   d.chdman.ok   ? d.chdman.version   : 'no encontrado — configura ruta en Settings') +
      row('adb',      d.adb.ok,      d.adb.ok      ? d.adb.version      : 'no encontrado — coloca adb.exe en tools/') +
      row('rclone',   d.rclone.ok,   rcloneDetail) +
      row('RA API key', d.ra_key.ok, d.ra_key.ok   ? 'configurada'      : 'falta — necesaria para logros') +
      row('Catálogos DAT', d.catalogs.ok, catDetail) +
      row('Biblioteca', d.library.ok, d.library.ok ? d.library.path     : 'no configurada — ve a Ajustes');
  } catch(e) {
    if (el) el.textContent = 'Error al comprobar estado: ' + e.message;
  }
}

// ── Cloud folder auto-detection ───────────────────────────────────────────────
async function detectCloudFolder() {
  const res = document.getElementById('cloud-detect-result');
  if (!res) return;
  res.classList.remove('hidden');
  res.textContent = 'Detectando…';
  try {
    const d = await apiFetch('/api/detect-cloud-folder');
    if (!d.detected.length) {
      res.innerHTML = '⚠ No se detectó ningún cliente de nube instalado (Dropbox, OneDrive, Google Drive).<br>'
        + '<span style="color:#555">Para sincronizar sin cliente local, configura rclone manualmente.</span>';
      return;
    }
    res.innerHTML = d.detected.map(item => `
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap">
        <span style="color:#4ec9b0;min-width:90px"><strong>${_h(item.service)}</strong></span>
        <span style="color:#888;font-size:11px;flex:1">${_h(item.local_folder)}</span>
        <button class="btn primary" style="font-size:11px;padding:3px 10px;flex-shrink:0"
          onclick="useCloudFolder(${JSON.stringify(item.suggested_remote)})">Usar esta carpeta</button>
      </div>`).join('') +
      '<div style="color:#555;margin-top:6px;font-size:11px">La app copiará los saves a esta carpeta. ' +
      'El cliente de nube se encarga de subirlos. En la consola Android instala la app de nube correspondiente.</div>';
  } catch(e) {
    res.textContent = 'Error: ' + e.message;
  }
}

function useCloudFolder(path) {
  const inp = document.getElementById('cfg-rclone-remote');
  if (inp) {
    inp.value = path;
    inp.dispatchEvent(new Event('input'));
    showToast('Ruta configurada — guarda los ajustes para aplicar', 'ok');
  }
  const res = document.getElementById('cloud-detect-result');
  if (res) res.classList.add('hidden');
}

// ── Autostart toggle ───────────────────────────────────────────────────────────
async function loadAutostart() {
  try {
    const d = await apiFetch('/api/autostart-status');
    const badge = document.getElementById('autostart-badge');
    const btn   = document.getElementById('autostart-btn');
    const note  = document.getElementById('autostart-note');
    const trayNote = document.getElementById('autostart-tray-note');
    if (!badge || !btn) return;
    if (d.enabled) {
      badge.textContent = 'ACTIVADO';
      badge.style.color = '#6a9955';
      btn.textContent   = 'Desactivar inicio automatico';
      btn.classList.add('danger');
      if (note) note.classList.remove('hidden');
    } else {
      badge.textContent = 'desactivado';
      _txtCls(badge, 'txt-muted');
      btn.textContent   = 'Activar inicio automatico';
      btn.classList.remove('danger');
      if (note) note.classList.add('hidden');
    }
    if (trayNote) trayNote.classList.toggle('hidden', !(d.tray_running));
  } catch (e) {
    console.warn('loadAutostart:', e);
  }
}

async function toggleAutostart() {
  const btn = document.getElementById('autostart-btn');
  if (btn) btn.disabled = true;
  try {
    const d = await apiFetch('/api/autostart-toggle', { method: 'POST' });
    if (d.ok) {
      const msg = d.enabled ? 'Inicio automatico activado' : 'Inicio automatico desactivado';
      showToast(msg, 'ok');
      loadAutostart();
    } else {
      showToast(d.error || 'Error al cambiar el inicio automatico', 'error');
    }
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function shutdownServer() {
  if (!confirm('¿Cerrar Retro Vault? Tendrás que relanzarlo desde la terminal.')) return;
  try {
    await apiFetch('/api/shutdown', { method: 'POST' });
  } catch (_) { /* conexión cortada — es lo esperado */ }
  document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace;color:#555;font-size:14px">Retro Vault cerrado. Puedes cerrar esta pestaña.</div>';
}

// ── Android setup panel ──────────────────────────────────────────────────────
async function loadAndroidSetupPanel() {
  try {
    const d = await apiFetch('/api/local-url');
    const ip = d.ip || location.hostname;
    const port = d.port || 7777;
    _androidSetupUrl = `http://${ip}:${port}/api/anbernic-setup.sh`;
    const curlCmd = `curl -s "${_androidSetupUrl}" | bash`;

    // Settings panel QR
    renderQR(_androidSetupUrl, 'android-setup-qr');
    const urlEl = document.getElementById('android-setup-url');
    if (urlEl) urlEl.textContent = _androidSetupUrl;
    const curlEl = document.getElementById('android-setup-curl');
    if (curlEl) { curlEl.textContent = curlCmd; curlEl.classList.remove('hidden'); }

    // Android detected panel
    const panelCurl = document.getElementById('android-panel-curl');
    if (panelCurl) panelCurl.textContent = curlCmd;
  } catch(e) {
    console.warn('loadAndroidSetupPanel:', e);
  }
}

function copyAndroidSetupUrl() {
  if (!_androidSetupUrl) return;
  navigator.clipboard?.writeText(_androidSetupUrl)
    .then(() => showToast('URL copiada', 'ok'))
    .catch(() => {});
}

function copyAndroidCurlCmd() {
  const el = document.getElementById('android-panel-curl');
  const cmd = el?.textContent?.trim();
  if (!cmd) return;
  navigator.clipboard?.writeText(cmd)
    .then(() => showToast('Comando copiado', 'ok'))
    .catch(() => {});
}

function downloadAndroidSetupSh() {
  if (!_androidSetupUrl) return;
  const a = document.createElement('a');
  a.href = _androidSetupUrl;
  a.download = 'retrovault-setup.sh';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function _checkAndroidUserAgent() {
  if (/Android/i.test(navigator.userAgent)) {
    const panel = document.getElementById('android-detected-panel');
    if (panel) panel.classList.remove('hidden');
    loadAndroidSetupPanel();
  }
}

// ── Anbernic tab ─────────────────────────────────────────────────────────────
async function loadAnbernicTab() {
  try {
    const d = await apiFetch('/api/local-url');
    const ip = d.ip || location.hostname;
    const port = d.port || 7777;
    _anbernicBaseUrl = `http://${ip}:${port}`;
    const setupUrl = `${_anbernicBaseUrl}/s`;
    const curlCmd  = `curl -s "${setupUrl}" | bash`;

    // Step 1 — big IP display
    const ipDisplay = document.getElementById('anb-ip-display');
    if (ipDisplay) ipDisplay.textContent = _anbernicBaseUrl;

    // Step 5 — command box
    const cmdFull = document.getElementById('anb-cmd-full');
    if (cmdFull) cmdFull.textContent = curlCmd;

    // Step 5 — download .sh link
    const dlLink = document.getElementById('anb-script-download');
    if (dlLink) dlLink.href = `${_anbernicBaseUrl}/api/anbernic-setup.sh`;

    // Sync android overlay curl cmd too
    const panelCurl = document.getElementById('android-panel-curl');
    if (panelCurl) panelCurl.textContent = curlCmd;
    _androidSetupUrl = setupUrl;
  } catch(e) {
    console.warn('loadAnbernicTab:', e);
  }
}

function copyAnbernicUrl() {
  if (!_anbernicBaseUrl) return;
  navigator.clipboard?.writeText(_anbernicBaseUrl)
    .then(() => showToast('URL copiada', 'ok'))
    .catch(() => {});
}

function copyAnbernicCmd() {
  const cmd = document.getElementById('anb-cmd-full')?.textContent?.trim();
  if (!cmd || cmd === 'Cargando…') return;
  navigator.clipboard?.writeText(cmd)
    .then(() => showToast('Comando copiado', 'ok'))
    .catch(() => {});
}

// ── Rclone setup wizard ───────────────────────────────────────────────────────
function toggleRcloneSetup() {
  const panel = document.getElementById('rclone-setup-panel');
  if (!panel) return;
  const showing = !panel.classList.contains('hidden');
  panel.classList.toggle('hidden', showing);
  if (!showing) loadRcloneStatus();
}

async function loadRcloneStatus() {
  const info = document.getElementById('rclone-status-info');
  const remPanel = document.getElementById('rclone-remotes-panel');
  if (info) info.textContent = 'Comprobando rclone\u2026';
  if (remPanel) remPanel.classList.add('hidden');
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
      if (remPanel) remPanel.classList.remove('hidden');
    }
  } catch(e) {
    if (info) info.textContent = '\u274C Error: ' + e.message;
  }
}

async function openRcloneConfig() {
  const btn = document.getElementById('btn-rclone-open-config');
  if (btn) { btn.disabled = true; btn.textContent = 'Abriendo\u2026'; }
  try {
    const d = await apiPost('/api/rclone-open-config', {});
    if (d.ok) {
      showToast('Terminal abierto con rclone config', 'ok');
    } else {
      showToast('Error: ' + (d.error || 'no se pudo abrir el terminal'), 'err');
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Configurar nuevo remote\u2026'; }
  }
}

async function testRcloneRemote() {
  const remote = document.getElementById('rclone-remote-select')?.value || '';
  const res = document.getElementById('rclone-test-result');
  if (!remote) { if (res) { res.textContent = 'Selecciona un remote.'; res.style.color = '#dcdcaa'; } return; }
  if (res) { res.textContent = 'Verificando\u2026'; res.style.color = '#888'; }
  try {
    const d = await apiPost('/api/rclone-test-remote', { remote });
    if (d.ok) {
      const entries = d.entries > 0 ? ` · ${d.entries} carpeta(s) en ra\xedz` : ' · ra\xedz vac\xeda o sin permiso de lectura';
      if (res) { res.innerHTML = '\u2705 Conexi\xf3n OK' + entries; res.style.color = '#4ec9b0'; }
    } else {
      if (res) { res.innerHTML = '\u274C ' + (d.error || 'error'); res.style.color = '#f44747'; }
    }
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; res.style.color = '#f44747'; }
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
    if (res) { res.innerHTML = '\u2705 Guardado: <code>' + fullRemote + '</code>'; _txtCls(res, 'txt-ok'); }
    const cfgInp = document.getElementById('cfg-rclone-remote');
    if (cfgInp) cfgInp.value = fullRemote;
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; _txtCls(res, 'txt-err'); }
  }
}

// ── Cable Sync ────────────────────────────────────────────────────────────────
function _isAdbMode() {
  return document.querySelector('input[name="cable-ab-mode"]:checked')?.value === 'adb';
}

function _onCableModeChange() {
  const adb = _isAdbMode();
  const fsEl  = document.getElementById('cable-fs-section');
  const adbEl = document.getElementById('cable-adb-section');
  if (fsEl)  fsEl.classList.toggle('hidden', adb);
  if (adbEl) adbEl.classList.toggle('hidden', !(adb));
}

function _onCableDryRunChange() {
  const cb = document.getElementById('cable-dry-run');
  const warn = document.getElementById('cable-dry-run-warning');
  if (warn) warn.classList.toggle('hidden', cb?.checked);
}

function _onCableDirectionChange() {
  const dir = document.querySelector('input[name="cable-direction"]:checked')?.value;
  const row = document.getElementById('cable-sha1-row');
  if (row) row.classList.toggle('hidden', !((dir === 'anbernic_to_pc')));
  const mirrorLabel = document.getElementById('cable-mirror-label');
  if (mirrorLabel) mirrorLabel.classList.toggle('hidden', dir === 'newest');
}

async function testCablePath(which) {
  const inputId  = which === 'pc' ? 'cable-pc-path' : 'cable-ab-path';
  const statusId = which === 'pc' ? 'cable-pc-path-status' : 'cable-ab-path-status';
  const path = document.getElementById(inputId)?.value.trim();
  const statusEl = document.getElementById(statusId);
  if (!path) { if (statusEl) { _txtCls(statusEl, 'txt-muted'); statusEl.textContent = 'Introduce una ruta primero.'; } return; }
  if (statusEl) { _txtCls(statusEl, 'txt-dim'); statusEl.textContent = 'Verificando…'; }
  try {
    const d = await apiFetch('/api/test-path?path=' + encodeURIComponent(path));
    if (d.accessible) {
      _txtCls(statusEl, 'txt-ok');
      statusEl.textContent = `✓ Accesible — ${d.entries} entradas en la carpeta`;
    } else {
      _txtCls(statusEl, 'txt-err');
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { _txtCls(statusEl, 'txt-err'); statusEl.textContent = '✗ ' + e.message; }
  }
}

async function detectDrives() {
  const listEl = document.getElementById('cable-drives-list');
  if (!listEl) return;
  listEl.classList.remove('hidden');
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
        <button class="btn" style="padding:1px 8px;font-size:11px;margin-left:auto" onclick="document.getElementById('cable-ab-path').value='${dr.letter.replace(/\\/g, '\\\\')}';testCablePath('ab');document.getElementById('cable-drives-list').classList.add('hidden')">Usar</button>
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
  if (status) { _txtCls(status, 'txt-dim'); status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      if (status) { _txtCls(status, 'txt-err'); status.textContent = '✗ ' + d.error; }
      return;
    }
    if (!d.devices?.length) {
      if (status) { _txtCls(status, 'txt-warn'); status.textContent = 'No se encontraron dispositivos. ¿Cable conectado? ¿Depuración USB activada?'; }
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
      _txtCls(status, ready.length ? 'txt-ok' : 'txt-warn');
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
    if (status) { _txtCls(status, 'txt-err'); status.textContent = '✗ ' + e.message; }
  }
}

async function testAdbPath() {
  const serial  = document.getElementById('cable-adb-device')?.value.trim();
  const ap      = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
  const statusEl = document.getElementById('cable-adb-path-status');
  if (!serial) { if (statusEl) { _txtCls(statusEl, 'txt-muted'); statusEl.textContent = 'Selecciona un dispositivo primero.'; } return; }
  if (statusEl) { _txtCls(statusEl, 'txt-dim'); statusEl.textContent = 'Verificando ruta en el dispositivo…'; }
  try {
    const d = await apiFetch(`/api/test-adb-path?serial=${encodeURIComponent(serial)}&path=${encodeURIComponent(ap)}`);
    if (d.accessible) {
      _txtCls(statusEl, 'txt-ok');
      statusEl.textContent = `✓ Ruta accesible — ${d.entries} entradas`;
    } else {
      _txtCls(statusEl, 'txt-err');
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { _txtCls(statusEl, 'txt-err'); statusEl.textContent = '✗ ' + e.message; }
  }
}

async function loadCableSync() {
  // QoL-14: offline badge for ADB
  apiFetch('/api/system-status').then(st => {
    const banner = document.getElementById('cable-offline-banner');
    if (banner) banner.classList.toggle('hidden', st.adb?.ok);
  }).catch(() => {});
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

  const wantSaves     = document.getElementById('cable-what-saves').checked;
  const wantRoms      = document.getElementById('cable-what-roms').checked;
  const wantAssets    = document.getElementById('cable-what-assets')?.checked ?? false;
  const wantGamelists = document.getElementById('cable-what-gamelists')?.checked ?? false;
  if (!wantSaves && !wantRoms && !wantAssets && !wantGamelists) { alert('Selecciona al menos qué sincronizar.'); return; }

  const what = [];
  if (wantSaves)     what.push('saves');
  if (wantRoms)      what.push('roms');
  if (wantAssets)    what.push('assets');
  if (wantGamelists) what.push('gamelists');

  const direction    = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const dryRun       = document.getElementById('cable-dry-run').checked;
  const skipExisting = document.getElementById('cable-skip-existing')?.checked ?? true;
  const safeMode     = document.getElementById('cable-safe-mode')?.checked ?? true;
  const skipSha1Dups = direction === 'anbernic_to_pc' && (document.getElementById('cable-skip-sha1')?.checked ?? false);
  const deleteExtra  = direction !== 'newest' && (document.getElementById('cable-mirror')?.checked ?? false);

  let body;
  if (adb) {
    const serial      = document.getElementById('cable-adb-device')?.value.trim();
    const androidPath = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    body = { pc_path: pcPath, use_adb: true, adb_serial: serial, android_path: androidPath,
             what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode, delete_extra: deleteExtra };
  } else {
    const abPath = document.getElementById('cable-ab-path')?.value.trim();
    if (!abPath) { alert('Introduce la ruta de la tarjeta SD / consola Android.'); return; }
    // Persist paths for next session
    localStorage.setItem('anbernic_path', abPath);
    if (pcPath) localStorage.setItem('cable_pc_path', pcPath);
    body = { pc_path: pcPath, anbernic_path: abPath, what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode, delete_extra: deleteExtra };
  }

  const btn      = document.getElementById('btn-cable-sync');
  const resultEl = document.getElementById('cable-result');
  btn.disabled = true;
  btn.textContent = 'Sincronizando…';
  resultEl.className = 'job-result';
  document.getElementById('cable-details-wrap').classList.add('hidden');
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
  const mirrorMsg   = r.deleted_extra > 0
    ? `  |  <span title="Espejo: archivos extra eliminados del destino" style="color:#f48771">&#x1F5D1; Espejo: ${r.deleted_extra} eliminado${r.deleted_extra !== 1 ? 's' : ''}</span>` : '';

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
  resultEl.innerHTML = `${verb}: <strong>${r.copied}</strong> archivo(s) (${fmtSize(r.copied_bytes)})  |  Omitidos: ${r.skipped}  |  Errores: <strong style="${r.errors > 0 ? 'color:#f44747' : ''}">${r.errors}</strong>${existsMsg}${sha1Msg}${safeMsg}${mirrorMsg}${countMsg}${diffWarn}  —  ${dirStr}${dryTag}`
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
    detailsWrap.classList.remove('hidden');
  }
}

// ── Cable Sync log viewer ─────────────────────────────────────────────────────
function toggleCableSyncLog() {
  const wrap = document.getElementById('cable-log-wrap');
  if (!wrap) return;
  const visible = !wrap.classList.contains('hidden');
  wrap.classList.toggle('hidden', visible);
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

async function exportPegasus() {
  const el = document.getElementById('pegasus-result');
  if (el) { el.textContent = 'Exportando...'; el.classList.remove('hidden'); el.className = 'job-result visible'; }
  try {
    const d = await apiPost('/api/export-pegasus', {});
    if (d.error) { if (el) { el.textContent = '\u2717 ' + d.error; el.className = 'job-result visible error-r'; } return; }
    if (el) { el.textContent = `\u2713 ${d.games} juegos en ${d.platforms} plataformas exportados`; el.className = 'job-result visible success'; }
    showToast('Pegasus exportado: ' + d.games + ' juegos', 'ok');
  } catch(e) { if (el) { el.textContent = '\u2717 ' + e.message; el.className = 'job-result visible error-r'; } }
}

// ── Auto-sync UI ─────────────────────────────────────────────────────────────
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
      _txtCls(statusEl, 'txt-warn');
    } else if (state === 'syncing') {
      const dev = s.last_device || '';
      statusEl.textContent = 'Sincronizando' + (dev ? ' con ' + dev : '') + '...';
      _txtCls(statusEl, 'txt-ok');
    } else if (state === 'idle' && s.last_sync_at) {
      statusEl.textContent = 'Ultimo sync: ' + s.last_sync_at + (s.last_error ? ' | Error: ' + s.last_error : '');
      _txtCls(statusEl, s.last_error ? 'txt-warn' : 'txt-ok');
    } else {
      statusEl.textContent = 'Esperando conexion...';
      _txtCls(statusEl, 'txt-muted');
    }
  }

  // Banner
  if (!enabled) {
    banner.classList.remove('hidden');
    banner.style.background = '#2a2a12';
    banner.style.borderBottomColor = '#4a4a1a';
    icon.textContent = 'Sync automatico desactivado';
    _txtCls(icon, 'txt-warn');
    text.textContent = 'Activa el sync automatico en la pestana Cable Sync.';
    _txtCls(text, 'txt-muted');
  } else if (state === 'syncing' || sdState === 'syncing') {
    const dev = state === 'syncing' ? (s.last_device || 'consola') : 'tarjeta SD';
    banner.classList.remove('hidden');
    banner.style.background = '#0d1f16';
    banner.style.borderBottomColor = '#1a4a2a';
    icon.textContent = sdState === 'syncing' ? 'Sincronizando saves (tarjeta SD)...' : ('Sincronizando saves con ' + dev + '...');
    _txtCls(icon, 'txt-ok');
    text.textContent = '';
  } else if (state === 'idle' && s.last_sync_at) {
    banner.classList.remove('hidden');
    banner.style.background = '#0d1a12';
    banner.style.borderBottomColor = '#1a3a22';
    const lastErr = s.last_error ? ' (' + s.last_error + ')' : '';
    icon.textContent = 'Ultimo sync automatico: ' + s.last_sync_at + lastErr;
    _txtCls(icon, s.last_error ? 'txt-warn' : 'txt-ok');
    text.textContent = '';
  } else if (sdState === 'watching') {
    banner.classList.remove('hidden');
    banner.style.background = '#0d1520';
    banner.style.borderBottomColor = '#1a2a3a';
    icon.textContent = 'Tarjeta SD detectada — sincronizacion automatica activa';
    _txtCls(icon, 'txt-ok');
    text.textContent = '';
  } else {
    banner.classList.add('hidden');
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
    if (label) { label.textContent = 'Activado'; _txtCls(label, 'txt-ok'); }
  } else {
    wrap.style.background = '#444';
    if (knob) knob.style.left = '3px';
    if (label) { label.textContent = 'Desactivado'; _txtCls(label, 'txt-muted'); }
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
      _txtCls(statusEl, d.enabled ? 'txt-muted' : 'txt-warn');
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
      if (resultEl) { resultEl.classList.remove('hidden'); _txtCls(resultEl, 'txt-err'); resultEl.textContent = 'Error: ' + d.error; }
    } else {
      if (resultEl) { resultEl.classList.remove('hidden'); _txtCls(resultEl, 'txt-ok'); resultEl.textContent = 'Guardado'; setTimeout(() => { if (resultEl) resultEl.classList.add('hidden'); }, 2500); }
      showToast('Ajustes de auto-sync guardados', 'ok');
    }
  } catch(e) {
    if (resultEl) { resultEl.classList.remove('hidden'); _txtCls(resultEl, 'txt-err'); resultEl.textContent = 'Error: ' + e.message; }
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

export {
  // Cloud Sync
  loadSync,
  loadAssets,
  loadSystemStatus,
  detectCloudFolder,
  useCloudFolder,
  loadAutostart,
  toggleAutostart,
  shutdownServer,
  // Android / Anbernic setup
  loadAndroidSetupPanel,
  copyAndroidSetupUrl,
  copyAndroidCurlCmd,
  downloadAndroidSetupSh,
  _checkAndroidUserAgent,
  loadAnbernicTab,
  copyAnbernicUrl,
  copyAnbernicCmd,
  // Rclone
  toggleRcloneSetup,
  loadRcloneStatus,
  openRcloneConfig,
  testRcloneRemote,
  applyRcloneRemote,
  // Cable Sync
  _isAdbMode,
  _onCableModeChange,
  _onCableDryRunChange,
  _onCableDirectionChange,
  testCablePath,
  detectDrives,
  detectAdbDevices,
  testAdbPath,
  loadCableSync,
  loadCableSyncPreview,
  doCableSync,
  _renderCableSyncResult,
  toggleCableSyncLog,
  loadCableSyncLog,
  exportPegasus,
  // Auto-sync
  _updateAutoSyncBanner,
  _updateAutoSyncToggleUI,
  toggleAutoSync,
  saveAutoSyncSettings,
  startAutoSyncPolling,
};
