from __future__ import annotations

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ROM Manager</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f0f; color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; }
  a { color: #4ec9b0; text-decoration: none; }
  a:hover { text-decoration: underline; }

  header { background: #1a1a2e; padding: 16px 24px; border-bottom: 2px solid #4ec9b0; display: flex; align-items: center; gap: 16px; }
  header h1 { color: #4ec9b0; font-size: 20px; letter-spacing: 2px; }
  header .subtitle { color: #888; font-size: 12px; }

  nav { background: #16213e; display: flex; gap: 2px; padding: 0 24px; border-bottom: 1px solid #333; }
  nav button { background: none; border: none; color: #888; padding: 12px 20px; cursor: pointer; font: inherit; font-size: 13px; border-bottom: 2px solid transparent; transition: color .15s; }
  nav button:hover { color: #d4d4d4; }
  nav button.active { color: #4ec9b0; border-bottom-color: #4ec9b0; }

  main { padding: 24px; max-width: 1400px; }

  .tab { display: none; }
  .tab.active { display: block; }

  .cards { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; }
  .card { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 16px 20px; min-width: 160px; }
  .card .label { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .card .value { color: #4ec9b0; font-size: 28px; font-weight: bold; }
  .card .sub { color: #666; font-size: 11px; margin-top: 4px; }

  .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
  .toolbar input, .toolbar select { background: #1e1e2e; border: 1px solid #444; color: #d4d4d4; padding: 6px 10px; border-radius: 4px; font: inherit; font-size: 13px; }
  .toolbar input:focus, .toolbar select:focus { outline: none; border-color: #4ec9b0; }
  .btn { background: #1e1e2e; border: 1px solid #4ec9b0; color: #4ec9b0; padding: 6px 14px; border-radius: 4px; cursor: pointer; font: inherit; font-size: 13px; transition: background .15s, color .15s; }
  .btn:hover:not(:disabled) { background: #4ec9b0; color: #0f0f0f; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn.danger { border-color: #f44747; color: #f44747; }
  .btn.danger:hover:not(:disabled) { background: #f44747; color: #0f0f0f; }
  .btn.primary { border-color: #569cd6; color: #569cd6; }
  .btn.primary:hover:not(:disabled) { background: #569cd6; color: #0f0f0f; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #1a1a2e; color: #888; font-weight: normal; text-align: left; padding: 8px 10px; border-bottom: 1px solid #333; position: sticky; top: 0; }
  td { padding: 7px 10px; border-bottom: 1px solid #1e1e1e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px; }
  tr:hover td { background: #1e1e2e; }

  .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 11px; }
  .badge.high { background: #1a3a2a; color: #4ec9b0; }
  .badge.low  { background: #3a2a1a; color: #ce9178; }
  .badge.none { background: #2a2a2a; color: #666; }
  .badge.conflict { background: #3a1a1a; color: #f44747; }
  .badge.pending  { background: #1a2a3a; color: #569cd6; }
  .badge.ok       { background: #1a3a2a; color: #4ec9b0; }
  .badge.error    { background: #3a1a1a; color: #f44747; }
  .badge.skipped  { background: #2a2a2a; color: #888; }
  .badge.upload   { background: #1a2a3a; color: #569cd6; }
  .badge.download { background: #1a3a1a; color: #6a9955; }

  .config-grid { display: grid; grid-template-columns: auto 1fr; gap: 6px 16px; font-size: 13px; background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 14px 16px; margin-top: 16px; max-width: 600px; }
  .config-grid .cfg-key { color: #888; }
  .config-grid .cfg-val { color: #d4d4d4; }
  .config-grid .cfg-val.missing { color: #555; font-style: italic; }

  .actions-panel { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 16px 20px; margin-top: 20px; max-width: 700px; }
  .actions-panel h3 { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; }
  .actions-row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 10px; }
  .actions-row label { color: #888; font-size: 11px; display: block; margin-bottom: 4px; }
  .actions-row input[type="text"] { background: #0f0f0f; border: 1px solid #444; color: #d4d4d4; padding: 6px 10px; border-radius: 4px; font: inherit; font-size: 13px; width: 340px; }
  .actions-row input[type="text"]:focus { outline: none; border-color: #4ec9b0; }
  .job-result { font-size: 12px; margin-top: 8px; padding: 8px 10px; border-radius: 4px; background: #161626; border: 1px solid #2a2a3a; color: #888; display: none; }
  .job-result.visible { display: block; }
  .job-result.success { border-color: #1a3a2a; color: #4ec9b0; }
  .job-result.error-r { border-color: #3a1a1a; color: #f44747; }

  .dup-group { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; margin-bottom: 12px; padding: 14px 16px; }
  .dup-group .title { color: #4ec9b0; margin-bottom: 8px; }
  .dup-group .entry { color: #888; font-size: 12px; padding: 2px 0; }
  .dup-group .entry span { color: #d4d4d4; }

  .fmt-options { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 14px 16px; margin-bottom: 16px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
  .fmt-options span { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-right: 4px; }
  .fmt-check { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; color: #d4d4d4; }
  .fmt-check input[type="checkbox"] { accent-color: #4ec9b0; width: 14px; height: 14px; cursor: pointer; }

  .empty { color: #555; padding: 40px 0; text-align: center; }
  .loading { color: #555; padding: 24px 0; }
  .error-msg { color: #f44747; padding: 12px; background: #2a1a1a; border-radius: 4px; margin-bottom: 12px; }
</style>
</head>
<body>

<header>
  <h1>&#x1F3AE; ROM Manager</h1>
  <span class="subtitle">local library</span>
</header>

<nav>
  <button class="active" onclick="showTab('overview')">Overview</button>
  <button onclick="showTab('games')">Games</button>
  <button onclick="showTab('plan')">Plan</button>
  <button onclick="showTab('duplicates')">Duplicates</button>
  <button onclick="showTab('assets')">Assets</button>
  <button onclick="showTab('sync')">Sync</button>
  <button onclick="showTab('scraper')">Scraper</button>
  <button onclick="showTab('tools')">Tools</button>
  <button onclick="showTab('settings')">Settings</button>
</nav>

<main>

<!-- OVERVIEW -->
<div id="tab-overview" class="tab active">
  <div id="overview-cards" class="cards"><p class="loading">Loading…</p></div>

  <!-- Actions panel -->
  <div class="actions-panel">
    <h3>Acciones</h3>

    <div class="actions-row">
      <div>
        <label for="scan-path">Ruta a escanear</label>
        <input id="scan-path" type="text" placeholder="C:/ROMs o /mnt/roms">
      </div>
      <label class="fmt-check" style="margin-left:8px" title="No calcula hashes — mucho más rápido, pero Match y Sync no funcionarán hasta hacer un scan completo">
        <input type="checkbox" id="scan-quick"> Quick (sin hash)
      </label>
      <button id="btn-scan" class="btn" onclick="doScan()">Scan</button>
    </div>

    <div class="actions-row">
      <button id="btn-match" class="btn primary" onclick="doMatch()">Match catálogos</button>
      <span style="color:#555;font-size:12px">Asocia los ROMs escaneados a No-Intro / Redump</span>
    </div>

    <div class="actions-row">
      <button id="btn-fix-platforms" class="btn" onclick="doFixPlatforms()">Fix plataformas</button>
      <span style="color:#555;font-size:12px">Infiere la plataforma desde el nombre de carpeta (sin re-escanear)</span>
    </div>
    <div id="job-result-fix-platforms" class="job-result"></div>

    <div id="job-result-scan"  class="job-result"></div>
    <div id="job-result-match" class="job-result"></div>
  </div>

  <!-- Workflow guide -->
  <div style="margin-top:28px;max-width:700px">
    <h3 style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Cómo usar ROM Manager</h3>
    <div style="display:flex;gap:0;counter-reset:steps">
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#4ec9b0;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">① Scan</div>
        <div style="color:#888;font-size:12px;line-height:1.5">Introduce la ruta de tu carpeta de ROMs y pulsa <strong style="color:#d4d4d4">Scan</strong>. Se calculará el hash de cada archivo y se guardará en la base de datos.</div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#569cd6;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">② Match</div>
        <div style="color:#888;font-size:12px;line-height:1.5">Pulsa <strong style="color:#d4d4d4">Match catálogos</strong>. Se compara cada ROM contra los catálogos No-Intro / Redump para identificar título canónico y región.</div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#ce9178;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">③ Plan</div>
        <div style="color:#888;font-size:12px;line-height:1.5">Ve a la pestaña <strong style="color:#d4d4d4">Plan</strong> para ver los renombrados propuestos. Marca qué información incluir (región, revisión) y previsualiza el resultado.</div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;padding:14px 16px">
        <div style="color:#4ec9b0;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">④ Apply</div>
        <div style="color:#888;font-size:12px;line-height:1.5">Pulsa <strong style="color:#d4d4d4">Aplicar renombrado</strong> cuando estés conforme. Los archivos se mueven en disco y queda todo registrado en el log.</div>
      </div>
    </div>
  </div>
</div>

<!-- GAMES -->
<div id="tab-games" class="tab">
  <div class="toolbar">
    <input id="games-search" type="text" placeholder="Search title or filename…" oninput="onGamesFilterChange()">
    <select id="games-platform" onchange="onGamesFilterChange()"><option value="">All platforms</option></select>
    <select id="games-matched" onchange="onGamesFilterChange()">
      <option value="">All</option>
      <option value="matched">Matched only</option>
      <option value="unmatched">Unmatched only</option>
    </select>
    <span id="games-count" style="color:#666;margin-left:8px;"></span>
    <a href="/api/report.csv" class="btn" style="margin-left:auto">&#x2193; CSV</a>
    <a href="/api/report.json" class="btn">&#x2193; JSON</a>
  </div>
  <div style="overflow-x:auto">
    <table id="games-table">
      <thead><tr>
        <th>Platform</th><th>Canonical title</th><th>Original filename</th>
        <th>Region</th><th>Match</th><th>Size</th><th>SHA1</th>
      </tr></thead>
      <tbody id="games-tbody"></tbody>
    </table>
  </div>
  <p id="games-empty" class="empty" style="display:none">No games match the filter.</p>
  <div id="games-pagination" style="display:flex;gap:8px;align-items:center;margin-top:12px;color:#888;font-size:13px"></div>
</div>

<!-- PLAN -->
<div id="tab-plan" class="tab">
  <!-- Format options -->
  <div class="fmt-options">
    <span>Incluir en el nombre:</span>
    <label class="fmt-check">
      <input type="checkbox" id="fmt-region" checked onchange="loadPlan()"> Región
    </label>
    <label class="fmt-check">
      <input type="checkbox" id="fmt-revision" checked onchange="loadPlan()"> Revisión
    </label>
    <label class="fmt-check">
      <input type="checkbox" id="fmt-platform" onchange="loadPlan()"> Plataforma
    </label>
    <label class="fmt-check">
      <input type="checkbox" id="fmt-sha" onchange="loadPlan(); toggleShaLength()"> SHA
    </label>
    <label class="fmt-check" id="sha-length-label" style="display:none">
      <span style="color:#888;font-size:11px;margin-right:4px">Dígitos:</span>
      <select id="fmt-sha-length" onchange="loadPlan()"
        style="background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:2px 6px;border-radius:4px;font:inherit;font-size:12px">
        <option value="8" selected>8</option>
        <option value="12">12</option>
        <option value="16">16</option>
        <option value="40">40 (completo)</option>
      </select>
    </label>
    <button id="btn-apply" class="btn primary" style="margin-left:auto" onclick="doApply()">Aplicar renombrado</button>
  </div>
  <div id="fmt-preview" style="font-size:12px;color:#888;margin-bottom:12px;padding:6px 10px;background:#161626;border:1px solid #2a2a3a;border-radius:4px;display:none">
    <span style="color:#555">Ejemplo: </span><span id="fmt-preview-text" style="color:#4ec9b0"></span>
  </div>
  <div id="plan-content"><p class="loading">Loading…</p></div>
</div>

<!-- DUPLICATES -->
<div id="tab-duplicates" class="tab">
  <div id="dup-content"><p class="loading">Loading…</p></div>
</div>

<!-- SYNC -->
<div id="tab-sync" class="tab">
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Sincronización de saves</h3>
    <div class="actions-row">
      <button id="btn-sync-dry" class="btn" onclick="doSync(true)">Estado (dry run)</button>
      <span style="color:#555;font-size:12px">Muestra qué se sincronizaría sin transferir nada</span>
    </div>
    <div class="actions-row">
      <button id="btn-sync-apply" class="btn primary" onclick="doSync(false)">Sincronizar</button>
      <span style="color:#555;font-size:12px">Transfiere archivos entre local y la nube</span>
    </div>
    <div id="job-result-sync" class="job-result"></div>
    <div id="sync-decisions" style="margin-top:12px"></div>
  </div>
  <div id="sync-content"><p class="loading">Loading…</p></div>
</div>

<!-- ASSETS -->
<div id="tab-assets" class="tab">
  <div class="toolbar">
    <select id="assets-filter" onchange="loadAssets()">
      <option value="all">Todas las plataformas</option>
      <option value="orphans">Solo huérfanos (assets sin ROMs)</option>
      <option value="missing">Solo sin assets</option>
    </select>
  </div>
  <div id="assets-content"><p class="loading">Loading…</p></div>
</div>

<!-- SCRAPER -->
<div id="tab-scraper" class="tab">
  <div class="actions-panel" style="max-width:800px">
    <h3>ScreenScraper — Metadatos y portadas</h3>
    <p style="color:#888;font-size:12px;margin-bottom:16px">
      Requiere cuenta gratuita en <a href="https://www.screenscraper.fr" target="_blank">screenscraper.fr</a>.
      Configura usuario y contraseña en la pestaña <strong>Settings</strong>.
    </p>

    <div class="actions-row" style="flex-wrap:wrap;gap:16px">
      <div>
        <label>Plataforma (opcional)</label>
        <input id="scrape-platform" type="text" placeholder="Game Boy Advance" style="width:200px">
      </div>
      <div>
        <label>Límite de ROMs (0 = todos)</label>
        <input id="scrape-limit" type="number" value="0" min="0" style="width:80px;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px">
      </div>
      <label class="fmt-check" style="align-self:flex-end">
        <input type="checkbox" id="scrape-images"> Descargar portadas
      </label>
    </div>
    <div class="actions-row" style="margin-top:10px">
      <button id="btn-scrape" class="btn primary" onclick="doScrape()">Iniciar scraping</button>
      <span style="color:#555;font-size:12px">Respeta el rate limit de ScreenScraper (~1 req/s)</span>
    </div>
    <div id="job-result-scrape" class="job-result"></div>
  </div>

  <div style="margin-top:24px;max-width:800px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h3 style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px">Estado del scraping por plataforma</h3>
      <button class="btn" onclick="loadScraperSummary()">&#x21BB; Actualizar</button>
    </div>
    <div id="scraper-summary"><p class="loading">Loading…</p></div>
  </div>

  <div class="actions-panel" style="max-width:800px;margin-top:24px">
    <h3>Exportar gamelist.xml</h3>
    <p style="color:#888;font-size:12px;margin-bottom:16px">
      Genera un <code>gamelist.xml</code> por plataforma en el formato de EmulationStation (Anbernic).
      Sin estos archivos, la consola muestra sólo texto plano.
    </p>
    <div class="actions-row">
      <div>
        <label>Carpeta de salida (vacío = library_root)</label>
        <input id="gamelist-output-dir" type="text" placeholder="Ruta opcional" style="width:300px">
      </div>
      <div>
        <label>Plataforma (opcional)</label>
        <input id="gamelist-platform" type="text" placeholder="Todas" style="width:160px">
      </div>
    </div>
    <div class="actions-row">
      <button class="btn primary" onclick="doExportGamelists()">Exportar gamelist.xml</button>
    </div>
    <div id="gamelist-result" class="job-result"></div>
  </div>
</div>

<!-- TOOLS -->
<div id="tab-tools" class="tab">
  <div class="actions-panel">
    <h3>Convertir a CHD (PSX)</h3>
    <div class="actions-row">
      <div>
        <label for="chd-path">Carpeta con archivos .cue/.bin</label>
        <input id="chd-path" type="text" placeholder="C:/ROMs/psx">
      </div>
    </div>
    <div class="actions-row" style="gap:20px;align-items:center">
      <label class="fmt-check">
        <input type="checkbox" id="chd-dry-run" checked> Dry run (solo previsualizar)
      </label>
      <label class="fmt-check">
        <input type="checkbox" id="chd-delete-source"> Eliminar .cue/.bin tras convertir
      </label>
    </div>
    <div class="actions-row">
      <button id="btn-convert-chd" class="btn primary" onclick="doConvertChd()">Convertir a CHD</button>
      <span style="color:#555;font-size:12px">Requiere chdman en PATH o configurado en config.toml</span>
    </div>
    <div id="job-result-convert-chd" class="job-result"></div>
    <div id="chd-results" style="margin-top:16px"></div>
  </div>
</div>

<!-- SETTINGS -->
<div id="tab-settings" class="tab">
  <div class="actions-panel" style="max-width:640px">
    <h3>Configuración</h3>
    <p style="color:#555;font-size:11px;margin-bottom:16px">Los cambios se guardan en <code>config.toml</code>. Reinicia el servidor para que surtan efecto en el sync.</p>

    <div class="actions-row" style="flex-direction:column;align-items:flex-start;gap:12px">
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">library_root — carpeta raíz de la biblioteca (ROMs + saves)</label>
        <input id="cfg-library-root" type="text" style="width:100%" placeholder="E:/ROMs">
      </div>
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">rclone remote — ruta en el cloud para saves</label>
        <input id="cfg-rclone-remote" type="text" style="width:100%" placeholder="dropbox:/RetroSync/saves">
      </div>
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">ScreenScraper usuario</label>
        <input id="cfg-ss-user" type="text" style="width:100%" placeholder="tu_usuario">
      </div>
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">ScreenScraper contraseña</label>
        <input id="cfg-ss-pass" type="password" style="width:100%" placeholder="••••••••">
      </div>
    </div>

    <div class="actions-row" style="margin-top:16px">
      <button class="btn primary" onclick="saveSettings()">Guardar config.toml</button>
    </div>
    <div id="settings-result" class="job-result"></div>
  </div>
</div>

</main>

<script>
"use strict";

// Pagination state for Games tab
let gamesState = { offset: 0, limit: 100, total: 0, platform: '', status: '' };
let platformsLoaded = false;
let _pollingTimer = null;

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.currentTarget.classList.add('active');
  if (name === 'overview')   loadOverview();
  if (name === 'games')      loadGames(0);
  if (name === 'plan')       loadPlan();
  if (name === 'duplicates') loadDuplicates();
  if (name === 'assets')     loadAssets();
  if (name === 'sync')       loadSync();
  if (name === 'scraper')    loadScraperSummary();
  if (name === 'settings')   loadSettings();
  if (name === 'tools')      {}
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtSize(n) {
  const units = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + units[i];
}

function badge(cls, text) {
  return `<span class="badge ${cls}">${text}</span>`;
}

async function apiFetch(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ── Overview ─────────────────────────────────────────────────────────────────
async function loadOverview() {
  const el = document.getElementById('overview-cards');
  try {
    const [d, cfg] = await Promise.all([apiFetch('/api/status'), apiFetch('/api/config')]);
    const matchPct = d.total_games > 0 ? Math.round(d.matched_games / d.total_games * 100) : 0;
    const cfgHtml = `
      <div class="config-grid" style="margin-top:24px">
        <span class="cfg-key">library_root</span>
        <span class="cfg-val ${cfg.library_root ? '' : 'missing'}">${cfg.library_root || '(not set — configure en Settings)'}</span>
        <span class="cfg-key">rclone remote</span>
        <span class="cfg-val ${cfg.rclone_remote ? '' : 'missing'}">${cfg.rclone_remote || '(not set)'}</span>
        <span class="cfg-key">ScreenScraper</span>
        <span class="cfg-val ${cfg.screenscraper_user ? '' : 'missing'}">${cfg.screenscraper_user || '(not set)'}</span>
        <span class="cfg-key">web</span>
        <span class="cfg-val">${cfg.web_host}:${cfg.web_port}</span>
      </div>`;
    el.innerHTML = `
      ${card('Games', d.total_games)}
      ${card('Matched', d.matched_games, matchPct + '% of library')}
      ${card('Unmatched', d.unmatched_games)}
      ${card('Saves', d.total_saves)}
      ${card('Assets', d.total_assets)}
      ${card('Dup groups', d.duplicate_groups, fmtSize(d.wasted_bytes) + ' wasted')}
      ${card('Last scan', d.last_scan_at ? d.last_scan_at.replace('T',' ') : 'never')}
      ${cfgHtml}
    `;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function card(label, value, sub) {
  return `<div class="card">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    ${sub ? `<div class="sub">${sub}</div>` : ''}
  </div>`;
}

// ── Job polling ───────────────────────────────────────────────────────────────
function startPolling() {
  if (_pollingTimer) return;
  _pollingTimer = setInterval(async () => {
    try {
      const s = await apiFetch('/api/job-status');
      _applyJobStatus(s);
      if (!s.scan_running && !s.match_running && !s.sync_running && !s.convert_chd_running && !s.scrape_running) {
        clearInterval(_pollingTimer);
        _pollingTimer = null;
      }
    } catch(_) {}
  }, 2000);
}

function _applyJobStatus(s) {
  const btnScan  = document.getElementById('btn-scan');
  const btnMatch = document.getElementById('btn-match');

  if (btnScan) {
    btnScan.disabled = s.scan_running;
    btnScan.textContent = s.scan_running ? 'Escaneando…' : 'Scan';
  }
  if (btnMatch) {
    btnMatch.disabled = s.match_running;
    btnMatch.textContent = s.match_running ? 'Matching…' : 'Match catálogos';
  }

  const btnSyncDry   = document.getElementById('btn-sync-dry');
  const btnSyncApply = document.getElementById('btn-sync-apply');
  const btnChd       = document.getElementById('btn-convert-chd');

  if (btnSyncDry)   btnSyncDry.disabled   = s.sync_running;
  if (btnSyncApply) btnSyncApply.disabled = s.sync_running;
  if (btnChd)       btnChd.disabled       = s.convert_chd_running;

  if (!s.scan_running && s.scan_result) {
    _showJobResult('scan', s.scan_result);
    // Refresh stats cards after scan completes
    loadOverview();
  }
  if (!s.match_running && s.match_result) {
    _showJobResult('match', s.match_result);
    loadOverview();
  }
  if (!s.sync_running && s.sync_result) {
    _renderSyncResult(s.sync_result);
  }
  if (!s.convert_chd_running && s.convert_chd_result) {
    _renderChdResult(s.convert_chd_result);
  }
  if (!s.scrape_running && s.scrape_result) {
    const el = document.getElementById('job-result-scrape');
    const btn = document.getElementById('btn-scrape');
    if (el) {
      if (s.scrape_result.error) {
        el.className = 'job-result visible error-r';
        el.textContent = 'Error: ' + s.scrape_result.error;
      } else {
        el.className = 'job-result visible success';
        el.textContent = `Completado — Encontrados: ${s.scrape_result.found}  |  No encontrados: ${s.scrape_result.skipped}  (de ${s.scrape_result.total})`;
      }
    }
    if (btn) { btn.disabled = false; btn.textContent = 'Iniciar scraping'; }
    loadScraperSummary();
  }
}

function _showJobResult(type, result) {
  const el = document.getElementById('job-result-' + type);
  if (!el) return;
  if (result.error) {
    el.className = 'job-result visible error-r';
    el.textContent = 'Error: ' + result.error;
  } else if (type === 'scan') {
    el.className = 'job-result visible success';
    el.textContent = `Scan completado — ROMs: ${result.roms_detected}  |  Saltados: ${result.roms_skipped}  |  Saves: ${result.saves_detected}  |  Errores: ${result.errors}`;
  } else if (type === 'match') {
    el.className = 'job-result visible success';
    el.textContent = `Match completado — SHA1: ${result.matched_high}  |  Nombre: ${result.matched_low}  |  Sin match: ${result.unmatched}  (de ${result.total} ROMs)`;
  } else if (type === 'convert-chd') {
    el.className = 'job-result visible success';
    const verb = result.dry_run ? 'Convertiría' : 'Convertidos';
    el.textContent = `${verb}: ${result.converted}  |  Omitidos: ${result.skipped}  |  Fallidos: ${result.failed}`;
  }
}

// ── Scan action ───────────────────────────────────────────────────────────────
async function doScan() {
  const pathVal = document.getElementById('scan-path').value.trim();
  if (!pathVal) {
    alert('Introduce una ruta para escanear.');
    return;
  }
  const btn = document.getElementById('btn-scan');
  btn.disabled = true;
  btn.textContent = 'Escaneando…';
  const resultEl = document.getElementById('job-result-scan');
  resultEl.className = 'job-result';

  try {
    const quick = document.getElementById('scan-quick')?.checked || false;
    const d = await apiPost('/api/scan', { source_path: pathVal, quick });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un scan en curso…';
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Scan';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Fix platforms action ─────────────────────────────────────────────────────
async function doFixPlatforms() {
  const btn = document.getElementById('btn-fix-platforms');
  const resultEl = document.getElementById('job-result-fix-platforms');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/fix-platforms', {});
    resultEl.className = 'job-result visible success';
    resultEl.textContent = `Plataformas actualizadas: ${d.updated} juegos`;
    loadOverview();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Fix plataformas';
  }
}

// ── Match action ──────────────────────────────────────────────────────────────
async function doMatch() {
  const btn = document.getElementById('btn-match');
  btn.disabled = true;
  btn.textContent = 'Matching…';
  const resultEl = document.getElementById('job-result-match');
  resultEl.className = 'job-result';

  try {
    const d = await apiPost('/api/match', {});
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un match en curso…';
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Match catálogos';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Games ────────────────────────────────────────────────────────────────────
function onGamesFilterChange() {
  gamesState.platform = document.getElementById('games-platform').value;
  gamesState.status   = document.getElementById('games-matched').value;
  loadGames(0);
}

async function loadGames(offset) {
  gamesState.offset = offset ?? 0;
  const tbody = document.getElementById('games-tbody');
  tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading…</td></tr>';

  const q = document.getElementById('games-search').value.toLowerCase();
  const params = new URLSearchParams({
    offset: gamesState.offset,
    limit:  gamesState.limit,
  });
  if (gamesState.platform) params.set('platform', gamesState.platform);
  if (gamesState.status)   params.set('status',   gamesState.status);

  try {
    const d = await apiFetch('/api/games?' + params);

    // Populate platform filter from current page (best effort)
    if (!platformsLoaded) {
      platformsLoaded = true;
      const plats = [...new Set(d.games.map(g => g.platform || 'Unknown'))].sort();
      const sel = document.getElementById('games-platform');
      while (sel.options.length > 1) sel.remove(1);
      plats.forEach(p => {
        const o = document.createElement('option');
        o.value = p; o.text = p;
        sel.add(o);
      });
    }

    gamesState.total = d.total;
    document.getElementById('games-count').textContent =
      `${d.total} game${d.total !== 1 ? 's' : ''} (page ${Math.floor(gamesState.offset / gamesState.limit) + 1} of ${Math.max(1, Math.ceil(d.total / gamesState.limit))})`;

    let rows = d.games;
    if (q) {
      rows = rows.filter(g =>
        (g.canonical_title || '').toLowerCase().includes(q) ||
        g.original_filename.toLowerCase().includes(q)
      );
    }

    const empty = document.getElementById('games-empty');
    if (rows.length === 0) { tbody.innerHTML = ''; empty.style.display = ''; }
    else {
      empty.style.display = 'none';
      tbody.innerHTML = rows.map(g => `<tr>
        <td>${g.platform || ''}</td>
        <td title="${g.canonical_title||''}">${g.canonical_title || '<span style="color:#555">—</span>'}</td>
        <td title="${g.original_filename}">${g.original_filename}</td>
        <td>${g.region || ''}</td>
        <td>${g.match_confidence ? badge(g.match_confidence, g.match_confidence) : badge('none','—')}</td>
        <td>${fmtSize(g.size_bytes)}</td>
        <td style="color:#555;font-size:11px">${g.sha1.slice(0,12)}…</td>
      </tr>`).join('');
    }

    renderPagination();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" class="error-msg">${e.message}</td></tr>`;
  }
}

function renderPagination() {
  const pg = document.getElementById('games-pagination');
  const total = gamesState.total;
  const limit = gamesState.limit;
  const offset = gamesState.offset;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  const prevDisabled = offset === 0 ? 'disabled style="opacity:.4;cursor:default"' : '';
  const nextDisabled = offset + limit >= total ? 'disabled style="opacity:.4;cursor:default"' : '';

  pg.innerHTML = `
    <button class="btn" ${prevDisabled} onclick="loadGames(${Math.max(0, offset - limit)})">&#x2190; Prev</button>
    <span>Page ${currentPage} of ${totalPages}</span>
    <button class="btn" ${nextDisabled} onclick="loadGames(${offset + limit})">Next &#x2192;</button>
    <select style="background:#1e1e2e;border:1px solid #444;color:#d4d4d4;padding:4px 8px;border-radius:4px;font:inherit;font-size:13px" onchange="gamesState.limit=+this.value;loadGames(0)">
      ${[50,100,200,500].map(n => `<option value="${n}"${n===limit?' selected':''}>${n} / page</option>`).join('')}
    </select>`;
}

// ── Plan ─────────────────────────────────────────────────────────────────────
function _chk(id, def = '1') {
  const el = document.getElementById(id);
  return el ? (el.checked ? '1' : '0') : def;
}

function toggleShaLength() {
  const label = document.getElementById('sha-length-label');
  if (label) label.style.display = document.getElementById('fmt-sha').checked ? '' : 'none';
}

function _planQueryString() {
  const shaLength = document.getElementById('fmt-sha-length')?.value || '8';
  return `?include_region=${_chk('fmt-region')}&include_revision=${_chk('fmt-revision')}` +
         `&include_platform=${_chk('fmt-platform', '0')}&include_sha=${_chk('fmt-sha', '0')}` +
         `&sha_length=${shaLength}`;
}

async function loadPlan() {
  const el = document.getElementById('plan-content');
  el.innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await apiFetch('/api/plan' + _planQueryString());

    // Update preview bar
    const previewEl  = document.getElementById('fmt-preview');
    const previewTxt = document.getElementById('fmt-preview-text');
    const firstPending = d.pending?.[0] || d.already_correct_example;
    if (previewEl && previewTxt && d.pending.length > 0) {
      previewTxt.textContent = d.pending[0].target_name;
      previewEl.style.display = '';
    } else if (previewEl) {
      previewEl.style.display = 'none';
    }

    if (d.total === 0) {
      el.innerHTML = '<p class="empty">No matched games found. Run <strong>Match catálogos</strong> primero.</p>';
      return;
    }
    let html = '';
    if (d.pending.length) {
      html += `<h3 style="color:#569cd6;margin-bottom:12px">Pending renames — ${d.pending.length}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Platform</th><th>From</th><th>To</th></tr></thead><tbody>';
      html += d.pending.map(op => `<tr>
        <td>${op.platform||'<span style="color:#555">Unknown</span>'}</td>
        <td title="${op.source}">${op.source_name}</td>
        <td style="color:#4ec9b0" title="${op.target}">${op.target_name}</td>
      </tr>`).join('');
      html += '</tbody></table></div>';
    }
    if (d.conflicts.length) {
      html += `<h3 style="color:#f44747;margin:20px 0 12px">Conflicts — ${d.conflicts.length}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>From</th><th>To (blocked)</th></tr></thead><tbody>';
      html += d.conflicts.map(op => `<tr>
        <td>${op.source_name}</td>
        <td style="color:#f44747">${op.target_name}</td>
      </tr>`).join('');
      html += '</tbody></table></div>';
    }
    if (d.already_correct > 0) {
      html += `<p style="color:#555;margin-top:16px">${d.already_correct} file(s) already have the correct name.</p>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Apply action ──────────────────────────────────────────────────────────────
async function doApply() {
  if (!confirm('¿Aplicar el renombrado? Esta operación mueve archivos en disco.')) return;
  const btn = document.getElementById('btn-apply');
  btn.disabled = true;
  btn.textContent = 'Aplicando…';

  try {
    const d = await apiPost('/api/apply', {
      format_opts: {
        include_region:   document.getElementById('fmt-region').checked,
        include_revision: document.getElementById('fmt-revision').checked,
        include_platform: document.getElementById('fmt-platform').checked,
        include_sha:      document.getElementById('fmt-sha').checked,
        sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
      }
    });
    const el = document.getElementById('plan-content');
    const msg = document.createElement('p');
    msg.style.cssText = 'margin-top:16px;color:#4ec9b0;font-size:13px';
    const savesInfo = d.saves_renamed > 0 ? `  |  Saves renombrados: ${d.saves_renamed}` : '';
    msg.textContent = `Renombrados: ${d.renamed}  |  Fallidos: ${d.failed}  |  Conflictos: ${d.conflicts}${savesInfo}`;
    el.prepend(msg);
    // Reload plan and stats
    await loadPlan();
    loadOverview();
  } catch(e) {
    alert('Error al aplicar: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Aplicar renombrado';
  }
}

// ── Duplicates ────────────────────────────────────────────────────────────────
async function loadDuplicates() {
  const el = document.getElementById('dup-content');
  try {
    const d = await apiFetch('/api/duplicates');
    if (d.groups.length === 0) { el.innerHTML = '<p class="empty">No duplicates found.</p>'; return; }
    let html = `<p style="color:#888;margin-bottom:16px">${d.groups.length} group(s) — ${d.total_files} files — ~${fmtSize(d.wasted_bytes)} wasted</p>`;
    html += d.groups.map(g => `
      <div class="dup-group" id="dup-${g.sha1}">
        <div class="title">${g.canonical_title || '(unmatched)'}
          <span style="color:#555;font-size:11px;margin-left:8px">${g.platform||'Unknown'} · SHA1: ${g.sha1.slice(0,12)}…</span>
        </div>
        ${g.entries.map((e, i) => `
          <div class="entry" style="display:flex;align-items:center;gap:10px;padding:4px 0" id="dup-entry-${e.id}">
            ${i === 0
              ? '<span class="badge ok" style="min-width:44px;text-align:center">keep</span>'
              : `<button class="btn danger" style="padding:2px 10px;font-size:11px" onclick="deleteDuplicate(${e.id}, '${e.source_path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">Delete</button>`}
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${e.source_path}">${e.source_path}</span>
            <span style="color:#555;flex-shrink:0">${fmtSize(e.size_bytes)}</span>
          </div>`).join('')}
      </div>`).join('');
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function deleteDuplicate(gameId, sourcePath) {
  const filename = sourcePath.split(/[\\/]/).pop();
  if (!confirm(`¿Eliminar "${filename}" del disco?\n\nEsta operación no se puede deshacer.`)) return;
  try {
    await apiPost('/api/duplicates/delete', { game_id: gameId, source_path: sourcePath });
    const row = document.getElementById('dup-entry-' + gameId);
    if (row) row.remove();
    loadOverview();
  } catch(e) {
    alert('Error al eliminar: ' + e.message);
  }
}

// ── Sync ──────────────────────────────────────────────────────────────────────
async function loadSync() {
  const el = document.getElementById('sync-content');
  try {
    const [sl, cfg] = await Promise.all([apiFetch('/api/sync-log'), apiFetch('/api/config')]);
    let html = '';
    if (cfg.rclone_remote) {
      html += `<p style="color:#888;margin-bottom:16px">Remote: <span style="color:#4ec9b0">${cfg.rclone_remote}</span></p>`;
    } else {
      html += `<p class="error-msg" style="margin-bottom:16px">No rclone remote configured. Set <code>[sync] remote</code> in config.toml and run <code>rommgr sync-saves</code>.</p>`;
    }
    if (sl.entries.length === 0) {
      html += '<p class="empty">No sync events recorded yet. Run <code>rommgr sync-saves</code> to start syncing.</p>';
      el.innerHTML = html;
      return;
    }
    html += `<p style="color:#666;margin-bottom:12px">${sl.entries.length} event(s)</p>`;
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Date</th><th>Direction</th><th>Result</th><th>Local path</th><th>Remote path</th><th>Message</th>';
    html += '</tr></thead><tbody>';
    html += sl.entries.map(e => {
      const dirBadge = badge(e.direction, e.direction);
      const resBadge = badge(e.result, e.result);
      const msg  = e.message ? `<span style="color:#888">${e.message}</span>` : '';
      const date = e.created_at ? e.created_at.replace('T', ' ') : '';
      return `<tr><td>${date}</td><td>${dirBadge}</td><td>${resBadge}</td><td title="${e.local_path}">${e.local_path.split(/[\\/]/).pop()}</td><td title="${e.remote_path}">${e.remote_path}</td><td>${msg}</td></tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Assets ───────────────────────────────────────────────────────────────────
async function loadAssets() {
  const el = document.getElementById('assets-content');
  el.innerHTML = '<p class="loading">Loading…</p>';
  const filter = document.getElementById('assets-filter')?.value || 'all';
  try {
    const d = await apiFetch('/api/assets');
    let stats = d.stats;
    if (filter === 'orphans') stats = stats.filter(s => s.orphan_assets > 0);
    if (filter === 'missing') stats = stats.filter(s => s.rom_count > 0 && s.image_count === 0 && s.video_count === 0);
    if (stats.length === 0) { el.innerHTML = '<p class="empty">No data.</p>'; return; }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>ROMs</th><th>Imágenes</th><th>Vídeos</th><th>XML</th><th>Huérfanos</th>';
    html += '</tr></thead><tbody>';
    html += stats.map(s => `<tr>
      <td>${s.platform}</td>
      <td style="text-align:right">${s.rom_count}</td>
      <td style="text-align:right;color:${s.image_count ? '#4ec9b0' : '#555'}">${s.image_count}</td>
      <td style="text-align:right;color:${s.video_count ? '#4ec9b0' : '#555'}">${s.video_count}</td>
      <td style="text-align:right;color:${s.xml_count ? '#4ec9b0' : '#555'}">${s.xml_count}</td>
      <td style="text-align:right;color:${s.orphan_assets ? '#f44747' : '#555'}">${s.orphan_assets || '—'}</td>
    </tr>`).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Sync actions ─────────────────────────────────────────────────────────────
async function doSync(dryRun) {
  const btnDry   = document.getElementById('btn-sync-dry');
  const btnApply = document.getElementById('btn-sync-apply');
  const resultEl = document.getElementById('job-result-sync');
  if (btnDry)   btnDry.disabled   = true;
  if (btnApply) btnApply.disabled = true;
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/sync', { dry_run: dryRun });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay un sync en curso…';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    if (btnDry)   btnDry.disabled   = false;
    if (btnApply) btnApply.disabled = false;
  }
}

function _renderSyncResult(result) {
  const resultEl = document.getElementById('job-result-sync');
  const decisionsEl = document.getElementById('sync-decisions');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    const verb = result.dry_run ? 'Sincronizaría' : 'Sincronizado';
    resultEl.className = 'job-result visible success';
    resultEl.textContent = `${verb} — ↑ ${result.uploaded}  ↓ ${result.downloaded}  ✓ ${result.up_to_date}  ⚠ ${result.conflicts}  ✗ ${result.errors}`;
    if (decisionsEl && result.decisions?.length) {
      const colors = { upload: '#569cd6', download: '#6a9955', conflict: '#f44747' };
      decisionsEl.innerHTML = result.decisions.map(d =>
        `<div style="font-size:12px;color:${colors[d.action]||'#888'};padding:2px 0">[${d.action.toUpperCase()}] ${d.relative}</div>`
      ).join('');
    }
    loadSync(); // Refresh sync log
  }
  const btnDry   = document.getElementById('btn-sync-dry');
  const btnApply = document.getElementById('btn-sync-apply');
  if (btnDry)   btnDry.disabled   = false;
  if (btnApply) btnApply.disabled = false;
}

// ── Convert CHD ──────────────────────────────────────────────────────────────
async function doConvertChd() {
  const pathVal    = document.getElementById('chd-path').value.trim();
  const dryRun     = document.getElementById('chd-dry-run').checked;
  const delSource  = document.getElementById('chd-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .cue/.bin'); return; }
  const btn = document.getElementById('btn-convert-chd');
  const resultEl = document.getElementById('job-result-convert-chd');
  btn.disabled = true;
  btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/convert-chd', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una conversión en curso…';
      btn.disabled = false;
      btn.textContent = 'Convertir a CHD';
      return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Convertir a CHD';
  }
}

function _renderChdResult(result) {
  const resultEl   = document.getElementById('job-result-convert-chd');
  const resultsDiv = document.getElementById('chd-results');
  const btn        = document.getElementById('btn-convert-chd');
  if (!resultEl) return;
  if (result.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + result.error;
  } else {
    _showJobResult('convert-chd', result);
    if (resultsDiv && result.results?.length) {
      resultsDiv.innerHTML = result.results.map(r => {
        const color = r.success ? '#4ec9b0' : '#f44747';
        const tag   = r.success ? (result.dry_run ? 'PREVIEW' : 'OK') : 'FAIL';
        const extra = r.error ? ` — ${r.error}` : (r.success ? ` → ${r.chd}` : '');
        return `<div style="font-size:12px;color:${color};padding:2px 0">[${tag}] ${r.cue}${extra}</div>`;
      }).join('');
    }
  }
  if (btn) { btn.disabled = false; btn.textContent = 'Convertir a CHD'; }
}

// ── Scraper ──────────────────────────────────────────────────────────────────
async function loadScraperSummary() {
  const el = document.getElementById('scraper-summary');
  if (!el) return;
  try {
    const d = await apiFetch('/api/scrape-summary');
    if (!d.platforms || d.platforms.length === 0) {
      el.innerHTML = '<p class="empty">No hay datos. Ejecuta un scan primero.</p>';
      return;
    }
    let html = '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Total ROMs</th><th>Scrapeados</th><th>Pendientes</th></tr></thead><tbody>';
    html += d.platforms.map(p => {
      const pct = p.total > 0 ? Math.round(p.scraped / p.total * 100) : 0;
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

async function doScrape() {
  const btn = document.getElementById('btn-scrape');
  const resultEl = document.getElementById('job-result-scrape');
  btn.disabled = true;
  btn.textContent = 'Scraping…';
  resultEl.className = 'job-result';
  try {
    const d = await apiPost('/api/scrape', {
      platform: document.getElementById('scrape-platform').value.trim() || null,
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
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Iniciar scraping';
  }
}

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
      resultEl.textContent = d.written.map(w => `${w.platform}: ${w.entries} entradas → ${w.path}`).join('\n');
      resultEl.style.whiteSpace = 'pre';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Settings ──────────────────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const cfg = await apiFetch('/api/config');
    document.getElementById('cfg-library-root').value  = cfg.library_root  || '';
    document.getElementById('cfg-rclone-remote').value = cfg.rclone_remote || '';
    document.getElementById('cfg-ss-user').value       = cfg.screenscraper_user || '';
    document.getElementById('cfg-ss-pass').value       = cfg.screenscraper_pass || '';
  } catch(e) { /* silent */ }
}

async function saveSettings() {
  const resultEl = document.getElementById('settings-result');
  resultEl.className = 'job-result';
  const updates = {};
  const lr = document.getElementById('cfg-library-root').value.trim();
  const rr = document.getElementById('cfg-rclone-remote').value.trim();
  const su = document.getElementById('cfg-ss-user').value.trim();
  const sp = document.getElementById('cfg-ss-pass').value;
  if (lr) updates['library.library_root'] = lr;
  if (rr) updates['sync.remote']          = rr;
  if (su) updates['screenscraper.user']   = su;
  if (sp) updates['screenscraper.pass']   = sp;
  if (Object.keys(updates).length === 0) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Nada que guardar — rellena al menos un campo.';
    return;
  }
  try {
    const d = await apiPost('/api/config', updates);
    if (d.error) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + d.error;
    } else {
      resultEl.className = 'job-result visible success';
      resultEl.textContent = 'Guardado: ' + d.saved.join(', ') + '. Reinicia el servidor para aplicar.';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
loadOverview();
</script>
</body>
</html>
"""
