// js/tabs/duplicates.js — Selector de contexto PC/Android para Herramientas.
// TABS-FIX-6: el resto de este archivo (pestaña Duplicados, RA duplicates,
// conflictos del plan) se fusionó en tabs/review_copies.js.

import { apiFetch } from '../api.js';

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
      // HERR-FIX-2: FORMATOS-UX-1 solo rellenaba inputs vacíos para no pisar
      // una ruta que el usuario escribió a mano — pero eso también bloqueaba
      // el propio cambio de contexto: tras rellenar la ruta de PC, pulsar
      // "Consola Android" ya no hacía nada (el input dejó de estar vacío).
      // Fix: si el valor actual es el que puso este mismo selector la última
      // vez (`dataset.ctxAuto`), se sobreescribe igual; solo se respeta una
      // edición real del usuario (`isTrusted`, nunca disparado por nuestro
      // propio `dispatchEvent`).
      const toolInputIds = [
        'zip-path', 'chd-path', 'cso-path', 'verify-chd-path', 'm3u-path', 'folder-analysis-path',
        'orphan-path', 'junk-path', 'report-path',
      ];
      for (const id of toolInputIds) {
        const el = document.getElementById(id);
        if (!el) continue;
        if (!el.dataset.ctxListenerBound) {
          el.dataset.ctxListenerBound = '1';
          el.addEventListener('input', (e) => {
            if (e.isTrusted) delete el.dataset.ctxAuto;
          });
        }
        const filled = (!el.value.trim() || el.dataset.ctxAuto === '1') && rootPath;
        if (filled) {
          el.value = rootPath;
          el.dataset.ctxAuto = '1';
          el.dispatchEvent(new Event('input'));
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
