// flow_wizard.js — FLOW-WIZARD: scan → organize → duplicates → sync, step by step.

import { apiFetch, apiPost } from './api.js';

// ── State ─────────────────────────────────────────────────────────────────────

let _step = -1;        // -1=intro, 0=scan, 1=organize, 2=dupes, 3=sync, 4=summary
let _results = {};     // accumulated per-step results
let _skipped = {};     // steps the user skipped
let _pollTimer = null;
let _prevResultTs = {}; // last seen result_ts per job, to detect fresh results

// ── Public API ────────────────────────────────────────────────────────────────

export function openFlowWizard() {
  _step = -1;
  _results = {};
  _skipped = {};
  _prevResultTs = {};
  _stopPoll();
  document.getElementById('flow-wizard-modal')?.classList.remove('hidden');
  _render();
}

export function closeFlowWizard() {
  _stopPoll();
  document.getElementById('flow-wizard-modal')?.classList.add('hidden');
}

// ── Core rendering ────────────────────────────────────────────────────────────

function _render() {
  _updateStepIndicator();
  if      (_step === -1) _renderIntro();
  else if (_step ===  0) _renderScan();
  else if (_step ===  1) _renderOrganize();
  else if (_step ===  2) _renderDupes();
  else if (_step ===  3) _renderSync();
  else                   _renderSummary();
}

function _updateStepIndicator() {
  const STEP_IDS = ['fw-si-scan', 'fw-si-organize', 'fw-si-dupes', 'fw-si-sync'];
  STEP_IDS.forEach((id, i) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = 'fw-si-item';
    if (_step === 4 || i < _step)       el.classList.add('fw-si-done');
    else if (i === _step)               el.classList.add('fw-si-active');
  });
}

function _setBody(html) {
  const el = document.getElementById('fw-body');
  if (el) el.innerHTML = html;
}

function _setActions(nextLabel, nextFn, skipLabel, skipFn) {
  const next = document.getElementById('fw-btn-next');
  const skip = document.getElementById('fw-btn-skip');
  if (next) {
    next.textContent = nextLabel;
    next.disabled = !nextFn;
    next.onclick = nextFn ?? null;
  }
  if (skip) {
    if (skipFn) {
      skip.textContent = skipLabel || 'Omitir';
      skip.classList.remove('hidden');
      skip.onclick = skipFn;
    } else {
      skip.classList.add('hidden');
    }
  }
}

function _stopPoll() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Step –1: Intro ────────────────────────────────────────────────────────────

function _renderIntro() {
  _setBody(`
    <p style="color:#888;margin:0 0 16px;line-height:1.7;font-size:13px">
      Este asistente ejecuta los pasos principales en orden.<br>
      Puedes <strong style="color:#ccc">omitir</strong> cualquier paso que no necesites ahora.
    </p>
    <div style="display:flex;flex-direction:column;gap:7px">
      ${_introRow('🔍', 'Escanear', 'Detecta ROMs nuevos o movidos')}
      ${_introRow('✏️', 'Organizar', 'Aplica renombres pendientes según DATs')}
      ${_introRow('🗂️', 'Duplicados', 'Detecta y elimina duplicados')}
      ${_introRow('☁️', 'Sync', 'Sincroniza saves con la nube (dry-run primero)')}
    </div>
  `);
  _setActions('Comenzar', () => { _step = 0; _render(); }, null, null);
}

function _introRow(icon, label, desc) {
  return `
    <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--bg-panel);border:1px solid var(--border-s);border-radius:6px">
      <span style="font-size:17px;min-width:22px;text-align:center">${icon}</span>
      <div>
        <div style="color:#ccc;font-size:13px;font-weight:600">${label}</div>
        <div style="color:#555;font-size:11px">${desc}</div>
      </div>
    </div>`;
}

// ── Step 0: Scan ──────────────────────────────────────────────────────────────

async function _renderScan() {
  _setBody('<p style="color:#888;font-size:13px">Iniciando escaneo…</p>');
  _setActions('Siguiente', null, 'Omitir', () => { _skipped.scan = true; _step = 1; _render(); });

  try {
    const status = await apiFetch('/api/job-status');
    _prevResultTs.scan = status.scan_result?.result_ts ?? '';
    await apiPost('/api/scan', {});
    _setBody('<p style="color:#888;font-size:13px">Escaneando biblioteca…</p>');
    _pollScan();
  } catch (e) {
    _setBody(`<p class="error-msg">Error al iniciar escaneo: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 1; _render(); }, null, null);
  }
}

function _pollScan() {
  _stopPoll();
  _pollTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      if (s.scan_running && s.scan_progress) {
        const p = s.scan_progress;
        _setBody(`<p style="color:#888;font-size:13px">Escaneando… <strong style="color:#ccc">${p.scanned ?? p.files_seen ?? 0}</strong> archivos hasta ahora</p>`);
        return;
      }
      const r = s.scan_result;
      if (!s.scan_running && r && r.result_ts && r.result_ts !== _prevResultTs.scan) {
        _stopPoll();
        _results.scan = r;
        if (r.error) {
          _setBody(`<p class="error-msg">Error en escaneo: ${_h(r.error)}</p>`);
        } else {
          _setBody(`
            <div style="text-align:center;padding:20px 0">
              <div style="font-size:30px;margin-bottom:8px">✅</div>
              <div style="color:#ccc;font-size:14px;font-weight:600">Escaneo completado</div>
              <div style="color:#888;font-size:12px;margin-top:8px">
                <strong style="color:#4ec9b0">${r.roms_detected ?? 0}</strong> ROMs detectados
                &nbsp;·&nbsp; ${r.files_seen ?? 0} archivos vistos
                ${r.errors ? ` &nbsp;·&nbsp; <span style="color:#f38ba8">${r.errors} errores</span>` : ''}
              </div>
            </div>
          `);
        }
        _setActions('Siguiente', () => { _step = 1; _render(); }, null, null);
      }
    } catch {}
  }, 2000);
}

// ── Step 1: Organize ──────────────────────────────────────────────────────────

async function _renderOrganize() {
  _setBody('<p style="color:#888;font-size:13px">Calculando renombres pendientes…</p>');
  _setActions('Aplicar', null, 'Omitir', () => { _skipped.organize = true; _step = 2; _render(); });

  try {
    const plan = await apiFetch('/api/plan');
    const ops = plan.operations ?? [];
    const count = ops.length;
    _results.organize = { plan_count: count };

    if (count === 0) {
      _setBody(`
        <div style="text-align:center;padding:20px 0">
          <div style="font-size:28px;margin-bottom:8px">✅</div>
          <div style="color:#888;font-size:13px">Nada que organizar — todo al día</div>
        </div>
      `);
      _setActions('Siguiente', () => { _step = 2; _render(); }, null, null);
      return;
    }

    const preview = ops.slice(0, 6).map(op => {
      const src = op.source_name ?? op.source_path?.split(/[\\/]/).pop() ?? '';
      const tgt = op.target_name ?? op.target_path?.split(/[\\/]/).pop() ?? '';
      return `<div style="font-size:11px;color:#666;padding:3px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
        ✏️ ${_h(src)} <span style="color:#444">→</span> <span style="color:#9cdcfe">${_h(tgt)}</span>
      </div>`;
    }).join('');
    const more = count > 6 ? `<div style="color:#444;font-size:11px;margin-top:4px">…y ${count - 6} más</div>` : '';

    _setBody(`
      <div style="color:#ccc;font-size:13px;margin-bottom:10px">
        <strong style="color:#7aa2f7">${count}</strong> renombre${count !== 1 ? 's' : ''} pendiente${count !== 1 ? 's' : ''}
      </div>
      <div style="background:var(--bg-panel);border:1px solid var(--border-s);border-radius:6px;padding:10px;max-height:150px;overflow-y:auto">
        ${preview}${more}
      </div>
    `);
    _setActions('Aplicar renombres', _applyOrganize, 'Omitir', () => { _skipped.organize = true; _step = 2; _render(); });
  } catch (e) {
    _setBody(`<p class="error-msg">Error al calcular plan: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 2; _render(); }, null, null);
  }
}

async function _applyOrganize() {
  _setBody('<p style="color:#888;font-size:13px">Aplicando renombres…</p>');
  _setActions('Siguiente', null, null, null);

  try {
    const status = await apiFetch('/api/job-status');
    _prevResultTs.apply = status.apply_result?.result_ts ?? '';
    await apiPost('/api/apply', { dry_run: false });
    _pollApply();
  } catch (e) {
    _setBody(`<p class="error-msg">Error al aplicar: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 2; _render(); }, null, null);
  }
}

function _pollApply() {
  _stopPoll();
  _pollTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      const r = s.apply_result;
      if (!s.apply_running && r && r.result_ts && r.result_ts !== _prevResultTs.apply) {
        _stopPoll();
        _results.organize = { ...(_results.organize ?? {}), renamed: r.renamed ?? 0, failed: r.failed ?? 0 };
        if (r.error) {
          _setBody(`<p class="error-msg">Error al aplicar: ${_h(r.error)}</p>`);
        } else {
          _setBody(`
            <div style="text-align:center;padding:20px 0">
              <div style="font-size:30px;margin-bottom:8px">✅</div>
              <div style="color:#ccc;font-size:14px;font-weight:600">Renombres aplicados</div>
              <div style="color:#888;font-size:12px;margin-top:8px">
                <strong style="color:#4ec9b0">${r.renamed ?? 0}</strong> renombrados
                ${r.failed ? ` &nbsp;·&nbsp; <span style="color:#f38ba8">${r.failed} fallidos</span>` : ''}
              </div>
            </div>
          `);
        }
        _setActions('Siguiente', () => { _step = 2; _render(); }, null, null);
      }
    } catch {}
  }, 2000);
}

// ── Step 2: Duplicates ────────────────────────────────────────────────────────

async function _renderDupes() {
  _setBody('<p style="color:#888;font-size:13px">Buscando duplicados…</p>');
  _setActions('Eliminar duplicados', null, 'Omitir', () => { _skipped.dupes = true; _step = 3; _render(); });

  try {
    const data = await apiFetch('/api/duplicates');
    const groups = data.groups ?? [];
    const count = groups.length;
    _results.dupes = { count };

    if (count === 0) {
      _setBody(`
        <div style="text-align:center;padding:20px 0">
          <div style="font-size:28px;margin-bottom:8px">✅</div>
          <div style="color:#888;font-size:13px">Sin duplicados</div>
        </div>
      `);
      _setActions('Siguiente', () => { _step = 3; _render(); }, null, null);
      return;
    }

    const freed = groups.reduce((acc, g) => acc + (g.entries?.slice(1).reduce((s, e) => s + (e.size_bytes ?? 0), 0) ?? 0), 0);

    _setBody(`
      <div style="color:#ccc;font-size:13px;margin-bottom:10px">
        <strong style="color:#f38ba8">${count}</strong> grupo${count !== 1 ? 's' : ''} de duplicados
        ${freed > 0 ? `&nbsp;·&nbsp; <span style="color:#888">${_fmtBytes(freed)} recuperables</span>` : ''}
      </div>
      <p style="color:#666;font-size:12px;margin:0">
        En cada grupo se conserva la mejor versión; las demás se eliminan.
      </p>
    `);
    _setActions('Eliminar duplicados', _deleteDupes, 'Omitir', () => { _skipped.dupes = true; _step = 3; _render(); });
  } catch (e) {
    _setBody(`<p class="error-msg">Error al buscar duplicados: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 3; _render(); }, null, null);
  }
}

async function _deleteDupes() {
  _setBody('<p style="color:#888;font-size:13px">Eliminando duplicados…</p>');
  _setActions('Siguiente', null, null, null);

  try {
    const r = await apiPost('/api/duplicates/delete-all', {});
    _results.dupes = { ...(_results.dupes ?? {}), deleted: r.deleted ?? 0, freed_bytes: r.freed_bytes ?? 0 };
    _setBody(`
      <div style="text-align:center;padding:20px 0">
        <div style="font-size:30px;margin-bottom:8px">✅</div>
        <div style="color:#ccc;font-size:14px;font-weight:600">Duplicados eliminados</div>
        <div style="color:#888;font-size:12px;margin-top:8px">
          <strong style="color:#4ec9b0">${r.deleted ?? 0}</strong> archivos eliminados
          ${r.freed_bytes > 0 ? ` &nbsp;·&nbsp; ${_fmtBytes(r.freed_bytes)} liberados` : ''}
        </div>
      </div>
    `);
    _setActions('Siguiente', () => { _step = 3; _render(); }, null, null);
  } catch (e) {
    _setBody(`<p class="error-msg">Error al eliminar: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 3; _render(); }, null, null);
  }
}

// ── Step 3: Sync ──────────────────────────────────────────────────────────────

async function _renderSync() {
  _setBody('<p style="color:#888;font-size:13px">Calculando cambios de sync…</p>');
  _setActions('Sincronizar', null, 'Omitir', () => { _skipped.sync = true; _step = 4; _render(); });

  try {
    const status = await apiFetch('/api/job-status');
    _prevResultTs.sync = status.sync_result?.result_ts ?? '';
    await apiPost('/api/sync', { dry_run: true });
    _pollSync(true);
  } catch (e) {
    _setBody(`<p class="error-msg">Error al calcular sync: ${_h(e.message)}</p>`);
    _setActions('Siguiente', () => { _step = 4; _render(); }, null, null);
  }
}

function _pollSync(isDryRun) {
  _stopPoll();
  _pollTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      const r = s.sync_result;
      if (!s.sync_running && r && r.result_ts && r.result_ts !== _prevResultTs.sync) {
        _stopPoll();
        _prevResultTs.sync = r.result_ts;

        if (isDryRun) {
          const up   = r.uploaded   ?? 0;
          const down = r.downloaded ?? 0;
          const conf = r.conflicts  ?? 0;
          _results.sync = { preview: r };

          if (up === 0 && down === 0) {
            _setBody(`
              <div style="text-align:center;padding:20px 0">
                <div style="font-size:28px;margin-bottom:8px">✅</div>
                <div style="color:#888;font-size:13px">Saves al día — nada que sincronizar</div>
              </div>
            `);
            _setActions('Siguiente', () => { _step = 4; _render(); }, null, null);
          } else {
            _setBody(`
              <div style="color:#ccc;font-size:13px;margin-bottom:12px">Vista previa de sync:</div>
              <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px">
                <span>⬆️ <strong style="color:#7aa2f7">${up}</strong> para subir</span>
                <span>⬇️ <strong style="color:#4ec9b0">${down}</strong> para bajar</span>
                ${conf ? `<span>⚠️ <strong style="color:#e5c200">${conf}</strong> conflictos</span>` : ''}
              </div>
              ${r.error ? `<p class="error-msg" style="margin-top:10px">${_h(r.error)}</p>` : ''}
            `);
            _setActions('Sincronizar ahora', _runSync, 'Omitir', () => { _skipped.sync = true; _step = 4; _render(); });
          }
        } else {
          _results.sync = { result: r };
          _setBody(`
            <div style="text-align:center;padding:20px 0">
              <div style="font-size:30px;margin-bottom:8px">✅</div>
              <div style="color:#ccc;font-size:14px;font-weight:600">Sync completado</div>
              <div style="color:#888;font-size:12px;margin-top:8px">
                ⬆️ <strong style="color:#7aa2f7">${r.uploaded ?? 0}</strong> subidos
                &nbsp;·&nbsp;
                ⬇️ <strong style="color:#4ec9b0">${r.downloaded ?? 0}</strong> descargados
                ${r.errors ? ` &nbsp;·&nbsp; <span style="color:#f38ba8">${r.errors} errores</span>` : ''}
              </div>
            </div>
          `);
          _setActions('Ver resumen', () => { _step = 4; _render(); }, null, null);
        }
      }
    } catch {}
  }, 2000);
}

async function _runSync() {
  _setBody('<p style="color:#888;font-size:13px">Sincronizando…</p>');
  _setActions('Siguiente', null, null, null);

  try {
    const status = await apiFetch('/api/job-status');
    _prevResultTs.sync = status.sync_result?.result_ts ?? '';
    await apiPost('/api/sync', { dry_run: false });
    _pollSync(false);
  } catch (e) {
    _setBody(`<p class="error-msg">Error en sync: ${_h(e.message)}</p>`);
    _setActions('Ver resumen', () => { _step = 4; _render(); }, null, null);
  }
}

// ── Step 4: Summary ───────────────────────────────────────────────────────────

function _renderSummary() {
  _updateStepIndicator();
  const rows = [];

  const scan = _results.scan;
  if (_skipped.scan) {
    rows.push(_summaryRow('⏭️', 'Escaneo', 'Omitido'));
  } else if (scan) {
    rows.push(_summaryRow('🔍', 'Escaneo',
      scan.error ? `Error` : `${scan.roms_detected ?? 0} ROMs detectados`));
  }

  const org = _results.organize;
  if (_skipped.organize) {
    rows.push(_summaryRow('⏭️', 'Organizar', 'Omitido'));
  } else if (org) {
    const n = org.renamed ?? org.plan_count ?? 0;
    rows.push(_summaryRow('✏️', 'Organizar', n === 0 ? 'Ya organizado' : `${n} renombrados`));
  }

  const dupes = _results.dupes;
  if (_skipped.dupes) {
    rows.push(_summaryRow('⏭️', 'Duplicados', 'Omitido'));
  } else if (dupes) {
    const n = dupes.deleted ?? 0;
    rows.push(_summaryRow('🗂️', 'Duplicados',
      n === 0 ? 'Sin duplicados' : `${n} eliminados${dupes.freed_bytes > 0 ? ' · ' + _fmtBytes(dupes.freed_bytes) + ' lib.' : ''}`));
  }

  const sync = _results.sync;
  if (_skipped.sync) {
    rows.push(_summaryRow('⏭️', 'Sync', 'Omitido'));
  } else if (sync?.result) {
    const r = sync.result;
    rows.push(_summaryRow('☁️', 'Sync', `⬆️${r.uploaded ?? 0} ⬇️${r.downloaded ?? 0}${r.errors ? ' ⚠️' + r.errors : ''}`));
  } else if (sync?.preview) {
    rows.push(_summaryRow('☁️', 'Sync', 'Vista previa calculada (no ejecutado)'));
  }

  _setBody(`
    <div style="color:#888;font-size:12px;margin-bottom:12px">Todas las operaciones completadas.</div>
    <div style="display:flex;flex-direction:column;gap:6px">${rows.join('')}</div>
  `);
  _setActions('Cerrar', closeFlowWizard, null, null);
}

function _summaryRow(icon, label, value) {
  return `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--bg-panel);border:1px solid var(--border-s);border-radius:6px">
      <span style="color:#ccc;font-size:13px">${icon} ${label}</span>
      <span style="color:#888;font-size:12px">${value}</span>
    </div>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _h(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function _fmtBytes(n) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(1)} ${units[i]}`;
}
