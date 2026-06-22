// js/tabs/tools.js — Tool conversions: CHD, CSO, ZIP, M3U, multidisc, N64, LPL, library structure
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Utility functions ──────────────────────────────────────────────────────────
function fmtSize(n) {
  const units = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

function _h(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Late import for main.js functions (avoid circular imports)
let _startPolling, _showJobResult;
export function _initToolsImports(startPolling, showJobResult) {
  _startPolling = startPolling;
  _showJobResult = showJobResult;
}

// ── State variables ────────────────────────────────────────────────────────────
let _chdResults = [];
let _chdIsDry = false;
let _verifyChdResults = [];
let _faUid = 0;

// ── Convert CHD ────────────────────────────────────────────────────────────────
export async function doConvertChd() {
  const pathVal    = document.getElementById('chd-path').value.trim();
  const dryRun     = document.getElementById('chd-dry-run').checked;
  const delSource  = document.getElementById('chd-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .cue/.bin'); return; }
  const btn = document.getElementById('btn-convert-chd');
  const resultEl = document.getElementById('job-result-convert-chd');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/convert-chd', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una conversión en curso…';
      btn.disabled = false;
      btn.textContent = 'Convertir a CHD';
      return;
    }
    _startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Convertir a CHD';
  }
}

export function _renderChdResult(result) {
  const resultEl   = document.getElementById('job-result-convert-chd');
  const btn        = document.getElementById('btn-convert-chd');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    _showJobResult('convert-chd', result);
    _chdResults = result.results || [];
    _chdIsDry = result.dry_run === true;
    // Show filter header if there are results
    const hdr = document.getElementById('chd-results-header');
    if (hdr) hdr.classList.toggle('hidden', !(_chdResults.length));
    // Default: show errors-only if any failures exist
    const hasFails = _chdResults.some(r => !r.success && r.error);
    const cb = document.getElementById('chd-filter-errors');
    if (cb) cb.checked = hasFails;
    applyChdFilter();
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a CHD'; }
}

export function applyChdFilter() {
  const resultsDiv = document.getElementById('chd-results');
  const countEl    = document.getElementById('chd-results-count');
  if (!resultsDiv) return;
  const errorsOnly = document.getElementById('chd-filter-errors')?.checked ?? false;
  const visible = errorsOnly ? _chdResults.filter(r => !r.success) : _chdResults;
  if (countEl) countEl.textContent = `${visible.length} / ${_chdResults.length} entradas`;
  if (!visible.length) {
    resultsDiv.innerHTML = errorsOnly
      ? '<p style="color:var(--c-teal);font-size:12px;margin:4px 0">Sin errores.</p>'
      : '';
    return;
  }
  const isDry = _chdIsDry;
  resultsDiv.innerHTML = visible.map(r => {
    if (r.success) {
      const tag = isDry ? 'PREVIEW' : 'OK';
      const bins = r.bin_count > 0 ? ` <span style="color:#555;font-size:10px">(${r.bin_count} bin)</span>` : '';
      return `<div style="font-size:12px;color:var(--c-teal);padding:2px 0">[${tag}] ${_h(r.cue)} → ${_h(r.chd)}${bins}</div>`;
    } else {
      const bins = r.bin_count > 0 ? ` <span style="color:#555;font-size:10px">(${r.bin_count} bin)</span>` : '';
      const errMsg = r.error ? `<div style="color:var(--c-red);font-size:11px;margin-top:2px;padding-left:8px">${_h(r.error)}</div>` : '';
      return `<div style="padding:4px 0;border-bottom:1px solid #2a1a1a"><span style="font-size:12px;color:var(--c-red)"><strong>[FAIL]</strong> ${_h(r.cue)}${bins}</span>${errMsg}</div>`;
    }
  }).join('');
}

// ── Convert CSO/ZSO ───────────────────────────────────────────────────────────
export async function doConvertCso() {
  const pathVal   = document.getElementById('cso-path').value.trim();
  const delSource = document.getElementById('cso-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .cso/.zso'); return; }
  const btn = document.getElementById('btn-convert-cso');
  const resultEl = document.getElementById('job-result-convert-cso');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/convert-cso', { source_path: pathVal, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una conversión CSO en curso…';
      btn.disabled = false;
      btn.textContent = 'Convertir a ISO';
      return;
    }
    _startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Convertir a ISO';
  }
}

export function _renderCsoResult(result) {
  const resultEl = document.getElementById('job-result-convert-cso');
  const btn = document.getElementById('btn-convert-cso');
  const resultsDiv = document.getElementById('cso-results');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    const tot = result.converted + result.failed + result.skipped;
    const summary = `Convertidos: ${result.converted} | Omitidos: ${result.skipped} | Fallidos: ${result.failed}`;
    resultEl.className = 'job-result visible ' + (result.failed > 0 ? 'warning-r' : 'success');
    resultEl.textContent = summary;
    // Render detailed results
    if (resultsDiv && result.results) {
      resultsDiv.innerHTML = result.results.map(r => {
        if (r.success) {
          return `<div style="font-size:12px;color:var(--c-teal);padding:2px 0">[OK] ${_h(r.file)}</div>`;
        } else {
          const errMsg = r.error ? `<div style="color:var(--c-red);font-size:11px;margin-top:2px;padding-left:8px">${_h(r.error)}</div>` : '';
          return `<div style="padding:4px 0;border-bottom:1px solid #2a1a1a"><span style="font-size:12px;color:var(--c-red)"><strong>[FAIL]</strong> ${_h(r.file)}</span>${errMsg}</div>`;
        }
      }).join('');
    }
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a ISO'; }
}

// ── Cleanup ZIPs ───────────────────────────────────────────────────────────────
export async function doCleanupZips() {
  const pathVal = document.getElementById('zip-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  const n = (document.querySelectorAll('#zip-results div').length) || '?';
  if (!confirm(`¿Eliminar TODOS los archivos .zip de:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-zips', { source_path: pathVal });
    const el = document.getElementById('job-result-extract-zip');
    el.className = 'job-result visible success';
    el.textContent = `ZIPs eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message + '\n\nVerifica que los archivos no estén en uso por otro programa.'); }
}

export async function doCleanupCueBin() {
  const pathVal = document.getElementById('chd-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  if (!confirm(`¿Eliminar los archivos .cue y .bin que ya tienen su .chd en:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-cue-bin', { source_path: pathVal });
    const el = document.getElementById('job-result-convert-chd');
    el.className = 'job-result visible success';
    el.textContent = `Archivos eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.skipped ? `  |  Sin .chd (no tocados): ${d.skipped}` : ''}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message + '\n\nVerifica que los archivos no estén en uso por otro programa.'); }
}

export async function doExtractZip() {
  const pathVal   = document.getElementById('zip-path').value.trim();
  const dryRun    = document.getElementById('zip-dry-run').checked;
  const delSource = document.getElementById('zip-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .zip'); return; }
  const btn = document.getElementById('btn-extract-zip');
  const resultEl = document.getElementById('job-result-extract-zip');
  btn.disabled = true; btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  document.getElementById('zip-results').innerHTML = '';
  try {
    const d = await apiPost('/api/extract-zip', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay una extracción en curso…';
      btn.disabled = false; btn.textContent = 'Descomprimir ZIPs'; return;
    }
    _startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false; btn.textContent = 'Descomprimir ZIPs';
  }
}

// ── M3U Generator ──────────────────────────────────────────────────────────────
export async function doGenerateM3U() {
  const pathVal = document.getElementById('m3u-path').value.trim();
  const dryRun  = document.getElementById('m3u-dry-run').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta de ROMs'); return; }
  const resultEl = document.getElementById('m3u-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Buscando grupos multi-disco…</p>';
  try {
    const d = await apiPost('/api/generate-m3u', { source_path: pathVal, dry_run: dryRun });
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
    const verb = dryRun ? 'Crearía' : 'Creados';
    let html = `<p style="color:var(--c-teal);margin-bottom:12px">${verb}: <strong>${d.created}</strong>  |  Ya existían: <strong>${d.skipped}</strong></p>`;
    if (d.groups.length) {
      html += '<div style="max-height:300px;overflow-y:auto">';
      html += d.groups.map(g => {
        const color = g.discs.length >= 2 ? 'var(--c-teal)' : '#888';
        return `<div style="font-size:12px;color:${color};padding:2px 0"><strong>${g.m3u}</strong> → ${g.discs.join(', ')}</div>`;
      }).join('');
      html += '</div>';
    } else {
      html += '<p style="color:#555;font-size:12px">No se encontraron grupos multi-disco.</p>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

export async function autodetectM3UFolders() {
  const btn = document.getElementById('btn-m3u-autodetect');
  const wrap = document.getElementById('m3u-folder-select-wrap');
  const listEl = document.getElementById('m3u-folder-list');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando…'; }
  try {
    const d = await apiFetch('/api/disc-folders');
    const folders = d.folders || [];
    if (folders.length === 0) {
      alert('No se detectaron carpetas de plataformas de disco en library_root.');
    } else if (folders.length === 1) {
      document.getElementById('m3u-path').value = folders[0];
      if (wrap) wrap.classList.add('hidden');
    } else {
      // Show folder buttons to pick one
      listEl.innerHTML = folders.map(f => {
        const name = f.split(/[\\/]/).pop();
        return `<button class="btn" style="font-size:12px;padding:3px 10px" onclick="document.getElementById('m3u-path').value='${f.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}';document.getElementById('m3u-folder-select-wrap').classList.add('hidden')">${name}</button>`;
      }).join('');
      if (wrap) wrap.classList.remove('hidden');
    }
  } catch(e) {
    alert('Error al detectar carpetas: ' + e.message + '\n\nConsulta los logs para más detalles.');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Autodetectar carpetas'; }
  }
}

// ── Multi-disc Verifier ────────────────────────────────────────────────────────
let _lastVerifiedPaths = [];

export async function generateM3uFromVerify() {
  const resultEl = document.getElementById('multidisc-result');
  const statusEl = document.createElement('p');
  statusEl.style.cssText = 'margin-top:8px;font-size:12px;color:#888';
  statusEl.textContent = 'Generando .m3u…';
  resultEl.appendChild(statusEl);
  let created = 0;
  try {
    for (const p of _lastVerifiedPaths) {
      const d = await apiPost('/api/generate-m3u', { source_path: p, dry_run: false });
      if (!d.error) created += d.created;
    }
    statusEl.style.color = 'var(--c-teal)';
    statusEl.textContent = `✓ ${created} archivo(s) .m3u creados. Vuelve a verificar para confirmar.`;
  } catch(e) {
    statusEl.style.color = 'var(--c-red)';
    statusEl.textContent = `Error: ${e.message}`;
  }
}

export async function doVerifyMultidisc() {
  const rawVal = document.getElementById('verify-multidisc-path').value.trim();
  if (!rawVal) { alert('Introduce al menos una carpeta de ROMs'); return; }
  const paths = rawVal.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
  _lastVerifiedPaths = paths;
  const resultEl = document.getElementById('multidisc-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Verificando…</p>';
  // Aggregate results across all paths
  let totalOk = 0, totalIssues = 0;
  const allIssues = [];
  try {
    for (const pathVal of paths) {
      const d = await apiPost('/api/verify-multidisc', { source_path: pathVal });
      if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
      totalOk += d.groups_ok; totalIssues += d.groups_with_issues;
      allIssues.push(...d.issues);
    }
    const d = { groups_ok: totalOk, groups_with_issues: totalIssues, issues: allIssues };
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }

    const realIssues    = d.issues.filter(i => i.issue_type !== 'unmatched');
    const unmatchedOnly = d.issues.filter(i => i.issue_type === 'unmatched');
    const realBad = new Set(realIssues.map(i => i.base_name));
    // Groups with only "unmatched" and no real structural issues are OK structurally
    const structurallyBad = d.groups_with_issues - [...new Set(unmatchedOnly.map(i => i.base_name))].filter(n => !realBad.has(n)).length;
    const total = d.groups_ok + d.groups_with_issues;

    let html = `<p style="margin-bottom:8px">`;
    html += `<span style="color:var(--c-teal)">✓ ${d.groups_ok + (d.groups_with_issues - structurallyBad)} grupos OK estructuralmente</span>`;
    if (structurallyBad > 0) html += `  <span style="color:var(--c-red)">✗ ${structurallyBad} con problemas reales</span>`;
    if (unmatchedOnly.length > 0) html += `  <span style="color:#888">⚠ ${unmatchedOnly.length} sin match en catálogo (normal si no has hecho Match aún)</span>`;
    html += `  <span style="color:#555">(${total} grupos)</span></p>`;

    const issueLabels = { gap: 'Set incompleto', mixed_ext: 'Extensiones mezcladas', missing_file: 'Archivo no encontrado', unmatched: 'Sin match en catálogo', missing_m3u: 'Sin .m3u' };

    // ── Missing .m3u banner + action ─────────────────────────────────────────
    const missingM3u = d.issues.filter(i => i.issue_type === 'missing_m3u');
    if (missingM3u.length) {
      html += `<div style="display:flex;align-items:center;gap:12px;padding:8px 10px;background:var(--bg-nav);border:1px solid var(--border);border-radius:4px;margin-bottom:12px">
        <span style="font-size:12px;color:#888">&#x26A0; ${missingM3u.length} juego(s) multidisco sin .m3u — RetroArch no podrá cambiar de disco</span>
        <button class="btn primary" style="flex-shrink:0;font-size:12px;padding:3px 12px" onclick="generateM3uFromVerify()">Generar .m3u (${missingM3u.length})</button>
      </div>`;
    }

    // ── Structural issues (gap, mixed_ext, missing_file) ─────────────────────
    const structuralIssues = realIssues.filter(i => i.issue_type !== 'missing_m3u');
    const gapIssues  = structuralIssues.filter(i => i.issue_type === 'gap');
    const otherIssues = structuralIssues.filter(i => i.issue_type !== 'gap');

    if (gapIssues.length) {
      html += `<p style="color:var(--c-red);font-size:12px;margin:10px 0 4px">Sets incompletos — falta al menos un disco (${gapIssues.length}):</p>`;
      html += `<p style="color:#666;font-size:11px;margin:0 0 6px">Si tienes todos los archivos, revisa que los nombres incluyan "(Disc N)" sin variaciones.</p>`;
      html += '<div style="max-height:200px;overflow-y:auto;margin-bottom:12px">';
      html += gapIssues.map(i => `<div style="font-size:12px;padding:3px 0;border-bottom:1px solid var(--c-panel)">
        ${i.platform ? `<span style="color:var(--c-blue);font-size:11px;background:#1a2233;padding:1px 5px;border-radius:3px;margin-right:6px">${_h(i.platform)}</span>` : ''}
        <span style="color:var(--c-text)">${_h(i.base_name)}</span>
        <span style="color:#555;margin-left:8px">${_h(i.detail)}</span>
      </div>`).join('');
      html += '</div>';
    }
    if (otherIssues.length) {
      html += `<p style="color:var(--c-red);font-size:12px;margin:10px 0 6px">Otros problemas estructurales (${otherIssues.length}):</p>`;
      html += '<div style="max-height:200px;overflow-y:auto;margin-bottom:12px">';
      html += otherIssues.map(i => `<div style="font-size:12px;padding:3px 0;border-bottom:1px solid var(--c-panel)">
        <span style="color:var(--c-red)">${issueLabels[i.issue_type] || i.issue_type}</span>
        <span style="color:#888;margin:0 6px">·</span>
        ${i.platform ? `<span style="color:var(--c-blue);font-size:11px;background:#1a2233;padding:1px 5px;border-radius:3px;margin-right:6px">${_h(i.platform)}</span>` : ''}
        <span style="color:var(--c-text)">${_h(i.base_name)}</span>
        <span style="color:#555;margin-left:8px">${_h(i.detail)}</span>
      </div>`).join('');
      html += '</div>';
    }

    // ── Unmatched: catalog action ─────────────────────────────────────────────
    if (unmatchedOnly.length) {
      html += `<div style="padding:8px 10px;background:var(--bg-nav);border:1px solid var(--border);border-radius:4px;margin-top:4px">`;
      html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <span style="font-size:12px;color:#888">&#x1F50D; ${unmatchedOnly.length} discos sin identificar en catálogo</span>
        <button class="btn" style="flex-shrink:0;font-size:11px;padding:2px 10px" onclick="showTab('settings');setTimeout(()=>{const el=document.getElementById('dat-catalog-list');if(el)el.scrollIntoView({behavior:'smooth'})},350)">Ajustes → Catálogos DAT</button>
      </div>`;
      html += `<p style="font-size:11px;color:#555;margin:0 0 6px">Si ya tienes un DAT, ve a la pestaña <strong>Organizar</strong> y pulsa Identificar. Si no, carga un catálogo DAT en Ajustes.</p>`;
      html += `<details style="font-size:11px;color:#555"><summary style="cursor:pointer;color:#666">Ver lista (${unmatchedOnly.length})</summary>`;
      html += '<div style="max-height:160px;overflow-y:auto;margin-top:4px">';
      html += unmatchedOnly.map(i => `<div style="padding:2px 0">${_h(i.base_name)} — ${_h(i.detail)}</div>`).join('');
      html += '</div></details></div>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Playlists RetroArch .lpl ───────────────────────────────────────────────────
export async function doExportLpl() {
  const el = document.getElementById('lpl-result');
  const outputDir = document.getElementById('lpl-output-dir')?.value.trim() || '';
  if (el) { el.innerHTML = '<span class="loading">Generando…</span>'; el.classList.remove('hidden'); }
  try {
    const d = await apiPost('/api/export-lpl', outputDir ? { output_dir: outputDir } : {});
    if (d.error) {
      if (el) el.innerHTML = `<span style="color:var(--c-red)">✗ ${_h(d.error)}</span>`;
    } else {
      if (el) el.innerHTML = `<span style="color:var(--c-teal)">✓ ${d.platforms} plataformas · ${d.games} juegos → <code style="font-size:11px">${_h(d.output_dir)}</code></span>`;
    }
  } catch (e) {
    if (el) el.innerHTML = `<span style="color:var(--c-red)">✗ ${e.message}</span>`;
  }
}

// ── N64 converter ──────────────────────────────────────────────────────────────
export async function doN64Scan() {
  const path = document.getElementById('n64-path')?.value.trim();
  const el = document.getElementById('n64-scan-result');
  if (!path || !el) return;
  el.innerHTML = '<span class="loading">Escaneando…</span>';
  try {
    const d = await apiFetch('/api/n64-scan?path=' + encodeURIComponent(path));
    const roms = d.roms || [];
    if (!roms.length) { el.innerHTML = '<p style="color:#555;font-size:12px">No se encontraron ROMs de N64 en esa carpeta.</p>'; return; }
    const needConv = roms.filter(r => r.needs_conversion);
    let html = `<p style="font-size:12px;color:#888;margin-bottom:8px">${roms.length} ROMs encontrados — ${needConv.length} necesitan conversión a .z64</p>`;
    if (needConv.length) {
      html += `<div style="max-height:200px;overflow-y:auto">`;
      html += needConv.map(r => `<div style="display:flex;gap:8px;align-items:center;padding:3px 0;border-bottom:1px solid #1a1a2a;font-size:12px">
        <span style="color:var(--c-amber);width:36px;flex-shrink:0">${_h(r.format.toUpperCase())}</span>
        <span style="color:var(--c-text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_h(r.filename)}</span>
        <button class="btn" style="padding:1px 8px;font-size:11px;flex-shrink:0" onclick="doN64Convert(${JSON.stringify(r.path)})">Convertir</button>
      </div>`).join('');
      html += `</div>`;
    } else {
      html += `<p style="color:var(--c-teal);font-size:12px">&#x2713; Todos los ROMs ya están en formato .z64</p>`;
    }
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<p style="color:var(--c-softred);font-size:12px">Error: ${_h(e.message)}</p>`; }
}

export async function doN64Convert(sourcePath) {
  try {
    const d = await apiPost('/api/convert-n64', { source_path: sourcePath });
    if (d.success) {
      showToast(`✓ Convertido: ${d.target_path.split(/[\\/]/).pop()}`, 'ok');
      doN64Scan();  // refresh list
    } else {
      showToast(`✗ ${d.error || 'Error desconocido'}`, 'err');
    }
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

// ── Folder analysis ────────────────────────────────────────────────────────────
function _faCollapsibleList(items, renderItem, limit = 10) {
  if (!items || items.length === 0) return '';
  const uid = 'falist_' + (++_faUid);
  const visible = items.slice(0, limit);
  const hidden  = items.slice(limit);
  let html = `<div style="max-height:220px;overflow-y:auto;border:1px solid #222;border-radius:4px;padding:4px 0;margin-bottom:4px">`;
  html += '<ul style="margin:0;padding-left:20px">';
  html += visible.map(renderItem).join('');
  if (hidden.length > 0) {
    html += `</ul><ul id="${uid}_rest" style="margin:0;padding-left:20px;display:none">`;
    html += hidden.map(renderItem).join('');
  }
  html += '</ul></div>';
  if (hidden.length > 0) {
    html += `<button onclick="(function(){var r=document.getElementById('${uid}_rest'),b=document.getElementById('${uid}_btn');if(r.classList.contains('hidden')){r.classList.remove('hidden');b.textContent='▲ Mostrar menos';}else{r.classList.add('hidden');b.textContent='▼ Ver todos (${items.length})';}})()" id="${uid}_btn" style="background:none;border:none;color:var(--c-blue);font-size:11px;cursor:pointer;padding:2px 0">▼ Ver todos (${items.length})</button>`;
  }
  return html;
}

// Note: doFolderAnalysis is NOT in this migration as it was added after tools.js split
// If needed, it can be migrated separately

// ── Library Structure ──────────────────────────────────────────────────────────
export async function createLibraryStructure() {
  const resultEl = document.getElementById('job-result-structure');
  resultEl.className = 'job-result';
  const alsoAndroid = document.getElementById('struct-also-android')?.checked || false;
  try {
    const d = await apiPost('/api/create-library-structure', { also_android: alsoAndroid });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    resultEl.className = 'job-result visible success';
    resultEl.innerHTML = `✓ PC: ${d.created.length} carpeta${d.created.length !== 1 ? 's' : ''} creada${d.created.length !== 1 ? 's' : ''} en <code>${d.root}</code>`;
    if (d.skipped.length > 0) resultEl.innerHTML += `<br><span style="font-size:11px;color:#555">${d.skipped.length} ya existían</span>`;
    if (d.android && d.android.root) {
      if (d.android.error) {
        resultEl.innerHTML += `<br><span style="color:var(--c-yellow);font-size:11px">⚠ Android: ${d.android.error}</span>`;
      } else {
        resultEl.innerHTML += `<br><span style="color:var(--c-teal);font-size:11px">✓ Android: ${d.android.created.length} carpetas creadas en <code>${d.android.root}</code></span>`;
      }
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message + '\n\nVerifica que library_root esté configurado en Ajustes.';
  }
}

export async function organizeLibrary(dryRun) {
  const resultEl = document.getElementById('job-result-structure');
  resultEl.className = 'job-result';
  if (!dryRun) {
    if (!confirm('¿Organizar la biblioteca?\n\n• ROMs → carpetas de plataforma\n• Saves → saves/\n• BIOS conocidas → bios/\n\nLas rutas en la base de datos se actualizarán. Haz una copia de seguridad si es tu primera vez.')) return;
  }
  try {
    const d = await apiPost('/api/organize-library', { dry_run: dryRun });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    const verb = dryRun ? 'Se moverían' : 'Movidos';
    const total = (d.moves_roms || 0) + (d.moves_saves || 0) + (d.moves_bios || 0);
    resultEl.className = 'job-result visible ' + (d.errors?.length ? 'error-r' : 'success');
    resultEl.innerHTML = `${verb}: <strong>${total}</strong> archivos total` +
      `<span style="color:#555;font-size:11px;margin-left:10px">ROMs: ${d.moves_roms || 0} · Saves: ${d.moves_saves || 0} · BIOS: ${d.moves_bios || 0}</span>`;
    if (d.errors && d.errors.length > 0) {
      resultEl.innerHTML += `<br><span style="color:var(--c-yellow);font-size:11px">⚠ ${d.errors.length} errores (ver logs)</span>`;
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Verify CHD (P6) ──────────────────────────────────────────────────────────
export async function doVerifyChd() {
  const pathVal = document.getElementById('verify-chd-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .chd'); return; }
  const btn = document.getElementById('btn-verify-chd');
  const resultEl = document.getElementById('verify-chd-result');
  btn.disabled = true;
  btn.textContent = 'Iniciando…';
  if (resultEl) { resultEl.className = 'job-result'; resultEl.textContent = ''; }
  const listEl = document.getElementById('verify-chd-list');
  if (listEl) listEl.innerHTML = '';
  try {
    const d = await apiPost('/api/verify-chd', { source_path: pathVal });
    if (d.status === 'already_running') {
      if (resultEl) { resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay una verificación en curso…'; }
      btn.disabled = false;
      btn.textContent = 'Verificar CHDs';
      return;
    }
    _startPolling();
  } catch(e) {
    if (resultEl) { resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message; }
    btn.disabled = false;
    btn.textContent = 'Verificar CHDs';
  }
}

export function _renderVerifyChdResult(result) {
  const resultEl = document.getElementById('verify-chd-result');
  const btn = document.getElementById('btn-verify-chd');
  const listEl = document.getElementById('verify-chd-list');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    const cancelled = result.cancelled ? ' (cancelado)' : '';
    const cls = result.failed > 0 ? 'error-r' : 'success';
    resultEl.className = 'job-result visible ' + cls;
    resultEl.innerHTML = `${result.ok} / ${result.total} CHDs correctos` +
      (result.failed > 0 ? ` &nbsp;·&nbsp; <span style="color:var(--c-red)">${result.failed} corruptos</span>` : '') +
      `<span style="color:#555;font-size:11px;margin-left:8px">${cancelled}</span>`;
    _verifyChdResults = result.results || [];
    if (listEl && _verifyChdResults.length) {
      const errorsOnly = document.getElementById('verify-chd-filter-errors')?.checked ?? true;
      _renderVerifyChdList(listEl, errorsOnly);
    }
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Verificar CHDs'; btn.onclick = window.doVerifyChd; btn.classList.remove('danger'); }
}

export function applyVerifyChdFilter() {
  const listEl = document.getElementById('verify-chd-list');
  const errorsOnly = document.getElementById('verify-chd-filter-errors')?.checked ?? false;
  if (listEl) _renderVerifyChdList(listEl, errorsOnly);
}

function _renderVerifyChdList(listEl, errorsOnly) {
  const visible = errorsOnly ? _verifyChdResults.filter(r => !r.ok) : _verifyChdResults;
  const countEl = document.getElementById('verify-chd-count');
  if (countEl) countEl.textContent = `${visible.length} / ${_verifyChdResults.length}`;
  if (!visible.length) {
    listEl.innerHTML = errorsOnly
      ? '<p style="color:var(--c-teal);font-size:12px;padding:4px 0">Todos los CHDs son correctos.</p>'
      : '<p style="color:#555;font-size:12px;padding:4px 0">Sin resultados.</p>';
    return;
  }
  listEl.innerHTML = visible.map(r => {
    if (r.ok) {
      return `<div style="font-size:12px;color:var(--c-teal);padding:2px 0">[OK] ${_h(r.file)}</div>`;
    }
    const errMsg = r.error ? `<div style="color:var(--c-red);font-size:11px;padding-left:8px;margin-top:1px">${_h(r.error)}</div>` : '';
    return `<div style="padding:3px 0;border-bottom:1px solid #2a1a1a"><span style="font-size:12px;color:var(--c-red)">[CORRUPT] ${_h(r.file)}</span>${errMsg}</div>`;
  }).join('');
}