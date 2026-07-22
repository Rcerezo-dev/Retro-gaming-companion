// js/tabs/duplicates.js — Selector de contexto PC/Android para Herramientas.
// TABS-FIX-6: el resto de este archivo (pestaña Duplicados, RA duplicates,
// conflictos del plan) se fusionó en tabs/review_copies.js.

import { apiFetch } from '../api.js';
import { _setIfEmpty } from './config.js';

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
      rootPath = cfg.anbernic_root || localStorage.getItem('anbernic_path') || localStorage.getItem('cable_ab_path') || '';
    }
    if (lbl) lbl.textContent = rootPath ? '— ' + rootPath : '(sin ruta configurada)';
    if (rootPath) {
      // Solo rellena inputs vacíos — nunca pisa una ruta que el usuario ya escribió (FORMATOS-UX-1)
      const toolInputIds = [
        'zip-path', 'chd-path', 'cso-path', 'verify-chd-path', 'm3u-path', 'folder-analysis-path',
        'orphan-path', 'junk-path', 'report-path',
      ];
      for (const id of toolInputIds) {
        if (_setIfEmpty(id, rootPath)) {
          document.getElementById(id)?.dispatchEvent(new Event('input'));
        }
      }
    }
  }).catch(() => {});
}

async function _initToolsContext() {
  const ctx = localStorage.getItem('tools_context') || 'pc';
  setToolsContext(ctx);
}

// ── Public exports ────────────────────────────────────────────────────────────
export { setToolsContext, _initToolsContext };
