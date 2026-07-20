// js/tabs/esde.js — ES-DE status, BIOS checker, RetroArch diagnostic, RA compatibility
// Extracted from app.js during Phase 2 migration; RA check functions added in Phase 2g.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Local helper ──────────────────────────────────────────────────────────────
const _h = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// ── ES-DE Status ──────────────────────────────────────────────────────────────
export async function loadEsdeStatus() {
  const el = document.getElementById('esde-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Detectando…</p>';
  try {
    const d = await apiFetch('/api/esde-status');
    if (!d.installed) {
      el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">&#x2717; ES-DE no detectado en las rutas conocidas.</p>
        <p style="color:var(--c-dim);font-size:11px">Instala ES-DE desde <a href="https://es-de.org" target="_blank" style="color:var(--c-teal)">es-de.org</a> o configura la ruta manualmente.</p>`;
      return;
    }
    el.innerHTML = `
      <div style="font-size:12px;color:var(--c-teal);margin-bottom:8px">&#x2713; ES-DE detectado</div>
      <table style="font-size:12px;border-collapse:collapse;width:100%">
        <tr><td style="color:var(--c-dim);padding:2px 6px 2px 0;white-space:nowrap">Carpeta</td><td><code style="color:var(--c-orange)">${_h(d.install_dir)}</code></td></tr>
        <tr><td style="color:var(--c-dim);padding:2px 6px 2px 0;white-space:nowrap">ROMs</td><td><code style="color:var(--c-orange)">${_h(d.roms_path || '—')}</code></td></tr>
        <tr><td style="color:var(--c-dim);padding:2px 6px 2px 0;white-space:nowrap">Gamelists</td><td><code style="color:var(--c-orange)">${_h(d.gamelists_dir || '—')}</code></td></tr>
      </table>
      ${d.gamelists_dir ? `<div style="margin-top:10px"><button class="btn primary" onclick="doExportGamelistsAll(${JSON.stringify(d.gamelists_dir)})" style="font-size:12px">&#x2193; Exportar todas las gamelists a ES-DE</button></div>` : ''}`;
  } catch(e) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`; }
}

// ── BIOS Checker ──────────────────────────────────────────────────────────────
export async function loadBiosStatus() {
  const el = document.getElementById('bios-status-content');
  if (!el) return;
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Buscando…</p>';
  try {
    const d = await apiFetch('/api/bios-status');
    const bios = d.bios || [];
    if (!bios.length) { el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">No hay definiciones de BIOS.</p>'; return; }
    const byPlat = {};
    bios.forEach(b => { (byPlat[b.platform] = byPlat[b.platform] || []).push(b); });
    let html = '';
    Object.entries(byPlat).sort(([a],[b]) => a.localeCompare(b)).forEach(([plat, entries]) => {
      const total = entries.length, found = entries.filter(e => e.found).length;
      const clr = found === total ? 'var(--c-teal)' : (found > 0 ? 'var(--c-amber)' : 'var(--c-softred)');
      html += `<div style="margin-bottom:12px">
        <div style="font-size:12px;font-weight:600;color:${clr};margin-bottom:4px">${_h(plat)} <span style="font-weight:400;color:var(--c-dim)">(${found}/${total})</span></div>`;
      entries.forEach(b => {
        const icon = b.found ? (b.md5_match === false ? '&#x26A0;' : '&#x2713;') : (b.required ? '&#x2717;' : '&#x25A1;');
        const clrIcon = b.found ? (b.md5_match === false ? 'var(--c-amber)' : 'var(--c-teal)') : (b.required ? 'var(--c-softred)' : '#555');
        const md5note = b.found && b.md5_match === false ? ' <span style="color:var(--c-amber);font-size:10px">MD5 no coincide</span>' : '';
        html += `<div style="display:flex;gap:6px;align-items:center;padding:2px 0;font-size:11px">
          <span style="color:${clrIcon};width:14px;flex-shrink:0">${icon}</span>
          <code style="color:var(--c-orange);flex:1">${_h(b.filename)}</code>
          <span style="color:var(--c-dim)">${_h(b.notes)}</span>${md5note}
        </div>`;
      });
      html += `</div>`;
    });
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`; }
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

    const okColor = d.ok ? 'var(--c-teal)' : 'var(--c-softred)';
    const okIcon  = d.ok ? '&#x2713; Todo correcto' : '&#x26A0; Hay problemas';
    status.innerHTML = `<span style="color:${okColor}">${okIcon}</span>`;

    const cell = (txt, mono) => mono
      ? `<td style="padding:2px 0 2px 8px"><code style="color:var(--c-orange);font-size:11px">${_h(txt)}</code></td>`
      : `<td style="padding:2px 0 2px 8px;color:var(--c-text);font-size:11px">${_h(txt)}</td>`;
    const icon = ok => ok
      ? `<td style="color:var(--c-teal);font-size:11px;width:14px">&#x2713;</td>`
      : `<td style="color:var(--c-softred);font-size:11px;width:14px">&#x2717;</td>`;

    let html = '';
    html += `<tr>${icon(d.exe_configured)}<td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">Ruta configurada</td>${cell(d.exe_path || '\u2014', true)}</tr>`;
    if (d.exe_configured) {
      html += `<tr>${icon(d.exe_exists)}<td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">Ejecutable existe</td>${cell(d.exe_exists ? 'S\xed' : 'No', false)}</tr>`;
      html += `<tr>${icon(d.cfg_exists)}<td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">retroarch.cfg</td>${cell(d.cfg_exists ? 'Encontrado' : 'No encontrado', false)}</tr>`;
      html += `<tr>${icon(d.cores_dir_exists)}<td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">Cores</td>${cell(d.cores_dir_exists ? d.cores_count + ' cores' : 'No encontrado', false)}</tr>`;
      if (d.savefile_dir)  html += `<tr><td></td><td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">Saves dir</td>${cell(d.savefile_dir, true)}</tr>`;
      if (d.savestate_dir) html += `<tr><td></td><td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">States dir</td>${cell(d.savestate_dir, true)}</tr>`;
      if (d.esde_ra_path) {
        const matchIcon  = d.esde_ra_match === true ? '&#x2713;' : (d.esde_ra_match === false ? '&#x26A0;' : '?');
        const matchColor = d.esde_ra_match === true ? 'var(--c-teal)' : 'var(--c-amber)';
        html += `<tr><td style="color:${matchColor};font-size:11px">${matchIcon}</td><td style="color:var(--c-muted);font-size:11px;white-space:nowrap;padding:2px 4px">ES-DE apunta a</td>${cell(d.esde_ra_path, true)}</tr>`;
      }
    }
    rows.innerHTML = html;

    if (d.issues && d.issues.length) {
      issues.innerHTML = d.issues.map(i =>
        `<div style="font-size:11px;color:var(--c-amber);margin-bottom:3px">&#x26A0; ${_h(i)}</div>`
      ).join('');
    } else {
      issues.innerHTML = '';
    }

    if (d.key_cores && Object.keys(d.key_cores).length) {
      coresWrap.classList.remove('hidden');
      coresList.innerHTML = Object.entries(d.key_cores).map(([lbl, found]) => {
        const bg = found ? '#1e3a2f' : '#2a1a1a';
        const fg = found ? 'var(--c-teal)' : '#666';
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
    status.innerHTML = `<span style="color:var(--c-softred)">Error: ${_h(e.message)}</span>`;
    rows.innerHTML = '';
    issues.innerHTML = '';
    coresWrap.classList.add('hidden');
  }
}

// ── RetroAchievements Compatibility Check ──────────────────────────────────
// State variables for RA check
let _raResults = [];
let _raPage = 0;
const _RA_PAGE_SIZE = 20;

export async function doRaCheck() {
  const btn = document.getElementById('btn-ra-check');
  const progressWrap = document.getElementById('ra-progress-wrap');
  const resultEl = document.getElementById('ra-result');

  if (!btn || !progressWrap) return;

  btn.disabled = true;
  btn.textContent = 'Comprobando…';
  progressWrap.classList.remove('hidden');
  resultEl.innerHTML = '';

  try {
    const d = await apiPost('/api/ra-check', {});
    if (d.status === 'already_running') {
      showToast('RA check ya en curso…', 'info');
      btn.disabled = false;
      btn.textContent = 'Comprobar compatibilidad RA';
      progressWrap.classList.add('hidden');
      return;
    }
    // Job started, polling will handle results via _renderRaResult
    if (typeof window.startPolling === 'function') {
      window.startPolling();
    }
  } catch(e) {
    resultEl.innerHTML = `<p style="color:var(--c-red)">Error: ${_h(e.message)}</p>`;
    btn.disabled = false;
    btn.textContent = 'Comprobar compatibilidad RA';
    progressWrap.classList.add('hidden');
    showToast('Error en RA check: ' + e.message, 'err');
  }
}

// Export helper functions for rendering
export function _updateRaProgress(label, filename) {
  const labelEl = document.getElementById('ra-progress-label');
  const fileEl = document.getElementById('ra-progress-file');
  if (labelEl) labelEl.textContent = label;
  if (fileEl) fileEl.textContent = filename;
}

export function _renderRaResult(result) {
  const btn = document.getElementById('btn-ra-check');
  const progressWrap = document.getElementById('ra-progress-wrap');
  const resultEl = document.getElementById('ra-result');
  const filterRow = document.getElementById('ra-filter-row');
  const platformSelect = document.getElementById('ra-platform-filter');

  if (!resultEl) return;

  if (result.error) {
    resultEl.innerHTML = `<p style="color:var(--c-red)">Error: ${_h(result.error)}</p>`;
  } else {
    _raResults = result.results || [];
    // Sort: supported first, then alternatives, then unsupported
    _raResults.sort((a, b) => {
      const statusOrder = { 'supported': 0, 'no_support_alternative': 1, 'no_support': 2, 'no_md5': 3, 'platform_unknown': 4 };
      return (statusOrder[a.status] || 5) - (statusOrder[b.status] || 5);
    });
    _raPage = 0;

    // Populate platform filter
    if (filterRow && platformSelect && _raResults.length) {
      const platforms = [...new Set(_raResults.map(r => r.platform))].sort();
      platformSelect.innerHTML = '<option value="">Todas las plataformas</option>';
      platforms.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        platformSelect.appendChild(opt);
      });
      filterRow.classList.remove('hidden');
    }

    // Render results
    _renderRaPage();
  }

  if (btn) {
    btn.disabled = false;
    btn.textContent = 'Comprobar compatibilidad RA';
  }
  if (progressWrap) {
    progressWrap.classList.add('hidden');
  }
}

export function filterRaByPlatform() {
  _raPage = 0;
  _renderRaPage();
}

export function clearRaFilter() {
  const platformSelect = document.getElementById('ra-platform-filter');
  if (platformSelect) {
    platformSelect.value = '';
  }
  _raPage = 0;
  _renderRaPage();
}

export function _raGoToPage(page) {
  _raPage = Math.max(0, page);
  _renderRaPage();
}

function _renderRaPage() {
  const resultEl = document.getElementById('ra-result');
  const platformFilter = document.getElementById('ra-platform-filter')?.value || '';

  if (!resultEl) return;

  // Filter results by platform
  const filtered = platformFilter
    ? _raResults.filter(r => r.platform === platformFilter)
    : _raResults;

  if (!filtered.length) {
    resultEl.innerHTML = '<p style="color:var(--c-muted);font-size:12px">Sin resultados para esta plataforma.</p>';
    return;
  }

  // Summary stats
  const supported = filtered.filter(r => r.status === 'supported').length;
  const alternative = filtered.filter(r => r.status === 'no_support_alternative').length;
  const noSupport = filtered.filter(r => r.status === 'no_support').length;
  const noMd5 = filtered.filter(r => r.status === 'no_md5').length;

  let html = `<div style="margin-bottom:12px;font-size:12px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
    <div style="flex:1;min-width:300px">
      <span style="color:var(--c-teal)">✓ ${supported} compatibles</span>
      <span style="color:var(--c-amber);margin-left:8px">⚠ ${alternative} con alternativa</span>
      <span style="color:var(--c-softred);margin-left:8px">✗ ${noSupport} sin soporte</span>
      ${noMd5 > 0 ? `<span style="color:var(--c-muted);margin-left:8px">? ${noMd5} sin MD5</span>` : ''}
    </div>
    <div style="display:flex;gap:6px">
      ${noSupport > 0 ? `<button class="btn danger" style="padding:3px 8px;font-size:11px" onclick="window.discardRaNoSupport()" title="Mover ${noSupport} juegos sin soporte a _descartados/">Descartar sin soporte</button>` : ''}
      ${platformFilter ? `<button class="btn" style="padding:3px 8px;font-size:11px" onclick="window.clearRaFilter()">✕ Limpiar filtro</button>` : ''}
    </div>
  </div>`;

  // Paginate
  const start = _raPage * _RA_PAGE_SIZE;
  const end = start + _RA_PAGE_SIZE;
  const page = filtered.slice(start, end);
  const totalPages = Math.ceil(filtered.length / _RA_PAGE_SIZE);

  const totalShown = filtered.length;
  const allResults = _raResults.length;
  html += `<p style="color:var(--c-muted);font-size:11px;margin-bottom:8px">
    Mostrando ${Math.min((start + 1), totalShown)}–${Math.min(end, totalShown)} de ${totalShown}
    ${platformFilter ? `(${allResults} total)` : ''}
    — Página ${_raPage + 1}/${totalPages}
  </p>`;

  html += '<div style="max-height:420px;overflow-y:auto;border:1px solid #222;border-radius:4px">';

  // Group by status
  const groupedPage = page.reduce((acc, r) => {
    acc[r.status] = acc[r.status] || [];
    acc[r.status].push(r);
    return acc;
  }, {});

  const statusGroups = [
    { key: 'supported', label: '✓ Compatibles', color: '#1e3a2f' },
    { key: 'no_support_alternative', label: '⚠ Con alternativa', color: '#2a2a1a' },
    { key: 'no_support', label: '✗ Sin soporte', color: '#2a1a1a' },
    { key: 'no_md5', label: '? Sin MD5', color: '#1a1a1a' },
    { key: 'platform_unknown', label: '— Plataforma desconocida', color: '#1a1a1a' }
  ];

  statusGroups.forEach(group => {
    const groupResults = groupedPage[group.key] || [];
    if (!groupResults.length) return;

    html += `<div style="background:${group.color};padding:4px 6px;font-size:11px;color:var(--c-muted);border-top:1px solid #333;font-weight:600">${group.label}</div>`;

    groupResults.forEach(r => {
      const statusIcon = _raStatusIcon(r.status);
      const statusColor = _raStatusColor(r.status);
      const filename = (r.original_filename || '?').split(/[\\/]/).pop();
      const filenameNoExt = filename.replace(/\.[^.]+$/, '');
      const raTitle = r.alternative ? r.alternative.title : '—';
      const achievements = r.alternative ? (r.alternative.achievements || 0) : '—';
      const raId = r.alternative ? r.alternative.id : null;

      let row = `<div style="display:grid;grid-template-columns:20px 1fr 1fr 60px 1fr;gap:6px;padding:6px;align-items:center;border-bottom:1px solid #333;font-size:11px">
        <div style="color:${statusColor};text-align:center">${statusIcon}</div>
        <div style="color:var(--c-orange);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(r.original_filename || '')}">${_h(filename)}</div>
        <div style="color:var(--c-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_h(raTitle)}</div>
        <div style="text-align:center;color:var(--c-muted)">${achievements}</div>
        <div style="display:flex;gap:3px;justify-content:flex-end">
          <button class="btn" style="padding:1px 4px;font-size:9px" onclick="window._copyText('${filenameNoExt.replace(/'/g, "\\'")}', 'nombre')" title="Copiar nombre del juego">📋</button>
          <button class="btn" style="padding:1px 4px;font-size:9px" onclick="window._googleQuery('${filenameNoExt.replace(/'/g, "\\'")} ROM')" title="Google búsqueda">🔍</button>
          <button class="btn" style="padding:1px 4px;font-size:9px" onclick="window._openArchiveOrg('${filenameNoExt.replace(/'/g, "\\'")}', '${r.platform.replace(/'/g, "\\'")}')" title="Archive.org">📦</button>
          ${raId ? `<button class="btn" style="padding:1px 4px;font-size:9px" onclick="window._copyText('https://retroachievements.org/game/${raId}', 'link RA')" title="Copiar link RetroAchievements">🔗</button>` : ''}
        </div>`;

      if (r.status === 'no_support_alternative') {
        row += `<div style="grid-column:1/-1"><button class="btn" style="padding:2px 8px;font-size:10px;width:100%" onclick="window._raSelectAlternative(${_raResults.indexOf(r)})">✓ Usar alternativa</button></div>`;
      }

      row += `</div>`;
      html += row;
    });
  });

  html += '</div>';

  // Pagination controls
  if (totalPages > 1) {
    html += '<div style="margin-top:8px;display:flex;gap:6px;justify-content:center">';
    if (_raPage > 0) html += `<button class="btn" style="padding:2px 8px;font-size:11px" onclick="window._raGoToPage(${_raPage - 1})">← Anterior</button>`;
    if (_raPage < totalPages - 1) html += `<button class="btn" style="padding:2px 8px;font-size:11px" onclick="window._raGoToPage(${_raPage + 1})">Siguiente →</button>`;
    html += '</div>';
  }

  resultEl.innerHTML = html;
}

function _raStatusIcon(status) {
  const icons = {
    'supported': '✓',
    'no_support_alternative': '⚠',
    'no_support': '✗',
    'no_md5': '?',
    'platform_unknown': '—'
  };
  return icons[status] || '?';
}

function _raStatusColor(status) {
  const colors = {
    'supported': 'var(--c-teal)',
    'no_support_alternative': 'var(--c-amber)',
    'no_support': 'var(--c-softred)',
    'no_md5': '#888',
    'platform_unknown': '#555'
  };
  return colors[status] || '#888';
}

export async function discardRaNoSupport() {
  const noSupportGames = _raResults.filter(r => r.status === 'no_support');

  if (!noSupportGames.length) {
    showToast('No hay juegos sin soporte RA para descartar.', 'info');
    return;
  }

  // Show confirmation dialog
  if (!window._showConfirm) {
    // Fallback if confirm component not available
    const confirmed = confirm(`¿Descartar ${noSupportGames.length} juegos sin soporte RA?\n\nLos archivos se moverán a una carpeta _descartados en su ubicación actual.\nEsta acción se registrará en la base de datos.`);
    if (!confirmed) return;
  } else {
    // Use confirm modal if available
    const confirmed = await new Promise(resolve => {
      const origCallback = window._confirmCallback;
      window._confirmCallback = (result) => {
        window._confirmCallback = origCallback;
        resolve(result);
      };
      window._showConfirm(
        `¿Descartar ${noSupportGames.length} juegos sin soporte RA?`,
        'Los archivos se moverán a _descartados/. Haz una copia de seguridad si es tu primera vez.'
      );
    });
    if (!confirmed) return;
  }

  try {
    const d = await apiPost('/api/ra-check/discard-no-support', {});
    if (d.error) {
      showToast('Error: ' + d.error, 'err');
      return;
    }

    const { discarded, failed, errors } = d;
    const msg = `✓ ${discarded} descartados`;
    showToast(msg + (failed > 0 ? ` (${failed} fallos)` : ''), failed > 0 ? 'warn' : 'ok');

    // Remove discarded games from results
    _raResults = _raResults.filter(r => r.status !== 'no_support');
    _raPage = 0;
    _renderRaPage();

    // Show error details if any
    if (errors && errors.length > 0) {
      console.warn('RA discard errors:', errors);
      const errMsg = errors.slice(0, 3).join('\n');
      showToast(`⚠ Algunos errores: ${errors.length > 3 ? '...' : ''}`, 'warn');
    }
  } catch(e) {
    showToast('Error al descartar juegos: ' + e.message, 'err');
  }
}

export function _raSelectAlternative(idx) {
  // TODO: Implement in 2g-5 - allow user to swap game for alternative
}

// ── Utility Helper Functions ────────────────────────────────────────────────
export function _copyText(text, label) {
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast(`✓ Copiado${label ? ': ' + label : ''}`, 'ok');
  }).catch(() => {
    showToast('No se pudo copiar al portapapeles', 'err');
  });
}

export function _googleQuery(query) {
  if (!query) return;
  const searchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(query);
  window.open(searchUrl, '_blank');
}

export function _archiveOrgUrl(title, platform) {
  if (!title) return '';
  // Format: https://archive.org/advancedsearch.php?q=...&output=json
  // For browser, use simpler search URL
  const searchQuery = `${title} ${platform || ''} ROM`.trim();
  return 'https://archive.org/search.php?query=' + encodeURIComponent(searchQuery);
}

export function _openArchiveOrg(title, platform) {
  const url = _archiveOrgUrl(title, platform);
  if (url) {
    window.open(url, '_blank');
  }
}

export function _copyArchiveOrgLink(title, platform) {
  const url = _archiveOrgUrl(title, platform);
  if (url) {
    _copyText(url, 'Archive.org');
  }
}

// ── Health Check ──────────────────────────────────────────────────────────────
let _healthResults = null;  // HealthSummary from backend
let _healthFilter = 'all';   // Filter: 'all' | 'corrupted' | 'missing'

export async function doHealthCheck() {
  const btn = document.querySelector('[onclick="doHealthCheck()"]');
  if (btn) { btn.disabled = true; btn.textContent = 'Comprobando…'; }
  const el = document.getElementById('health-result');
  if (el) { el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Comprobando…</p>'; }

  try {
    // AUD-6: verificación profunda de CHDs (chdman verify), off por defecto
    const deepChd = document.getElementById('health-deep-chd')?.checked ?? false;
    const res = await apiPost('/api/health-check', { deep_chd: deepChd });
    if (res.job_id) {
      window.startPolling();
    }
  } catch(e) {
    showToast('Error al iniciar comprobación: ' + e.message, 'err');
    if (btn) { btn.disabled = false; btn.textContent = 'Iniciar Health Check'; btn.onclick = window.doHealthCheck; }
  }
}

export function _renderHealthResult(summary) {
  const el = document.getElementById('health-result');
  if (!el) return;

  _healthResults = summary;
  _healthFilter = 'all';

  const btn = document.querySelector('[onclick="doHealthCheck()"]');
  if (btn) { btn.disabled = false; btn.textContent = 'Iniciar Health Check'; btn.onclick = window.doHealthCheck; }

  if (!summary || !summary.results) {
    el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Sin resultados.</p>';
    return;
  }

  _renderHealthPage();
}

function _renderHealthPage() {
  const resultEl = document.getElementById('health-result');
  if (!resultEl) return;

  const filterVal = _healthFilter;
  const filtered = _filterHealthIssues(_healthResults.results, filterVal);

  if (!filtered.length && filterVal !== 'all') {
    resultEl.innerHTML = '<p style="color:var(--c-muted);font-size:12px">Sin problemas encontrados en este filtro.</p>';
    return;
  }

  // Summary stats
  const ok = _healthResults.ok || 0;
  const corrupted = _healthResults.corrupted || 0;
  const missing = _healthResults.missing || 0;
  const chdInvalid = _healthResults.chd_invalid || 0;
  const total = ok + corrupted + missing + chdInvalid;

  let html = `<div style="margin-bottom:12px;font-size:12px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
    <div style="flex:1;min-width:300px">
      <span style="color:var(--c-teal)">✓ ${ok} correctos</span>
      <span style="color:var(--c-softred);margin-left:8px">⚠ ${corrupted} corruptos</span>
      <span style="color:var(--c-softred);margin-left:8px">✗ ${missing} perdidos</span>
      ${chdInvalid ? `<span style="color:var(--c-softred);margin-left:8px">&#x1F4BF; ${chdInvalid} CHDs inválidos</span>` : ''}
    </div>
    <div style="display:flex;gap:6px">
      ${filterVal !== 'all' ? `<button class="btn" style="padding:3px 8px;font-size:11px" onclick="window._clearHealthFilter()">✕ Limpiar filtro</button>` : ''}
    </div>
  </div>`;

  html += `<p style="color:var(--c-muted);font-size:11px;margin-bottom:8px">
    ${filtered.length > 0 ? `${filtered.length} problemas encontrados de ${total}` : 'Biblioteca en buen estado'}
  </p>`;

  if (filtered.length === 0) {
    html += '<p style="color:var(--c-teal);font-size:12px">✓ No se encontraron problemas</p>';
    resultEl.innerHTML = html;
    return;
  }

  html += '<div style="max-height:420px;overflow-y:auto;border:1px solid #222;border-radius:4px">';

  // Group by status
  const groupedIssues = filtered.reduce((acc, r) => {
    acc[r.status] = acc[r.status] || [];
    acc[r.status].push(r);
    return acc;
  }, {});

  const statusGroups = [
    { key: 'corrupted', label: '⚠ Corruptos (SHA1 no coincide)', color: '#2a1a1a' },
    { key: 'missing', label: '✗ Perdidos (archivo no encontrado)', color: '#2a1a1a' },
    { key: 'chd_invalid', label: '💿 CHDs inválidos (chdman verify falló — checksums internos)', color: '#2a1a1a' }
  ];

  statusGroups.forEach(group => {
    const groupResults = groupedIssues[group.key] || [];
    if (!groupResults.length) return;

    html += `<div style="background:${group.color};padding:4px 6px;font-size:11px;color:var(--c-muted);border-top:1px solid #333;font-weight:600">${group.label}</div>`;

    groupResults.forEach(r => {
      html += _healthIssueRow(r);
    });
  });

  html += '</div>';
  resultEl.innerHTML = html;
}

export function _healthIssueRow(result) {
  const filename = (result.source_path || '?').split(/[\\/]/).pop();
  const platformStr = result.platform || 'Desconocida';
  const titleStr = result.canonical_title || filename;

  let html = `<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:6px;align-items:center;border-bottom:1px solid #333;font-size:11px">
    <div style="color:var(--c-orange);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(result.source_path || '')}">${_h(filename)}</div>
    <div style="color:var(--c-muted)">${_h(platformStr)}</div>
    <div style="color:var(--c-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(titleStr)}">${_h(titleStr)}</div>`;

  if (result.status === 'corrupted') {
    html += `<div style="grid-column:1/-1;font-size:10px;color:var(--c-muted)">
      <div>Esperado: <code style="color:var(--c-orange);font-size:9px">${_h(result.stored_sha1)}</code></div>
      <div>Actual: <code style="color:var(--c-softred);font-size:9px">${_h(result.computed_sha1 || '—')}</code></div>
    </div>`;
  }

  html += `</div>`;
  return html;
}

export function _filterHealthIssues(issues, filter) {
  if (!issues) return [];
  if (filter === 'all') return issues;
  return issues.filter(r => r.status === filter);
}

export function _clearHealthFilter() {
  _healthFilter = 'all';
  _renderHealthPage();
}

export async function loadOperationsTimeline() {
  const el = document.getElementById('operations-timeline-content');
  if (!el) return;
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Cargando…</p>';

  try {
    // TODO: Implement when /api/operations-timeline endpoint is available
    const d = await apiFetch('/api/operations-timeline');
    let html = '<ul style="font-size:12px;color:var(--c-muted);list-style:none;padding:0">';
    if (d.operations && d.operations.length) {
      d.operations.forEach(op => {
        const ts = new Date(op.timestamp).toLocaleString();
        html += `<li style="padding:6px;border-bottom:1px solid #222">
          <div style="color:var(--c-teal)">${_h(op.action)}</div>
          <div style="font-size:11px;color:var(--c-hint)">${ts}</div>
          ${op.details ? `<div style="font-size:11px;color:var(--c-muted)">${_h(op.details)}</div>` : ''}
        </li>`;
      });
    } else {
      html += '<li style="padding:6px;color:var(--c-hint)">Sin operaciones registradas</li>';
    }
    html += '</ul>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-muted);font-size:12px">Funcionalidad pendiente: Línea de tiempo de operaciones</p>`;
  }
}

// ── Junk Scan ─────────────────────────────────────────────────────────────────
let _junkResults = null;          // último resultado de /api/junk-scan
let _junkSelected = new Set();    // índices de categorías seleccionadas

export async function doJunkScan() {
  const btn = document.getElementById('btn-junk-scan');
  const el = document.getElementById('junk-result');
  if (!el) return;
  if (btn) { btn.disabled = true; btn.textContent = 'Buscando…'; }
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Buscando archivos innecesarios…</p>';

  try {
    const path = document.getElementById('junk-path')?.value.trim() || '';
    const res = await apiPost('/api/junk-scan', { path });
    _renderJunkResult(res);
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`;
    showToast('Error en búsqueda de basura: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Escanear archivos basura'; }
  }
}

export function _renderJunkResult(result) {
  const el = document.getElementById('junk-result');
  if (!el) return;

  if (result.error) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">${_h(result.error)}</p>`;
    return;
  }

  _junkResults = result;
  _junkSelected = new Set();

  const cats = result.categories || [];
  if (!cats.length) {
    el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ No se encontraron archivos basura.</p>';
    return;
  }

  let html = `<div style="margin-bottom:10px;font-size:12px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
    <div style="flex:1;min-width:260px">
      <span style="color:var(--c-softred)">⚠ ${result.total_junk_files} archivos basura</span>
      <span style="color:var(--c-muted);margin-left:8px">${_fmtSize(result.total_junk_bytes)} recuperables</span>
      <span style="color:var(--c-hint);font-size:11px;margin-left:8px">en <code style="color:var(--c-orange)">${_h(result.folder)}</code></span>
    </div>
    <div style="display:flex;gap:6px">
      <button class="btn" style="padding:3px 8px;font-size:11px" onclick="window.junkSelectAll()">Seleccionar todo</button>
      <button id="btn-junk-delete" class="btn danger" style="padding:3px 8px;font-size:11px" disabled onclick="window.junkDelete()">Eliminar seleccionados</button>
      ${_junkHasRoutable(cats) ? '<button id="btn-zip-route" class="btn" style="padding:3px 8px;font-size:11px;background:var(--c-teal);color:#000" onclick="window.zipRouteApply()">Organizar identificados (1 paso)</button>' : ''}
    </div>
  </div>`;

  html += '<div style="max-height:420px;overflow-y:auto;border:1px solid #222;border-radius:4px">';
  cats.forEach((c, i) => {
    const shown = c.files || [];
    // JUNK-SMART-3: solo safe_delete es seleccionable de entrada; review exige
    // expandir "Ver archivos" antes; misplaced (mover, no borrar) nunca
    const conf = c.confidence || 'safe_delete';
    const badge = conf === 'review'
      ? '<span style="font-size:10px;padding:1px 6px;border-radius:3px;background:var(--c-amber);color:#000">revisar</span>'
      : conf === 'misplaced'
        ? '<span style="font-size:10px;padding:1px 6px;border-radius:3px;background:var(--c-teal);color:#000">no borrar — mover</span>'
        : '';
    const cbAttrs = conf === 'misplaced'
      ? 'disabled title="No es basura: hay que mover/organizar estos archivos"'
      : conf === 'review'
        ? 'disabled data-review="1" title="Abre \'Ver archivos\' para poder seleccionar"'
        : '';
    html += `<div style="border-bottom:1px solid #222">
      <div style="display:flex;gap:8px;align-items:center;padding:6px;background:var(--c-panel)">
        <input type="checkbox" id="junk-cat-cb-${i}" ${cbAttrs} onchange="window.junkToggleCat(${i})">
        <label for="junk-cat-cb-${i}" style="flex:1;font-size:12px;font-weight:600;color:var(--c-amber);cursor:pointer">${_h(c.category)}</label>
        ${badge}
        <span style="font-size:11px;color:var(--c-muted)">${c.count} archivos · ${_fmtSize(c.total_bytes)}</span>
      </div>
      <details style="padding:0 6px 4px 26px" ${conf === 'review' ? `ontoggle="window.junkRevealCat(${i})"` : ''}>
        <summary style="font-size:11px;color:var(--c-hint);cursor:pointer">Ver archivos${c.count > shown.length ? ` (${shown.length} mayores de ${c.count})` : ''}</summary>
        ${shown.map(f => `<div style="font-size:11px;padding:2px 0;display:flex;gap:8px">
          <code style="color:var(--c-orange);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(f.full_path)}">${_h(f.path)}</code>
          ${f.identified_as || f.platform ? `<span style="color:var(--c-teal);flex-shrink:0" title="Identidad detectada por CRC/extensión">→ ${_h(f.identified_as || '')}${f.platform ? ` [${_h(f.platform)}]` : ''}${f.coverage != null ? ` (${Math.round(f.coverage * 100)}%)` : ''}</span>` : ''}
          <span style="color:var(--c-dim);flex-shrink:0">${_fmtSize(f.size_bytes)}</span>
        </div>`).join('')}
      </details>
    </div>`;
  });
  html += '</div>';
  el.innerHTML = html;
}

// ZIP-ROUTE-4: hay algo que organizar en un paso si el scan identificó
// arcade/consola/romhacks/colecciones (misplaced con destino o colección)
const _ZIP_ROUTE_CATS = [
  'ROMs arcade identificadas (renombrar al set y mover)',
  'ROMs arcade sin organizar (no borrar)',
  'ROMs de consola identificadas (mover a su plataforma)',
  'ROMs/romhacks por extensión (mover a su plataforma)',
  'Colecciones fuente (revisar)',
];

function _junkHasRoutable(cats) {
  return cats.some(c => _ZIP_ROUTE_CATS.includes(c.category));
}

export async function zipRouteApply() {
  const cats = _junkResults?.categories || [];
  const routable = cats.filter(c => _ZIP_ROUTE_CATS.includes(c.category));
  const total = routable.reduce((n, c) => n + c.count, 0);
  const lines = routable.map(c => `· ${c.category}: ${c.count}`).join('\n');
  if (!confirm(`Se organizarán ${total} ZIPs en un solo paso:\n${lines}\n\n` +
    'Arcade → arcade\\ (renombrando al set), colecciones extraídas, el resto ' +
    'pasa por el Inbox (emparejar → renombrar → mover) y el Inbox queda limpio.\n' +
    'Nada se sobreescribe: los conflictos se reportan.')) return;
  const btn = document.getElementById('btn-zip-route');
  if (btn) { btn.disabled = true; btn.textContent = 'Organizando…'; }
  try {
    const path = document.getElementById('junk-path')?.value.trim() || '';
    const res = await apiPost('/api/zip-route-apply', { path });
    if (res.status === 'already_running') {
      showToast('Ya hay un proceso de Inbox en marcha', 'err');
    } else {
      showToast('Organización en marcha — progreso en la pestaña Inbox', 'ok');
      if (typeof window.startPolling === 'function') window.startPolling();
    }
  } catch (e) {
    showToast('Error al organizar: ' + e.message, 'err');
    if (btn) { btn.disabled = false; btn.textContent = 'Organizar identificados (1 paso)'; }
  }
}

function _updateJunkDeleteBtn() {
  const btn = document.getElementById('btn-junk-delete');
  if (!btn || !_junkResults) return;
  const cats = _junkResults.categories || [];
  let files = 0, bytes = 0;
  _junkSelected.forEach(i => {
    const c = cats[i];
    if (c) { files += c.count; bytes += c.total_bytes; }
  });
  btn.disabled = files === 0;
  btn.textContent = files ? `Eliminar seleccionados (${files} · ${_fmtSize(bytes)})` : 'Eliminar seleccionados';
}

export function junkToggleCat(idx) {
  if (_junkSelected.has(idx)) _junkSelected.delete(idx);
  else _junkSelected.add(idx);
  _updateJunkDeleteBtn();
}

export function junkSelectAll() {
  // JUNK-SMART-3: "Seleccionar todo" solo toca las categorías habilitadas
  // (safe_delete + las review ya reveladas); misplaced queda siempre fuera
  const cats = _junkResults?.categories || [];
  const selectable = cats.map((_, i) => i).filter(i => {
    const cb = document.getElementById(`junk-cat-cb-${i}`);
    return cb && !cb.disabled;
  });
  const allSelected = selectable.length > 0 && selectable.every(i => _junkSelected.has(i));
  _junkSelected = allSelected ? new Set() : new Set(selectable);
  selectable.forEach(i => {
    const cb = document.getElementById(`junk-cat-cb-${i}`);
    if (cb) cb.checked = !allSelected;
  });
  _updateJunkDeleteBtn();
}

export function junkRevealCat(idx) {
  // El usuario ha abierto "Ver archivos" de una categoría review → ya puede seleccionarla
  const cb = document.getElementById(`junk-cat-cb-${idx}`);
  if (cb && cb.disabled && cb.dataset.review) {
    cb.disabled = false;
    cb.title = '';
  }
}

export function junkCatCheck(idx) {
  return _junkSelected.has(idx);
}

export async function junkDelete() {
  const cats = _junkResults?.categories || [];
  const paths = [];
  _junkSelected.forEach(i => { if (cats[i]) paths.push(...(cats[i].paths || [])); });
  if (!paths.length) {
    showToast('No hay categorías seleccionadas', 'warn');
    return;
  }

  const reviewCats = [..._junkSelected].filter(i => (cats[i]?.confidence) === 'review');
  const reviewWarn = reviewCats.length
    ? `\n\n⚠ Incluye ${reviewCats.length} categoría(s) marcadas "revisar" — comprueba la lista antes.`
    : '';
  if (!confirm(`¿Eliminar ${paths.length} archivos de ${_junkSelected.size} categoría(s)?${reviewWarn}\n\nEsta acción no se puede deshacer.`)) return;

  const btn = document.getElementById('btn-junk-delete');
  if (btn) { btn.disabled = true; btn.textContent = 'Eliminando…'; }

  try {
    const d = await apiPost('/api/junk-delete', { paths, dry_run: false });
    showToast(`✓ ${d.deleted} eliminados · ${_fmtSize(d.freed_bytes)} liberados` + (d.failed ? ` (${d.failed} fallos)` : ''), d.failed ? 'warn' : 'ok');
    if (d.errors && d.errors.length) console.warn('junk-delete errors:', d.errors);
    doJunkScan();  // re-escanear para refrescar la lista
  } catch(e) {
    showToast('Error al eliminar: ' + e.message, 'err');
    if (btn) { btn.disabled = false; _updateJunkDeleteBtn(); }
  }
}

// ── Orphaned Saves ────────────────────────────────────────────────────────────
let _orphanedSaves = [];

function _renderOrphansResult(orphans) {
  const el = document.getElementById('orphan-result');
  if (!el) return;
  _orphanedSaves = orphans.saves.map(s => s.path);

  if (!orphans.total) {
    el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ No hay saves huérfanos.</p>';
    return;
  }

  let html = `<div style="margin-bottom:10px;font-size:12px;color:var(--c-softred)">⚠ ${orphans.total} save(s) huérfano(s) — ${_fmtSize(orphans.total_bytes)} recuperables</div>`;
  html += `<div class="actions-row" style="margin-bottom:10px">
    <button class="btn danger" onclick="doDeleteOrphans()">Eliminar todos</button>
    <button class="btn" onclick="doMoveOrphansToArchive()">Archivar a _huerfanos</button>
  </div>`;
  html += '<div style="max-height:300px;overflow-y:auto;font-size:11px">';
  html += orphans.saves.map(s => `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
    ${_h(s.path.split(/[\\/]/).pop())} <span style="color:var(--c-dim)">(${_fmtSize(s.size_bytes)})</span>
    <div style="font-size:10px;color:var(--c-hint)">${_h(s.path)}</div>
  </div>`).join('');
  html += '</div>';
  el.innerHTML = html;
}

export async function doFindOrphans() {
  const path = document.getElementById('orphan-path')?.value.trim();
  const el = document.getElementById('orphan-result');
  if (!el) return;
  if (!path) { showToast('Introduce la carpeta de la biblioteca', 'err'); return; }
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Buscando saves huérfanos…</p>';

  try {
    // HERR-UX-2: /api/library-report ya calcula orphans — reutilizarlo en vez
    // de un endpoint dedicado que nunca se implementó.
    const d = await apiFetch('/api/library-report?source_path=' + encodeURIComponent(path));
    if (d.error) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">${_h(d.error)}</p>`; return; }
    _renderOrphansResult(d.orphans);
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`;
  }
}

export async function doDeleteOrphans() {
  if (!_orphanedSaves.length) {
    showToast('No hay saves huérfanos para eliminar', 'warn');
    return;
  }

  if (!confirm(`¿Eliminar ${_orphanedSaves.length} saves huérfanos?`)) return;

  try {
    const d = await apiPost('/api/orphaned-saves/delete', { paths: _orphanedSaves });
    showToast(`✓ Eliminados: ${d.deleted || 0}, Errores: ${d.failed || 0}`, 'ok');
    _orphanedSaves = [];
    const el = document.getElementById('orphan-result');
    if (el) el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ Eliminados</p>';
  } catch(e) {
    showToast('Error al eliminar: ' + e.message, 'err');
  }
}

export async function doMoveOrphansToArchive() {
  if (!_orphanedSaves.length) {
    showToast('No hay saves huérfanos para archivar', 'warn');
    return;
  }

  try {
    // HERR-UX-2: window.AppState no tiene .config (solo activeDevice/devName,
    // state.js:57) — esto hacía fallar SIEMPRE con "Biblioteca no configurada".
    const cfg = await apiFetch('/api/config');
    const libraryRoot = cfg.library_root || '';
    if (!libraryRoot) {
      showToast('Biblioteca no configurada', 'err');
      return;
    }

    const d = await apiPost('/api/orphaned-saves/move-to-archive', {
      paths: _orphanedSaves,
      library_root: libraryRoot
    });
    showToast(`✓ Archivados: ${d.moved || 0}, Errores: ${d.failed || 0}`, 'ok');
    _orphanedSaves = [];
    const el = document.getElementById('orphan-result');
    if (el) el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ Movidos a _huerfanos</p>';
  } catch(e) {
    showToast('Error al archivar: ' + e.message, 'err');
  }
}

export async function moveOrphanedSave(path, gameDir) {
  if (!path || !gameDir) {
    showToast('Ruta inválida', 'err');
    return;
  }

  try {
    const d = await apiPost('/api/orphaned-saves/move', {
      save_path: path,
      game_path: gameDir
    });
    showToast('✓ Save movido correctamente', 'ok');
    // Remove from list
    _orphanedSaves = _orphanedSaves.filter(p => p !== path);
  } catch(e) {
    showToast('Error al mover: ' + e.message, 'err');
  }
}

// ── Library Doctor ────────────────────────────────────────────────────────────
let _doctorIssues = [];

export async function doLibraryDoctor() {
  const el = document.getElementById('library-doctor-result');
  if (!el) return;
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Analizando…</p>';

  try {
    const d = await apiFetch('/api/library-doctor');
    if (d.error) { el.innerHTML = `<p class="error-msg">${_h(d.error)}</p>`; return; }
    if (d.total === 0) {
      el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ Biblioteca sana — no se encontraron problemas.</p>';
      return;
    }

    const sev = { error: 'var(--c-red)', warning: 'var(--c-orange)', info: '#555' };
    const icon = { misplaced_rom: '📁', incomplete_cue: '✗', empty_dir: '📂' };
    const label = { misplaced_rom: 'ROM mal ubicado', incomplete_cue: 'Set CUE incompleto', empty_dir: 'Carpeta vacía' };

    let html = `<div style="margin-bottom:10px;display:flex;gap:12px;flex-wrap:wrap;font-size:12px">`;
    for (const [type, count] of Object.entries(d.by_type || {})) {
      const s = sev[{misplaced_rom:'warning',incomplete_cue:'error',empty_dir:'info'}[type]||'info'];
      html += `<span style="color:${s}">${icon[type]||'·'} ${count} ${label[type]||type}</span>`;
    }
    html += `</div>`;
    html += '<div style="max-height:420px;overflow-y:auto">';
    html += '<table style="font-size:11px;width:100%;border-collapse:collapse"><thead><tr>';
    html += '<th style="text-align:left;padding:3px 6px;color:var(--c-dim);border-bottom:1px solid #222">Tipo</th>';
    html += '<th style="text-align:left;padding:3px 6px;color:var(--c-dim);border-bottom:1px solid #222">Archivo</th>';
    html += '<th style="text-align:left;padding:3px 6px;color:var(--c-dim);border-bottom:1px solid #222">Acción sugerida</th>';
    html += '<th style="padding:3px 6px;border-bottom:1px solid #222"></th>';
    html += '</tr></thead><tbody>';

    _doctorIssues = d.issues;
    for (let i = 0; i < d.issues.length; i++) {
      const iss = d.issues[i];
      const c = sev[iss.severity] || '#888';
      let actionBtn = '';
      if (iss.type === 'misplaced_rom') {
        actionBtn = `<button class="btn" style="font-size:10px;padding:2px 6px;min-height:unset" onclick="window.doctorMoveRom(${i})">Mover</button>`;
      } else if (iss.type === 'empty_dir') {
        actionBtn = `<button class="btn danger" style="font-size:10px;padding:2px 6px;min-height:unset" onclick="window.doctorDeleteDir(${i})">Eliminar</button>`;
      }
      html += `<tr id="doctor-row-${i}" style="border-bottom:1px solid #1a1a1a">`;
      html += `<td style="padding:3px 6px;color:${c};white-space:nowrap">${icon[iss.type]||''} ${label[iss.type]||iss.type}</td>`;
      html += `<td style="padding:3px 6px;color:var(--c-orange);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_h(iss.path)}">${_h(iss.file)}</td>`;
      html += `<td style="padding:3px 6px;color:var(--c-dim)">${_h(iss.action||'')}${iss.missing_bins ? ' (' + iss.missing_bins.map(_h).join(', ') + ')' : ''}</td>`;
      html += `<td style="padding:3px 6px">${actionBtn}</td>`;
      html += `</tr>`;
    }
    html += '</tbody></table></div>';
    if (d.total > 200) html += `<p style="color:var(--c-dim);font-size:11px;margin-top:6px">… y ${d.total - 200} más</p>`;
    el.innerHTML = html;

    const hasActionable = d.issues.some(iss => iss.type === 'misplaced_rom' || iss.type === 'empty_dir');
    const resolveBtn = document.getElementById('btn-doctor-resolve-all');
    if (resolveBtn) { resolveBtn.classList.toggle('hidden', !hasActionable); }
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`;
  }
}

export async function doctorMoveRom(idx) {
  const iss = _doctorIssues[idx];
  if (!iss) return;
  const row = document.getElementById('doctor-row-' + idx);

  try {
    const d = await apiPost('/api/doctor-move-rom', { path: iss.path, expected_dir: iss.expected_dir });
    if (d.error) {
      showToast('Error al mover: ' + d.error, 'err');
    } else {
      showToast('✓ ROM movido correctamente', 'ok');
      if (row) row.style.opacity = '0.5';
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  }
}

export async function doctorDeleteDir(idx) {
  const iss = _doctorIssues[idx];
  if (!iss) return;
  const row = document.getElementById('doctor-row-' + idx);

  if (!confirm(`¿Eliminar "${iss.file}"?`)) return;

  try {
    const d = await apiPost('/api/doctor-delete-dir', { path: iss.path });
    if (d.error) {
      showToast('Error al eliminar: ' + d.error, 'err');
    } else {
      showToast('✓ Carpeta eliminada', 'ok');
      if (row) row.style.opacity = '0.5';
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  }
}

export async function doctorResolveAll() {
  const actionable = _doctorIssues.filter(iss => iss.type === 'misplaced_rom' || iss.type === 'empty_dir');
  if (!actionable.length) {
    showToast('Sin problemas para resolver', 'warn');
    return;
  }

  if (!confirm(`¿Resolver ${actionable.length} problemas automáticamente?`)) return;

  const btn = document.getElementById('btn-doctor-resolve-all');
  if (btn) btn.disabled = true;

  let ok = 0, failed = 0;
  for (let i = 0; i < _doctorIssues.length; i++) {
    const iss = _doctorIssues[i];
    const row = document.getElementById('doctor-row-' + i);

    try {
      let d;
      if (iss.type === 'misplaced_rom') {
        d = await apiPost('/api/doctor-move-rom', {
          path: iss.path,
          expected_dir: iss.expected_dir
        });
      } else if (iss.type === 'empty_dir') {
        d = await apiPost('/api/doctor-delete-dir', { path: iss.path });
      } else {
        continue;
      }
      if (!d.error) { ok++; if (row) row.style.opacity = '0.5'; } else { failed++; }
    } catch(e) {
      failed++;
      console.warn('Error resolving issue:', e);
    }
  }

  // HERR-UX-8: contar ok/fallos reales y recargar el panel con datos frescos
  // del servidor, en vez de un toast fijo que ignora los errores.
  showToast(failed ? `${ok} resueltos, ${failed} con error` : `✓ ${ok} resueltos`, failed ? 'warn' : 'ok');
  await doLibraryDoctor();
}

export async function doFolderAnalysis() {
  const path = document.getElementById('folder-analysis-path')?.value.trim();
  const el = document.getElementById('folder-analysis-result');
  if (!el) return;
  if (!path) { showToast('Introduce la ruta de la carpeta a analizar', 'err'); return; }
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Analizando…</p>';

  try {
    const d = await apiPost('/api/folder-analysis', { source_path: path });
    if (d.error) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">${_h(d.error)}</p>`; return; }

    let html = '';

    // ── Extensiones encontradas ────────────────────────────────────────────
    const extensions = d.extensions || [];
    html += `<details style="margin-bottom:10px" open><summary style="cursor:pointer;color:var(--c-hint);font-size:12px">Extensiones encontradas (${extensions.length})</summary>`;
    if (extensions.length) {
      html += '<div style="max-height:180px;overflow-y:auto;margin-top:6px">';
      html += extensions.map(e => `<div style="display:flex;justify-content:space-between;font-size:12px;padding:2px 0;border-bottom:1px solid var(--c-panel)"><span style="color:var(--c-text)">${_h(e.ext)}</span><span style="color:var(--c-dim)">${e.count}</span></div>`).join('');
      html += '</div>';
    } else {
      html += '<p style="color:var(--c-dim);font-size:12px;margin:6px 0 0">Carpeta vacía.</p>';
    }
    html += '</details>';

    // ── Sets PSX con .bin faltante ─────────────────────────────────────────
    const psxIncomplete = d.psx_incomplete || [];
    html += `<details style="margin-bottom:10px"${psxIncomplete.length ? ' open' : ''}><summary style="cursor:pointer;color:var(--c-hint);font-size:12px">Sets PSX con .bin faltante (${psxIncomplete.length})</summary>`;
    if (psxIncomplete.length) {
      html += '<div style="max-height:180px;overflow-y:auto;margin-top:6px">';
      html += psxIncomplete.map(p => `<div style="font-size:12px;padding:3px 0;border-bottom:1px solid var(--c-panel)">
        <span style="color:var(--c-text)">${_h(p.cue)}</span>
        <div style="color:var(--c-red);font-size:11px;padding-left:8px">${p.errors.map(_h).join(', ')}</div>
      </div>`).join('');
      html += '</div>';
    } else {
      html += '<p style="color:var(--c-teal);font-size:12px;margin:6px 0 0">✓ Todos los sets .cue tienen sus .bin.</p>';
    }
    html += '</details>';

    // ── Formatos que necesitan conversión ──────────────────────────────────
    const n64Pending = d.n64_pending || [];
    const needsConversion = n64Pending.length + (d.cso_count || 0) + (d.zip_count || 0);
    html += `<details${needsConversion ? ' open' : ''}><summary style="cursor:pointer;color:var(--c-hint);font-size:12px">Formatos que necesitan conversión (${needsConversion})</summary>`;
    if (needsConversion) {
      html += '<div style="margin-top:6px;font-size:12px">';
      if (n64Pending.length) {
        html += `<div style="margin-bottom:6px"><strong>${n64Pending.length}</strong> ROM(s) N64 sin convertir a .z64:</div>`;
        html += '<div style="max-height:120px;overflow-y:auto;margin-bottom:8px">';
        html += n64Pending.map(r => `<div style="padding:2px 0;color:var(--c-text)"><span style="color:var(--c-amber)">${_h(r.format.toUpperCase())}</span> ${_h(r.filename)}</div>`).join('');
        html += '</div>';
      }
      if (d.cso_count) html += `<div>${d.cso_count} archivo(s) .cso/.zso — usa "CSO / ZSO → ISO" para convertirlos.</div>`;
      if (d.zip_count) html += `<div>${d.zip_count} archivo(s) .zip — usa "Descomprimir ZIPs" si tu emulador no los soporta.</div>`;
      html += '</div>';
    } else {
      html += '<p style="color:var(--c-teal);font-size:12px;margin:6px 0 0">✓ No se encontraron formatos pendientes de conversión.</p>';
    }
    html += '</details>';

    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`;
  }
}

// ── Unmatched Games ───────────────────────────────────────────────────────────
export async function loadUnmatchedDiagnosis() {
  const el = document.getElementById('unmatched-result');
  if (!el) return;
  el.innerHTML = '<span style="color:var(--c-dim);font-size:12px">Analizando biblioteca…</span>';

  try {
    const d = await apiFetch('/api/unmatched-by-platform');
    const total = d.total_unmatched || 0;
    const platforms = d.platforms || [];

    if (total === 0) {
      el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ Todos los juegos están identificados. No es necesario descargar catálogos.</p>';
      return;
    }

    let html = `<div style="margin-bottom:10px;font-size:12px;color:var(--c-softred)">⚠ ${total} juego(s) sin identificar en ${platforms.length} plataforma(s)</div>`;
    html += '<div style="max-height:180px;overflow-y:auto;border:1px solid #222;border-radius:4px;margin-bottom:12px">';
    platforms.forEach(plat => {
      const examples = (plat.examples || []).slice(0, 3);
      html += `<div style="background:var(--c-panel);padding:6px 10px;border-bottom:1px solid #222">
        <span style="font-weight:600;color:var(--c-amber)">${_h(plat.platform)}</span>
        <span style="color:var(--c-muted);font-size:11px;margin-left:6px">(${plat.count})</span>
        <div style="font-size:11px;color:var(--c-hint);margin-top:2px">${examples.map(f => '• ' + _h(f)).join('<br>')}</div>
      </div>`;
    });
    html += '</div>';
    // HERR-UX-5: diagnóstico puro — la descarga es un paso aparte, explícito
    html += `<div class="actions-row">
      <button class="btn primary" id="btn-download-missing-dats" onclick="downloadMissingDats()">Descargar catálogos que faltan (${platforms.length})</button>
    </div>
    <div id="unmatched-dl-info" style="font-size:12px;color:var(--c-muted);margin-top:8px"></div>
    <div class="hidden" id="unmatched-dl-bar-wrap" style="background:var(--c-border);border-radius:4px;height:8px;margin:6px 0 0;overflow:hidden">
      <div id="unmatched-dl-bar" style="height:100%;width:0%;background:var(--accent-blue);transition:width 0.3s"></div>
    </div>`;
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`;
  }
}

export async function downloadMissingDats() {
  const btn = document.getElementById('btn-download-missing-dats');
  const infoEl = () => document.getElementById('unmatched-dl-info');
  const barWrap = document.getElementById('unmatched-dl-bar-wrap');
  if (btn) { btn.disabled = true; btn.textContent = 'Descargando…'; }
  if (barWrap) barWrap.classList.remove('hidden');
  if (infoEl()) infoEl().textContent = 'Iniciando descarga de catálogos…';

  try {
    const r = await apiPost('/api/download-dats', { all: true });
    if (r.error) { infoEl().textContent = '❌ ' + r.error; if (btn) { btn.disabled = false; btn.textContent = 'Reintentar descarga'; } return; }
    if (r.status === 'already_running') { infoEl().textContent = 'Ya hay una descarga en curso…'; return; }

    const _poll = setInterval(async () => {
      try {
        const s = await apiFetch('/api/download-dats-status');
        const info = infoEl();
        const bar  = document.getElementById('unmatched-dl-bar');
        if (!info) { clearInterval(_poll); return; }
        if (s.running) {
          const pct = s.total > 0 ? Math.round((s.done / s.total) * 100) : 0;
          if (bar) bar.style.width = pct + '%';
          info.textContent = `Descargando… ${s.done}/${s.total} — ${s.current}`;
          return;
        }
        clearInterval(_poll);
        if (bar) bar.style.width = '100%';
        const res  = s.result || {};
        const ok   = (res.downloaded || []).length;
        const skip = (res.skipped   || []).length;
        const err  = (res.errors    || []).length;
        info.innerHTML = `✅ ${ok} catálogos descargados, ${skip} ya existían` + (err ? `, ❌ ${err} errores` : '') +
          ` &nbsp;·&nbsp; <a href="#" onclick="showTab('overview');setTimeout(()=>{const el=document.getElementById('btn-match');if(el)el.scrollIntoView({behavior:'smooth'})},350);return false" style="color:var(--c-blue)">Ir a Identificar →</a>`;
        info.style.color = 'var(--c-teal)';
        if (btn) { btn.disabled = false; btn.textContent = '✓ Catálogos descargados'; }
      } catch(e) {
        clearInterval(_poll);
        const info = infoEl();
        if (info) { info.textContent = '❌ ' + e.message; info.style.color = 'var(--c-softred)'; }
        if (btn) { btn.disabled = false; btn.textContent = 'Reintentar descarga'; }
      }
    }, 1000);
  } catch(e) {
    infoEl().textContent = '❌ ' + e.message;
    if (btn) { btn.disabled = false; btn.textContent = 'Reintentar descarga'; }
  }
}

// ── Library Report ────────────────────────────────────────────────────────────
// HERR-UX-1: el HTML real (tab-tools.html) tiene 6 sub-pestañas — zips,
// playlists, multidisc, orphans, ra, chd — respaldadas por /api/library-report
// (zips/playlists/multidisc/orphans, calculados por _build_library_report) y
// por los resultados cacheados de los jobs de RA/CHD (retroachievements/chd,
// misma fuente que ya usa el informe HTML exportable server-side,
// utils/library_report_html.py).
let _reportData = null;
let _reportTab = 'zips';
const _RPT_TABS = ['zips', 'playlists', 'multidisc', 'orphans', 'ra', 'chd'];

export async function generateReport() {
  const path = document.getElementById('report-path')?.value.trim();
  const loadingEl = document.getElementById('report-loading');
  const notAccessibleEl = document.getElementById('report-not-accessible');
  const contentEl = document.getElementById('report-content');
  if (!contentEl) return;

  contentEl.classList.add('hidden');
  if (notAccessibleEl) notAccessibleEl.classList.add('hidden');
  if (loadingEl) loadingEl.classList.remove('hidden');

  try {
    const qs = path ? '?path=' + encodeURIComponent(path) : '';
    const d = await apiFetch('/api/library-report' + qs);
    if (loadingEl) loadingEl.classList.add('hidden');
    if (d.error) {
      if (notAccessibleEl) { notAccessibleEl.textContent = d.error; notAccessibleEl.classList.remove('hidden'); }
      return;
    }
    if (!d.path_accessible) {
      if (notAccessibleEl) { notAccessibleEl.textContent = `Carpeta no accesible: ${d.source_path}`; notAccessibleEl.classList.remove('hidden'); }
      return;
    }
    _reportData = d;
    const exportBtn = document.getElementById('btn-export-report');
    if (exportBtn) exportBtn.classList.remove('hidden');
    contentEl.classList.remove('hidden');
    showReportTab(_reportTab);
  } catch(e) {
    if (loadingEl) loadingEl.classList.add('hidden');
    if (notAccessibleEl) { notAccessibleEl.textContent = 'Error: ' + e.message; notAccessibleEl.classList.remove('hidden'); }
  }
}

export function showReportTab(tab) {
  if (!_reportData || !_RPT_TABS.includes(tab)) return;
  _reportTab = tab;

  for (const t of _RPT_TABS) {
    document.getElementById(`rpt-tab-btn-${t}`)?.classList.toggle('active', t === tab);
    document.getElementById(`rpt-tab-${t}`)?.classList.toggle('hidden', t !== tab);
  }

  switch(tab) {
    case 'zips': _renderReportZips(); break;
    case 'playlists': _renderReportPlaylists(); break;
    case 'multidisc': _renderReportMultidisc(); break;
    case 'orphans': _renderReportOrphans(); break;
    case 'ra': _renderReportRA(); break;
    case 'chd': _renderReportChd(); break;
  }
}

export function _renderReportZips() {
  const el = document.getElementById('rpt-tab-zips');
  if (!el || !_reportData) return;
  const z = _reportData.zips || { total: 0, files: [] };

  if (!z.total) { el.innerHTML = '<p style="color:var(--c-teal);font-size:12px">✓ No hay ZIPs sueltos.</p>'; return; }

  let html = `<div style="margin-bottom:10px;font-size:12px;color:var(--c-muted)">${z.total} archivo(s) .zip</div>`;
  html += '<div style="max-height:420px;overflow-y:auto;font-size:11px">';
  html += z.files.map(f => `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
    ${_h(f.name)} <span style="color:var(--c-dim)">(${_fmtSize(f.size_bytes)})</span>
    ${f.is_disc_set ? '<span style="color:var(--c-amber);font-size:10px;margin-left:6px">set de disco</span>' : ''}
  </div>`).join('');
  html += '</div>';
  el.innerHTML = html;
}

export function _renderReportPlaylists() {
  const el = document.getElementById('rpt-tab-playlists');
  if (!el || !_reportData) return;
  const p = _reportData.playlists || { total_groups: 0, with_m3u: 0, without_m3u: 0, groups: [] };

  if (!p.total_groups) { el.innerHTML = '<p style="color:var(--c-muted);font-size:12px">No se encontraron grupos multi-disco.</p>'; return; }

  let html = `<div style="margin-bottom:10px;font-size:12px">
    <span style="color:var(--c-teal)">✓ ${p.with_m3u} con .m3u</span>
    ${p.without_m3u ? `<span style="color:var(--c-softred);margin-left:10px">⚠ ${p.without_m3u} sin .m3u</span>` : ''}
  </div>`;
  html += '<div style="max-height:420px;overflow-y:auto;font-size:11px">';
  html += p.groups.map(g => `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
    <span style="color:${g.m3u_exists ? 'var(--c-teal)' : 'var(--c-softred)'}">${_h(g.base_name)}</span>
    <span style="color:var(--c-dim)"> — ${g.disc_count} disco(s)${g.m3u_exists ? '' : ', sin .m3u'}</span>
  </div>`).join('');
  html += '</div>';
  el.innerHTML = html;
}

export function _renderReportMultidisc() {
  const el = document.getElementById('rpt-tab-multidisc');
  if (!el || !_reportData) return;
  const m = _reportData.multidisc || { groups_ok: 0, groups_with_issues: 0, issues: [] };

  let html = `<div style="margin-bottom:10px;font-size:12px">
    <span style="color:var(--c-teal)">✓ ${m.groups_ok} sets OK</span>
    ${m.groups_with_issues ? `<span style="color:var(--c-softred);margin-left:10px">⚠ ${m.groups_with_issues} con problemas</span>` : ''}
  </div>`;
  if (!m.issues.length) { el.innerHTML = html + '<p style="color:var(--c-teal);font-size:12px">✓ Sin problemas detectados.</p>'; return; }

  html += '<div style="max-height:420px;overflow-y:auto;font-size:11px">';
  html += m.issues.map(i => `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
    ${i.platform ? `<span style="color:var(--c-blue);font-size:10px;margin-right:6px">${_h(i.platform)}</span>` : ''}
    <span style="color:var(--c-orange)">${_h(i.base_name)}</span>
    <span style="color:var(--c-dim)"> — ${_h(i.detail)}</span>
  </div>`).join('');
  html += '</div>';
  el.innerHTML = html;
}

export function _renderReportOrphans() {
  const el = document.getElementById('rpt-tab-orphans');
  if (!el || !_reportData) return;
  const o = _reportData.orphans || { total: 0, total_bytes: 0, saves: [] };

  let html = `<div style="margin-bottom:12px;font-size:12px">
    ${o.total ? `<div style="color:var(--c-softred)">⚠ ${o.total} saves huérfanos</div>` : `<div style="color:var(--c-teal)">✓ Sin saves huérfanos</div>`}
    ${o.total ? `<div style="color:var(--c-muted);font-size:11px">${_fmtSize(o.total_bytes)} recuperables</div>` : ''}
  </div>`;

  if (!o.saves || !o.saves.length) { el.innerHTML = html; return; }

  html += '<div style="max-height:420px;overflow-y:auto;font-size:11px">';
  html += o.saves.map(s => {
    const name = (s.path || '?').split(/[\\/]/).pop();
    return `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
      ${_h(name)} <span style="color:var(--c-dim)">(${_fmtSize(s.size_bytes)})</span>
      <div style="font-size:10px;color:var(--c-hint)">${_h(s.path)}</div>
    </div>`;
  }).join('');
  html += '</div>';
  el.innerHTML = html;
}

export function _renderReportRA() {
  const el = document.getElementById('rpt-tab-ra');
  if (!el || !_reportData) return;
  // Mismos datos que usa el informe HTML exportable (ra_check_result cacheado
  // por el último job de /api/ra-check) — no dispara una comprobación nueva.
  const ra = _reportData.retroachievements;
  if (!ra || ra.note) {
    el.innerHTML = `<p style="color:var(--c-muted);font-size:12px">${_h(ra?.note || 'No hay datos de RetroAchievements.')} <a href="#" onclick="showTab('tools');return false" style="color:var(--c-blue)">Ir a Herramientas → Comprobar compatibilidad RA</a></p>`;
    return;
  }
  const alternatives = ra.alternatives || [];
  let html = `<div style="margin-bottom:10px;font-size:12px">
    <span style="color:var(--c-teal)">${ra.supported || 0} con soporte</span>
    <span style="color:var(--c-softred);margin-left:10px">${ra.no_support_alternative || 0} sin logros con alternativa</span>
    <span style="color:var(--c-dim);margin-left:10px">${ra.no_support || 0} sin logros</span>
  </div>`;
  if (!alternatives.length) { el.innerHTML = html + '<p style="color:var(--c-teal);font-size:12px">✓ Sin alternativas pendientes.</p>'; return; }

  html += '<div style="max-height:420px;overflow-y:auto;font-size:11px">';
  html += alternatives.map(r => `<div style="padding:4px;border-bottom:1px solid #222;color:var(--c-muted)">
    <span style="color:var(--c-blue);font-size:10px;margin-right:6px">${_h(r.platform || '')}</span>
    ${_h(r.filename || r.original_filename || '')} →
    <a href="https://retroachievements.org/game/${r.ra_id || ''}" target="_blank" style="color:var(--c-teal)">${_h(r.ra_title || '')}</a>
  </div>`).join('');
  html += '</div>';
  el.innerHTML = html;
}

export function _renderReportChd() {
  const el = document.getElementById('rpt-tab-chd');
  if (!el || !_reportData) return;
  // Mismos datos que usa el informe HTML exportable (convert_chd_result
  // cacheado por el último job de "Convertir a CHD") — no convierte nada aquí.
  const chd = _reportData.chd;
  if (!chd || chd.note) {
    el.innerHTML = `<p style="color:var(--c-muted);font-size:12px">${_h(chd?.note || 'No hay datos de conversión CHD.')} <a href="#" onclick="showTab('formats');return false" style="color:var(--c-blue)">Ir a Formatos → Convertir a CHD</a></p>`;
    return;
  }
  el.innerHTML = `<p style="font-size:12px">
    <span style="color:var(--c-teal)">${chd.converted || 0} convertidos</span>
    <span style="color:var(--c-dim);margin-left:10px">${chd.skipped || 0} omitidos (ya existían)</span>
    ${chd.failed ? `<span style="color:var(--c-softred);margin-left:10px">${chd.failed} fallidos</span>` : ''}
  </p>`;
}

function _fmtSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let idx = 0;
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024;
    idx++;
  }
  return size.toFixed(idx === 0 ? 0 : 1) + ' ' + units[idx];
}

export function exportReportHtml() {
  if (!_reportData) {
    showToast('No hay datos para exportar', 'warn');
    return;
  }

  // HERR-UX-11: colores hardcodeados — var(--c-*) no existe fuera de la app,
  // el HTML exportado se abre suelto (sin la hoja de estilos de Retro Vault).
  const d = _reportData;
  const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const lines = [
    `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Informe Biblioteca — ${ts}</title>`,
    `<style>body{font-family:monospace;background:#1a1a24;color:#ddd;padding:20px;font-size:13px}`,
    `h1{color:#4ec9b0}h2{color:#aaa;border-bottom:1px solid #333;padding-bottom:4px;margin-top:20px}`,
    `table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:4px 8px;border-bottom:1px solid #222}`,
    `.ok{color:#4ec9b0}.warn{color:#e0a030}.bad{color:#f44747}.dim{color:#888}</style></head><body>`,
    `<h1>Informe de Biblioteca Retro Vault</h1>`,
    `<p class="dim">Generado: ${ts} — ${_h(d.source_path || '')}</p>`,
  ];

  // ZIPs
  const z = d.zips || { total: 0, files: [] };
  lines.push(`<h2>ZIPs (${z.total})</h2>`);
  if (z.files.length) {
    lines.push(`<table><thead><tr><th>Archivo</th><th style="text-align:right">Tamaño</th></tr></thead><tbody>`);
    z.files.forEach(f => lines.push(`<tr><td>${_h(f.name)}${f.is_disc_set ? ' <span class="warn">(set de disco)</span>' : ''}</td><td style="text-align:right">${_fmtSize(f.size_bytes)}</td></tr>`));
    lines.push(`</tbody></table>`);
  } else {
    lines.push(`<p class="ok">Sin ZIPs sueltos.</p>`);
  }

  // Playlists
  const p = d.playlists || { total_groups: 0, groups: [] };
  lines.push(`<h2>Playlists / Multi-disco (${p.total_groups})</h2>`);
  if (p.groups.length) {
    lines.push(`<table><thead><tr><th>Grupo</th><th>Discos</th><th>.m3u</th></tr></thead><tbody>`);
    p.groups.forEach(g => lines.push(`<tr><td>${_h(g.base_name)}</td><td>${g.disc_count}</td><td class="${g.m3u_exists ? 'ok' : 'bad'}">${g.m3u_exists ? 'sí' : 'no'}</td></tr>`));
    lines.push(`</tbody></table>`);
  }

  // Multidisc issues
  const m = d.multidisc || { groups_ok: 0, groups_with_issues: 0, issues: [] };
  lines.push(`<h2>Verificación multi-disco</h2><p>${m.groups_ok} OK / <span class="${m.groups_with_issues ? 'bad' : 'ok'}">${m.groups_with_issues} con problemas</span></p>`);
  if (m.issues.length) {
    lines.push(`<table><thead><tr><th>Plataforma</th><th>Set</th><th>Detalle</th></tr></thead><tbody>`);
    m.issues.forEach(i => lines.push(`<tr><td>${_h(i.platform || '')}</td><td>${_h(i.base_name)}</td><td>${_h(i.detail)}</td></tr>`));
    lines.push(`</tbody></table>`);
  }

  // Orphans
  const o = d.orphans || { total: 0, total_bytes: 0, saves: [] };
  lines.push(`<h2>Saves huérfanos (${o.total})</h2>`);
  if (o.total > 0) {
    lines.push(`<p class="warn">${_fmtSize(o.total_bytes)} recuperables</p><ul>`);
    o.saves.forEach(s => lines.push(`<li>${_h(s.path)} (${_fmtSize(s.size_bytes)})</li>`));
    lines.push(`</ul>`);
  } else {
    lines.push(`<p class="ok">Sin saves huérfanos.</p>`);
  }

  // RetroAchievements
  const ra = d.retroachievements;
  lines.push(`<h2>RetroAchievements</h2>`);
  if (!ra || ra.note) {
    lines.push(`<p class="dim">${_h(ra?.note || 'No hay datos de RetroAchievements.')}</p>`);
  } else {
    lines.push(`<p><span class="ok">${ra.supported || 0} con soporte</span> / <span class="warn">${ra.no_support_alternative || 0} sin logros con alternativa</span> / <span class="dim">${ra.no_support || 0} sin logros</span></p>`);
  }

  // CHD
  const chd = d.chd;
  lines.push(`<h2>Conversión CHD</h2>`);
  if (!chd || chd.note) {
    lines.push(`<p class="dim">${_h(chd?.note || 'No hay datos de conversión CHD.')}</p>`);
  } else {
    lines.push(`<p><span class="ok">${chd.converted || 0} convertidos</span> / <span class="dim">${chd.skipped || 0} omitidos</span>${chd.failed ? ` / <span class="bad">${chd.failed} fallidos</span>` : ''}</p>`);
  }

  lines.push(`</body></html>`);

  const blob = new Blob([lines.join('\n')], { type: 'text/html;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `informe-${ts.replace(/[: ]/g, '-')}.html`;
  a.click();
  showToast('✓ Informe exportado', 'ok');
}


// ── ES-DE systems.xml generator ───────────────────────────────────────────────
export async function generateEsSystems() {
  const btn = document.getElementById('btn-gen-es-systems');
  const res = document.getElementById('es-systems-result');
  if (btn) { btn.disabled = true; btn.textContent = 'Generando…'; }
  if (res) res.classList.add('hidden');

  try {
    const d = await apiFetch('/api/generate-es-systems');
    if (!res) return;
    res.classList.remove('hidden');

    if (d.error && !d.written) {
      res.innerHTML = `<p style="color:var(--c-pink)">&#x2717; ${_h(d.error)}</p>`;
      return;
    }

    const gen = d.generated ?? [];
    const miss = d.missing ?? [];

    let html = '';
    if (d.written) {
      html += `<p style="color:var(--c-teal);margin:0 0 8px">&#x2713; Archivo generado en <code style="font-size:10px">${_h(d.output_path)}</code></p>`;
    }
    if (d.error) {
      html += `<p style="color:var(--c-amber);margin:0 0 8px">&#x26A0; ${_h(d.error)}</p>`;
    }

    if (gen.length) {
      html += `<div style="color:var(--c-muted);font-size:11px;margin-bottom:4px">${gen.length} sistema${gen.length !== 1 ? 's' : ''} incluido${gen.length !== 1 ? 's' : ''}:</div>`;
      html += `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px">`;
      gen.forEach(s => {
        html += `<span style="background:var(--rv-tint-ok-bg);border:1px solid #2a4a2a;color:var(--c-teal);padding:2px 7px;border-radius:10px;font-size:10px" title="${_h(s.core_dll)}">${_h(s.fullname)}</span>`;
      });
      html += `</div>`;
    }

    if (miss.length) {
      html += `<div style="color:var(--c-dim);font-size:11px">Sin core: ${miss.map(m => _h(m)).join(', ')}</div>`;
    }

    res.innerHTML = html;
  } catch(e) {
    if (res) { res.classList.remove('hidden'); res.innerHTML = `<p style="color:var(--c-pink)">Error: ${_h(e.message)}</p>`; }
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '⚙ Generar'; }
  }
}
