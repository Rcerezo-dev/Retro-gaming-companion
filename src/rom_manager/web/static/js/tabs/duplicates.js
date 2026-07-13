// js/tabs/duplicates.js — Duplicados + RA Duplicados + Filtro plataforma
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';
import { _showConfirm } from '../components/modal.js';

const _txtCls = (el, cls) => {
  if (!el) return;
  el.classList.remove('txt-err', 'txt-ok', 'txt-warn', 'txt-muted', 'txt-dim', 'txt-fav');
  if (cls) el.classList.add(cls);
};

// ── Module state (platform filter) ───────────────────────────────────────────
let _dupAllGroups = [];
let _dupAllTitleGroups = [];

// ── Duplicates ────────────────────────────────────────────────────────────────
async function loadDuplicates() {
  const el = document.getElementById('dup-content');
  try {
    const cfg = await apiFetch('/api/config');
    // DEVSEL-FIX-3: duplicados siempre cruza ambas BDs, independiente del selector
    const pcPath = document.getElementById('ov-pc-path')?.value.trim() || cfg.library_root || '';
    const abPath = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '';
    let url = '/api/duplicates';
    const params = new URLSearchParams();
    if (pcPath) params.set('pc_root', pcPath);
    if (abPath) params.set('ab_root', abPath);
    if (params.toString()) url += '?' + params.toString();
    const d = await apiFetch(url);
    const dupBar = document.getElementById('dup-context-bar');
    if (dupBar) {
      const parts = [`PC: <span style="color:var(--c-teal)">${cfg.library_root || '(no configurado)'}</span>`];
      if (abPath) parts.push(`${window._devName}: <span style="color:var(--c-orange)">${abPath}</span>`);
      dupBar.innerHTML = `Viendo: ${parts.join(' &nbsp;+&nbsp; ')} &nbsp;·&nbsp; <span style="color:var(--c-dim)">Duplicados <em>dentro</em> del mismo dispositivo — las copias PC↔${window._devName} se excluyen</span>`;
      dupBar.classList.remove('hidden');
    }
    _dupAllGroups = d.groups || [];
    _dupAllTitleGroups = d.title_groups || [];

    const sel = document.getElementById('dup-platform-filter');
    if (sel) {
      const platforms = [...new Set([
        ..._dupAllGroups.map(g => g.platform || ''),
        ..._dupAllTitleGroups.map(g => g.platform || ''),
      ])].filter(Boolean).sort();
      sel.innerHTML = '<option value="">Todas las plataformas</option>';
      platforms.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p; opt.textContent = p;
        sel.appendChild(opt);
      });
      sel.classList.toggle('hidden', !(platforms.length > 1));
    }

    _renderDupContent(_dupAllGroups, _dupAllTitleGroups, '');
  } catch(e) {
    const el = document.getElementById('dup-content');
    if (el) el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function deleteAllDuplicates() {
  const rows = document.querySelectorAll('#dup-content .dup-group[id] .btn.danger');
  const count = rows.length;
  if (count === 0) { showToast('No hay duplicados para eliminar.', false); return; }
  _showConfirm(
    'Eliminar todos los duplicados',
    `Se eliminarán <strong>${count} archivo${count !== 1 ? 's' : ''}</strong> del disco.<br>Se conservará una copia de cada juego.<br><br><span style="color:var(--c-red)">Esta operación no se puede deshacer.</span>`,
    'Eliminar todos',
    async () => {
      const btn = document.getElementById('btn-delete-all-dups');
      if (btn) { btn.disabled = true; btn.textContent = 'Eliminando…'; }
      try {
        const d = await apiPost('/api/duplicates/delete-all', { source_root: '' });

        // Log diagnostics for troubleshooting
        if (d.diagnostics && d.diagnostics.length) {
          console.log('Delete-all diagnostics:', d.diagnostics);
        }

        await loadDuplicates();
        window.loadOverview();
        if (d.deleted === 0 && d.skipped === 0 && d.failed === 0) {
          showToast('Sin duplicados pendientes — la lista ya está limpia', 'info');
        } else {
          let msg = `✓ ${d.deleted} eliminados`;
          if (d.freed_bytes > 0) msg += ` · Liberados: ${window.fmtSize(d.freed_bytes)}`;
          if (d.skipped > 0) msg += ` · ${d.skipped} omitidos (no existen)`;
          if (d.failed > 0) {
            msg += ` · ⚠ ${d.failed} error${d.failed !== 1 ? 'es' : ''}`;
            if (d.errors && d.errors.length) msg += `: ${d.errors[0]}`;
          }
          showToast(msg, d.failed > 0 ? 'err' : 'ok');

          // Extra note if diagnostics show something unexpected
          if (d.diagnostics && d.diagnostics.some(d => d.exists && !d.deleted_file)) {
            console.warn('⚠️ Some files still exist after delete-all — see diagnostics');
          }
        }
      } catch(e) {
        showToast('Error: ' + e.message, true);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Eliminar todos los duplicados'; }
      }
    }
  );
}

async function deleteDuplicate(btn) {
  const gameId = parseInt(btn.dataset.id);
  const sourcePath = btn.dataset.path;
  const filename = sourcePath.split(/[\\/]/).pop();
  _showConfirm(
    'Eliminar archivo duplicado',
    `¿Eliminar <strong>${window._h(filename)}</strong> del disco?<br><br><span style="color:var(--c-red)">Esta operación no se puede deshacer.</span>`,
    'Eliminar',
    async () => {
      btn.disabled = true;
      btn.textContent = 'Eliminando…';
      try {
        await apiPost('/api/duplicates/delete', { game_id: gameId, source_path: sourcePath });
        const row = document.getElementById('dup-entry-' + gameId);
        if (row) {
          const group = row.closest('.dup-group');
          row.remove();
          if (group && !group.querySelector('.btn.danger')) group.remove();
        }
        window.loadOverview();
      } catch(e) {
        btn.disabled = false;
        btn.textContent = 'Eliminar';
        showToast('Error al eliminar: ' + e.message, true);
      }
    }
  );
}

async function resolveDuplicateRA(btn, keepPath, discardPathsStr) {
  const discardPaths = discardPathsStr.split('|').map(p => p.trim()).filter(Boolean);
  const filename = keepPath.split(/[\\/]/).pop();
  _showConfirm(
    'Resolver: mantener versión con logros RA',
    `Se eliminará${discardPaths.length > 1 ? 'n' : ''} <strong>${discardPaths.length}</strong> versión${discardPaths.length > 1 ? 'es' : ''} sin logros RA.<br>Se conservará: <strong>${window._h(filename)}</strong><br><br><span style="color:var(--c-red)">Esta operación no se puede deshacer.</span>`,
    'Resolver',
    async () => {
      btn.disabled = true;
      const btnText = btn.textContent;
      btn.textContent = 'Resolviendo…';
      try {
        const result = await apiPost('/api/resolve-duplicate-ra', {
          keep_path: keepPath,
          discard_paths: discardPaths,
        });
        await loadDuplicates();
        window.loadOverview();
        showToast(`Resuelto: ${result.discarded} archivo(s) eliminado(s)`, 'ok');
      } catch(e) {
        btn.disabled = false;
        btn.textContent = btnText;
        showToast('Error al resolver: ' + e.message, true);
      }
    }
  );
}

async function markAsIntentionalCopy(sha1) {
  _showConfirm(
    'Marcar como copia intencional',
    '¿Marcar este grupo como copia intencional PC↔consola?<br><br>No aparecerá más en la lista de duplicados.',
    'Confirmar',
    async () => {
      try {
        await apiPost('/api/duplicates/exclude', { sha1, source_root: '' });
        const el = document.getElementById('dup-' + sha1);
        if (el) el.remove();
        showToast('Grupo excluido de duplicados', 'ok');
      } catch(e) {
        showToast('Error: ' + e.message, true);
      }
    }
  );
}

// ── RA Duplicates ─────────────────────────────────────────────────────────────
async function loadRaDuplicates() {
  const el = document.getElementById('ra-dup-content');
  const btn = document.getElementById('btn-ra-dups');
  const batchBtn = document.getElementById('btn-ra-dups-discard-all');
  el.innerHTML = '<p style="color:var(--c-dim);font-size:12px">Cargando…</p>';
  if (btn) btn.disabled = true;
  if (batchBtn) batchBtn.classList.add('hidden');
  try {
    const d = await apiFetch('/api/ra-duplicates');
    if (d.note) {
      el.innerHTML = `<p style="color:var(--c-muted);font-size:12px">${d.note}</p>`;
      return;
    }
    if (d.total_groups === 0) {
      el.innerHTML = '<p style="color:var(--c-teal);font-size:13px">No se encontraron versiones candidatas a eliminar. ✓</p>';
      return;
    }
    if (batchBtn) batchBtn.classList.remove('hidden');
    let html = `<p style="color:var(--c-muted);font-size:12px;margin-bottom:12px">
      <strong style="color:var(--c-strong)">${d.total_groups}</strong> grupos encontrados —
      <strong style="color:var(--c-red)">${window.fmtSize(d.wasted_bytes)}</strong> recuperables eliminando versiones sin logros.
    </p>`;
    for (const g of d.groups) {
      html += `<div style="border:1px solid #2a2a3e;border-radius:4px;margin-bottom:10px;overflow:hidden">
        <div style="background:var(--c-bar);padding:7px 12px;display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:13px;font-weight:600;color:var(--c-purple)">${window._h(g.normalized_title)}</span>
          <span style="font-size:11px;color:var(--c-muted)">${window._h(g.platform)} — ${window.fmtSize(g.wasted_bytes)} recuperables</span>
        </div>
        <table style="width:100%;font-size:12px">
          <thead><tr>
            <th style="padding:5px 10px;text-align:left;color:var(--c-dim);font-size:11px">Archivo</th>
            <th style="padding:5px 10px;text-align:left;color:var(--c-dim);font-size:11px">Tamaño</th>
            <th style="padding:5px 10px;text-align:left;color:var(--c-dim);font-size:11px">Logros RA</th>
            <th style="padding:5px 10px;text-align:left;color:var(--c-dim);font-size:11px">Recomendación</th>
            <th style="padding:5px 10px;text-align:left;color:var(--c-dim);font-size:11px">Acción</th>
          </tr></thead>
          <tbody>`;
      for (const e of g.entries) {
        const raLabel = e.ra_supported
          ? `<span style="color:var(--c-teal)">✓ ${e.ra_achievements} logros</span>`
          : `<span style="color:var(--c-red)">✗ Sin logros</span>`;
        const rec = e.ra_supported
          ? '<span style="color:var(--c-teal)">Conservar</span>'
          : '<span style="color:var(--c-red)">Candidata a eliminar</span>';
        const rowBg = e.ra_supported ? '' : 'style="background:var(--rv-tint-warn-bg)"';
        const delBtn = e.ra_supported ? '' :
          `<button class="btn danger" style="font-size:11px;padding:2px 8px"
            onclick="deleteRaDuplicate(${e.id}, ${JSON.stringify(e.source_path)}, this)">Eliminar</button>`;
        html += `<tr ${rowBg}>
          <td style="padding:5px 10px;word-break:break-all">${window._h(e.filename)}</td>
          <td style="padding:5px 10px">${window.fmtSize(e.size_bytes)}</td>
          <td style="padding:5px 10px">${raLabel}</td>
          <td style="padding:5px 10px">${rec}</td>
          <td style="padding:5px 10px">${delBtn}</td>
        </tr>`;
      }
      html += '</tbody></table></div>';
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function deleteRaDuplicate(gameId, sourcePath, btn) {
  const filename = sourcePath.split(/[\\/]/).pop();
  if (!confirm(`¿Eliminar la versión sin logros RA?\n\n${filename}\n\nSe moverá a _descartados/. Esta acción es difícil de deshacer.`)) return;
  btn.disabled = true;
  btn.textContent = '…';
  try {
    const d = await apiPost('/api/ra-duplicates/discard', { path: sourcePath });
    if (d.error) {
      btn.disabled = false;
      btn.textContent = 'Eliminar';
      showToast('Error: ' + d.error, 'err');
      return;
    }
    const row = btn.closest('tr');
    if (row) row.remove();
    showToast(`Eliminado: ${filename}`, 'ok');
    window.loadOverview();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Eliminar';
    showToast('Error: ' + e.message, 'err');
  }
}

async function doResolveRaConflicts() {
  const btn = document.getElementById('btn-resolve-ra-conflicts');

  // Show warning about RA checker taking time
  _showConfirm(
    'Resolver conflictos con RetroAchievements',
    '⏱️ <strong>Atención:</strong> El sistema ejecutará primero la comprobación de RetroAchievements si no existe caché.<br><br>Esto puede tomar <strong>varios minutos</strong> dependiendo de tu biblioteca.<br><br>¿Continuar?',
    'Resolver',
    async () => {
      if (btn) { btn.disabled = true; btn.textContent = 'Resolviendo…'; }
      try {
        // First check if cache exists
        const d = await apiPost('/api/apply-ra-conflicts', {});
        if (d.error) {
          showToast('Error: ' + d.error, 'err');
        } else {
          let msg;
          if (d.no_cache) {
            msg = '⏳ Sin caché RA — iniciando comprobación de RetroAchievements (puede tomar varios minutos)…';
            showToast(msg, 'info');
            // Run RA check first
            if (typeof window.doRaCheck === 'function') {
              await window.doRaCheck();
              // Wait briefly for RA check to complete, then reapply conflicts
              showToast('RA check iniciado. Una vez complete, los conflictos se resolverán automáticamente.', 'info');
            }
          } else if (d.resolved === 0 && d.skipped_no_ra > 0) {
            msg = d.skipped_no_ra + ' conflictos sin datos RA (versión no reconocida por RA o plataforma sin soporte)';
            showToast(msg, 'info');
          } else {
            msg = '✓ RA resuelto: ' + d.resolved + ' conflictos' + (d.skipped_no_ra > 0 ? ' · ' + d.skipped_no_ra + ' sin datos RA' : '');
            showToast(msg, d.resolved > 0 ? 'ok' : 'info');
            await window.loadPlan();
            window.loadOverview();
          }
        }
      } catch(e) {
        showToast('Error: ' + e.message, 'err');
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Resolver por RA'; }
      }
    }
  );
}

async function discardAllRaDuplicates() {
  if (!confirm('¿Eliminar TODOS los archivos sin logros RA de todos los grupos de versión?\n\nSe moverán a una carpeta _descartados/ junto a cada archivo. Esta acción no se puede deshacer fácilmente.')) return;
  const btn = document.getElementById('btn-ra-dups-discard-all');
  if (btn) { btn.disabled = true; btn.textContent = 'Eliminando…'; }
  try {
    const d = await apiPost('/api/ra-duplicates/discard-all', {});
    if (d.error) {
      showToast('Error: ' + d.error, 'err');
    } else if (d.discarded === 0 && d.failed === 0) {
      showToast(d.note || 'Sin archivos que eliminar — ejecuta primero la comprobación RA en Tools para cargar el caché.', 'info');
    } else {
      showToast('Eliminados: ' + d.discarded + (d.failed > 0 ? ' · Fallidos: ' + d.failed : ''), d.failed > 0 ? 'info' : 'ok');
      await loadRaDuplicates();
      window.loadOverview();
    }
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Eliminar todos sin logros'; }
  }
}

// ── Tools context selector ────────────────────────────────────────────────────
function setToolsContext(ctx) {
  localStorage.setItem('tools_context', ctx);
  const btnPc  = document.getElementById('tools-ctx-pc');
  const btnAb  = document.getElementById('tools-ctx-android');
  const lbl    = document.getElementById('tools-ctx-path-label');
  if (btnPc)  btnPc.classList.toggle('active',  ctx === 'pc');
  if (btnAb)  btnAb.classList.toggle('active',  ctx === 'android');

  apiFetch('/api/config').then(cfg => {
    let rootPath = '';
    if (ctx === 'pc') {
      rootPath = cfg.library_root || '';
    } else {
      rootPath = localStorage.getItem('anbernic_path') || localStorage.getItem('cable_ab_path') || '';
    }
    if (lbl) lbl.textContent = rootPath ? '— ' + rootPath : '(sin ruta configurada)';
    const toolInputIds = ['zip-path', 'chd-path', 'orphan-path', 'folder-analysis-path', 'junk-path', 'health-path'];
    for (const id of toolInputIds) {
      const el = document.getElementById(id);
      if (el && rootPath) { el.value = rootPath; el.dispatchEvent(new Event('input')); }
    }
  }).catch(() => {});
}

async function _initToolsContext() {
  const ctx = localStorage.getItem('tools_context') || 'pc';
  setToolsContext(ctx);
}

// ── 32-2: Platform filter ─────────────────────────────────────────────────────
function filterDuplicatesByPlatform() {
  const sel = document.getElementById('dup-platform-filter');
  const plat = sel ? sel.value : '';
  _renderDupContent(_dupAllGroups, _dupAllTitleGroups, plat);
}

function _renderDupContent(groups, titleGroups, platformFilter) {
  const el = document.getElementById('dup-content');
  if (!el) return;
  const filtered = platformFilter
    ? groups.filter(g => (g.platform || '') === platformFilter)
    : groups;

  if (filtered.length === 0) {
    if (platformFilter) {
      el.innerHTML = `<p style="color:var(--c-muted)">Sin duplicados en <strong>${window._h(platformFilter)}</strong>.</p>`;
    } else {
      el.innerHTML = window._emptyState('✅', 'Sin duplicados', 'Los duplicados son ROMs con el mismo contenido exacto (SHA1 idéntico).<br>Si acabas de añadir juegos, ejecuta un Scan y luego un Match.', 'Ir a Inicio', () => window.showTab('overview'));
    }
    return;
  }

  const totalFiles = filtered.reduce((s, g) => s + g.entries.length, 0);
  const wastedBytes = filtered.reduce((s, g) => s + (g.entries[0]?.size_bytes || 0) * (g.entries.length - 1), 0);
  let html = `<p style="color:var(--c-muted);margin-bottom:16px">${filtered.length} grupo${filtered.length !== 1 ? 's' : ''} — ${totalFiles} archivos — ~${window.fmtSize(wastedBytes)} ocupados de más</p>`;
  html += filtered.map(g => `
    <div class="dup-group" id="dup-${g.sha1}">
      <div class="title" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
        <span>${g.canonical_title || '(unmatched)'}
          <span style="color:var(--c-dim);font-size:11px;margin-left:8px">${g.platform||'Unknown'} · SHA1: ${g.sha1.slice(0,12)}…</span>
        </span>
        <button class="btn" style="padding:2px 10px;font-size:11px;color:var(--c-muted);border-color:var(--c-ghost)" onclick="markAsIntentionalCopy('${g.sha1}')">Copia intencional ✓</button>
      </div>
      ${g.entries.map((e, i) => `
        <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
          ${i === 0
            ? '<span class="badge ok" style="min-width:44px;text-align:center">keep</span>'
            : `<button class="btn danger" style="padding:2px 10px;font-size:11px" data-id="${e.id}" data-path="${e.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" onclick="deleteDuplicate(this)">Eliminar</button>`}
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${e.source_path}">${e.source_path}</span>
          <span style="color:var(--c-dim);flex-shrink:0">${window.fmtSize(e.size_bytes)}</span>
        </div>`).join('')}
    </div>`).join('');

  const filteredTg = platformFilter
    ? titleGroups.filter(g => (g.platform || '') === platformFilter)
    : titleGroups;
  if (filteredTg.length > 0) {
    html += `<div style="margin-top:24px;padding-top:16px;border-top:1px solid var(--c-border)">
      <p style="color:var(--c-yellow);font-size:12px;margin-bottom:12px">⚠ ${filteredTg.length} posible${filteredTg.length !== 1?'s':''} duplicado${filteredTg.length !== 1?'s':''} semántico${filteredTg.length !== 1?'s':''} — mismo título canónico, SHA1 distinto</p>`;
    html += filteredTg.map(g => {
      const hasRaSupport = g.entries.some(e => (e.ra_achievements || 0) > 0);
      const raEntry = g.entries.find(e => (e.ra_achievements || 0) > 0);
      return `
      <div class="dup-group" style="border-color:var(--rv-tint-amber-border)">
        <div class="title" style="color:var(--c-yellow)">${window._h(g.canonical_title)}
          <span style="color:var(--c-dim);font-size:11px;margin-left:8px">${window._h(g.platform)}</span>
        </div>
        ${g.entries.map((e, i) => {
          const isRaEntry = hasRaSupport && raEntry && raEntry.id === e.id;
          const raBadge = (e.ra_achievements || 0) > 0 ? `<span style="color:var(--c-amber);font-size:10px;margin-left:4px">🏆 ${e.ra_achievements} logros</span>` : '';
          if (hasRaSupport && isRaEntry) {
            return `
          <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
            <span class="badge ok" style="min-width:44px;text-align:center">keep</span>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px" title="${e.source_path}">${e.source_path}</span>
            <span style="color:var(--c-dim);flex-shrink:0;font-size:11px">${e.sha1.slice(0,10)}… · ${window.fmtSize(e.size_bytes)}${raBadge}</span>
            <button class="btn" style="padding:2px 8px;font-size:10px;color:var(--c-teal);border-color:var(--c-teal)" data-keep="${e.id}" data-discard="${g.entries.map(x => x.id).filter(id => id !== e.id).join(',')}" onclick="resolveDuplicateRA(this, '${e.source_path.replace(/'/g, "\\'")}', '${g.entries.filter(x => x.id !== e.id).map(x => x.source_path.replace(/'/g, "\\'")).join('|')}')">Resolver: mantener éste</button>
          </div>`;
          } else if (hasRaSupport && !isRaEntry) {
            return `
          <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
            <button class="btn danger" style="padding:2px 10px;font-size:11px" data-id="${e.id}" data-path="${e.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" onclick="deleteDuplicate(this)">Eliminar</button>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px" title="${e.source_path}">${e.source_path}</span>
            <span style="color:var(--c-dim);flex-shrink:0;font-size:11px">${e.sha1.slice(0,10)}… · ${window.fmtSize(e.size_bytes)}${raBadge}</span>
          </div>`;
          } else {
            return `
          <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
            ${i === 0
              ? '<span class="badge ok" style="min-width:44px;text-align:center">keep</span>'
              : `<button class="btn danger" style="padding:2px 10px;font-size:11px" data-id="${e.id}" data-path="${e.source_path.replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" onclick="deleteDuplicate(this)">Eliminar</button>`}
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px" title="${e.source_path}">${e.source_path}</span>
            <span style="color:var(--c-dim);flex-shrink:0;font-size:11px">${e.sha1.slice(0,10)}… · ${window.fmtSize(e.size_bytes)}${raBadge}</span>
          </div>`;
          }
        }).join('')}
      </div>`;
    }).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

// ── Public exports ────────────────────────────────────────────────────────────
export {
  loadDuplicates, deleteAllDuplicates, deleteDuplicate,
  resolveDuplicateRA, markAsIntentionalCopy,
  loadRaDuplicates, deleteRaDuplicate,
  doResolveRaConflicts, discardAllRaDuplicates,
  setToolsContext, _initToolsContext,
  filterDuplicatesByPlatform, _renderDupContent,
};
