// js/tabs/scan.js — Scan, Match, Fix-platforms, DAT catalog
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// Local helper (duplicated from app.js pending full migration)
const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// ── ADB scan helpers ──────────────────────────────────────────────────────────
function _onScanAdbChange() {
  const cb  = document.getElementById('scan-include-adb');
  const box = document.getElementById('scan-adb-options');
  if (box) box.classList.toggle('hidden', !(cb?.checked));
}

async function detectAdbDevicesForScan() {
  const sel    = document.getElementById('scan-adb-device');
  const status = document.getElementById('scan-adb-status');
  if (status) { _txtCls(status, 'txt-dim'); status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) { if (status) { _txtCls(status, 'txt-err'); status.textContent = '✗ ' + d.error; } return; }
    if (!d.devices?.length) {
      if (status) { _txtCls(status, 'txt-warn'); status.textContent = `No se encontraron dispositivos — conecta la ${window._devName} y activa Depuración USB`; }
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
      _txtCls(status, readyCount ? 'txt-ok' : 'txt-warn');
      status.textContent = readyCount ? `✓ ${readyCount} dispositivo(s) listo(s)` : `⚠ Acepta el diálogo de depuración USB en la ${window._devName}`;
    }
  } catch(e) { if (status) { _txtCls(status, 'txt-err'); status.textContent = '✗ ' + e.message; } }
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
      window.startPolling();
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
    window.startPolling();
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
    window.showTab('overview');
    window.startPolling();
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
    window.showTab('overview');
    window.startPolling();
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
    window.loadOverview();
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
    window.startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Identificar (catálogos)';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Catalog DAT management ─────────────────────────────────────────────────────
async function loadCatalogStatus() {
  const el   = document.getElementById('catalog-status');
  const ovEl = document.getElementById('ov-catalog-status');
  try {
    const d = await apiFetch('/api/catalog-status');
    const ni = d.nointro.length, rd = d.redump.length, arc = (d.arcade || []).length;
    const niE = (d.total_nointro_entries || 0).toLocaleString();
    const rdE = (d.total_redump_entries || 0).toLocaleString();
    const arcE = (d.total_arcade_entries || 0).toLocaleString();
    let html = '';
    if (ni === 0 && rd === 0 && arc === 0) {
      html = '<span style="color:#dcdcaa">\u26A0 No hay cat\u00e1logos DAT cargados.</span> El cruce de hashes no estar\u00e1 disponible hasta que importes archivos DAT.';
    } else {
      const parts = [];
      if (ni > 0) parts.push(`<strong style="color:#4ec9b0">${ni}</strong> No-Intro (${niE} entradas)`);
      if (rd > 0) parts.push(`<strong style="color:#4ec9b0">${rd}</strong> Redump (${rdE} entradas)`);
      if (arc > 0) {
        const arcFiles = (d.arcade || []).map(f => {
          const lbl = f.name.toLowerCase().endsWith('.xml') ? 'MAME' : 'FBNeo';
          return `${lbl}: ${f.entries.toLocaleString()}`;
        }).join(', ');
        parts.push(`<strong style="color:#4ec9b0">${arc}</strong> Arcade (${arcFiles})`);
      }
      html = '\u2705 ' + parts.join(' &middot; ');
    }
    html += `<br><span style="color:#555;font-size:10px">No-Intro: <code>${d.nointro_dir}</code> &middot; Redump: <code>${d.redump_dir}</code> &middot; Arcade: <code>${d.arcade_dir}</code></span>`;
    if (el) el.innerHTML = html;
    if (ovEl && (ni > 0 || rd > 0 || arc > 0)) {
      const _p = [];
      if (ni > 0) _p.push(ni + ' No-Intro');
      if (rd > 0) _p.push(rd + ' Redump');
      if (arc > 0) _p.push(arc + ' Arcade');
      ovEl.innerHTML = `\u2705 ${_p.join(' \u00b7 ')} <a href="#" onclick="showTab('settings');return false" style="color:#555;font-size:10px">gestionar \u2192</a>`;
    } else if (ovEl) {
      ovEl.innerHTML = `<span style="color:#dcdcaa">\u26A0 Sin cat\u00e1logos DAT</span> \u2014 los ROMs no se pueden identificar. `
        + `<a href="#" onclick="showTab('settings');setTimeout(function(){var s=document.getElementById('dat-catalog-list');if(s)s.scrollIntoView({behavior:'smooth'})},350);return false" style="color:#7aadff">Descargar cat\u00e1logos \u2192</a>`;
    }
  } catch(e) {
    if (el) el.textContent = 'Error al cargar estado de cat\u00e1logos.';
  }
}

async function importArcadeCatalog() {
  const path = (document.getElementById('arcade-catalog-path')?.value || '').trim();
  if (!path) { alert('Introduce la carpeta o archivo con el catálogo arcade.'); return; }
  const res = document.getElementById('arcade-catalog-result');
  if (res) { res.textContent = 'Importando\u2026'; _txtCls(res, 'txt-muted'); }
  try {
    const d = await apiPost('/api/import-arcade-catalog', { path });
    if (d.error) {
      if (res) { res.textContent = '\u274C ' + d.error; _txtCls(res, 'txt-err'); }
      return;
    }
    const lines = d.imported.map(f => {
      const lbl = f.format === 'mame_xml' ? 'MAME' : 'FBNeo';
      return `${f.name} (${lbl}, ${f.entries.toLocaleString()} entradas)`;
    }).join('<br>');
    const errTxt = d.errors.length ? ` &mdash; ${d.errors.length} error(es)` : '';
    if (res) {
      res.innerHTML = `\u2705 ${d.total_files} archivo(s), ${d.total_entries.toLocaleString()} entradas importadas${errTxt}<br><span style="color:#555;font-size:11px">${lines}</span>`;
      _txtCls(res, 'txt-ok');
    }
    loadCatalogStatus();
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; _txtCls(res, 'txt-err'); }
  }
}

async function importDats() {
  const folder = (document.getElementById('import-dats-folder')?.value || '').trim();
  if (!folder) { alert('Introduce la carpeta con los archivos DAT.'); return; }
  const res = document.getElementById('import-dats-result');
  if (res) { res.textContent = 'Importando\u2026'; _txtCls(res, 'txt-muted'); }
  try {
    const d = await apiPost('/api/import-dats', { source_folder: folder });
    if (d.error) {
      if (res) { res.textContent = '\u274C ' + d.error; _txtCls(res, 'txt-err'); }
      return;
    }
    const ni = d.imported.filter(x => x.catalog === 'nointro').length;
    const rd = d.imported.filter(x => x.catalog === 'redump').length;
    const msg = d.total > 0
      ? `\u2705 ${d.total} archivo(s) importados: ${ni} No-Intro, ${rd} Redump.` + (d.errors.length ? ` (${d.errors.length} errores)` : '')
      : '\u26A0 No se encontraron archivos DAT reconocidos en esa carpeta.';
    if (res) { res.innerHTML = msg; _txtCls(res, d.total > 0 ? 'txt-ok' : null); }
    loadCatalogStatus();
  } catch(e) {
    if (res) { res.textContent = '\u274C ' + e.message; _txtCls(res, 'txt-err'); }
  }
}

// ── DAT auto-download ─────────────────────────────────────────────────────────
let _datDlPollTimer = null;

async function loadDatCatalogList() {
  const container = document.getElementById('dat-catalog-list');
  if (!container) return;
  container.innerHTML = '<span class="txt-muted">Cargando catálogo…</span>';
  try {
    const data = await apiFetch('/api/dat-catalog-list');
    if (data.error) { container.textContent = '❌ ' + data.error; return; }
    const byType = {};
    for (const sys of data.systems) {
      const k = sys.catalog === 'redump' ? 'Redump (óptico)' : 'No-Intro (cartuchos)';
      (byType[k] = byType[k] || []).push(sys);
    }
    let html = '';
    for (const [label, systems] of Object.entries(byType)) {
      html += `<div class="dat-catalog-group"><strong>${label}</strong><div class="dat-catalog-items">`;
      for (const sys of systems) {
        const chk = sys.present ? 'checked' : '';
        const cls = sys.present ? 'dat-item-present' : '';
        html += `<label class="dat-item ${cls}">
          <input type="checkbox" name="dat-sys" value="${sys.name}" ${chk}> ${sys.short}
        </label>`;
      }
      html += '</div></div>';
    }
    container.innerHTML = html;
  } catch(e) {
    container.textContent = '❌ ' + e.message;
  }
}

async function downloadDats(all) {
  const bar     = document.getElementById('dat-dl-bar');
  const barFill = document.getElementById('dat-dl-bar-fill');
  const status  = document.getElementById('dat-dl-status');
  let systems;
  if (all) {
    systems = null; // backend downloads all
  } else {
    const checked = [...document.querySelectorAll('input[name="dat-sys"]:checked')];
    systems = checked.map(el => el.value);
    if (!systems.length) { alert('Selecciona al menos un sistema.'); return; }
  }
  if (status) { status.textContent = 'Iniciando descarga…'; _txtCls(status, 'txt-muted'); }
  if (bar)     bar.classList.remove('hidden');
  if (barFill) barFill.style.width = '0%';
  try {
    const body = systems ? { systems } : { all: true };
    const d = await apiPost('/api/download-dats', body);
    if (d.error) {
      if (status) { status.textContent = '❌ ' + d.error; _txtCls(status, 'txt-err'); }
      return;
    }
    clearInterval(_datDlPollTimer);
    _datDlPollTimer = setInterval(_pollDatDownload, 1000);
  } catch(e) {
    if (status) { status.textContent = '❌ ' + e.message; _txtCls(status, 'txt-err'); }
  }
}

async function _pollDatDownload() {
  const barFill = document.getElementById('dat-dl-bar-fill');
  const status  = document.getElementById('dat-dl-status');
  const bar     = document.getElementById('dat-dl-bar');
  try {
    const d = await apiFetch('/api/download-dats-status');
    if (d.running) {
      const pct = d.total > 0 ? Math.round((d.done / d.total) * 100) : 0;
      if (barFill) barFill.style.width = pct + '%';
      if (status)  status.textContent  = `Descargando… ${d.done}/${d.total} — ${d.current}`;
      return;
    }
    clearInterval(_datDlPollTimer);
    _datDlPollTimer = null;
    if (barFill) barFill.style.width = '100%';
    const r = d.result || {};
    const ok   = (r.downloaded || []).length;
    const skip = (r.skipped    || []).length;
    const err  = (r.errors     || []).length;
    const msg  = `✅ ${ok} descargados, ${skip} ya existían` + (err ? `, ❌ ${err} errores` : '');
    if (status) { status.textContent = msg; _txtCls(status, 'txt-ok'); }
    if (bar && !err) setTimeout(() => bar.classList.add('hidden'), 3000);
    loadCatalogStatus();
    loadDatCatalogList();
  } catch(e) {
    clearInterval(_datDlPollTimer);
    if (status) { status.textContent = '❌ ' + e.message; _txtCls(status, 'txt-err'); }
  }
}

// ── Public exports ────────────────────────────────────────────────────────────
export {
  _onScanAdbChange, detectAdbDevicesForScan,
  doScan, quickScanPC, quickScanAndroid,
  doFixPlatforms, doMatch,
  loadCatalogStatus, importArcadeCatalog, importDats,
  loadDatCatalogList, downloadDats,
};
