// js/components/modal.js — Confirm modal
// Extracted from app.js during Phase 2 migration.

let _confirmOkHandler = null;

function _showConfirm(title, bodyHtml, okLabel, onConfirm) {
  const modal = document.getElementById('confirm-modal');
  if (!modal) return;
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-body').innerHTML = bodyHtml;
  const okBtn = document.getElementById('confirm-ok');
  if (okBtn) okBtn.textContent = okLabel || 'Confirmar';
  _confirmOkHandler = onConfirm;
  modal.classList.remove('hidden');
}

function _closeConfirm() {
  const modal = document.getElementById('confirm-modal');
  if (modal) modal.classList.add('hidden');
  _confirmOkHandler = null;
}

// Wire up confirm-ok button on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('confirm-ok');
  if (btn) btn.addEventListener('click', () => {
    if (_confirmOkHandler) _confirmOkHandler();
    _closeConfirm();
  });
});

window._showConfirm = _showConfirm;
window._closeConfirm = _closeConfirm;

export { _showConfirm, _closeConfirm };
