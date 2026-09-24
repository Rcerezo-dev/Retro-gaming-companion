// js/tabs/organize.js — Plan (rename) + Apply
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { getDeviceConnected, getActiveDevice } from '../state.js';

// ── Plan ─────────────────────────────────────────────────────────────────────
function _chk(id, def = '1') {
  const el = document.getElementById(id);
  return el ? (el.checked ? '1' : '0') : def;
}

function toggleShaLength() {
  const label = document.getElementById('sha-length-label');
  if (label) label.classList.toggle('hidden', !(document.getElementById('fmt-sha').checked));
}

function _planQueryString() {
  const shaLength = document.getElementById('fmt-sha-length')?.value || '8';
  return `?include_region=${_chk('fmt-region')}&include_revision=${_chk('fmt-revision')}` +
         `&include_platform=${_chk('fmt-platform', '0')}&include_sha=${_chk('fmt-sha', '0')}` +
         `&sha_length=${shaLength}`;
}

// UX-1/2-5: Update button disabled state based on device connectivity
function _updateApplyButtonState() {
  const btn = document.getElementById('btn-apply');
  if (!btn) return;

  const activeDevice = getActiveDevice();
  const deviceConnected = getDeviceConnected();
  const targetsDevice = activeDevice === 'anbernic';

  const shouldDisable = btn.disabled || (targetsDevice && !deviceConnected);
  const wasDisabled = btn.disabled;

  btn.disabled = shouldDisable;

  // Update tooltip if needed
  if (targetsDevice && !deviceConnected) {
    btn.title = 'Consola Android no conectada. Conecta por USB o inserta la SD card.';
  } else if (wasDisabled && shouldDisable) {
    btn.title = ''; // Clear old tooltip if button is disabled for other reasons
  }
}

async function loadPlan() {
  const el = document.getElementById('plan-content');
  el.innerHTML = '<p class="loading">Cargando…</p>';
  try {
    const root = window._deviceRoot();
    const rootParam = root ? `&source_root=${encodeURIComponent(root)}` : '';
    const [d, cfg] = await Promise.all([apiFetch('/api/plan' + _planQueryString() + rootParam), apiFetch('/api/config')]);
    const planBar = document.getElementById('plan-context-bar');
    if (planBar) {
      let barHtml = '';
      if (window._activeDevice === 'pc') {
        const r = cfg.library_root || '(no configurado)';
        barHtml = `Viendo: <span style="color:var(--c-teal)">PC — ${r}</span> &nbsp;·&nbsp; <span style="color:var(--c-dim)">Los saves se renombran junto al ROM · Cada cambio queda registrado en la base de datos</span>`;
      } else {
        const r = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        barHtml = `Viendo: <span style="color:var(--c-orange)">${window._devName} — ${r}</span> &nbsp;·&nbsp; <span style="color:var(--c-dim)">Los saves se renombran junto al ROM · Cada cambio queda registrado en la base de datos</span>`;
      }
      planBar.innerHTML = barHtml;
      planBar.classList.remove('hidden');
    }

    // Update preview bar
    const previewEl  = document.getElementById('fmt-preview');
    const previewTxt = document.getElementById('fmt-preview-text');
    const firstPending = d.pending?.[0] || d.already_correct_example;
    if (previewEl && previewTxt && d.pending.length > 0) {
      previewTxt.textContent = d.pending[0].target_name;
      previewEl.classList.remove('hidden');
    } else if (previewEl) {
      previewEl.classList.add('hidden');
    }

    // ── C2: Summary bar ──────────────────────────────────────────────────────
    const summaryBar = document.getElementById('plan-summary-bar');
    if (summaryBar) {
      const pendingN   = d.pending.length;
      const conflictsN = d.conflicts.length;
      const unmatchedN = d.unmatched_count || 0;
      const correctN   = d.already_correct || 0;
      const parts = [];
      if (pendingN > 0)   parts.push(`<span style="color:var(--c-teal);font-weight:600">${pendingN}</span> <span style="color:var(--c-muted)">listos para renombrar</span>`);
      if (correctN > 0)   parts.push(`<span style="color:var(--c-dim)">${correctN} ya correctos</span>`);
      if (conflictsN > 0) parts.push(`<span style="color:var(--c-red);font-weight:600">${conflictsN}</span> <span style="color:var(--c-muted)">conflictos</span>`);
      if (unmatchedN > 0) parts.push(`<span style="color:var(--c-muted)">${unmatchedN} sin match en catálogo</span>`);
      summaryBar.innerHTML = parts.join('<span style="color:var(--c-ghost);margin:0 4px">·</span>');
      summaryBar.classList.toggle('hidden', !(parts.length));
    }

    // PLAN-UX-3: filtro por dispositivo retirado — /api/plan ya devuelve un solo
    // dispositivo (el activo global) desde DEVSEL-FIX-3
    const pending = d.pending || [];

    // ── C3: Update action buttons with counts ─────────────────────────────────
    const btnApply    = document.getElementById('btn-apply');
    const btnResolve  = document.getElementById('btn-resolve-conflicts');
    if (btnApply) {
      const n = pending.length;
      btnApply.textContent = n > 0 ? `Renombrar ${n} archivo${n !== 1 ? 's' : ''}` : 'Nada que renombrar';
      btnApply.disabled = n === 0;
      // UX-1/2-5: Update disabled state based on device connectivity
      _updateApplyButtonState();
    }
    if (btnResolve) {
      const collisions = (d.conflicts || []).filter(c => c.reason === 'collision').length;
      if (collisions > 0) {
        btnResolve.textContent = `Resolver ${collisions} colisión${collisions !== 1 ? 'es' : ''}`;
        btnResolve.classList.remove('hidden');
      } else {
        btnResolve.classList.add('hidden');
      }
    }
    if (d.total === 0) {
      if (window._activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        el.innerHTML = `<p class="empty">No hay ROMs de esta ruta en la base de datos.<br><span style="color:var(--c-muted);font-size:12px">Ruta ${window._devName}: <code>${ab}</code><br>Escanea la consola primero (Overview → Escanear → consola Android por ADB).</span></p>`;
      } else {
        el.innerHTML = '<p class="empty">Sin juegos identificados. Ejecuta <strong>Identificar (catálogos)</strong> primero desde la pestaña Inicio.</p>';
      }
      return;
    }

    let html = '';
    if (pending.length) {
      const savesNote = d.total_saves_affected > 0 ? ` <span style="color:var(--c-yellow);font-size:11px">· ${d.total_saves_affected} save(s) se renombrarán también</span>` : '';
      html += `<h3 style="color:var(--c-blue);margin-bottom:12px">Listos para renombrar — ${pending.length}${savesNote}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Platform</th><th>Dispositivo</th><th>From</th><th>To</th><th style="text-align:center">Saves</th></tr></thead><tbody>';
      html += pending.map(op => {
        const devLabel = op.device === 'pc'
          ? '<span style="color:var(--c-teal);font-size:10px">PC</span>'
          : '<span style="color:var(--c-orange);font-size:10px">Android</span>';
        return `<tr>
          <td>${op.platform||'<span style="color:var(--c-dim)">Unknown</span>'}</td>
          <td>${devLabel}</td>
          <td title="${window._h(op.source)}">${window._h(op.source_name)}</td>
          <td style="color:var(--c-teal)" title="${window._h(op.target)}">${window._h(op.target_name)}</td>
          <td style="text-align:center;color:${op.companion_saves > 0 ? 'var(--c-yellow)' : '#555'}">${op.companion_saves > 0 ? op.companion_saves : '—'}</td>
        </tr>`;
      }).join('');
      html += '</tbody></table></div>';
    }
    if (d.conflicts.length) {
      // PLAN-UX-5: el backend solo emite 'collision' o 'disk' (collision_resolver.py:46,
      // operation_planner.py:140) — la rama "unknown" era código muerto y se retiró
      const collisions = d.conflicts.filter(c => c.reason === 'collision');
      const diskConflicts = d.conflicts.filter(c => c.reason === 'disk');

      html += `<h3 style="color:var(--c-red);margin:20px 0 8px">Conflictos — ${d.conflicts.length}</h3>`;

      if (collisions.length) {
        const hasRaData = collisions.some(c => c.ra_achievements != null);
        html += `<div style="background:var(--rv-tint-amber-bg);border:1px solid var(--rv-tint-amber-border);border-left:3px solid var(--c-orange);border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:var(--c-orange);font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26A0; Colisión de plan (${collisions.length}) — dos ROMs quieren el mismo nombre canónico`;
        html += `</div>`;
        html += `<div style="color:var(--c-muted);font-size:11px;margin-bottom:10px">`;
        html += `Causa habitual: tienes múltiples versiones del mismo juego (regional, revisión) y la opción <strong>Región</strong> o <strong>Revisión</strong> está desactivada en el formato. Actívalas para que cada versión obtenga un nombre único.<br>`;
        html += `Opciones: <button class="btn" style="padding:2px 10px;font-size:11px;margin:0 4px" onclick="applyKeepBoth()">Renombrar (añadir sufijo _1 _2)</button><br>`;
        html += `Si tienes caché de RetroAchievements, resuélvelo desde <strong>2. Revisar copias</strong> (abajo), que conserva solo la versión con logros.`;
        html += `</div>`;
        if (hasRaData) {
          html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th style="text-align:center">Logros RA</th><th>Nombre canónico</th><th>Resultado previsto</th></tr></thead><tbody>';
          html += collisions.map(op => {
            const safeSource = op.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
            const safeName   = op.source_name.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
            const raCell = op.ra_achievements != null
              ? `<span style="color:var(--c-yellow)">${op.ra_achievements}</span>`
              : '<span style="color:var(--c-dim)">—</span>';
            let roleCell = '';
            if (op.ra_role === 'winner') {
              roleCell = `<span style="color:var(--c-teal);font-weight:600">&#x2713; Ganador RA</span>`;
            } else if (op.ra_role === 'loser') {
              roleCell = `<span style="color:var(--c-muted)">&#x2192; _descartados/</span>`;
            } else {
              roleCell = `<button class="btn" style="padding:1px 8px;font-size:11px;color:var(--c-orange);border-color:var(--c-orange)" onclick="_discardCollisionEntry(${op.game_id},'${safeSource}','${safeName}')">Descartar</button>`;
            }
            return `<tr style="${op.ra_role === 'winner' ? 'background:var(--rv-tint-ok-bg)' : op.ra_role === 'loser' ? 'opacity:0.6' : ''}">
              <td class="mono" style="color:var(--c-lblue)" data-game-id="${op.game_id}" data-path="${safeSource}" data-target="${window._h(op.target_name)}">${window._h(op.source_name)}</td>
              <td style="text-align:center">${raCell}</td>
              <td class="mono" style="color:var(--c-orange)">${window._h(op.target_name)}</td>
              <td style="font-size:11px">${roleCell}</td>
            </tr>`;
          }).join('');
          html += '</tbody></table></div></div>';
        } else {
          html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Nombre bloqueado</th><th></th></tr></thead><tbody>';
          html += collisions.map(op => {
            const safeSource = op.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
            const safeName   = op.source_name.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
            return `<tr>
              <td class="mono" style="color:var(--c-lblue)" data-game-id="${op.game_id}" data-path="${safeSource}" data-target="${window._h(op.target_name)}">${window._h(op.source_name)}</td>
              <td class="mono" style="color:var(--c-orange)">${window._h(op.target_name)}</td>
              <td><button class="btn" style="padding:1px 8px;font-size:11px;color:var(--c-orange);border-color:var(--c-orange)" onclick="_discardCollisionEntry(${op.game_id},'${safeSource}','${safeName}')">Descartar</button></td>
            </tr>`;
          }).join('');
          html += '</tbody></table></div></div>';
        }
      }

      if (diskConflicts.length) {
        const hasRaData = diskConflicts.some(c => c.ra_achievements != null || c.ra_target_achievements != null);
        html += `<div style="background:var(--rv-tint-warn-bg);border:1px solid var(--rv-tint-warn-border);border-left:3px solid var(--c-red);border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:var(--c-red);font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26D4; Conflicto de disco (${diskConflicts.length}) — el nombre de destino ya está ocupado por un archivo diferente`;
        html += `</div>`;
        html += `<div style="color:var(--c-muted);font-size:11px;margin-bottom:10px">`;
        html += `<strong style="color:var(--c-text)">¿Por qué no se detecta como duplicado?</strong><br>`;
        html += `Un duplicado tiene el <strong>mismo contenido exacto</strong> (mismo hash SHA1). `;
        html += `Estos conflictos son distintos: el archivo que quieres renombrar y el que ya ocupa el nombre de destino son ROMs <em>diferentes</em> (distinto contenido), `;
        html += `pero el catálogo les asigna el mismo nombre canónico — por ejemplo, <code>Super Mario Bros (E)</code> y <code>Super Mario Bros (Europe)</code> son el mismo juego con nombres distintos.<br><br>`;
        html += `<strong style="color:var(--c-text)">Qué hacer:</strong> este conflicto ya aparece en <strong>2. Revisar copias</strong> (abajo) con el criterio RA aplicado. `;
        html += `Si son versiones distintas y quieres conservar ambas, activa la opción <strong>Región</strong> o <strong>Revisión</strong> en el formato (arriba) para que cada una obtenga un nombre único.`;
        html += `</div>`;
        html += `<div style="margin-bottom:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">`;
        html += `<button class="btn" style="font-size:12px;padding:4px 12px" title="Activa Región y Revisión en las opciones de formato y recalcula el plan para que cada versión obtenga un nombre único" onclick="document.getElementById('fmt-region').checked=true;document.getElementById('fmt-revision').checked=true;loadPlan()">&#x21BB; Recalcular con Región + Revisión</button>`;
        html += `<span style="color:var(--c-dim);font-size:11px">Resuelve la mayoría de conflictos de disco añadiendo la región o versión al nombre</span>`;
        html += `</div>`;
        if (hasRaData) {
          html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM (pendiente)</th><th style="text-align:center">Logros RA</th><th>Destino bloqueado</th><th style="text-align:center">Logros RA</th><th>Resultado previsto</th></tr></thead><tbody>';
          html += diskConflicts.map(op => {
            const srcRa = op.ra_achievements != null ? `<span style="color:var(--c-yellow)">${op.ra_achievements}</span>` : '<span style="color:var(--c-dim)">—</span>';
            const tgtRa = op.ra_target_achievements != null ? `<span style="color:var(--c-yellow)">${op.ra_target_achievements}</span>` : '<span style="color:var(--c-dim)">—</span>';
            let roleCell = '';
            if (op.ra_role === 'winner') roleCell = `<span style="color:var(--c-teal);font-weight:600">&#x2713; Ganador RA — se renombrará</span>`;
            else if (op.ra_role === 'loser') roleCell = `<span style="color:var(--c-muted)">&#x2192; _descartados/ (menos logros)</span>`;
            return `<tr>
              <td class="mono" style="color:var(--c-lblue)">${window._h(op.source_name)}</td>
              <td style="text-align:center">${srcRa}</td>
              <td class="mono" style="color:var(--c-red)">${window._h(op.target_name)}</td>
              <td style="text-align:center">${tgtRa}</td>
              <td style="font-size:11px">${roleCell}</td>
            </tr>`;
          }).join('');
          html += '</tbody></table></div></div>';
        } else {
          html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Destino bloqueado</th></tr></thead><tbody>';
          html += diskConflicts.map(op => `<tr>
            <td class="mono" style="color:var(--c-lblue)">${window._h(op.source_name)}</td>
            <td class="mono" style="color:var(--c-red)">${window._h(op.target_name)}</td>
          </tr>`).join('');
          html += '</tbody></table></div></div>';
        }
      }

    }
    if (d.already_correct > 0) {
      html += `<p style="color:var(--c-dim);margin-top:16px">${d.already_correct} archivo(s) ya tienen el nombre correcto.</p>`;
    }
    if (d.unmatched_count > 0) {
      html += `<details style="margin-top:20px;border:1px solid var(--c-border);border-radius:6px;padding:10px 14px;background:var(--rv-tint-neutral-bg)">`;
      html += `<summary style="cursor:pointer;color:var(--c-muted);font-size:13px;user-select:none">`;
      html += `${d.unmatched_count} ROM${d.unmatched_count !== 1 ? 's' : ''} sin match en catálogo (no se renombrarán) `;
      html += `— <a href="#" style="color:var(--c-blue);font-size:12px" onclick="event.preventDefault();goToGames(null,'unmatched')">Ver en Games →</a>`;
      html += `</summary>`;
      const _reasonLabels = {
        'no_sha1':       { text: 'sin hashear', color: '#888',    tip: 'Ejecuta un scan completo (sin Quick mode) para calcular el hash' },
        'no_dat':        { text: 'sin catálogo DAT', color: 'var(--c-yellow)', tip: 'No se ha cargado ninguna base de datos (DAT) para esta plataforma — pulsa Identificar (catálogos) primero' },
        'hash_not_found':{ text: 'hash no en DAT', color: 'var(--c-orange)', tip: 'El hash del archivo no está en ningún DAT cargado — puede ser una versión no reconocida' },
      };
      html += `<div style="margin-top:10px;overflow-x:auto"><table><thead><tr><th>Platform</th><th>Filename</th><th>Razón</th></tr></thead><tbody>`;
      html += d.unmatched.map(g => {
        const r = _reasonLabels[g.unmatched_reason] || { text: g.unmatched_reason || '?', color: '#555', tip: '' };
        const badge = `<span style="font-size:10px;color:${r.color};background:var(--c-panel);padding:1px 6px;border-radius:3px" title="${window._h(r.tip)}">${window._h(r.text)}</span>`;
        return `<tr>
          <td>${window._platBadge(g.platform)}</td>
          <td class="mono" style="color:var(--c-lblue);font-size:12px">${window._h(g.original_filename)}</td>
          <td>${badge}</td>
        </tr>`;
      }).join('');
      html += `</tbody></table></div></details>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Apply action ──────────────────────────────────────────────────────────────
async function applyKeepBoth() {
  const btnR = document.getElementById('btn-resolve-conflicts');
  const n = parseInt(btnR?.textContent?.match(/\d+/)?.[0] || '0');
  // PLAN-UX-2: modal propio en vez de confirm() nativo
  _showConfirm(
    'Resolver colisiones',
    `¿Resolver <strong>${n} colisión${n !== 1 ? 'es' : ''}</strong> añadiendo sufijo _1 _2?<br>Los archivos en conflicto recibirán nombres únicos.`,
    'Resolver',
    async () => {
      const applyBody = {
        keep_both: true,
        format_opts: {
          include_region:   document.getElementById('fmt-region').checked,
          include_revision: document.getElementById('fmt-revision').checked,
          include_platform: document.getElementById('fmt-platform').checked,
          include_sha:      document.getElementById('fmt-sha').checked,
          sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
        }
      };
      const applyRoot = window._deviceRoot();
      if (applyRoot) applyBody.source_root = applyRoot;

      if (btnR) { btnR.disabled = true; btnR.textContent = 'Resolviendo…'; }
      const btn = document.getElementById('btn-apply');
      if (btn) btn.disabled = true;

      const wrap = document.getElementById('apply-progress-wrap');
      const bar  = document.getElementById('apply-progress-bar');
      const lbl  = document.getElementById('apply-progress-label');
      const pct  = document.getElementById('apply-progress-pct');
      if (wrap) wrap.classList.remove('hidden');

      try {
        await apiPost('/api/apply', applyBody);
        let done = false;
        while (!done) {
          await new Promise(r => setTimeout(r, 500));
          const s = await apiFetch('/api/job-status');
          if (s.apply_running && s.apply_progress) {
            const p = s.apply_progress;
            const fraction = p.total > 0 ? p.current / p.total : 0;
            if (bar) bar.style.width = Math.round(fraction * 100) + '%';
            if (pct) pct.textContent = Math.round(fraction * 100) + '%';
            if (lbl) lbl.textContent = p.current_file ? `Resolviendo: ${p.current_file}` : 'Resolviendo…';
          }
          if (!s.apply_running && s.apply_result) {
            done = true;
            const r = s.apply_result;
            if (!r.error) showToast(`Resueltos: ${r.renamed} renombrados, ${r.conflicts} conflictos restantes`, r.conflicts > 0 ? 'info' : 'ok');
          }
        }
        await loadPlan();
        window.loadOverview();
      } catch(e) {
        showToast('Error: ' + e.message, 'err');
      } finally {
        setTimeout(() => { if (wrap) wrap.classList.add('hidden'); if (bar) bar.style.width = '0%'; }, 2000);
        if (btn) btn.disabled = false;
      }
    }
  );
}

// Discard a single collision entry from the plan view (row-level button)
async function _discardCollisionEntry(gameId, sourcePath, filename) {
  _showConfirm(
    'Descartar ROM',
    `¿Mover <strong>${window._h(filename)}</strong> a <code>_descartados/</code> y eliminar de la base de datos?<br>` +
    `<span style="color:var(--c-yellow)">Los archivos de <code>_descartados/</code> se purgan a los 30 días.</span>`,
    'Descartar',
    async () => {
      try {
        await apiPost('/api/duplicates/delete', { game_id: gameId, source_path: sourcePath });
        showToast(`✓ ${filename} eliminado`, 'ok');
        setTimeout(() => loadPlan(), 800);
      } catch (e) {
        showToast('Error: ' + e.message, 'err');
      }
    }
  );
}

async function doApply() {
  const btn = document.getElementById('btn-apply');
  const total = parseInt(btn?.textContent?.match(/\d+/)?.[0] || '0');
  if (!total) return;

  // UX-1/2-5: Check device connectivity if targeting Android device
  const activeDevice = getActiveDevice();
  if (activeDevice === 'anbernic' && !getDeviceConnected()) {
    showToast('Consola Android no conectada. Conecta por USB o inserta la SD card.', 'err');
    return;
  }

  // PLAN-UX-2: modal propio en vez de confirm() nativo.
  _showConfirm(
    'Renombrar archivos',
    `¿Renombrar <strong>${total} archivo${total !== 1 ? 's' : ''}</strong> en disco?<br>Los saves compañeros se moverán automáticamente.<br><span style="color:var(--c-muted)">Cada cambio queda registrado en la base de datos — puedes deshacerlo con "Deshacer último apply" si algo sale mal.</span>`,
    'Renombrar',
    async () => {
      const applyBody = {
        format_opts: {
          include_region:   document.getElementById('fmt-region').checked,
          include_revision: document.getElementById('fmt-revision').checked,
          include_platform: document.getElementById('fmt-platform').checked,
          include_sha:      document.getElementById('fmt-sha').checked,
          sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
        }
      };
      const applyRoot = window._deviceRoot();
      if (applyRoot) applyBody.source_root = applyRoot;

      // Disable buttons while running
      if (btn) { btn.disabled = true; btn.textContent = 'Renombrando…'; }
      const btnR = document.getElementById('btn-resolve-conflicts');
      if (btnR) btnR.disabled = true;

      const wrap = document.getElementById('apply-progress-wrap');
      const bar  = document.getElementById('apply-progress-bar');
      const lbl  = document.getElementById('apply-progress-label');
      const pct  = document.getElementById('apply-progress-pct');
      if (wrap) wrap.classList.remove('hidden');

      try {
        await apiPost('/api/apply', applyBody);

        // Poll for completion
        let done = false;
        while (!done) {
          await new Promise(r => setTimeout(r, 500));
          const s = await apiFetch('/api/job-status');
          if (s.apply_running && s.apply_progress) {
            const p = s.apply_progress;
            const fraction = p.total > 0 ? p.current / p.total : 0;
            const pctVal = Math.round(fraction * 100);
            if (bar) bar.style.width = pctVal + '%';
            if (pct) pct.textContent = pctVal + '%';
            if (lbl) lbl.textContent = p.current_file ? `Renombrando: ${p.current_file}` : 'Renombrando…';
          }
          if (!s.apply_running && s.apply_result) {
            done = true;
            const r = s.apply_result;
            if (r.error) {
              showToast('Error: ' + r.error, 'err');
            } else {
              const savesInfo   = r.saves_renamed > 0 ? ` · ${r.saves_renamed} saves` : '';
              const zipsInfo    = r.zips_extracted > 0 ? ` · ${r.zips_extracted} ZIPs descomprimidos` : '';
              const failedInfo  = r.failed > 0 ? ` · ${r.failed} fallidos` : '';
              const conflictInfo = r.conflicts > 0 ? ` · ${r.conflicts} conflictos restantes` : '';
              showToast(`✓ ${r.renamed} renombrados${savesInfo}${zipsInfo}${failedInfo}${conflictInfo}`,
                r.failed > 0 || r.conflicts > 0 ? 'info' : 'ok');
              if (bar) bar.style.width = '100%';
              if (pct) pct.textContent = '100%';
              if (lbl) lbl.textContent = 'Completado';
              // D8-2: show error details if any
              const errDetails = r.error_details || r.skip_details || [];
              const errPanel = document.getElementById('apply-error-details');
              const errList  = document.getElementById('apply-error-list');
              const errCount = document.getElementById('apply-error-count');
              if (errDetails.length > 0 && errPanel && errList && errCount) {
                errCount.textContent = errDetails.length + ' archivo(s) con errores o no encontrados:';
                errList.innerHTML = errDetails.map(e => '<div style="padding:1px 0">&#x25B8; ' + window._h(e) + '</div>').join('');
                errPanel.classList.remove('hidden');
              } else if (errPanel) {
                errPanel.classList.add('hidden');
              }
            }
          }
        }

        await loadPlan();
        window.loadOverview();
      } catch(e) {
        showToast('Error al aplicar: ' + e.message, 'err');
      } finally {
        setTimeout(() => { if (wrap) wrap.classList.add('hidden'); if (bar) bar.style.width = '0%'; }, 2000);
        if (btnR) btnR.disabled = false;
      }
    }
  );
}

// ── MEJ-2: deshacer el último apply ──────────────────────────────────────────
async function doUndoLastApply() {
  _showConfirm(
    'Deshacer último apply',
    'Se revertirán los renombrados del último apply (el que se ejecutó más recientemente), archivo por archivo.<br><span style="color:var(--c-muted)">Si algún archivo se movió o borró después del apply, ese se salta y se reporta.</span>',
    'Deshacer',
    async () => {
      const btn = document.getElementById('btn-undo-apply');
      if (btn) { btn.disabled = true; btn.textContent = 'Deshaciendo…'; }
      try {
        const applyRoot = window._deviceRoot();
        await apiPost('/api/undo-last-apply', applyRoot ? { source_root: applyRoot } : {});

        let done = false;
        while (!done) {
          await new Promise(r => setTimeout(r, 500));
          const s = await apiFetch('/api/undo-last-apply-status');
          if (!s.running && s.result) {
            done = true;
            const r = s.result;
            if (r.error) {
              showToast('Error: ' + r.error, 'err');
            } else if (r.message) {
              showToast(r.message, 'info');
            } else {
              const failedInfo  = r.failed  > 0 ? ` · ${r.failed} fallidos`  : '';
              const skippedInfo = r.skipped > 0 ? ` · ${r.skipped} saltados` : '';
              showToast(`✓ ${r.undone} deshechos${failedInfo}${skippedInfo}`,
                r.failed > 0 ? 'info' : 'ok');
            }
          }
        }
        await loadPlan();
        window.loadOverview();
      } catch (e) {
        showToast('Error al deshacer: ' + e.message, 'err');
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Deshacer último apply'; }
      }
    }
  );
}

// ── Public exports ────────────────────────────────────────────────────────────
export {
  _chk, toggleShaLength, _planQueryString,
  loadPlan, applyKeepBoth, doApply, doUndoLastApply, _discardCollisionEntry,
};
