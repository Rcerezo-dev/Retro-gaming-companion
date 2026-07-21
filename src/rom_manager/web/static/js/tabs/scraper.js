// js/tabs/scraper.js — ScreenScraper, gamelists, Pegasus export
// Extracted from app.js during Phase 2 migration.

import { apiFetch, apiPost } from '../api.js';
import { showToast } from '../components/toast.js';

// SCRAPER-UX-4: e.message crudo (p.ej. "Failed to fetch") no dice nada al
// usuario — el caso real más común es el servidor caído o sin red.
function _friendlyError(e) {
  const msg = e?.message || String(e);
  if (/fetch|network/i.test(msg)) {
    return 'No se pudo conectar con el servidor — comprueba que Retro Vault sigue en marcha.';
  }
  return msg;
}

// ── Gamelists / ES-DE helpers ─────────────────────────────────────────────────
async function doExportGamelistsAll(gamelistsDir) {
  try {
    const d = await apiPost('/api/export-gamelists', { output_dir: gamelistsDir });
    if (d.error) showToast('✗ ' + d.error, 'err');
    else showToast(`✓ Gamelists exportadas: ${d.written || 0} archivos`, 'ok');
  } catch(e) { showToast('Error: ' + e.message, 'err'); }
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
      const color = p.missing === 0 ? 'var(--c-teal)' : p.scraped > 0 ? 'var(--c-orange)' : '#555';
      return `<tr>
        <td>${p.platform}</td>
        <td style="text-align:right">${p.total}</td>
        <td style="text-align:right;color:${color}">${p.scraped} (${pct}%)</td>
        <td style="text-align:right;color:${p.missing > 0 ? 'var(--c-red)' : '#555'}">${p.missing || '—'}</td>
      </tr>`;
    }).join('');
    html += '</tbody></table></div>';
    const dc = d.description_coverage;
    if (dc && dc.total > 0) {
      const dcColor = dc.pct >= 90 ? 'var(--c-teal)' : 'var(--c-orange)';
      html += `<p style="font-size:12px;color:var(--c-muted);margin-top:8px">
        Descripciones: <span style="color:${dcColor}">${dc.with_description} / ${dc.total} (${dc.pct}%)</span>
        — objetivo: &gt;90%</p>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// SCRAPER-UX-1: la cuota vive tanto en Settings (`ss-quota-*`) como en la
// pestaña Scraper (`ss-quota-*-scraper`, donde de verdad se necesita mientras
// se scrapea). Un único fetch alimenta los paneles que existan en el DOM.
async function loadSsQuota() {
  const targets = ['', '-scraper']
    .map(suffix => ({
      label: document.getElementById('ss-quota-label' + suffix),
      bar:   document.getElementById('ss-quota-bar' + suffix),
      fill:  document.getElementById('ss-quota-fill' + suffix),
    }))
    .filter(t => t.label);
  if (!targets.length) return;
  try {
    const d = await apiFetch('/api/ss-quota');
    const today  = parseInt(d.requests_today) || 0;
    const max    = parseInt(d.max_requests_per_day) || 0;
    const hasDev = d.has_dev_account;
    targets.forEach(({ label, bar, fill }) => {
      if (!today && !max) {
        label.textContent = hasDev
          ? 'Cuenta dev detectada (~3 req/s). Realiza un scraping para ver cuota.'
          : 'Realiza un scraping para ver la cuota.';
        label.style.color = hasDev ? 'var(--c-teal)' : '#555';
        if (bar) bar.classList.add('hidden');
        return;
      }
      const pct   = max > 0 ? Math.min(100, Math.round(today / max * 100)) : 0;
      const color = pct > 90 ? 'var(--c-red)' : pct > 70 ? 'var(--c-orange)' : 'var(--c-teal)';
      label.textContent = `${today.toLocaleString()} / ${max.toLocaleString()} peticiones hoy (${pct}%)${hasDev ? ' · Cuenta dev ✓' : ''}`;
      label.style.color = color;
      if (bar)  bar.classList.remove('hidden');
      if (fill) { fill.style.background = color; fill.style.width = pct + '%'; }
    });
  } catch(e) {
    targets.forEach(({ label }) => { label.textContent = 'No disponible'; label.style.color = '#555'; });
  }
}

// SCRAPER-UX-3: chequeo proactivo de credenciales SS, mismo patrón que ya
// usa Herramientas para la API key de RA (config.js: panel "ra-api-key-status").
async function loadSsCredsStatus() {
  const el = document.getElementById('ss-creds-status');
  if (!el) return;
  try {
    const cfg = await apiFetch('/api/config');
    if (cfg.screenscraper_user) {
      el.style.color = 'var(--c-teal)';
      el.textContent = '✓ Credenciales de ScreenScraper configuradas';
    } else {
      el.style.color = 'var(--c-red)';
      el.innerHTML = '✗ Configura usuario y contraseña de ScreenScraper — <a href="#" onclick="showTab(\'settings\');return false" style="color:var(--c-blue)">ir a Settings</a>';
    }
  } catch(e) {
    el.style.color = '#555';
    el.textContent = 'No se pudo comprobar el estado de las credenciales';
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
  // SCRAPER-UX-3: comprobación proactiva, en vez de dejar que el job falle
  // a mitad — mismo patrón que HERR-UX-9 en el batch de Herramientas.
  try {
    const cfg = await apiFetch('/api/config');
    if (!cfg.screenscraper_user) {
      showToast('Configura usuario y contraseña de ScreenScraper en Ajustes antes de scrapear.', 'err');
      return;
    }
  } catch(_) { /* si /api/config falla, deja que el intento real de scrape lo reporte */ }
  btn.disabled = true;
  btn.textContent = 'Scraping…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/scrape', {
      platform: document.getElementById('scrape-platform').value || null,
      limit:    parseInt(document.getElementById('scrape-limit').value) || 0,
      images:   document.getElementById('scrape-images').checked,
      missing_descriptions: document.getElementById('scrape-missing-desc').checked,
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
    resultEl.textContent = 'Error: ' + _friendlyError(e);
    btn.disabled = false;
    btn.textContent = 'Iniciar scraping';
  }
}

// ── Gamelist export ───────────────────────────────────────────────────────────
async function doExportGamelists() {
  // SCRAPER-UX-7: mismo patrón de disabled+texto que doScrape() mientras dura la llamada.
  const btn      = document.getElementById('btn-export-gamelist');
  const resultEl = document.getElementById('gamelist-result');
  if (btn) { btn.disabled = true; btn.textContent = 'Exportando…'; }
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
    resultEl.textContent = 'Error: ' + _friendlyError(e);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Exportar gamelist.xml'; }
  }
}

export {
  doExportGamelistsAll,
  loadScraperSummary,
  loadSsQuota,
  loadSsCredsStatus,
  loadScrapePlatforms,
  doScrape,
  doExportGamelists,
};
