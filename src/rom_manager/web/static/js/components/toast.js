// js/components/toast.js — Toast notification system
// Extracted from app.js during Phase 2 migration.

// UI-IA-1r: el CSS solo define ok/err/info/warn; 'error'/'success' llegaban sin color.
const _TOAST_ALIAS = { error: 'err', success: 'ok' };

function showToast(msg, type = 'ok', duration = 3000) {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + (_TOAST_ALIAS[type] || type);
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transition = 'opacity .3s';
    setTimeout(() => t.remove(), 320);
  }, duration);
}

// Expose on window for legacy app.js callers and inline onclick handlers
window.showToast = showToast;

export { showToast };
