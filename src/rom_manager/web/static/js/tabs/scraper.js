// js/tabs/scraper.js — ScreenScraper, gamelists, Pegasus export
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// ── Module state ──────────────────────────────────────────────────────────────
// gamelists_dir kept for status display only (NOT used as export output dir)
let _esdeGamelistsDir = '';

// ── Gamelists / ES-DE helpers ─────────────────────────────────────────────────
async function doExportGamelistsAll(gamelistsDir) {
  try {
    const d = await apiPost('/api/export-gamelists', { output_dir: gamelistsDir });
    if (d.error) showToast('✗ ' + d.error, 'err');
    else showToast(`✓ Gamelists exportadas: ${d.written || 0} archivos`, 'ok');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
}

async function _autoFillEsdeGamelistDir() {
  // Only fetch for informational display — do NOT auto-fill the export dir.
  try {
    const d = await apiFetch('/api/esde-status');
    if (d.gamelists_dir) _esdeGamelistsDir = d.gamelists_dir;
  } catch(_) {}
}

function useEsdeGamelistDir() {
  // For ES-DE: leave the field empty so export defaults to library_root.
  const inp = document.getElementById('gamelist-output-dir');
  if (inp) { inp.value = ''; inp.placeholder = 'Vacío = library_root (correcto para ES-DE)'; }
  showToast('ES-DE: deja vacío para exportar a library_root (junto a los ROMs)', 'ok');
}

// ── Scraper summary & quota ───────────────────────────────────────────────────
async function loadScraperSummary() {
  const el = document.getElementById('scraper-summary');
  if (!el) return;
  try {
    const d = await apiFetch('/api/scrape-summary?t=' + Date.now());
    if (!d.platforms || d.platforms.length === 0) {
      el.innerHTML = '<p class="empty">No hay datos. Ejecuta un scan primero.</p>';
      return;
    }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Total ROMs</th><th>Scrapeados</th><th>Pendientes</th></tr></thead><tbody>';
    html += d.platforms.map(p => {
      const pct   = p.total > 0 ? Math.round(p.scraped / p.total * 100) : 0;
      const color = p.missing === 0 ? '#4ec9b0' : p.scraped > 0 ? '#ce9178' : '#555';
      return `<tr>
        <td>${p.platform}</td>
        <td style="text-align:right">${p.total}</td>
        <td style="text-align:right;color:${color}">${p.scraped} (${pct}%)</td>
        <td style="text-align:right;color:${p.missing > 0 ? '#f44747' : '#555'}">${p.missing || '—'}</td>
      </tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function loadSsQuota() {
  const label = document.getElementById('ss-quota-label');
  const bar   = document.getElementById('ss-quota-bar');
  const fill  = document.getElementById('ss-quota-fill');
  if (!label) return;
  try {
    const d = await apiFetch('/api/ss-quota');
    const today  = parseInt(d.requests_today) || 0;
    const max    = parseInt(d.max_requests_per_day) || 0;
    const hasDev = d.has_dev_account;
    if (!today && !max) {
      label.textContent = hasDev
        ? 'Cuenta dev detectada (~3 req/s). Realiza un scraping para ver cuota.'
        : 'Realiza un scraping para ver la cuota.';
      label.style.color = hasDev ? '#4ec9b0' : '#555';
      if (bar) bar.classList.add('hidden');
      return;
    }
    const pct   = max > 0 ? Math.min(100, Math.round(today / max * 100)) : 0;
    const color = pct > 90 ? '#f44747' : pct > 70 ? '#ce9178' : '#4ec9b0';
    label.textContent = `${today.toLocaleString()} / ${max.toLocaleString()} peticiones hoy (${pct}%)${hasDev ? ' · Cuenta dev ✓' : ''}`;
    label.style.color = color;
    if (bar)  bar.classList.remove('hidden');
    if (fill) { fill.style.background = color; fill.style.width = pct + '%'; }
  } catch(e) {
    if (label) { label.textContent = 'No disponible'; label.style.color = '#555'; }
  }
}

async function loadScrapePlatforms() {
  const sel = document.getElementById('scrape-platform');
  if (!sel) return;
  try {
    const d = await apiFetch('/api/games/filter-options');
    const current = sel.value;
    sel.innerHTML = '<option value="">Todas las plataformas</option>';
    (d.platforms || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      sel.appendChild(opt);
    });
    if (current) sel.value = current;
  } catch (_) {}
}

// ── Scrape job ────────────────────────────────────────────────────────────────
async function doScrape() {
  const btn      = document.getElementById('btn-scrape');
  const resultEl = document.getElementById('job-result-scrape');
  btn.disabled = true;
  btn.textContent = 'Scraping…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/scrape', {
      platform: document.getElementById('scrape-platform').value || null,
      limit:    parseInt(document.getElementById('scrape-limit').value) || 0,
      images:   document.getElementById('scrape-images').checked,
    });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un scraping en curso…';
      btn.disabled = false;
      btn.textContent = 'Iniciar scraping';
      return;
    }
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      btn.disabled = false;
      btn.textContent = 'Iniciar scraping';
      return;
    }
    window.startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Iniciar scraping';
  }
}

// ── Gamelist export ───────────────────────────────────────────────────────────
async function doExportGamelists() {
  const resultEl = document.getElementById('gamelist-result');
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/export-gamelists', {
      output_dir: document.getElementById('gamelist-output-dir').value.trim() || null,
      platform:   document.getElementById('gamelist-platform').value.trim() || null,
    });
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
      return;
    }
    resultEl.className = 'job-result visible success';
    if (d.written.length === 0) {
      resultEl.textContent = 'No hay metadatos scrapeados para exportar.';
    } else {
      const esNote = d.es_detected ? '\n✔ EmulationStation detectado — gamelist.xml también escrito en ~/.emulationstation/gamelists/' : '';
      resultEl.textContent = d.written.map(w => `${w.platform}: ${w.entries} entradas → ${w.path}`).join('\n') + esNote;
      resultEl.style.whiteSpace = 'pre';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

export {
  doExportGamelistsAll,
  _autoFillEsdeGamelistDir,
  useEsdeGamelistDir,
  loadScraperSummary,
  loadSsQuota,
  loadScrapePlatforms,
  doScrape,
  doExportGamelists,
};
