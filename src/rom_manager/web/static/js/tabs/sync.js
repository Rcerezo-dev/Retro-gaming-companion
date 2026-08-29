// js/tabs/sync.js — Cloud Sync, Cable Sync, Auto-sync, Rclone, Android setup
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { _showConfirm } from '../components/modal.js';
import { getActiveDevice, getDevName } from '../state.js';
import { badge } from './games.js';

const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// ── Module-level state ────────────────────────────────────────────────────────
let _anbernicBaseUrl = '';

// Copiar al portapapeles con fallback: en la consola la UI se sirve por HTTP
// plano y navigator.clipboard no existe (solo https/localhost).
function _copyText(text) {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } finally { document.body.removeChild(ta); }
  return Promise.resolve();
}
let _autoSyncTimer = null;
let _autoSyncEnabled = true;

// CLOUD-UX-10: los mensajes de esta pestaña apuntan a su propio bloque de
// setup, no a config.toml ni a Settings.
function openCloudSetup() {
  const setup = document.getElementById('cloud-setup-block');
  if (!setup) return;
  setup.open = true;
  setup.scrollIntoView({ behavior: 'smooth' });
}

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
    // CLOUD-UX-3: los remotes implícitos saves_remote/states_remote también
    // son fuentes válidas — el aviso solo aplica si no hay ninguna de las dos.
    const implicit = [];
    if (cfg.saves_remote)  implicit.push(`saves &rarr; <code>${cfg.saves_remote}</code>`);
    if (cfg.states_remote) implicit.push(`states &rarr; <code>${cfg.states_remote}</code>`);
    const syncBar = document.getElementById('sync-context-bar');
    if (syncBar) {
      if (sources.length || implicit.length) {
        const names = sources.map(s => `<span style="color:var(--c-teal)">${s.name}</span>`)
          .concat(implicit.map(t => `<span style="color:var(--c-teal)">${t}</span>`))
          .join(' &nbsp;·&nbsp; ');
        syncBar.innerHTML = `Fuentes configuradas: ${names}`;
      } else {
        syncBar.innerHTML = `<span style="color:var(--c-softred)">Sin destino de sync — <a href="#" onclick="openCloudSetup();return false" style="color:var(--c-teal)">Conectar y elegir carpeta</a></span>`;
      }
      syncBar.classList.remove('hidden');
    }
    if (!sources.length && !implicit.length) {
      html += `<p class="error-msg" style="margin-bottom:16px">No hay destino de sync configurado. <a href="#" onclick="openCloudSetup();return false" style="color:var(--c-teal)">Abre la configuración cloud</a> (Conectar &rarr; Elegir carpeta &rarr; Probar). Para varias fuentes personalizadas existe el modo avanzado <code>[[sync.sources]]</code> en config.toml.</p>`;
    }
    if (sl.entries.length === 0) {
      html += '<p class="empty">Aún no hay registros de sincronización. Pulsa <strong>Sincronizar</strong> para empezar.</p>';
      el.innerHTML = html;
      return;
    }
    html += `<p style="color:var(--c-hint);margin-bottom:12px">${sl.entries.length} evento${sl.entries.length !== 1 ? 's' : ''}</p>`;
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Fecha</th><th>Dirección</th><th>Resultado</th><th>Ruta local</th><th>Ruta remota</th><th>Mensaje</th>';
    html += '</tr></thead><tbody>';
    html += sl.entries.map(e => {
      const dirBadge = badge(e.direction, e.direction);
      const resBadge = badge(e.result, e.result)
        + (e.verified ? ' <span title="Integridad verificada tras la transferencia" style="color:var(--c-teal)">✓</span>' : '');
      const msg  = e.message ? `<span style="color:var(--c-muted)">${e.message}</span>` : '';
      const date = e.created_at ? e.created_at.replace('T', ' ') : '';
      return `<tr><td>${date}</td><td>${dirBadge}</td><td>${resBadge}</td><td title="${e.local_path}">${e.local_path.split(/[\\/]/).pop()}</td><td title="${e.remote_path}">${e.remote_path}</td><td>${msg}</td></tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message} — Comprueba la <a href="#" onclick="openCloudSetup();return false" style="color:var(--c-teal)">configuración cloud de esta pestaña</a> (rclone instalado y remote conectado).</p>`;
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
      const _ad = getActiveDevice(), _dn = getDevName();
      let barHtml = '';
      if (_ad === 'pc') {
        barHtml = `Viendo: <span style="color:var(--c-teal)">PC — ${cfg.library_root || '(no configurado)'}</span> &nbsp;·&nbsp; <span style="color:var(--c-dim)">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      } else {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || cfg.anbernic_root || localStorage.getItem('anbernic_path') || '(no configurado)';
        barHtml = `Viendo: <span style="color:var(--c-orange)">${_dn} — ${ab}</span> &nbsp;·&nbsp; <span style="color:var(--c-dim)">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      }
      assetsBar.innerHTML = barHtml;
      assetsBar.classList.remove('hidden');
    }
    let stats = d.stats;
    if (stats.length === 0) {
      el.innerHTML = `<p class="empty">Sin datos de assets todavía. Ejecuta un <a href="#" onclick="showTab('plan');return false" style="color:var(--c-teal)">Scan</a> para indexar la biblioteca.</p>`;
      return;
    }
    if (filter === 'orphans') stats = stats.filter(s => s.orphan_assets > 0);
    if (filter === 'missing') stats = stats.filter(s => s.rom_count > 0 && s.image_count === 0 && s.video_count === 0);
    if (stats.length === 0) { el.innerHTML = '<p class="empty">✓ Sin resultados para este filtro.</p>'; return; }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>ROMs</th><th>Imágenes</th><th>Vídeos</th><th>XML</th><th>Huérfanos</th>';
    html += '</tr></thead><tbody>';
    html += stats.map(s => `<tr>
      <td>${s.platform}</td>
      <td style="text-align:right">${s.rom_count}</td>
      <td style="text-align:right;color:${s.image_count ? 'var(--c-teal)' : '#555'}">${s.image_count}</td>
      <td style="text-align:right;color:${s.video_count ? 'var(--c-teal)' : '#555'}">${s.video_count}</td>
      <td style="text-align:right;color:${s.xml_count ? 'var(--c-teal)' : '#555'}">${s.xml_count}</td>
      <td style="text-align:right;color:${s.orphan_assets ? 'var(--c-red)' : '#555'}">${s.orphan_assets
        ? `${s.orphan_assets} &nbsp;<a href="#" onclick="showOrphanAssets('${s.platform.replace(/'/g, "\\'")}');return false" style="color:var(--c-teal);font-size:11px">Ver</a>`
        : '—'}</td>
    </tr>`).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message} — Comprueba la ruta configurada en <a href="#" onclick="showTab('settings');return false" style="color:var(--c-teal)">Ajustes</a>.</p>`;
  }
}

// ASSETS-UX-4: lista de archivos huérfanos concretos de una plataforma
async function showOrphanAssets(platform) {
  const esc = window._h || (s => s);
  try {
    const root = _deviceRoot();
    let url = `/api/assets/orphans?platform=${encodeURIComponent(platform)}`;
    if (root) url += `&root=${encodeURIComponent(root)}`;
    const d = await apiFetch(url);
    const files = d.files || [];
    const body = files.length
      ? `<ul style="max-height:320px;overflow-y:auto;margin:0;padding-left:18px;font-size:12px;line-height:1.7">
          ${files.map(f => `<li title="${esc(f.source_path)}">${esc(f.asset_type)} &nbsp;·&nbsp; ${esc(f.source_path)}</li>`).join('')}
        </ul>`
      : '<p class="empty">No se encontraron archivos huérfanos para esta plataforma.</p>';
    _showConfirm(`Huérfanos — ${platform} (${files.length})`, body, 'Cerrar', () => {});
  } catch (e) {
    showToast(`No se pudo cargar la lista: ${e.message}`, 'err');
  }
}

// ── System status ─────────────────────────────────────────────────────────────
async function loadSystemStatus() {
  const el = document.getElementById('system-status-grid');
  if (!el) return;
  try {
    const d = await apiFetch('/api/system-status');
    const row = (label, ok, detail) => {
      const icon = ok ? '<span style="color:var(--c-teal)">✓</span>' : '<span style="color:var(--c-red)">✗</span>';
      const det = detail ? `<span style="color:var(--c-dim);margin-left:4px">${_h(detail)}</span>` : '';
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
        + '<span style="color:var(--c-dim)">Para sincronizar sin cliente local, configura rclone manualmente.</span>';
      return;
    }
    res.innerHTML = d.detected.map(item => `
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap">
        <span style="color:var(--c-teal);min-width:90px"><strong>${_h(item.service)}</strong></span>
        <span style="color:var(--c-muted);font-size:11px;flex:1">${_h(item.local_folder)}</span>
        <button class="btn primary" style="font-size:11px;padding:3px 10px;flex-shrink:0"
          onclick="useCloudFolder(${JSON.stringify(item.suggested_remote)})">Usar esta carpeta</button>
      </div>`).join('') +
      '<div style="color:var(--c-dim);margin-top:6px;font-size:11px">La app copiará los saves a esta carpeta. ' +
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
      badge.style.color = 'var(--c-green)';
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
  document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace;color:var(--c-dim);font-size:14px">Retro Vault cerrado. Puedes cerrar esta pestaña.</div>';
}

// ── Android detected panel (ANBERNIC-UX-5) ───────────────────────────────────
function _checkAndroidUserAgent() {
  if (/Android/i.test(navigator.userAgent)) {
    const panel = document.getElementById('android-detected-panel');
    if (panel) panel.classList.remove('hidden');
    tvCheckServer();
    tvCheckStatus();
  }
}

// Comprobación real del servidor (antes: dot verde hardcodeado)
async function tvCheckServer() {
  const dot  = document.getElementById('tv-status-dot');
  const text = document.getElementById('tv-status-text');
  try {
    await apiFetch('/api/version');
    if (dot)  dot.style.background = 'var(--c-teal)';
    if (text) text.textContent = 'PC conectado';
  } catch {
    if (dot)  dot.style.background = 'var(--c-red)';
    if (text) text.textContent = 'Sin conexión con el PC';
  }
}

// Primera vez: mostrar la guía de instalación con el comando de setup
async function tvToggleSetup() {
  const box = document.getElementById('tv-setup');
  if (!box) return;
  const showing = !box.classList.contains('hidden');
  box.classList.toggle('hidden', showing);
  if (showing) return;
  const cmdEl = document.getElementById('tv-setup-cmd');
  if (!cmdEl) return;
  try {
    const [d, tok] = await Promise.all([
      apiFetch('/api/local-url'),
      apiFetch('/api/anbernic-setup-token'),
    ]);
    const ip = d.ip || location.hostname;
    cmdEl.textContent = `curl -s "http://${ip}:${d.port || 7777}/s?t=${tok.token}" | bash`;
  } catch (e) {
    cmdEl.textContent = 'Error al generar el comando: ' + e.message;
  }
}

// Copiar el comando de setup desde el navegador de la consola → pegar en Termux
function tvCopySetupCmd() {
  const cmd = document.getElementById('tv-setup-cmd')?.textContent?.trim();
  if (!cmd || !cmd.startsWith('curl')) return;
  _copyText(cmd)
    .then(() => showToast('Comando copiado — pégalo en Termux (mantén pulsado → Pegar)', 'ok'))
    .catch(() => {});
}

// ── ANBERNIC-TV: Touch-friendly guided sync flow ──────────────────────────────
let _tvSyncPollTimer = null;
let _tvSyncResultTs  = null;

function tvSkipToFull() {
  const panel = document.getElementById('android-detected-panel');
  if (panel) panel.style.display = 'none';
}

function _tvShowStep(n) {
  [1, 2, 3].forEach(i => {
    const el = document.getElementById('tv-step-' + i);
    if (el) el.classList.toggle('hidden', i !== n);
  });
}

async function tvCheckStatus() {
  const subEl = document.getElementById('tv-last-sync');
  if (!subEl) return;
  try {
    const d = await apiFetch('/api/auto-sync-status');
    const st = d.status || {};
    if (st.last_sync_at) {
      const ts = new Date(st.last_sync_at);
      subEl.textContent = `Último sync: ${ts.toLocaleDateString('es-ES')} ${ts.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      subEl.textContent = 'Sin synchronización previa registrada';
    }
  } catch {
    subEl.textContent = 'Estado desconocido';
  }
}

async function tvStartSync() {
  clearTimeout(_tvSyncPollTimer);
  _tvSyncResultTs = null;
  _tvShowStep(2);
  const msgEl = document.getElementById('tv-sync-msg');
  if (msgEl) msgEl.textContent = 'Iniciando sync…';
  try {
    // CLOUD-UX-6: /api/do-sync nunca existió — el endpoint real es /api/sync
    await apiPost('/api/sync', { dry_run: false });
  } catch (e) {
    tvShowResult({ error: e.message });
    return;
  }
  _tvPollSync();
}

function _tvPollSync() {
  _tvSyncPollTimer = setTimeout(async () => {
    try {
      const d = await apiFetch('/api/job-status');
      const msgEl = document.getElementById('tv-sync-msg');
      if (d.sync_running) {
        if (msgEl) msgEl.textContent = 'Sincronizando saves…';
        _tvPollSync();
        return;
      }
      const res = d.sync_result;
      if (res && res.result_ts !== _tvSyncResultTs) {
        _tvSyncResultTs = res.result_ts;
        tvShowResult(res);
      } else {
        _tvPollSync();
      }
    } catch (e) {
      tvShowResult({ error: 'Error de conexión: ' + e.message });
    }
  }, 2000);
}

function tvShowResult(result) {
  clearTimeout(_tvSyncPollTimer);
  _tvShowStep(3);
  const iconEl = document.getElementById('tv-result-icon');
  const bodyEl = document.getElementById('tv-result-body');
  if (!bodyEl) return;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  if (result.error) {
    if (iconEl) iconEl.textContent = '❌ Error';
    bodyEl.innerHTML = `<div class="tv-result-err">${esc(result.error)}</div>`;
    return;
  }

  if (iconEl) iconEl.textContent = '✅ Sync completado';
  const sources = result.sources || [];
  const up   = sources.reduce((s, r) => s + (r.uploaded   || 0), 0);
  const down = sources.reduce((s, r) => s + (r.downloaded || 0), 0);
  const errs = sources.reduce((s, r) => s + (r.errors     || 0), 0);
  let html = `<div class="tv-result-row">&#x2191; ${up} enviado${up !== 1 ? 's' : ''}</div>`;
  html    += `<div class="tv-result-row">&#x2193; ${down} recibido${down !== 1 ? 's' : ''}</div>`;
  if (errs) html += `<div class="tv-result-row tv-result-err">&#x26A0; ${errs} error${errs !== 1 ? 'es' : ''}</div>`;
  bodyEl.innerHTML = html;
}

function tvReset() {
  _tvShowStep(1);
  tvCheckStatus();
}

// ── Anbernic tab ─────────────────────────────────────────────────────────────
async function loadAnbernicTab() {
  const ipDisplay = document.getElementById('anb-ip-display');
  const cmdFull   = document.getElementById('anb-cmd-full');
  try {
    const [d, tok] = await Promise.all([
      apiFetch('/api/local-url'),
      apiFetch('/api/anbernic-setup-token'),
    ]);
    const ip = d.ip || location.hostname;
    const port = d.port || 7777;
    _anbernicBaseUrl = `http://${ip}:${port}`;
    const curlCmd = `curl -s "${_anbernicBaseUrl}/s?t=${tok.token}" | bash`;

    // Step 1 — big IP display (enlace clicable: la consola no tiene cámara) + QR para el móvil
    if (ipDisplay) { ipDisplay.textContent = _anbernicBaseUrl; ipDisplay.href = _anbernicBaseUrl; }
    renderQR(_anbernicBaseUrl, 'anb-qr');

    // Step 5 — command box + download .sh link (mismo generador /s)
    if (cmdFull) cmdFull.textContent = curlCmd;
    const dlLink = document.getElementById('anb-script-download');
    if (dlLink) dlLink.href = `${_anbernicBaseUrl}/s?t=${tok.token}`;

    _renderAnbPrereqs(d);
  } catch(e) {
    // ANBERNIC-UX-8: error visible en vez de "Detectando…" eterno
    if (ipDisplay) ipDisplay.textContent = '✗ Sin conexión — pulsa ↻ Actualizar IP';
    if (cmdFull) cmdFull.textContent = '—';
    console.warn('loadAnbernicTab:', e);
  }
}

// ── Prerequisitos (ANBERNIC-UX-7) ────────────────────────────────────────────
function _renderAnbPrereqs(localUrl) {
  const el = document.getElementById('anb-prereq');
  if (!el) return;
  const line = (ok, okTxt, badHtml) =>
    `<div style="padding:2px 0">${ok
      ? `<span style="color:var(--c-teal)">✓</span> <span style="color:var(--c-muted)">${okTxt}</span>`
      : `<span style="color:var(--c-orange)">⚠</span> ${badHtml}`}</div>`;

  const serverOk = !!localUrl.lan_bound && localUrl.firewall_ok !== false;
  const serverBad = !localUrl.lan_bound
    ? 'El servidor solo escucha en localhost (<code>web_host</code>) — la consola no podrá conectarse.'
    : 'El firewall de Windows puede estar bloqueando el puerto — permite "Retro Vault (LAN)" o crea la regla.';
  let html = line(serverOk, 'Servidor accesible por red', serverBad);

  el.innerHTML = html;
  el.classList.remove('hidden');

  apiFetch('/api/rclone-status').then(rc => {
    const cloudOk = rc.installed && rc.remotes?.length > 0;
    const cloudBad = !rc.installed
      ? 'rclone no encontrado en el PC — el setup descargará una config vacía.'
      : 'rclone sin remotes configurados — conéctate a la nube en <a href="#" onclick="showTab(\'sync\');return false" style="color:var(--c-teal)">Cloud Sync</a> antes de configurar la consola.';
    el.innerHTML = line(cloudOk, `Cloud configurado (${cloudOk ? rc.remotes.join(', ') : ''})`, cloudBad) + html;
  }).catch(() => {});
}

function copyAnbernicCmd() {
  const cmd = document.getElementById('anb-cmd-full')?.textContent?.trim();
  if (!cmd || !cmd.startsWith('curl')) return;
  _copyText(cmd)
    .then(() => showToast('Comando copiado', 'ok'))
    .catch(() => {});
}

function copyAnbernicUrl() {
  if (!_anbernicBaseUrl) return;
  _copyText(_anbernicBaseUrl)
    .then(() => showToast('URL copiada', 'ok'))
    .catch(() => {});
}

// ── Rclone setup wizard ───────────────────────────────────────────────────────
function _rcloneActiveTargetHtml() {
  const saves  = document.getElementById('cfg-saves-remote')?.value.trim()  || '';
  const states = document.getElementById('cfg-states-remote')?.value.trim() || '';
  const legacy = document.getElementById('cfg-rclone-remote')?.value.trim() || '';
  if (saves || states) {
    return 'Sync actual &rarr; saves: <code>' + (saves || '&mdash;') + '</code>'
      + ' &middot; states: <code>' + (states || '&mdash;') + '</code>';
  }
  if (legacy) {
    return 'Sync actual &rarr; remote &uacute;nico (legado): <code>' + legacy + '</code>';
  }
  return '<span style="color:var(--c-yellow)">Sin remote de sync configurado &mdash; elige uno abajo.</span>';
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
        + 'Desc\u00e1rgalo de <strong style="color:var(--c-text)">rclone.org/downloads</strong> y ponlo en PATH, '
        + 'o indica la ruta en <code>config.toml</code> bajo <code>[sync]</code> como <code>rclone = "C:/tools/rclone.exe"</code>.';
      return;
    }
    let statusHtml = '\u2705 ' + d.version;
    if (d.remotes.length === 0) {
      statusHtml += '<br>\u26A0 Sin remotes configurados. Ejecuta <code>rclone config</code> en un terminal para a\u00f1adir uno (Dropbox, Google Drive, OneDrive\u2026).';
    } else {
      statusHtml += ` &middot; ${d.remotes.length} remote(s): <strong style="color:var(--c-text)">${d.remotes.join('  ')}</strong>`;
    }
    statusHtml += '<br>' + _rcloneActiveTargetHtml();
    if (info) info.innerHTML = statusHtml;
    if (d.remotes.length) {
      const sel = document.getElementById('rclone-remote-select');
      if (sel) {
        // CLOUD-UX-2: el value conserva el ':' — applyRclone* concatenan
        // remote + ruta y sin él guardaban "dropboxRetroSync/saves" (inválido).
        sel.innerHTML = d.remotes.map(r => `<option value="${r}:">${r}</option>`).join('');
        // Pre-select current remote
        const currentFull = document.getElementById('cfg-rclone-remote')?.value || '';
        if (currentFull && currentFull.includes(':')) {
          const currentRemote = currentFull.split(':')[0] + ':';
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
  if (!remote) { if (res) { res.textContent = 'Selecciona un remote.'; res.style.color = 'var(--c-yellow)'; } return; }
  if (res) { res.textContent = 'Verificando\u2026'; res.style.color = '#888'; }
  try {
    const d = await apiPost('/api/rclone-test-remote', { remote });
    if (d.ok) {
      const entries = d.entries > 0 ? ` · ${d.entries} carpeta(s) en ra\xedz` : ' · ra\xedz vac\xeda o sin permiso de lectura';
      if (res) { res.innerHTML = '\u2705 Conexi\xf3n OK' + entries; res.style.color = 'var(--c-teal)'; }
    } else {
      if (res) { res.innerHTML = '\u274C ' + (d.error || 'error'); res.style.color = 'var(--c-red)'; }
    }
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; res.style.color = 'var(--c-red)'; }
  }
}

async function applyRcloneRemote() {
  const remote = document.getElementById('rclone-remote-select')?.value || '';
  const pathVal = (document.getElementById('rclone-path-input')?.value || '').trim().replace(/^\/+/, '');
  const res = document.getElementById('rclone-apply-result');
  if (!remote) { if (res) { res.textContent = 'Selecciona un remote.'; res.style.color = 'var(--c-yellow)'; } return; }
  const fullRemote = remote + pathVal;
  try {
    await apiPost('/api/config', { 'sync.remote': fullRemote });
    if (res) { res.innerHTML = '\u2705 Guardado: <code>' + fullRemote + '</code>'; _txtCls(res, 'txt-ok'); }
    const cfgInp = document.getElementById('cfg-rclone-remote');
    if (cfgInp) cfgInp.value = fullRemote;
    const info = document.getElementById('rclone-status-info');
    if (info) info.innerHTML = info.innerHTML.replace(/Sync actual.*$|Sin remote de sync.*$/s, _rcloneActiveTargetHtml());
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; _txtCls(res, 'txt-err'); }
  }
}

async function applyRcloneSavesStates() {
  const remote = document.getElementById('rclone-remote-select')?.value || '';
  const baseVal = (document.getElementById('rclone-path-input')?.value || '').trim().replace(/^\/+/, '').replace(/\/+$/, '');
  const res = document.getElementById('rclone-apply-result');
  if (!remote) { if (res) { res.textContent = 'Selecciona un remote.'; res.style.color = 'var(--c-yellow)'; } return; }
  const base = baseVal || 'RetroSync';
  const savesRemote = `${remote}${base}/saves`;
  const statesRemote = `${remote}${base}/states`;
  try {
    await apiPost('/api/config', {
      'sync.saves_remote': savesRemote,
      'sync.states_remote': statesRemote,
    });
    if (res) {
      res.innerHTML = '\u2705 Guardado &#x2014; saves: <code>' + savesRemote + '</code> &middot; states: <code>' + statesRemote + '</code>';
      _txtCls(res, 'txt-ok');
    }
    const savesInp = document.getElementById('cfg-saves-remote');
    const statesInp = document.getElementById('cfg-states-remote');
    if (savesInp) savesInp.value = savesRemote;
    if (statesInp) statesInp.value = statesRemote;
    const info = document.getElementById('rclone-status-info');
    if (info) info.innerHTML = info.innerHTML.replace(/Sync actual.*$|Sin remote de sync.*$/s, _rcloneActiveTargetHtml());
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; _txtCls(res, 'txt-err'); }
  }
}

// ── Cable Sync ────────────────────────────────────────────────────────────────
function _isAdbMode() {
  return document.querySelector('input[name="cable-ab-mode"]:checked')?.value === 'adb';
}

// ANBERNIC-PICK-6: acceso directo desde Herramientas a la sincronización
// avanzada (ya existía, pero plegada y sin enlace desde donde el usuario la buscaba)
function goToCableSyncAdvanced() {
  showTab('cable');
  const details = document.getElementById('cable-advanced-details');
  if (details) {
    details.open = true;
    details.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function _onCableModeChange() {
  const adb = _isAdbMode();
  const fsEl  = document.getElementById('cable-fs-section');
  const adbEl = document.getElementById('cable-adb-section');
  if (fsEl)  fsEl.classList.toggle('hidden', adb);
  if (adbEl) adbEl.classList.toggle('hidden', !(adb));
}

// ANBERNIC-PICK-2: el checkbox "solo marcados" solo tiene sentido si se van a
// sincronizar ROMs — se oculta si esa casilla no está marcada.
function _onCableWhatRomsChange() {
  const wrap = document.getElementById('cable-only-tagged-wrap');
  if (wrap) wrap.style.display = document.getElementById('cable-what-roms')?.checked ? '' : 'none';
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
        <code style="color:var(--c-orange);min-width:36px">${dr.letter}</code>
        <span style="color:var(--c-muted)">${label}${size}</span>
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

// B0-3d: confirma por ADB que <ruta Android>/config existe — el candidato que
// list_overrides()/read_override() (CFG-PORGAME-6/7/8) asumen para leer y
// escribir overrides del lado Android. No requiere ningún campo nuevo: la
// ruta candidata sale de auto-sync-android-path, ya guardado en config.toml.
async function detectAndroidRaConfigDir() {
  const resultEl = document.getElementById('android-ra-config-detect-result');
  if (resultEl) { _txtCls(resultEl, 'txt-dim'); resultEl.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/detect-android-ra-config-dir');
    if (d.found) {
      if (resultEl) { _txtCls(resultEl, 'txt-ok'); resultEl.textContent = '✓ Encontrado: ' + d.ra_config_dir; }
    } else if (resultEl) {
      _txtCls(resultEl, 'txt-err');
      resultEl.textContent = '✗ ' + (d.error || 'No encontrado');
    }
  } catch (e) {
    if (resultEl) { _txtCls(resultEl, 'txt-err'); resultEl.textContent = '✗ Error: ' + e.message; }
  }
}

async function testAdbPath() {
  const serial  = document.getElementById('cable-adb-device')?.value.trim();
  // CABLE-UX-5: ruta Android única, compartida con la tarjeta de auto-sync
  const ap      = document.getElementById('auto-sync-android-path')?.value.trim() || '/storage/emulated/0';
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

// ── AUD-1: Sync Doctor ────────────────────────────────────────────────────────
function _skewLabel(seconds) {
  const abs = Math.abs(seconds);
  return abs >= 120 ? `${(abs / 60).toFixed(1)} min` : `${abs.toFixed(0)} s`;
}

function _sdList(title, items, total, color) {
  if (!total) return '';
  const extra = total > items.length ? `<div style="color:var(--c-dim)">… y ${total - items.length} más</div>` : '';
  return `<details style="margin-top:6px"><summary style="cursor:pointer;color:${color}">${title}: ${total}</summary>
    <div style="max-height:180px;overflow-y:auto;margin:4px 0 0 14px;color:var(--c-muted)">
    ${items.map(f => `<div>${_h(f)}</div>`).join('')}${extra}</div></details>`;
}

function _renderSyncDoctor(d) {
  const dir = d.skew_seconds > 0 ? 'adelantado' : 'atrasado';
  let html = '';
  if (d.skew_exceeded) {
    html += `<div class="rv-tint-warn" style="padding:8px 12px;border-left:3px solid var(--c-red);border-radius:4px;margin-bottom:10px;color:var(--c-softred)">
      &#x26A0; <strong>Reloj de la consola ${dir} ${_skewLabel(d.skew_seconds)}</strong> respecto al PC (umbral: ${d.threshold_seconds} s).<br>
      La resolución de conflictos por fecha (mtime) no es fiable: el lado equivocado puede ganar y sobreescribir progreso.
      Ajusta la hora de la consola antes de usar "Igualar ambos dispositivos".</div>`;
  } else {
    html += `<div style="color:var(--c-teal);margin-bottom:10px">✓ Reloj OK — desviación de ${_skewLabel(d.skew_seconds)} (umbral: ${d.threshold_seconds} s)</div>`;
  }
  html += `<div style="color:var(--c-muted)">Saves — PC: <strong style="color:var(--c-text)">${d.local_total}</strong>
    · Consola: <strong style="color:var(--c-text)">${d.remote_total}</strong>
    · En ambos: <strong style="color:var(--c-text)">${d.in_both}</strong></div>`;
  html += _sdList('&#x23F0; Saves con fecha futura en PC (reloj mal puesto)', d.future_local, d.future_local.length, 'var(--c-red)');
  html += _sdList('&#x23F0; Saves con fecha futura en consola (reloj mal puesto)', d.future_remote, d.future_remote.length, 'var(--c-red)');
  html += _sdList('Solo en PC', d.only_local, d.only_local_total, 'var(--c-amber)');
  html += _sdList('Solo en consola', d.only_remote, d.only_remote_total, 'var(--c-amber)');
  if (d.last_syncs?.length) {
    html += `<details style="margin-top:6px"><summary style="cursor:pointer;color:var(--c-blue)">Último sync por archivo: ${d.last_syncs.length}</summary>
      <div style="max-height:220px;overflow-y:auto;margin-top:4px"><table><thead><tr><th>Archivo</th><th>Dirección</th><th>Resultado</th><th>Fecha</th></tr></thead><tbody>
      ${d.last_syncs.map(s => `<tr><td>${_h(s.file)}</td><td>${_h(s.direction || '')}</td><td>${_h(s.result || '')}</td><td>${_h((s.created_at || '').replace('T', ' '))}</td></tr>`).join('')}
      </tbody></table></div></details>`;
  } else {
    html += `<div style="color:var(--c-dim);margin-top:6px">Sin eventos en save_sync_log todavía.</div>`;
  }
  return html;
}

async function runSyncDoctor() {
  const el = document.getElementById('sync-doctor-result');
  if (!el) return;
  let serial = document.getElementById('cable-adb-device')?.value.trim();
  if (!serial) {
    // CABLE-UX-8: no exigir el ritual manual "Modo ADB → Detectar dispositivos"
    // — si hay un device ready, usarlo directamente.
    el.innerHTML = '<span style="color:var(--c-dim)">Buscando dispositivo ADB…</span>';
    try {
      const d = await apiFetch('/api/adb-devices');
      const ready = (d.devices || []).find(dv => dv.ready);
      if (ready) serial = ready.serial;
    } catch (_) { /* sin adb disponible — se informa abajo */ }
    if (!serial) {
      el.innerHTML = '<span style="color:var(--c-yellow)">No se encontró ningún dispositivo ADB listo. Conecta la consola y activa la depuración USB.</span>';
      return;
    }
  }
  // CABLE-UX-5: rutas únicas, compartidas con el formulario manual/auto-sync
  const androidPath = document.getElementById('auto-sync-android-path')?.value.trim() || '';
  const pcPath = document.getElementById('cable-pc-path')?.value.trim() || '';
  el.innerHTML = '<span style="color:var(--c-dim)">Diagnosticando… (puede tardar si hay muchos saves)</span>';
  try {
    const params = new URLSearchParams({ serial });
    if (androidPath) params.set('android_path', androidPath);
    if (pcPath) params.set('pc_path', pcPath);
    const d = await apiFetch('/api/sync-doctor?' + params);
    if (d.error) { el.innerHTML = `<span style="color:var(--c-red)">✗ ${_h(d.error)}</span>`; return; }
    el.innerHTML = _renderSyncDoctor(d);
  } catch (e) {
    el.innerHTML = `<span style="color:var(--c-red)">✗ ${_h(e.message)}</span>`;
  }
}

// CABLE-UX-3: preseleccionar el modo una sola vez por sesión de pestaña — no
// pelear con un cambio manual del usuario en visitas posteriores.
let _cableModeAutoSelected = false;

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
    // CABLE-UX-10: config (library_root/anbernic_root) como única fuente de
    // verdad — fuera el localStorage, que quedaba como estado fantasma tras
    // cambiar la ruta en Settings. El override de Overview (ov-*) es la misma
    // convención puntual que usan Assets/Colección/Organizar/Juegos.
    _setIfEmpty('cable-pc-path', ovPc || cfg.library_root || '');
    _setIfEmpty('cable-ab-path', ovAb || cfg.anbernic_root || '');

    // VAL-FIX-6: decidir el modo ADB/SD *antes* de validar rutas, para que el
    // aviso de la ruta SD no se calcule (ni se vea de refilón) cuando el modo
    // final va a ser ADB.
    if (!_cableModeAutoSelected) {
      _cableModeAutoSelected = true;
      const devs = await apiFetch('/api/adb-devices').catch(() => ({ devices: [] }));
      const hasReady = (devs.devices || []).some(d => d.ready);
      const adbRadio = document.querySelector('input[name="cable-ab-mode"][value="adb"]');
      const fsRadio  = document.querySelector('input[name="cable-ab-mode"][value="fs"]');
      if (hasReady && adbRadio) {
        adbRadio.checked = true;
        _onCableModeChange();
        detectAdbDevices();
      } else if (!hasReady && cfg.anbernic_root && fsRadio) {
        fsRadio.checked = true;
        _onCableModeChange();
      }
    }

    if (document.getElementById('cable-pc-path')?.value) testCablePath('pc');
    if (!_isAdbMode() && document.getElementById('cable-ab-path')?.value) testCablePath('ab');
    _onCableWhatRomsChange(); // ANBERNIC-PICK-2: por si el navegador recordó "ROMs" marcado

    // CABLE-UX-6: los avisos condicionales deben reflejar el estado inicial de
    // los controles, no solo actualizarse tras un onchange manual del usuario.
    _onCableDryRunChange();
    _onCableDirectionChange();
  } catch(_) {}
}

async function loadCableSyncPreview() {
  const adb = _isAdbMode();
  // CABLE-UX-5: ruta de PC única para ambos modos
  const pcPath = document.getElementById('cable-pc-path')?.value.trim();
  const abPath = adb ? null : document.getElementById('cable-ab-path')?.value.trim();
  const direction = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const mode = adb ? 'adb' : 'sd';
  const previewEl = document.getElementById('cable-preview-result');
  if (!previewEl) return;
  previewEl.className = 'cable-preview visible';
  previewEl.innerHTML = '<span style="color:var(--c-dim)">Calculando…</span>';
  try {
    const params = new URLSearchParams({ mode, direction });
    if (pcPath)  params.set('pc_path',  pcPath);
    if (abPath)  params.set('ab_path',  abPath);
    if (adb) {
      // VAL-FIX-5: reutiliza el mismo serial/ruta que Sync Doctor para contar
      // saves remotos por ADB en vez de mostrar siempre "no accesible".
      const serial = document.getElementById('cable-adb-device')?.value.trim();
      if (serial) params.set('serial', serial);
      const androidPath = document.getElementById('auto-sync-android-path')?.value.trim();
      if (androidPath) params.set('android_path', androidPath);
    }
    const d = await apiFetch('/api/cable-sync-preview?' + params);
    const pcN  = d.pc_saves !== null && d.pc_saves !== undefined ? `<span class="cp-num">${d.pc_saves}</span>` : `<span class="cp-null">?</span>`;
    const abN  = d.android_saves !== null && d.android_saves !== undefined ? `<span class="cp-num">${d.android_saves}</span>` : `<span class="cp-null">${d.android_message || 'no accesible'}</span>`;
    const cpN  = d.to_copy !== null && d.to_copy !== undefined ? `<span class="cp-num">${d.to_copy}</span>` : `<span class="cp-null">—</span>`;
    previewEl.innerHTML =
      `<span class="cp-stat">PC: ${pcN} saves</span>` +
      `<span style="color:var(--c-ghost);margin-right:12px">·</span>` +
      `<span class="cp-stat">Consola: ${abN} saves</span>` +
      `<span style="color:var(--c-ghost);margin-right:12px">·</span>` +
      `<span class="cp-stat">Se copiarán ≈ ${cpN} archivos</span>`;
  } catch(e) {
    previewEl.innerHTML = `<span style="color:var(--c-red)">Error: ${e.message}</span>`;
  }
}

// ── CABLE-UX-2: botón primario "Sincronizar saves ahora" ─────────────────────
// Reutiliza /api/cable-sync (mismo motor que el formulario avanzado) con los
// parámetros de la tarjeta de auto-sync — nada de un segundo camino de copia.
async function doQuickSync() {
  const btn = document.getElementById('btn-quick-sync');
  const statusEl = document.getElementById('quick-sync-status');
  if (btn) { btn.disabled = true; btn.textContent = 'Sincronizando…'; }
  if (statusEl) { statusEl.textContent = ''; _txtCls(statusEl, ''); }
  try {
    const [cfg, autoSt, devs] = await Promise.all([
      apiFetch('/api/config'),
      apiFetch('/api/auto-sync-status'),
      apiFetch('/api/adb-devices').catch(() => ({ devices: [] })),
    ]);
    const pcPath = cfg.library_root;
    if (!pcPath) throw new Error('Configura la carpeta de biblioteca (library_root) en Ajustes primero.');
    const direction = autoSt.config?.direction || 'newest';
    const androidPath = autoSt.config?.android_path || '/storage/emulated/0/RetroArch';

    let body;
    const ready = (devs.devices || []).filter(d => d.ready);
    if (ready.length) {
      body = { pc_path: pcPath, use_adb: true, adb_serial: ready[0].serial, android_path: androidPath,
               what: ['saves'], direction, dry_run: false, skip_existing: true, safe_mode: false };
    } else if (cfg.anbernic_root) {
      body = { pc_path: pcPath, anbernic_path: cfg.anbernic_root,
               what: ['saves'], direction, dry_run: false, skip_existing: true, safe_mode: false };
    } else {
      throw new Error('No se detecta la consola por ADB ni hay una ruta SD configurada (anbernic_root en Ajustes).');
    }

    _requestNotifPermission();
    const d = await apiPost('/api/cable-sync', body);
    if (d.status === 'already_running') {
      if (statusEl) statusEl.textContent = 'Ya hay una sincronización en curso…';
      return;
    }
    if (statusEl) statusEl.textContent = 'Sincronizando…';
    startPolling();
  } catch (e) {
    if (statusEl) { statusEl.textContent = '✗ ' + e.message; _txtCls(statusEl, 'txt-err'); }
    if (btn) { btn.disabled = false; btn.textContent = '▶ Sincronizar saves ahora'; }
  }
}

async function doCableSync() {
  const adb = _isAdbMode();
  // CABLE-UX-5: ruta de PC única para ambos modos
  const pcPath = document.getElementById('cable-pc-path')?.value.trim();
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
  // ANBERNIC-PICK-2: solo tiene efecto con roms + pc_to_anbernic (ver _wanted en sync_cable.py)
  const onlyTagged   = wantRoms && (document.getElementById('cable-only-tagged')?.checked ?? false);

  let body;
  if (adb) {
    const serial      = document.getElementById('cable-adb-device')?.value.trim();
    // CABLE-UX-5: ruta Android única, compartida con la tarjeta de auto-sync
    const androidPath = document.getElementById('auto-sync-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    // CABLE-UX-1: el pre-flight de reloj ahora vive en el backend (bloquea con
    // error en vez de confirm()) — cubre este camino y el auto-sync por igual.
    body = { pc_path: pcPath, use_adb: true, adb_serial: serial, android_path: androidPath,
             what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode, delete_extra: deleteExtra, only_tagged: onlyTagged };
  } else {
    const abPath = document.getElementById('cable-ab-path')?.value.trim();
    if (!abPath) { alert('Introduce la ruta de la tarjeta SD / consola Android.'); return; }
    // CABLE-UX-10: sin localStorage — config (anbernic_root/library_root en
    // Ajustes) es la única fuente persistente; esto es solo la sesión actual.
    body = { pc_path: pcPath, anbernic_path: abPath, what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups, safe_mode: safeMode, delete_extra: deleteExtra, only_tagged: onlyTagged };
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
  const _dn = getDevName();
  const dirMap = { pc_to_anbernic: `PC → ${_dn}`, anbernic_to_pc: `${_dn} → PC`, newest: 'Más reciente gana', pc_to_device: `PC → ${_dn}`, device_to_pc: `${_dn} → PC`, remove_selected: `Eliminados de ${_dn} (saves preservados)` };
  const dirStr = dirMap[r.direction] || r.direction;
  const dryTag = r.dry_run ? ' [DRY RUN — nada fue copiado]' : '';
  const sha1Msg     = r.sha1_skipped > 0 ? `  |  Dups SHA1: ${r.sha1_skipped}` : '';
  const existsCount = r.details ? r.details.filter(d => d.file === 'EXISTS').length : 0;
  const existsMsg   = existsCount > 0 ? `  |  Ya existen: ${existsCount}` : '';
  const safeMsg     = r.safe_mode_skipped_overwrites > 0
    ? `  |  <span title="Modo seguro: archivos existentes no sobreescritos" style="color:var(--c-amber)">&#x26A0; Modo seguro: ${r.safe_mode_skipped_overwrites} no sobreescritos</span>` : '';
  const mirrorMsg   = r.deleted_extra > 0
    ? (r.direction === 'remove_selected'
        ? `  |  <span title="Juegos eliminados de la consola (saves preservados en el PC)" style="color:var(--c-softred)">&#x1F5D1; ${r.deleted_extra} juego${r.deleted_extra !== 1 ? 's' : ''} eliminado${r.deleted_extra !== 1 ? 's' : ''}</span>`
        : `  |  <span title="Espejo: archivos extra eliminados del destino" style="color:var(--c-softred)">&#x1F5D1; Espejo: ${r.deleted_extra} eliminado${r.deleted_extra !== 1 ? 's' : ''}</span>`)
    : '';

  const needsScan = !r.dry_run && r.copied > 0 && (r.direction === 'anbernic_to_pc' || r.direction === 'newest');
  // D8-6: file count display
  const pcCount = r.pc_file_count > 0 ? r.pc_file_count : null;
  const abCount = r.ab_file_count > 0 ? r.ab_file_count : null;
  const countMsg = (pcCount && abCount && !r.dry_run && !r.use_adb)
    ? `  |  PC: ${pcCount} archivos  Consola: ${abCount} archivos`
    : '';
  const countDiff = pcCount && abCount && Math.abs(pcCount - abCount) > Math.max(pcCount, abCount) * 0.05;
  const diffWarn = countDiff ? ' <span style="color:var(--c-yellow);font-size:11px">&#x26A0; Los conteos difieren — puede haber archivos que no se sincronizaron</span>' : '';
  resultEl.className = 'job-result visible success';
  if (!r.dry_run) _sendNotif('Cable Sync completado', r.copied + ' archivos copiados');
  resultEl.innerHTML = `${verb}: <strong>${r.copied}</strong> archivo(s) (${fmtSize(r.copied_bytes)})  |  Omitidos: ${r.skipped}  |  Errores: <strong style="${r.errors > 0 ? 'color:var(--c-red)' : ''}">${r.errors}</strong>${existsMsg}${sha1Msg}${safeMsg}${mirrorMsg}${countMsg}${diffWarn}  —  ${dirStr}${dryTag}`
    + (needsScan ? `<br><span style="color:var(--c-yellow);font-size:11px">&#x26A0; Archivos copiados al PC — indexa la BD: <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:6px" onclick="quickScanPC()">Escanear ahora</button></span>` : '')
    + (!r.dry_run && r.copied > 0 && r.direction === 'newest'
        ? '<br><span style="color:var(--c-blue);font-size:11px">Para actualizar conteos en Overview: <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:6px" onclick="quickScanPC()">Escanear PC</button> <button class="btn" style="padding:2px 8px;font-size:11px;margin-left:4px" onclick="quickScanAndroid()">Escanear consola</button></span>'
        : '');

  if (r.details && r.details.length > 0) {
    // Separate error entries from normal entries
    const errEntries = r.details.filter(d => d.file && d.file.startsWith('ERROR'));
    const okEntries  = r.details.filter(d => !d.file || !d.file.startsWith('ERROR'));

    let detailHtml = '';
    if (errEntries.length > 0) {
      detailHtml += `<div style="background:var(--rv-tint-warn-bg);border:1px solid var(--c-red);border-radius:4px;padding:8px 12px;margin-bottom:8px">`
        + `<div style="color:var(--c-red);font-weight:bold;margin-bottom:6px;font-size:12px">&#x2717; ${errEntries.length} archivo(s) fallaron al copiarse:</div>`
        + errEntries.map(d => `<div style="padding:1px 0;color:var(--c-softred);font-size:11px">&#x25B8; ${_h(d.path)}</div>`).join('')
        + `</div>`;
    }
    detailHtml += okEntries.map(d => {
      const isDup    = d.file === 'DUP';
      const isExists = d.file === 'EXISTS';
      const isSafe   = d.file === 'SAFE';
      const tagColor = isDup ? 'var(--c-blue)' : isExists ? '#444' : isSafe ? '#f4c842' : 'var(--c-teal)';
      return `<div style="padding:2px 0;color:var(--c-muted)"><span style="color:${tagColor};margin-right:8px">${_h(d.file)}</span>${_h(d.path)}</div>`;
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
async function promptSyncNow() {
  const btn = document.getElementById('auto-sync-prompt-btn');
  if (btn) btn.classList.add('hidden');
  try {
    await apiFetch('/api/cable-sync', { method: 'POST', body: JSON.stringify({}) });
    showTab('cable');
  } catch(e) { /* silent — cable tab will show the error */ }
}

function _updateAutoSyncBanner(data, sdStatus) {
  const banner  = document.getElementById('auto-sync-banner');
  const icon    = document.getElementById('auto-sync-banner-icon');
  const text    = document.getElementById('auto-sync-banner-text');
  if (!banner || !icon || !text) return;

  // Reset prompt button on every update; shown only for device_prompt state
  const promptBtn = document.getElementById('auto-sync-prompt-btn');
  if (promptBtn) promptBtn.classList.add('hidden');

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
    banner.style.borderBottomColor = 'var(--rv-tint-amber-border)';
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
  } else if (state === 'device_prompt') {
    const dev = s.last_device || 'consola Android';
    banner.classList.remove('hidden');
    banner.style.background = '#1a150d';
    banner.style.borderBottomColor = '#3a2a1a';
    icon.textContent = '📱 ' + dev + ' conectado';
    _txtCls(icon, 'txt-warn');
    text.textContent = '¿Sincronizar saves ahora?';
    _txtCls(text, 'txt-muted');
    if (promptBtn) promptBtn.classList.remove('hidden');
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
      const _daysSince = (Date.now() - new Date(lastAt).getTime()) / 86400000;
      const _isStale = !s.last_error && _daysSince > 3;
      hdr.textContent = (_isStale ? '⚠ ' : '') + `Sync ${_relTime(lastAt)}`;
      hdr.className = s.last_error ? 'sync-err' : (_isStale ? 'sync-stale' : 'sync-ok');
      hdr.title = `Última sync: ${lastAt}`
        + (_isStale ? ` · Sin sync hace más de ${Math.round(_daysSince)}d` : '')
        + (s.last_error ? ` · Error: ${s.last_error}` : '');
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
    wrap.style.background = 'var(--c-teal)';
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
  const androidP  = document.getElementById('auto-sync-android-path')?.value.trim() || '/storage/emulated/0/RetroArch';
  const resultEl  = document.getElementById('auto-sync-save-result');
  try {
    const d = await apiPost('/api/auto-sync-save', {
      'sync.auto_sync_direction':   dir,
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
    // CABLE-UX-4: conflict_policy solo lo usa Cloud Sync — su control vive en
    // tab-sync.html, no en la tarjeta de auto-sync de Cable.
    const confEl = document.getElementById('cfg-conflict-policy');
    const pathEl = document.getElementById('auto-sync-android-path');
    if (confEl && !confEl.dataset.loaded && d.config) {
      confEl.value = d.config.conflict_policy || 'newest';
      confEl.dataset.loaded = '1';
    }
    if (dirEl && !dirEl.dataset.loaded && d.config) {
      dirEl.value = d.config.direction || 'newest';
      if (pathEl) pathEl.value = d.config.android_path || '/storage/emulated/0/RetroArch';
      dirEl.dataset.loaded = '1';
    }
    // CABLE-UX-7: abrir las instrucciones de conexión solo si nunca hubo un sync exitoso
    const howto = document.getElementById('cable-howto');
    if (howto && !howto.dataset.loaded) {
      howto.open = !(d.status?.last_sync_at);
      howto.dataset.loaded = '1';
    }
  } catch(_) { /* silent */ }
}

// CABLE-UX-4: guardado independiente — vive en Cloud Sync, no en la tarjeta de Cable
async function saveConflictPolicy() {
  const sel = document.getElementById('cfg-conflict-policy');
  const resultEl = document.getElementById('conflict-policy-result');
  if (!sel) return;
  try {
    await apiPost('/api/config', { 'sync.conflict_policy': sel.value });
    if (resultEl) { resultEl.textContent = '✓ Guardado'; setTimeout(() => { if (resultEl) resultEl.textContent = ''; }, 2500); }
    showToast('Política de conflictos guardada', 'ok');
  } catch (e) {
    if (resultEl) resultEl.textContent = '✗ ' + e.message;
  }
}

function startAutoSyncPolling() {
  if (_autoSyncTimer) return;
  _pollAutoSync();
  _autoSyncTimer = setInterval(_pollAutoSync, 5000);
}

// ── Tree diff ─────────────────────────────────────────────────────────────────

function _onTreeDiffSourceChange() {
  const isAdb = document.querySelector('input[name="tree-diff-source"]:checked')?.value === 'adb';
  const row = document.getElementById('tree-diff-adb-row');
  if (row) row.classList.toggle('hidden', !isAdb);
  if (isAdb) _loadTreeDiffDevices();
}

async function _loadTreeDiffDevices() {
  const sel = document.getElementById('tree-diff-serial');
  if (!sel) return;
  sel.innerHTML = '<option value="">Cargando…</option>';
  try {
    const d = await apiFetch('/api/adb-devices');
    const ready = (d.devices || []).filter(x => x.ready);
    if (!ready.length) {
      sel.innerHTML = '<option value="">Sin dispositivos conectados</option>';
      return;
    }
    sel.innerHTML = ready.map(x => `<option value="${x.serial}">${x.display}</option>`).join('');
  } catch(_) {
    sel.innerHTML = '<option value="">Error al cargar dispositivos</option>';
  }
}

async function doTreeDiff() {
  const pcPath      = document.getElementById('tree-diff-pc-path')?.value.trim() || '';
  const androidPath = document.getElementById('tree-diff-android-path')?.value.trim() || '';
  const source      = document.querySelector('input[name="tree-diff-source"]:checked')?.value || 'local';
  const serial      = document.getElementById('tree-diff-serial')?.value || '';
  const btn         = document.getElementById('btn-tree-diff');
  const resEl       = document.getElementById('tree-diff-result');

  if (btn) { btn.disabled = true; btn.textContent = 'Comparando…'; }
  if (resEl) resEl.innerHTML = '<p class="loading">Escaneando &#xe1;rboles de directorios…</p>';

  try {
    await apiPost('/api/rom-tree-diff', { pc_path: pcPath, android_path: androidPath, source, serial });
    import('../jobs.js').then(m => m.startPolling());
  } catch(e) {
    showToast('Error al iniciar comparaci\u00f3n: ' + e.message, 'err');
    if (btn) { btn.disabled = false; btn.textContent = 'Comparar \u00e1rboles'; }
    if (resEl) resEl.innerHTML = '';
  }
}

function _renderTreeDiff(r) {
  const btn   = document.getElementById('btn-tree-diff');
  const resEl = document.getElementById('tree-diff-result');
  if (btn) { btn.disabled = false; btn.textContent = 'Comparar \u00e1rboles'; }
  if (!resEl) return;

  if (r.error) {
    resEl.innerHTML = `<p class="error-msg">Error: ${r.error}</p>`;
    return;
  }

  const pcOnly      = r.only_pc_total     || 0;
  const androidOnly = r.only_android_total || 0;
  const both        = r.in_both           || 0;
  const totalPc     = r.total_pc          || 0;
  const totalAnd    = r.total_android     || 0;
  const MAX_SHOW    = 200;

  let html = `<div style="font-size:11px;color:var(--c-dim);margin-bottom:10px">
    PC: <strong>${totalPc.toLocaleString()}</strong> archivos &nbsp;·&nbsp;
    Consola: <strong>${totalAnd.toLocaleString()}</strong> archivos
  </div>
  <div style="display:flex;gap:10px;margin-bottom:14px">
    <div style="flex:1;padding:10px 14px;background:var(--rv-tint-ok-bg);border:1px solid var(--rv-tint-ok-border);border-radius:4px">
      <div style="font-size:20px;color:var(--c-teal);font-weight:bold">${both.toLocaleString()}</div>
      <div style="font-size:11px;color:#4a8a4a">en ambos</div>
    </div>
    <div style="flex:1;padding:10px 14px;background:var(--rv-tint-info-bg);border:1px solid var(--rv-tint-info-border);border-radius:4px">
      <div style="font-size:20px;color:var(--c-blue);font-weight:bold">${pcOnly.toLocaleString()}</div>
      <div style="font-size:11px;color:#556;margin-bottom:3px">solo en PC</div>
      <div style="font-size:11px;color:var(--c-muted)">(faltan en consola)</div>
    </div>
    <div style="flex:1;padding:10px 14px;background:var(--rv-tint-amber-bg);border:1px solid var(--rv-tint-amber-border);border-radius:4px">
      <div style="font-size:20px;color:var(--c-orange);font-weight:bold">${androidOnly.toLocaleString()}</div>
      <div style="font-size:11px;color:#6a4a38;margin-bottom:3px">solo en consola</div>
      <div style="font-size:11px;color:var(--c-muted)">(faltan en PC)</div>
    </div>
  </div>`;

  if (!pcOnly && !androidOnly) {
    html += `<p style="color:var(--c-teal)">&#x2713; Las rutas son id\u00e9nticas. No hay diferencias.</p>`;
  }

  if (r.only_pc?.length) {
    const extra = pcOnly > MAX_SHOW ? ` (mostrando ${Math.min(r.only_pc.length, MAX_SHOW)} de ${pcOnly.toLocaleString()})` : '';
    html += `<details style="margin-bottom:8px">
      <summary style="cursor:pointer;color:var(--c-blue);font-size:13px;user-select:none">Solo en PC${extra}</summary>
      <div style="max-height:280px;overflow-y:auto;font-size:11px;font-family:monospace;padding:8px;background:var(--rv-tint-info-bg);border-radius:4px;margin-top:6px">
        ${r.only_pc.slice(0, MAX_SHOW).map(p => `<div style="color:var(--c-muted);padding:1px 0">${p}</div>`).join('')}
      </div>
    </details>`;
  }

  if (r.only_android?.length) {
    const extra = androidOnly > MAX_SHOW ? ` (mostrando ${Math.min(r.only_android.length, MAX_SHOW)} de ${androidOnly.toLocaleString()})` : '';
    html += `<details style="margin-bottom:8px">
      <summary style="cursor:pointer;color:var(--c-orange);font-size:13px;user-select:none">Solo en consola${extra}</summary>
      <div style="max-height:280px;overflow-y:auto;font-size:11px;font-family:monospace;padding:8px;background:var(--rv-tint-amber-bg);border-radius:4px;margin-top:6px">
        ${r.only_android.slice(0, MAX_SHOW).map(p => `<div style="color:var(--c-muted);padding:1px 0">${p}</div>`).join('')}
      </div>
    </details>`;
  }

  resEl.innerHTML = html;
}

// ── Save Comparison & Library Diff ────────────────────────────────────────────
async function loadSaveComparison() {
  const el = document.getElementById('save-comparison-content');
  if (!el) return;
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Cargando…</p>';
  try {
    const d = await apiFetch('/api/save-comparison');
    const saves = d.saves || [];
    if (!saves.length) {
      el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">No hay saves en la biblioteca.</p>';
      return;
    }
    const _fmtDate = s => s ? s.replace('T', ' ').substring(0, 16) : '<span style="color:var(--c-ghost)">—</span>';
    const _syncBadge = s => {
      if (!s.last_sync_at) return '<span style="color:var(--c-hint);font-size:10px">Nunca</span>';
      const cls = s.last_result === 'ok' ? 'var(--c-teal)' : 'var(--c-softred)';
      return `<span style="color:${cls};font-size:10px">${_fmtDate(s.last_sync_at)}</span>`;
    };
    let html = `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead><tr style="color:var(--c-dim);border-bottom:1px solid #2a2a3a">
        <th style="text-align:left;padding:4px 6px">Plataforma</th>
        <th style="text-align:left;padding:4px 6px">Título</th>
        <th style="text-align:left;padding:4px 6px">Mod. local</th>
        <th style="text-align:left;padding:4px 6px">Último sync</th>
        <th style="text-align:left;padding:4px 6px">Dirección</th>
      </tr></thead><tbody>`;
    saves.forEach(s => {
      const stale = s.local_mtime && s.last_sync_at && s.local_mtime > s.last_sync_at;
      const rowStyle = stale ? 'background:var(--rv-tint-amber-bg)' : '';
      const _h = str => String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      html += `<tr style="${rowStyle};border-bottom:1px solid #1a1a2a">
        <td style="padding:4px 6px;color:var(--c-muted)">${_h(s.platform)}</td>
        <td style="padding:4px 6px;color:var(--c-text)">${_h(s.title)}</td>
        <td style="padding:4px 6px;color:${stale ? 'var(--c-amber)' : '#888'}">${_fmtDate(s.local_mtime)}</td>
        <td style="padding:4px 6px">${_syncBadge(s)}</td>
        <td style="padding:4px 6px;color:var(--c-dim);font-size:10px">${_h(s.last_direction || '—')}</td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    if (saves.some(s => s.local_mtime && s.last_sync_at && s.local_mtime > s.last_sync_at)) {
      html = `<div style="font-size:11px;color:var(--c-amber);margin-bottom:8px">⚠ Filas en amarillo: save modificado después del último sync.</div>` + html;
    }
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${String(e.message).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</p>`; }
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
        parityEl.innerHTML = '<span style="color:var(--c-pink)">⚠ ' + diff + ' ROM' + (diff !== 1 ? 's' : '') + ' difieren</span>';
      }
    }

    if (!resultEl) return;
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const makeTable = (rows, loc) => {
      if (!rows.length) return '<p style="color:var(--c-muted);font-size:13px;margin:6px 0 0">Ninguno.</p>';
      let t = '<table style="width:100%;border-collapse:collapse"><thead><tr><th style="text-align:left;padding:4px">Plataforma</th><th style="text-align:left;padding:4px">Título</th></tr></thead><tbody>';
      for (const r of rows) t += '<tr style="border-bottom:1px solid #1a1a2a"><td style="padding:4px">' + esc(r.platform) + '</td><td>' + esc(r.title) + '</td></tr>';
      return t + '</tbody></table>';
    };

    let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:4px">';
    html += '<div><h4 style="margin:0 0 6px;color:var(--c-pink)">Solo en PC (' + only_pc.length + ' / ' + total_pc + ')</h4>' + makeTable(only_pc) + '</div>';
    html += '<div><h4 style="margin:0 0 6px;color:var(--c-lblue)">Solo en Android (' + only_android.length + ' / ' + total_android + ')</h4>' + makeTable(only_android) + '</div>';
    html += '</div>';
    html += '<details style="margin-top:12px"><summary style="cursor:pointer;color:var(--c-muted);font-size:13px">En ambos (' + in_both.length + ')</summary>' + makeTable(in_both) + '</details>';

    resultEl.innerHTML = html;
  } catch (e) {
    if (parityEl) parityEl.textContent = '';
    if (resultEl) resultEl.innerHTML = '<p style="color:var(--c-pink)">Error: ' + String(e.message).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</p>';
  }
}

// SAVE-CONSOLIDATOR-1: agrupa saves por juego (ignora carpeta por-core y
// extensión), marca plantillas en blanco por contenido, y reporta grupos
// divergentes sin tocar nada — nunca fusiona ni borra automáticamente.
async function doSaveFragmentation() {
  const summaryEl = document.getElementById('save-frag-summary');
  const resultEl = document.getElementById('save-frag-result');
  if (summaryEl) summaryEl.textContent = 'Analizando…';
  if (resultEl) resultEl.innerHTML = '';
  try {
    const d = await apiFetch('/api/save-fragmentation');
    if (d.error) {
      if (summaryEl) summaryEl.innerHTML = '<span style="color:var(--c-pink)">' + d.error + '</span>';
      return;
    }
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const { summary, groups, roots } = d;
    const missing = roots.filter(r => !r.exists).map(r => r.name);
    if (summaryEl) {
      const parts = [];
      if (summary.divergent) parts.push('<span style="color:var(--c-pink)">' + summary.divergent + ' divergente' + (summary.divergent !== 1 ? 's' : '') + ' (necesitan tu decisión)</span>');
      if (summary.blank) parts.push('<span style="color:var(--c-amber)">' + summary.blank + ' solo-plantilla (seguro descartar)</span>');
      if (summary.identical) parts.push('<span style="color:#a6e3a1">' + summary.identical + ' idénticos (seguro deduplicar)</span>');
      if (!parts.length) parts.push('<span style="color:#a6e3a1">✓ Sin fragmentación detectada</span>');
      if (missing.length) parts.push('<span style="color:var(--c-dim)">(' + missing.join(', ') + ' no existe)</span>');
      summaryEl.innerHTML = parts.join(' &nbsp;·&nbsp; ');
    }
    if (!resultEl) return;
    if (!groups.length) { resultEl.innerHTML = ''; return; }
    const statusLabel = { divergent: 'Divergente', blank: 'Solo plantilla', identical: 'Idéntico' };
    const statusColor = { divergent: 'var(--c-pink)', blank: 'var(--c-amber)', identical: '#a6e3a1' };
    let html = '<div style="overflow-x:auto"><table><thead><tr><th>Estado</th><th>Juego</th><th>Copias</th></tr></thead><tbody>';
    html += groups.map((g, i) => {
      const rows = g.entries.map(e =>
        '<tr style="border-bottom:1px solid #1a1a2a"><td colspan="3" style="padding:2px 4px 2px 20px;font-size:11px;color:var(--c-dim)">'
        + esc(e.relative) + ' &middot; ' + e.size + ' B &middot; ' + esc(e.mtime.replace('T', ' ').slice(0, 16))
        + (e.is_blank ? ' &middot; <span style="color:var(--c-amber)">plantilla en blanco</span>' : '')
        + '</td></tr>'
      ).join('');
      return '<tr><td style="color:' + statusColor[g.status] + '">' + statusLabel[g.status] + '</td>'
        + '<td>' + esc(g.stem) + ' <span style="color:var(--c-dim);font-size:11px">(' + esc(g.root) + ')</span></td>'
        + '<td>' + g.entries.length + '</td></tr>' + rows;
    }).join('');
    html += '</tbody></table></div>';
    resultEl.innerHTML = html;
  } catch (e) {
    if (summaryEl) summaryEl.textContent = '';
    if (resultEl) resultEl.innerHTML = '<p style="color:var(--c-pink)">Error: ' + String(e.message).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</p>';
  }
}

async function doSync(dryRun) {
  const btnDry   = document.getElementById('btn-sync-dry');
  const btnApply = document.getElementById('btn-sync-apply');
  const resultEl = document.getElementById('job-result-sync');
  if (btnDry)   btnDry.disabled   = true;
  if (btnApply) btnApply.disabled = true;
  resultEl.className = 'job-result';
  if (!dryRun) {
    // Request notification permission if needed
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }
  try {
    const d = await apiPost('/api/sync', { dry_run: dryRun });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un sync en curso…';
      return;
    }
    window.startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible';
    resultEl.textContent = 'Error: ' + String(e.message).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    if (btnDry)   btnDry.disabled   = false;
    if (btnApply) btnApply.disabled = false;
  }
}

// CLOUD-UX-12: lista por fuente de qué archivo se mueve y en qué dirección —
// en dry run es el "plan" que se revisa antes de pulsar Sincronizar.
function _renderSyncDecisions(result) {
  const el = document.getElementById('sync-decisions');
  if (!el) return;
  if (result.error) { el.innerHTML = ''; return; }
  const ICONS = {
    upload:   ['&#x2191;', 'var(--c-teal)'],
    download: ['&#x2193;', 'var(--c-blue)'],
    conflict: ['&#x26A0;', 'var(--c-amber)'],
  };
  const blocks = (result.sources || []).map(src => {
    if (src.error) {
      return `<div style="font-size:12px;color:var(--c-softred);padding:2px 0">&#x2717; ${_h(src.name)} — ${_h(src.error)}</div>`;
    }
    const decs = src.decisions || [];
    if (!decs.length) return '';
    const conflicts = decs.filter(d => d.action === 'conflict').length;
    const rows = decs.map(d => {
      const [icon, color] = ICONS[d.action] || ['&#x2022;', 'var(--c-muted)'];
      const hl = d.action === 'conflict' ? ';background:var(--rv-tint-amber-bg)' : '';
      return `<div style="padding:1px 0;color:var(--c-muted)${hl}"><span style="color:${color};margin-right:8px">${icon}</span>${_h(d.relative)}</div>`;
    }).join('');
    const conflictTag = conflicts ? ` <span style="color:var(--c-amber)">&#x26A0; ${conflicts} conflicto${conflicts !== 1 ? 's' : ''}</span>` : '';
    return `<details open style="margin-top:6px">
      <summary style="cursor:pointer;font-size:12px;color:var(--c-soft)">${_h(src.name)}: ${decs.length} archivo${decs.length !== 1 ? 's' : ''}${conflictTag}</summary>
      <div style="max-height:220px;overflow-y:auto;font-size:11px;font-family:monospace;margin:4px 0 0 14px">${rows}</div>
    </details>`;
  }).filter(Boolean);
  if (!blocks.length) { el.innerHTML = ''; return; }
  const header = result.dry_run
    ? '<div style="font-size:11px;color:var(--c-dim)">Plan — esto es lo que se movería al pulsar <strong>Sincronizar</strong> (&#x2191; subir &middot; &#x2193; bajar &middot; &#x26A0; conflicto):</div>'
    : '<div style="font-size:11px;color:var(--c-dim)">Archivos sincronizados (&#x2191; subido &middot; &#x2193; bajado &middot; &#x26A0; conflicto):</div>';
  el.innerHTML = header + blocks.join('');
}

function _renderSyncResult(result) {
  _renderSyncDecisions(result);
  const resultEl = document.getElementById('job-result-sync');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible';
    resultEl.textContent = 'Error: ' + String(result.error).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  } else {
    const verb = result.dry_run ? 'Sincronizaría' : 'Sincronizado';
    const hasErrors = result.errors > 0;
    resultEl.className = 'job-result visible' + (hasErrors ? ' error' : ' success');
    const deltaNote = result.delta_skipped ? `  Δ ${result.delta_skipped}` : '';
    resultEl.textContent = `${verb} — ↑ ${result.uploaded}  ↓ ${result.downloaded}  ✓ ${result.up_to_date}  ⚠ ${result.conflicts}  ✗ ${result.errors}${deltaNote}`;
    if (!result.dry_run) {
      // Send notification if available
      if ('Notification' in window && Notification.permission === 'granted') {
        try {
          new Notification('Sync completado', {
            body: '↑ ' + result.uploaded + ' ↓ ' + result.downloaded + ' ✓ ' + result.up_to_date,
            icon: '/static/icon.png'
          });
        } catch(e) {
          // Notification might fail silently
        }
      }
    }
  }
}

// ── S29: Backup de saves (CLOUD-UX-1) ────────────────────────────────────────
async function backupNow() {
  const el = document.getElementById('job-result-backup-now');
  try {
    const d = await apiPost('/api/backup-now', {});
    if (d.status === 'already_running') {
      if (el) { el.className = 'job-result visible'; el.textContent = 'Ya hay un backup en curso…'; }
      return;
    }
    startPolling();
  } catch (e) {
    if (el) { el.className = 'job-result visible error-r'; el.textContent = 'Error: ' + e.message; }
  }
}

async function loadManualBackups() {
  const el = document.getElementById('manual-backups-list');
  if (!el) return;
  try {
    const d = await apiFetch('/api/manual-backups');
    const zips = d.zips || [];
    if (!zips.length) {
      el.innerHTML = '<span style="color:var(--c-dim)">Aún no hay ZIPs de backup.</span>';
      return;
    }
    el.innerHTML = zips.map(z => `<div style="display:flex;gap:12px;padding:2px 0;color:var(--c-muted)">
      <span style="flex:1" title="${_h(z.path)}">${_h(z.filename)}</span>
      <span style="color:var(--c-dim)">${_h((z.timestamp || '').replace('T', ' '))}</span>
      <span style="color:var(--c-dim);min-width:70px;text-align:right">${fmtSize(z.size)}</span>
    </div>`).join('');
  } catch (e) {
    el.innerHTML = `<span style="color:var(--c-softred)">Error: ${_h(e.message)}</span>`;
  }
}

// ── SYNC-SETUP: Cloud auth wizard ────────────────────────────────────────────

let _cloudAuthPolling = null;

async function loadCloudAuthStatus() {
  const el = document.getElementById('cloud-auth-status');
  if (!el) return;
  try {
    const [data, cfg] = await Promise.all([
      apiFetch('/api/cloud-auth/status'),
      apiFetch('/api/config').catch(() => ({})),
    ]);
    if (data.error) {
      el.innerHTML = `<span style="color:var(--c-softred)">${data.error}</span>`;
      return;
    }
    let html = data.providers.map(p => {
      const label = p.label;
      const configured = p.configured;
      const badge = configured
        ? `<span style="color:var(--c-green);font-weight:600">&#x2713; Conectado</span>`
        : `<span style="color:var(--c-dim)">No configurado</span>`;
      const connectBtn = configured ? '' :
        `<button class="btn" onclick="startCloudAuth('${p.id}')" style="font-size:11px;padding:3px 10px;margin-left:10px">Conectar</button>`;
      const disconnectBtn = configured
        ? `<button class="btn" onclick="disconnectCloud('${p.remote_name}')" style="font-size:11px;padding:3px 10px;margin-left:10px;color:var(--c-softred)">Desconectar</button>`
        : '';
      return `<div style="display:flex;align-items:center;gap:4px;margin-bottom:6px">
        <span style="min-width:100px;font-weight:500">${label}</span>
        ${badge}${connectBtn}${disconnectBtn}
      </div>`;
    }).join('');
    // CLOUD-UX-9: "Conectado" (remote en rclone) ≠ "sync configurado"
    // (saves_remote en config) — mostrar el destino activo en la tarjeta y,
    // si falta, ofrecer configurarlo a un clic.
    const saves = cfg.saves_remote || '';
    const states = cfg.states_remote || '';
    const connected = (data.providers || []).filter(p => p.configured);
    if (saves || states) {
      html += `<div style="margin-top:8px;font-size:11px;color:var(--c-muted)">Destino de sync — saves: <code>${_h(saves) || '&mdash;'}</code> &middot; states: <code>${_h(states) || '&mdash;'}</code></div>`;
    } else if (connected.length) {
      html += `<div style="margin-top:8px;font-size:12px">
        <span style="color:var(--c-yellow)">Conectado, pero sin destino de sync.</span>
        ${connected.map(p => `<button class="btn primary" style="font-size:11px;padding:3px 10px;margin-left:8px" onclick="useRemoteForSync('${p.remote_name}')">Usar ${_h(p.remote_name)}:RetroSync para saves + states</button>`).join('')}
      </div>`;
    }
    el.innerHTML = html;
    // CLOUD-UX-8: el bloque de setup se colapsa cuando todo está en verde
    // (provider conectado + destino de sync configurado).
    const setup = document.getElementById('cloud-setup-block');
    const setupBadge = document.getElementById('cloud-setup-badge');
    const ready = connected.length > 0 && !!(saves || states);
    if (setupBadge) {
      setupBadge.innerHTML = ready
        ? '<span style="color:var(--c-green)">&#x2713; configurado</span>'
        : '<span style="color:var(--c-yellow)">pendiente de configurar</span>';
    }
    if (setup) {
      const wasOpen = setup.open;
      setup.open = !ready;
      // Si ya estaba abierto, ontoggle no dispara — cargar el paso 2 a mano
      if (setup.open && wasOpen) loadRcloneStatus();
    }
  } catch (e) {
    el.innerHTML = `<span style="color:var(--c-softred)">Error al comprobar estado: ${e.message}</span>`;
  }
}

// CLOUD-UX-9: un clic desde la tarjeta "Conexión cloud" deja el sync funcional
async function useRemoteForSync(remoteName) {
  try {
    await apiPost('/api/config', {
      'sync.saves_remote': `${remoteName}:RetroSync/saves`,
      'sync.states_remote': `${remoteName}:RetroSync/states`,
    });
    showToast(`Sync configurado — ${remoteName}:RetroSync (saves + states)`, 'ok');
    loadCloudAuthStatus();
    loadSync();
  } catch (e) {
    _showCloudAuthError(e.message);
  }
}

async function startCloudAuth(providerId) {
  const progressEl = document.getElementById('cloud-auth-progress');
  const errorEl = document.getElementById('cloud-auth-error');
  if (progressEl) progressEl.classList.remove('hidden');
  if (errorEl) errorEl.classList.add('hidden');

  try {
    await apiPost('/api/cloud-auth/start', { provider: providerId });
    _cloudAuthPolling = setInterval(_pollCloudAuth, 2000);
  } catch (e) {
    if (progressEl) progressEl.classList.add('hidden');
    _showCloudAuthError(e.message);
  }
}

async function _pollCloudAuth() {
  try {
    const data = await apiFetch('/api/cloud-auth/poll');
    if (!data.done) return;
    clearInterval(_cloudAuthPolling);
    _cloudAuthPolling = null;
    const progressEl = document.getElementById('cloud-auth-progress');
    if (progressEl) progressEl.classList.add('hidden');

    if (data.error) {
      _showCloudAuthError(data.error);
      return;
    }
    // Auto-finalize with the captured token
    // CLOUD-UX-4: el poll devuelve el provider que inició el flujo — antes se
    // adivinaba "el primer provider no configurado" y el token de Google Drive
    // podía acabar bajo el remote dropbox.
    if (data.token && data.provider) {
      const res = await apiPost('/api/cloud-auth/finalize', {
        provider: data.provider,
        remote_name: data.remote_name,
        token: data.token,
      });
      if (res.error) { _showCloudAuthError(res.error); return; }
    }
    showToast('Conexión cloud configurada correctamente', 'ok');
    loadCloudAuthStatus();
  } catch (e) {
    clearInterval(_cloudAuthPolling);
    _cloudAuthPolling = null;
    _showCloudAuthError(e.message);
  }
}

function cancelCloudAuth() {
  if (_cloudAuthPolling) { clearInterval(_cloudAuthPolling); _cloudAuthPolling = null; }
  const progressEl = document.getElementById('cloud-auth-progress');
  if (progressEl) progressEl.classList.add('hidden');
  // CLOUD-UX-4: avisar al backend para matar el subprocess 'rclone authorize'
  apiPost('/api/cloud-auth/cancel', {}).catch(() => {});
}

async function disconnectCloud(remoteName) {
  if (!confirm(`¿Eliminar la conexión "${remoteName}" de rclone?`)) return;
  try {
    const res = await apiPost('/api/cloud-auth/disconnect', { remote_name: remoteName });
    if (res.error) { _showCloudAuthError(res.error); return; }
    showToast(`Remote "${remoteName}" eliminado`, 'ok');
    loadCloudAuthStatus();
  } catch (e) {
    _showCloudAuthError(e.message);
  }
}

function _showCloudAuthError(msg) {
  const el = document.getElementById('cloud-auth-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
}

export {
  // Save comparison & library diff
  loadSaveComparison,
  doLibraryDiff,
  doSaveFragmentation,
  doSync,
  _renderSyncResult,
  // Cloud Sync
  loadSync,
  loadAssets,
  showOrphanAssets,
  loadSystemStatus,
  detectCloudFolder,
  useCloudFolder,
  loadAutostart,
  toggleAutostart,
  shutdownServer,
  // Android / Anbernic setup
  _checkAndroidUserAgent,
  loadAnbernicTab,
  copyAnbernicCmd,
  copyAnbernicUrl,
  // ANBERNIC-TV: touch-friendly sync flow
  tvCheckStatus, tvCheckServer, tvToggleSetup, tvCopySetupCmd, tvStartSync, tvShowResult, tvReset, tvSkipToFull,
  // Cloud auth wizard (SYNC-SETUP)
  loadCloudAuthStatus,
  startCloudAuth,
  cancelCloudAuth,
  disconnectCloud,
  useRemoteForSync,
  openCloudSetup,
  // Rclone
  loadRcloneStatus,
  openRcloneConfig,
  testRcloneRemote,
  applyRcloneRemote,
  applyRcloneSavesStates,
  // Backup de saves (CLOUD-UX-1)
  backupNow,
  loadManualBackups,
  // Cable Sync
  goToCableSyncAdvanced,
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
  // Auto-sync
  _updateAutoSyncBanner,
  _updateAutoSyncToggleUI,
  toggleAutoSync,
  saveAutoSyncSettings,
  saveConflictPolicy,
  startAutoSyncPolling,
  promptSyncNow,
  // Tree diff
  _onTreeDiffSourceChange,
  _loadTreeDiffDevices,
  doTreeDiff,
  _renderTreeDiff,
};
