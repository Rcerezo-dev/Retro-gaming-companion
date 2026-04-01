// js/tabs/esde.js — ES-DE status, BIOS checker, RetroArch diagnostic
// Extracted from app.js during Phase 2 migration.

import { apiFetch } from '../api.js';

// ── Local helper ──────────────────────────────────────────────────────────────
const _h = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// ── ES-DE Status ──────────────────────────────────────────────────────────────
export async function loadEsdeStatus() {
  const el = document.getElementById('esde-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:#555;font-size:12px">Detectando…</p>';
  try {
    const d = await apiFetch('/api/esde-status');
    if (!d.installed) {
      el.innerHTML = `<p style="color:#e06c75;font-size:12px">&#x2717; ES-DE no detectado en las rutas conocidas.</p>
        <p style="color:#555;font-size:11px">Instala ES-DE desde <a href="https://es-de.org" target="_blank" style="color:#4ec9b0">es-de.org</a> o configura la ruta manualmente.</p>`;
      return;
    }
    el.innerHTML = `
      <div style="font-size:12px;color:#4ec9b0;margin-bottom:8px">&#x2713; ES-DE detectado</div>
      <table style="font-size:12px;border-collapse:collapse;width:100%">
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">Carpeta</td><td><code style="color:#ce9178">${_h(d.install_dir)}</code></td></tr>
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">ROMs</td><td><code style="color:#ce9178">${_h(d.roms_path || '—')}</code></td></tr>
        <tr><td style="color:#555;padding:2px 6px 2px 0;white-space:nowrap">Gamelists</td><td><code style="color:#ce9178">${_h(d.gamelists_dir || '—')}</code></td></tr>
      </table>
      ${d.gamelists_dir ? `<div style="margin-top:10px"><button class="btn primary" onclick="doExportGamelistsAll(${JSON.stringify(d.gamelists_dir)})" style="font-size:12px">&#x2193; Exportar todas las gamelists a ES-DE</button></div>` : ''}`;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

// ── BIOS Checker ──────────────────────────────────────────────────────────────
export async function loadBiosStatus() {
  const el = document.getElementById('bios-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:#555;font-size:12px">Buscando…</p>';
  try {
    const d = await apiFetch('/api/bios-status');
    const bios = d.bios || [];
    if (!bios.length) { el.innerHTML = '<p style="color:#555;font-size:12px">No hay definiciones de BIOS.</p>'; return; }
    const byPlat = {};
    bios.forEach(b => { (byPlat[b.platform] = byPlat[b.platform] || []).push(b); });
    let html = '';
    Object.entries(byPlat).sort(([a],[b]) => a.localeCompare(b)).forEach(([plat, entries]) => {
      const total = entries.length, found = entries.filter(e => e.found).length;
      const clr = found === total ? '#4ec9b0' : (found > 0 ? '#f9c74f' : '#e06c75');
      html += `<div style="margin-bottom:12px">
        <div style="font-size:12px;font-weight:600;color:${clr};margin-bottom:4px">${_h(plat)} <span style="font-weight:400;color:#555">(${found}/${total})</span></div>`;
      entries.forEach(b => {
        const icon = b.found ? (b.md5_match === false ? '&#x26A0;' : '&#x2713;') : (b.required ? '&#x2717;' : '&#x25A1;');
        const clrIcon = b.found ? (b.md5_match === false ? '#f9c74f' : '#4ec9b0') : (b.required ? '#e06c75' : '#555');
        const md5note = b.found && b.md5_match === false ? ' <span style="color:#f9c74f;font-size:10px">MD5 no coincide</span>' : '';
        html += `<div style="display:flex;gap:6px;align-items:center;padding:2px 0;font-size:11px">
          <span style="color:${clrIcon};width:14px;flex-shrink:0">${icon}</span>
          <code style="color:#ce9178;flex:1">${_h(b.filename)}</code>
          <span style="color:#555">${_h(b.notes)}</span>${md5note}
        </div>`;
      });
      html += `</div>`;
    });
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:#e06c75;font-size:12px">Error: ${_h(e.message)}</p>`; }
}

// ── RetroArch Diagnostic ──────────────────────────────────────────────────────
export async function loadRetroArchCheck() {
  const spinner  = document.getElementById('ra-check-spinner');
  const result   = document.getElementById('ra-check-result');
  const status   = document.getElementById('ra-check-status');
  const rows     = document.getElementById('ra-check-rows');
  const issues   = document.getElementById('ra-check-issues');
  const coresWrap = document.getElementById('ra-check-cores');
  const coresList = document.getElementById('ra-check-cores-list');
  if (!result) return;
  if (spinner) spinner.classList.remove('hidden');
  result.classList.add('hidden');
  try {
    const d = await apiFetch('/api/retroarch-check');
    if (spinner) spinner.classList.add('hidden');

    const okColor = d.ok ? '#4ec9b0' : '#e06c75';
    const okIcon  = d.ok ? '&#x2713; Todo correcto' : '&#x26A0; Hay problemas';
    status.innerHTML = `<span style="color:${okColor}">${okIcon}</span>`;

    const cell = (txt, mono) => mono
      ? `<td style="padding:2px 0 2px 8px"><code style="color:#ce9178;font-size:11px">${_h(txt)}</code></td>`
      : `<td style="padding:2px 0 2px 8px;color:#d4d4d4;font-size:11px">${_h(txt)}</td>`;
    const icon = ok => ok
      ? `<td style="color:#4ec9b0;font-size:11px;width:14px">&#x2713;</td>`
      : `<td style="color:#e06c75;font-size:11px;width:14px">&#x2717;</td>`;

    let html = '';
    html += `<tr>${icon(d.exe_configured)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Ruta configurada</td>${cell(d.exe_path || '\u2014', true)}</tr>`;
    if (d.exe_configured) {
      html += `<tr>${icon(d.exe_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Ejecutable existe</td>${cell(d.exe_exists ? 'S\xed' : 'No', false)}</tr>`;
      html += `<tr>${icon(d.cfg_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">retroarch.cfg</td>${cell(d.cfg_exists ? 'Encontrado' : 'No encontrado', false)}</tr>`;
      html += `<tr>${icon(d.cores_dir_exists)}<td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Cores</td>${cell(d.cores_dir_exists ? d.cores_count + ' cores' : 'No encontrado', false)}</tr>`;
      if (d.savefile_dir)  html += `<tr><td></td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">Saves dir</td>${cell(d.savefile_dir, true)}</tr>`;
      if (d.savestate_dir) html += `<tr><td></td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">States dir</td>${cell(d.savestate_dir, true)}</tr>`;
      if (d.esde_ra_path) {
        const matchIcon  = d.esde_ra_match === true ? '&#x2713;' : (d.esde_ra_match === false ? '&#x26A0;' : '?');
        const matchColor = d.esde_ra_match === true ? '#4ec9b0' : '#f9c74f';
        html += `<tr><td style="color:${matchColor};font-size:11px">${matchIcon}</td><td style="color:#888;font-size:11px;white-space:nowrap;padding:2px 4px">ES-DE apunta a</td>${cell(d.esde_ra_path, true)}</tr>`;
      }
    }
    rows.innerHTML = html;

    if (d.issues && d.issues.length) {
      issues.innerHTML = d.issues.map(i =>
        `<div style="font-size:11px;color:#f9c74f;margin-bottom:3px">&#x26A0; ${_h(i)}</div>`
      ).join('');
    } else {
      issues.innerHTML = '';
    }

    if (d.key_cores && Object.keys(d.key_cores).length) {
      coresWrap.classList.remove('hidden');
      coresList.innerHTML = Object.entries(d.key_cores).map(([lbl, found]) => {
        const bg = found ? '#1e3a2f' : '#2a1a1a';
        const fg = found ? '#4ec9b0' : '#666';
        const ic = found ? '&#x2713;' : '&#x2717;';
        return `<span style="background:${bg};color:${fg};font-size:10px;padding:2px 6px;border-radius:3px">${ic} ${_h(lbl)}</span>`;
      }).join('');
    } else {
      coresWrap.classList.add('hidden');
    }

    result.classList.remove('hidden');
  } catch(e) {
    if (spinner) spinner.classList.add('hidden');
    result.classList.remove('hidden');
    status.innerHTML = `<span style="color:#e06c75">Error: ${_h(e.message)}</span>`;
    rows.innerHTML = '';
    issues.innerHTML = '';
    coresWrap.classList.add('hidden');
  }
}
