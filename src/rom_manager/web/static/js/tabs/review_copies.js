// js/tabs/review_copies.js — TABS-FIX-6: "Revisar copias", cola única que
// fusiona duplicados SHA1/semánticos/RA y colisiones del plan de Organizar.
// Reemplaza la pestaña Duplicados + el botón "Resolver con RA" suelto.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { _showConfirm } from '../components/modal.js';

let _reviewGroups = [];

// Mismo texto en todas las confirmaciones de esta pantalla (TABS-FIX-4): nunca
// "no se puede deshacer" — el archivo va a _descartados/, recuperable 30 días.
const _TRASH_NOTE = '<span style="color:var(--c-yellow)">Los archivos se moverán a <code>_descartados/</code> (se purgan a los 30 días).</span>';

const _REASON_LABELS = {
  sha1: { text: 'SHA1 idéntico', color: 'var(--c-teal)' },
  title: { text: 'Otra versión', color: 'var(--c-yellow)' },
  ra: { text: 'Logros RA', color: 'var(--c-amber)' },
  disk: { text: 'Colisión de disco', color: 'var(--c-red)' },
  collision: { text: 'Colisión de nombre', color: 'var(--c-orange)' },
};

const _CONFLICT_REASONS = new Set(['disk', 'collision']);

function _jsStr(s) {
  return String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

async function loadReviewQueue() {
  const el = document.getElementById('review-queue-content');
  const btnAll = document.getElementById('btn-review-apply-all');
  if (!el) return;
  el.innerHTML = '<p class="loading">Cargando…</p>';
  try {
    const d = await apiFetch('/api/review-queue');
    _reviewGroups = d.groups || [];
    if (btnAll) {
      btnAll.classList.toggle('hidden', _reviewGroups.length === 0);
      btnAll.textContent = `Aplicar todas las recomendaciones (${_reviewGroups.length})`;
    }
    _renderReviewQueue(_reviewGroups, d.wasted_bytes || 0);
  } catch (e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function _renderReviewQueue(groups, wastedBytes) {
  const el = document.getElementById('review-queue-content');
  if (!el) return;
  if (groups.length === 0) {
    el.innerHTML = window._emptyState(
      '✅',
      'Sin copias pendientes de revisión',
      'Aquí aparecen juntos duplicados exactos, versiones alternativas, conflictos de logros RA y colisiones de nombre del plan de renombrado.',
      '',
      null
    );
    return;
  }
  let html = `<p style="color:var(--c-muted);margin-bottom:12px">${groups.length} grupo${groups.length !== 1 ? 's' : ''} — ~${window.fmtSize(wastedBytes)} recuperables</p>`;
  html += groups.map(_renderReviewGroup).join('');
  el.innerHTML = html;
}

function _renderReviewGroup(g) {
  const isConflictGroup = g.reasons.some((r) => _CONFLICT_REASONS.has(r));
  const badges = g.reasons
    .map((r) => {
      const info = _REASON_LABELS[r] || { text: r, color: 'var(--c-muted)' };
      return `<span class="badge" style="background:transparent;border:1px solid ${info.color};color:${info.color};font-size:10px;margin-left:4px">${info.text}</span>`;
    })
    .join('');
  const wastedLabel = g.wasted_bytes > 0 ? ` · ${window.fmtSize(g.wasted_bytes)} recuperables` : '';
  const actions = isConflictGroup
    ? `<button class="btn" style="font-size:11px;padding:3px 10px;border-color:var(--c-purple);color:var(--c-purple)" onclick="doResolveRaConflicts()">Resolver con RA (todos los conflictos del plan)</button>`
    : `<button class="btn primary" style="font-size:11px;padding:3px 10px" onclick="applyReviewGroup('${_jsStr(g.group_key)}')">Aplicar recomendación</button>
       <button class="btn" style="font-size:11px;padding:3px 10px;color:var(--c-muted)" onclick="markReviewGroupIntentional('${_jsStr(g.group_key)}')">Copia intencional</button>`;
  return `<details class="dup-group" style="margin-bottom:10px" open>
    <summary style="cursor:pointer;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:6px 0">
      <span>${window._h(g.canonical_title || '(sin título)')}
        <span style="color:var(--c-dim);font-size:11px;margin-left:8px">${window._h(g.platform || 'Unknown')}</span>${badges}
      </span>
      <span style="color:var(--c-dim);font-size:11px">${g.entries.length} copia${g.entries.length !== 1 ? 's' : ''}${wastedLabel}</span>
    </summary>
    <div style="padding:6px 4px 4px">
      ${g.entries.map((e) => _renderReviewEntry(e, g, isConflictGroup)).join('')}
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">${actions}</div>
    </div>
  </details>`;
}

function _renderReviewEntry(e, g, isConflictGroup) {
  const devBadge = e.is_device
    ? `<span class="badge pending" style="font-size:10px">${window._devName || 'Consola'}</span>`
    : '';
  const raBadge =
    e.ra_achievements != null
      ? `<span style="color:var(--c-amber);font-size:10px">🏆 ${e.ra_achievements}</span>`
      : '';
  const sizeLabel = e.size_bytes != null ? window.fmtSize(e.size_bytes) : '';
  let actionCell;
  if (isConflictGroup) {
    // disk/collision: informativo — se resuelven en bloque con "Resolver con RA",
    // no hay "elegir esta" por fila (ver TABS-FIX-6, apply_ra_conflicts opera
    // sobre todos los conflictos del plan de una vez).
    actionCell =
      e.conflict_role === 'winner'
        ? '<span class="badge ok" style="font-size:10px">ganador RA</span>'
        : e.conflict_role === 'loser'
          ? '<span style="color:var(--c-muted);font-size:11px">→ _descartados/</span>'
          : '<span style="color:var(--c-dim);font-size:11px">pendiente</span>';
  } else {
    actionCell = e.recommended
      ? '<span class="badge ok" style="min-width:80px;text-align:center;display:inline-block">recomendada</span>'
      : `<button class="btn" style="padding:2px 8px;font-size:11px" onclick="chooseReviewEntry('${_jsStr(g.group_key)}','${_jsStr(e.source_path)}')">Elegir esta</button>`;
  }
  const targetInfo = e.target_name
    ? `<span style="color:var(--c-dim);font-size:11px"> → bloqueado por <code>${window._h(e.target_name)}</code>${e.ra_target_achievements != null ? ` (🏆 ${e.ra_target_achievements})` : ''}</span>`
    : '';
  return `<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px">
    <span style="min-width:90px">${actionCell}</span>
    ${devBadge}
    <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${window._h(e.source_path)}">${window._h(e.filename)}</span>
    ${raBadge}
    <span style="color:var(--c-dim);flex-shrink:0">${sizeLabel}</span>
    ${targetInfo}
  </div>`;
}

async function _resolveReviewGroup(keepPath, discardPaths) {
  const filename = keepPath.split(/[\\/]/).pop();
  _showConfirm(
    'Aplicar recomendación',
    `Se conservará <strong>${window._h(filename)}</strong> y se descartará${discardPaths.length !== 1 ? 'n' : ''} ${discardPaths.length} copia${discardPaths.length !== 1 ? 's' : ''}.<br><br>${_TRASH_NOTE}`,
    'Aplicar',
    async () => {
      try {
        const result = await apiPost('/api/resolve-duplicate-ra', {
          keep_path: keepPath,
          discard_paths: discardPaths,
        });
        if (result.error) {
          showToast('Error: ' + result.error, 'err');
          return;
        }
        showToast(`Resuelto: ${result.discarded} archivo(s) descartado(s)`, 'ok');
        await loadReviewQueue();
        window.loadOverview();
      } catch (e) {
        showToast('Error: ' + e.message, 'err');
      }
    }
  );
}

async function applyReviewGroup(groupKey) {
  const group = _reviewGroups.find((g) => g.group_key === groupKey);
  if (!group) return;
  if (group.reasons.some((r) => _CONFLICT_REASONS.has(r))) {
    doResolveRaConflicts();
    return;
  }
  const recommended = group.entries.find((e) => e.recommended);
  if (!recommended) return;
  const discardPaths = group.entries
    .filter((e) => e.source_path !== recommended.source_path)
    .map((e) => e.source_path);
  if (discardPaths.length === 0) return;
  await _resolveReviewGroup(recommended.source_path, discardPaths);
}

async function chooseReviewEntry(groupKey, keepPath) {
  const group = _reviewGroups.find((g) => g.group_key === groupKey);
  if (!group) return;
  const discardPaths = group.entries
    .filter((e) => e.source_path !== keepPath)
    .map((e) => e.source_path);
  if (discardPaths.length === 0) return;
  await _resolveReviewGroup(keepPath, discardPaths);
}

async function markReviewGroupIntentional(groupKey) {
  _showConfirm(
    'Marcar como copia intencional',
    'Este grupo no volverá a aparecer en la cola de revisión.',
    'Confirmar',
    async () => {
      try {
        await apiPost('/api/review-queue/exclude', { group_key: groupKey });
        showToast('Grupo marcado como copia intencional', 'ok');
        await loadReviewQueue();
      } catch (e) {
        showToast('Error: ' + e.message, 'err');
      }
    }
  );
}

async function applyAllReviewRecommendations() {
  const n = _reviewGroups.length;
  if (n === 0) {
    showToast('No hay copias pendientes de revisión.', 'info');
    return;
  }
  _showConfirm(
    'Aplicar todas las recomendaciones',
    `Se aplicará la recomendación precalculada en <strong>${n}</strong> grupo${n !== 1 ? 's' : ''} (los conflictos del plan se resuelven con el criterio RA).<br><br>${_TRASH_NOTE}`,
    'Aplicar todas',
    async () => {
      const btn = document.getElementById('btn-review-apply-all');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Aplicando…';
      }
      try {
        const result = await apiPost('/api/review-queue/apply-all', {});
        let msg = `✓ ${result.resolved} resuelto${result.resolved !== 1 ? 's' : ''}`;
        if (result.errors && result.errors.length) msg += ` · ⚠ ${result.errors.length} error(es)`;
        showToast(msg, result.errors && result.errors.length ? 'info' : 'ok');
        await loadReviewQueue();
        window.loadPlan();
        window.loadOverview();
      } catch (e) {
        showToast('Error: ' + e.message, 'err');
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = `Aplicar todas las recomendaciones (${_reviewGroups.length})`;
        }
      }
    }
  );
}

// D8-3 (movido desde duplicates.js en TABS-FIX-6): resuelve TODOS los
// conflictos de disco/colisión del plan de una vez (apply_ra_conflicts no
// tiene un punto de entrada por grupo individual).
async function doResolveRaConflicts() {
  _showConfirm(
    'Resolver conflictos con RetroAchievements',
    '⏱️ <strong>Atención:</strong> el sistema ejecutará primero la comprobación de RetroAchievements si no existe caché.<br><br>Esto puede tomar <strong>varios minutos</strong> dependiendo de tu biblioteca.<br><br>¿Continuar?',
    'Resolver',
    async () => {
      try {
        const d = await apiPost('/api/apply-ra-conflicts', {});
        if (d.error) {
          showToast('Error: ' + d.error, 'err');
        } else if (d.no_cache) {
          showToast(
            '⏳ Sin caché RA — iniciando comprobación de RetroAchievements (puede tomar varios minutos)…',
            'info'
          );
          if (typeof window.doRaCheck === 'function') {
            await window.doRaCheck();
            showToast(
              'RA check iniciado. Una vez complete, vuelve a intentar resolver los conflictos.',
              'info'
            );
          }
        } else if (d.resolved === 0 && d.skipped_no_ra > 0) {
          showToast(
            d.skipped_no_ra + ' conflictos sin datos RA (versión no reconocida o plataforma sin soporte)',
            'info'
          );
        } else {
          showToast(
            '✓ RA resuelto: ' +
              d.resolved +
              ' conflictos' +
              (d.skipped_no_ra > 0 ? ' · ' + d.skipped_no_ra + ' sin datos RA' : ''),
            d.resolved > 0 ? 'ok' : 'info'
          );
          await loadReviewQueue();
          window.loadPlan();
          window.loadOverview();
        }
      } catch (e) {
        showToast('Error: ' + e.message, 'err');
      }
    }
  );
}

export {
  loadReviewQueue,
  applyReviewGroup,
  chooseReviewEntry,
  markReviewGroupIntentional,
  applyAllReviewRecommendations,
  doResolveRaConflicts,
};
