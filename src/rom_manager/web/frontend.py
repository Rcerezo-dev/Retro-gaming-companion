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
  <button onclick="showTab('cable')">Cable Sync</button>
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
        <label for="scan-path">Rutas a escanear (una por línea)</label>
        <textarea id="scan-path" rows="3" placeholder="C:/ROMs&#10;E:/Carpetas anbernic&#10;/mnt/roms" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 8px;border-radius:4px;font:inherit;font-size:12px;resize:vertical"></textarea>
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
  <div id="apply-preview-banner" style="display:none;font-size:12px;margin-bottom:12px;padding:8px 12px;background:#1a1a2e;border:1px solid #3a3a6a;border-radius:4px;color:#9cdcfe;line-height:1.6"></div>
  <div id="plan-content"><p class="loading">Loading…</p></div>
</div>

<!-- DUPLICATES -->
<div id="tab-duplicates" class="tab">
  <div class="toolbar" style="justify-content:space-between;align-items:center">
    <span style="color:#888;font-size:12px">Se conserva la primera copia de cada grupo; se eliminan las demás.</span>
    <button id="btn-delete-all-dups" class="btn danger" onclick="deleteAllDuplicates()">Eliminar todos los duplicados</button>
  </div>
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

<!-- CABLE SYNC -->
<div id="tab-cable" class="tab">

  <!-- Instrucciones de conexión -->
  <div style="max-width:780px;margin-bottom:20px;background:#1e1e2e;border:1px solid #333;border-radius:6px;padding:16px 20px">
    <h3 style="color:#4ec9b0;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px">Cómo conectar la Anbernic al PC</h3>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:8px 14px;font-size:13px">
      <span style="color:#4ec9b0;font-weight:bold">①</span>
      <span style="color:#d4d4d4">Conecta la Anbernic al PC mediante el cable USB.</span>
      <span style="color:#4ec9b0;font-weight:bold">②</span>
      <span style="color:#d4d4d4">En la Anbernic: desliza el panel de notificaciones → toca la notificación USB → selecciona <strong>Transferencia de archivos</strong> (File Transfer / MTP).</span>
      <span style="color:#4ec9b0;font-weight:bold">③</span>
      <span style="color:#d4d4d4">En Windows: abre "Este equipo" — la Anbernic aparece como dispositivo portátil.</span>
    </div>
    <div style="margin-top:14px;padding:10px 12px;background:#161626;border:1px solid #2a2a4a;border-radius:4px;font-size:12px;color:#888;line-height:1.7">
      <strong style="color:#569cd6">⚠ Nota sobre la ruta:</strong> Windows MTP no asigna letra de unidad directamente. Para acceder por ruta de carpeta usa una de estas opciones:<br>
      <span style="color:#4ec9b0">A)</span> <strong style="color:#d4d4d4">SD card</strong> — extrae la tarjeta SD de la Anbernic e insértala en el PC con un lector USB → aparecerá como letra de unidad (ej. <code style="color:#ce9178">F:\</code>)<br>
      <span style="color:#4ec9b0">B)</span> <strong style="color:#d4d4d4">Termux + SFTP</strong> — si ya tienes Termux instalado, ejecuta <code style="color:#ce9178">sshd</code> y accede por red (ej. <code style="color:#ce9178">\\192.168.1.x\share</code>)<br>
      <span style="color:#4ec9b0">C)</span> <strong style="color:#d4d4d4">WinFsp + MTPDrive</strong> — herramienta gratuita que monta el MTP como letra de unidad en Windows
    </div>
  </div>

  <!-- Formulario de sincronización -->
  <div class="actions-panel" style="max-width:780px">
    <h3>Sincronización por cable</h3>

    <!-- Qué sincronizar -->
    <div style="margin-bottom:16px">
      <div style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">¿Qué sincronizar?</div>
      <div style="display:flex;gap:20px">
        <label class="fmt-check">
          <input type="checkbox" id="cable-what-saves" checked> Saves y states
          <span style="color:#555;font-size:11px;margin-left:4px">(.sav, .srm, .state…)</span>
        </label>
        <label class="fmt-check">
          <input type="checkbox" id="cable-what-roms"> ROMs
          <span style="color:#555;font-size:11px;margin-left:4px">(todo lo demás)</span>
        </label>
      </div>
    </div>

    <!-- Dirección -->
    <div style="margin-bottom:16px">
      <div style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Dirección</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px">
          <input type="radio" name="cable-direction" value="pc_to_anbernic" checked style="margin-top:2px;accent-color:#4ec9b0">
          <span>
            <strong style="color:#d4d4d4">PC → Anbernic</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Copia del PC a la consola. Sobrescribe los archivos de la Anbernic.</span><br>
            <span style="color:#569cd6;font-size:11px">✓ Recomendado después de renombrar archivos en el PC</span>
          </span>
        </label>
        <label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px">
          <input type="radio" name="cable-direction" value="anbernic_to_pc" style="margin-top:2px;accent-color:#4ec9b0">
          <span>
            <strong style="color:#d4d4d4">Anbernic → PC</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Copia de la consola al PC. Sobrescribe los archivos del PC.</span><br>
            <span style="color:#569cd6;font-size:11px">✓ Útil para recuperar saves guardados en la consola</span>
          </span>
        </label>
        <label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px">
          <input type="radio" name="cable-direction" value="newest" style="margin-top:2px;accent-color:#4ec9b0">
          <span>
            <strong style="color:#d4d4d4">Más reciente gana</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Compara fechas de modificación y copia en la dirección correcta.</span><br>
            <span style="color:#ce9178;font-size:11px">⚠ Tras renombrar archivos en el PC, las fechas del PC pueden ser incorrectas — usa "PC → Anbernic" en ese caso</span>
          </span>
        </label>
      </div>
    </div>

    <!-- Rutas -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Ruta del PC (library_root)</label>
        <input id="cable-pc-path" type="text" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="E:/Carpetas anbernic">
      </div>
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Ruta de la Anbernic (en el PC)</label>
        <input id="cable-ab-path" type="text" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="F:/ o \\192.168.1.x\share">
      </div>
    </div>

    <!-- Dry run + botón -->
    <div class="actions-row">
      <label class="fmt-check">
        <input type="checkbox" id="cable-dry-run" checked> Dry run (previsualizar sin copiar)
      </label>
      <button id="btn-cable-sync" class="btn primary" onclick="doCableSync()" style="margin-left:auto">Iniciar sincronización</button>
    </div>

    <!-- Progreso -->
    <div id="cable-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="cable-progress-label" style="font-size:12px;color:#888"></span>
        <span id="cable-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="cable-progress-bar" style="height:100%;background:#4ec9b0;width:0%;transition:width 0.3s"></div>
      </div>
    </div>
    <div id="cable-result" class="job-result"></div>
  </div>

  <!-- Tabla de resultados -->
  <div id="cable-details-wrap" style="display:none;margin-top:16px;max-width:780px">
    <div style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Archivos procesados</div>
    <div id="cable-details-list" style="max-height:400px;overflow-y:auto;font-size:12px;background:#1e1e2e;border:1px solid #333;border-radius:6px;padding:10px 12px"></div>
  </div>

</div>

<!-- ASSETS -->
<div id="tab-assets" class="tab">
  <div class="toolbar" style="flex-direction:column;align-items:flex-start;gap:10px">
    <select id="assets-filter" onchange="loadAssets()">
      <option value="all">Todas las plataformas</option>
      <option value="orphans">Solo huérfanos (assets sin ROMs)</option>
      <option value="missing">Solo sin assets</option>
    </select>
    <details style="font-size:12px;color:#888;max-width:700px">
      <summary style="cursor:pointer;color:#569cd6">¿Qué son los archivos "Unknown"?</summary>
      <p style="margin:8px 0 0 0;line-height:1.6">
        Son archivos que el escáner no pudo clasificar como ROM, save, ni asset.
        Suelen ser: <strong>BIOS</strong> (.bin con nombre no reconocido),
        <strong>gamelist.xml</strong> y otros XMLs de metadatos,
        <strong>imágenes sueltas</strong> (.png/.jpg fuera de carpetas de assets),
        <strong>archivos de texto</strong> (.txt, .nfo, .dat de redump),
        <strong>ejecutables</strong> (.exe, .bat), o formatos de disco poco comunes
        no incluidos en la lista de extensiones reconocidas.
        No se tocan ni se renombran — están ahí solo para que los veas.
      </p>
    </details>
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
    <div id="scrape-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="scrape-progress-label" style="font-size:12px;color:#888"></span>
        <span id="scrape-progress-found" style="font-size:11px;color:#4ec9b0"></span>
        <span id="scrape-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="scrape-progress-bar" style="height:100%;background:#4ec9b0;width:0%;transition:width 0.4s"></div>
      </div>
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

  <!-- ── Descomprimir ZIPs ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Descomprimir ZIPs</h3>
    <p style="color:#888;font-size:12px;margin-bottom:12px">Extrae los ROMs dentro de archivos .zip. Omite ZIPs con .cue/.bin/.iso (usa el conversor CHD). RetroArch puede leer ZIPs directamente; usa esto si el emulador concreto no los soporta.</p>
    <div class="actions-row">
      <div><label>Carpeta con .zip</label><input id="zip-path" type="text" placeholder="C:/ROMs/gba"></div>
    </div>
    <div class="actions-row" style="gap:20px;align-items:center">
      <label class="fmt-check"><input type="checkbox" id="zip-dry-run" checked> Dry run (solo previsualizar)</label>
      <label class="fmt-check"><input type="checkbox" id="zip-delete-source"> Eliminar .zip tras extraer</label>
    </div>
    <div class="actions-row">
      <button id="btn-extract-zip" class="btn primary" onclick="doExtractZip()">Descomprimir ZIPs</button>
    </div>
    <div id="zip-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="zip-progress-label" style="font-size:12px;color:#888"></span>
        <span id="zip-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="zip-progress-bar" style="height:100%;background:#569cd6;width:0%;transition:width 0.3s"></div>
      </div>
    </div>
    <div id="job-result-extract-zip" class="job-result"></div>
    <div id="zip-results" style="margin-top:12px;max-height:300px;overflow-y:auto"></div>
    <div class="actions-row" style="margin-top:12px;border-top:1px solid #1e1e2e;padding-top:12px">
      <button class="btn danger" onclick="doCleanupZips()">Eliminar todos los .zip de esta carpeta</button>
      <span style="color:#555;font-size:12px">Para usar si ya extrajiste antes sin marcar "Eliminar .zip"</span>
    </div>
  </div>

  <!-- ── Generar playlists M3U ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Generar playlists M3U (multi-disco)</h3>
    <p style="color:#888;font-size:12px;margin-bottom:12px">Busca juegos con "(Disc 1)", "(Disc 2)"… y crea un archivo .m3u por cada grupo. Necesario para cambiar de disco en RetroArch sin salir del juego.</p>
    <div class="actions-row">
      <div><label>Carpeta de ROMs</label><input id="m3u-path" type="text" placeholder="C:/ROMs/psx"></div>
    </div>
    <div class="actions-row" style="gap:20px;align-items:center">
      <label class="fmt-check"><input type="checkbox" id="m3u-dry-run" checked> Dry run (solo previsualizar)</label>
    </div>
    <div class="actions-row">
      <button class="btn primary" onclick="doGenerateM3U()">Generar M3U</button>
    </div>
    <div id="m3u-result" style="margin-top:12px"></div>
  </div>

  <!-- ── Verificar multi-disco ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Verificar sets multi-disco</h3>
    <p style="color:#888;font-size:12px;margin-bottom:8px">Comprueba que todos los discos de cada juego están presentes, tienen la misma extensión, no hay huecos en la numeración y están en el catálogo.</p>
    <p id="multidisc-folder-hint" style="display:none;font-size:11px;color:#569cd6;margin-bottom:8px"></p>
    <div class="actions-row">
      <div style="flex:1"><label>Carpeta(s) de ROMs (una por línea)</label>
        <textarea id="verify-multidisc-path" rows="3" placeholder="C:/ROMs/psx&#10;C:/ROMs/ps2" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 8px;border-radius:4px;font:inherit;font-size:12px;resize:vertical"></textarea>
      </div>
    </div>
    <div class="actions-row">
      <button class="btn primary" onclick="doVerifyMultidisc()">Verificar</button>
    </div>
    <div id="multidisc-result" style="margin-top:12px"></div>
  </div>

  <!-- ── Saves huérfanos ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Saves huérfanos</h3>
    <p style="color:#888;font-size:12px;margin-bottom:12px">Archivos de save sin ROM asociada (la ROM fue eliminada o renombrada sin su save compañero).</p>
    <div class="actions-row">
      <div><label>Carpeta de la biblioteca</label><input id="orphan-path" type="text" placeholder="E:/Carpetas anbernic"></div>
      <button class="btn" onclick="doFindOrphans()">Buscar huérfanos</button>
    </div>
    <div id="orphan-result" style="margin-top:12px"></div>
  </div>

  <!-- ── Health check ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>Health Check — Verificar integridad</h3>
    <p style="color:#888;font-size:12px;margin-bottom:12px">Re-hashea cada ROM y compara con el SHA1 almacenado. Detecta archivos corruptos o eliminados. <strong style="color:#ce9178">Operación lenta</strong> (lee todos los archivos).</p>
    <div class="actions-row">
      <button id="btn-health-check" class="btn primary" onclick="doHealthCheck()">Iniciar Health Check</button>
    </div>
    <div id="health-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="health-progress-label" style="font-size:12px;color:#888"></span>
        <span id="health-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="health-progress-bar" style="height:100%;background:#4ec9b0;width:0%;transition:width 0.3s"></div>
      </div>
    </div>
    <div id="health-result" style="margin-top:12px"></div>
  </div>

  <!-- ── RetroAchievements ── -->
  <div class="actions-panel" style="margin-bottom:20px">
    <h3>RetroAchievements — Compatibilidad de logros</h3>
    <p style="color:#888;font-size:12px;margin-bottom:8px">Comprueba qué ROMs de tu biblioteca son compatibles con RetroAchievements. Si tienes una versión sin logros pero existe una alternativa compatible, te lo indica.</p>
    <p style="color:#555;font-size:11px;margin-bottom:12px">Necesita API key de <a href="https://retroachievements.org/settings" target="_blank" style="color:#4ec9b0">retroachievements.org → Settings → API</a>. Configúrala en la pestaña <strong style="color:#d4d4d4">Settings</strong>.</p>
    <div id="ra-api-key-status" style="margin-bottom:12px;font-size:12px;color:#555">Verificando API key…</div>
    <div class="actions-row">
      <button id="btn-ra-check" class="btn primary" onclick="doRaCheck()">Comprobar compatibilidad RA</button>
    </div>
    <div id="ra-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="ra-progress-label" style="font-size:12px;color:#888"></span>
        <span id="ra-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="ra-progress-bar" style="height:100%;background:#ce9178;width:0%;transition:width 0.3s"></div>
      </div>
    </div>
    <div id="ra-result" style="margin-top:12px"></div>
  </div>

  <!-- ── CHD ── -->
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
      <span id="chdman-status" style="font-size:12px;color:#555">Verificando chdman…</span>
    </div>
    <div id="chd-progress-wrap" style="display:none;margin-top:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <span id="chd-progress-label" style="font-size:12px;color:#888"></span>
        <span id="chd-progress-file" style="font-size:11px;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1"></span>
      </div>
      <div style="background:#161626;border-radius:4px;height:6px;overflow:hidden">
        <div id="chd-progress-bar" style="height:100%;background:#569cd6;width:0%;transition:width 0.3s"></div>
      </div>
    </div>
    <div id="job-result-convert-chd" class="job-result"></div>
    <div id="chd-results" style="margin-top:16px"></div>
    <div class="actions-row" style="margin-top:12px;border-top:1px solid #1e1e2e;padding-top:12px">
      <button class="btn danger" onclick="doCleanupCueBin()">Eliminar .cue/.bin originales</button>
      <span style="color:#555;font-size:12px">Solo elimina los que ya tienen su .chd correspondiente</span>
    </div>
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
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">chdman — ruta al binario (para conversión a CHD)</label>
        <div style="display:flex;gap:8px">
          <input id="cfg-chdman" type="text" style="flex:1" placeholder="chdman  o  C:/tools/chdman.exe">
          <button class="btn" onclick="testChdman()" style="flex-shrink:0">Probar</button>
        </div>
        <div id="chdman-test-result" style="font-size:11px;margin-top:4px;color:#555"></div>
      </div>
      <div style="width:100%">
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">RetroAchievements API key — <a href="https://retroachievements.org/settings" target="_blank" style="color:#4ec9b0">obtener en RA Settings → Web API Key</a></label>
        <input id="cfg-ra-api-key" type="text" style="width:100%" placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx">
      </div>
    </div>

    <div class="actions-row" style="margin-top:16px">
      <button class="btn primary" onclick="saveSettings()">Guardar config.toml</button>
    </div>
    <div id="settings-result" class="job-result"></div>
  </div>
  <div class="actions-panel" style="margin-top:20px">
    <h3>Base de datos</h3>
    <div class="actions-row">
      <a href="/api/db-backup" download class="btn">Descargar copia de seguridad (.sqlite)</a>
      <span style="color:#555;font-size:12px">Descarga library.sqlite — guárdala antes de operaciones destructivas</span>
    </div>
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
  if (name === 'cable')      loadCableSync();
  if (name === 'scraper')    loadScraperSummary();
  if (name === 'settings')   loadSettings();
  if (name === 'tools')      loadTools();
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
      if (!s.scan_running && !s.match_running && !s.sync_running && !s.convert_chd_running && !s.scrape_running && !s.extract_zip_running && !s.health_check_running && !s.ra_check_running && !s.cable_sync_running) {
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
  // CHD progress bar
  const chdWrap = document.getElementById('chd-progress-wrap');
  if (s.convert_chd_running && s.chd_progress && s.chd_progress.total > 0) {
    const p = s.chd_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (chdWrap) chdWrap.style.display = '';
    const bar = document.getElementById('chd-progress-bar');
    const lbl = document.getElementById('chd-progress-label');
    const file = document.getElementById('chd-progress-file');
    if (bar) bar.style.width = pct + '%';
    if (lbl) lbl.textContent = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.convert_chd_running) {
    if (chdWrap) chdWrap.style.display = 'none';
  }
  if (!s.convert_chd_running && s.convert_chd_result) {
    _renderChdResult(s.convert_chd_result);
  }
  // Scrape progress bar
  const scrapeWrap = document.getElementById('scrape-progress-wrap');
  if (s.scrape_running && s.scrape_progress && s.scrape_progress.total > 0) {
    const p = s.scrape_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (scrapeWrap) scrapeWrap.style.display = '';
    const bar   = document.getElementById('scrape-progress-bar');
    const lbl   = document.getElementById('scrape-progress-label');
    const found = document.getElementById('scrape-progress-found');
    const file  = document.getElementById('scrape-progress-file');
    if (bar)   bar.style.width  = pct + '%';
    if (lbl)   lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (found) found.textContent = p.found > 0 ? `✓ ${p.found} encontrados` : '';
    if (file)  file.textContent  = p.current_game;
  } else if (!s.scrape_running) {
    if (scrapeWrap) scrapeWrap.style.display = 'none';
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

  // ZIP progress
  const zipWrap = document.getElementById('zip-progress-wrap');
  const btnZip  = document.getElementById('btn-extract-zip');
  if (s.extract_zip_running && s.zip_progress && s.zip_progress.total > 0) {
    const p = s.zip_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (zipWrap) zipWrap.style.display = '';
    const bar  = document.getElementById('zip-progress-bar');
    const lbl  = document.getElementById('zip-progress-label');
    const file = document.getElementById('zip-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.extract_zip_running) {
    if (zipWrap) zipWrap.style.display = 'none';
  }
  if (btnZip) btnZip.disabled = s.extract_zip_running;
  if (!s.extract_zip_running && s.extract_zip_result) {
    const el = document.getElementById('job-result-extract-zip');
    const r  = s.extract_zip_result;
    if (el) {
      if (r.error) {
        el.className = 'job-result visible error-r';
        el.textContent = 'Error: ' + r.error;
      } else {
        const verb = r.dry_run ? 'Extraería' : 'Extraídos';
        el.className = 'job-result visible success';
        el.textContent = `${verb}: ${r.extracted}  |  Omitidos: ${r.skipped}  |  Fallidos: ${r.failed}`;
      }
      const div = document.getElementById('zip-results');
      if (div && r.results?.length) {
        div.innerHTML = r.results.map(x => {
          const color = x.success ? '#4ec9b0' : (x.skipped_reason ? '#888' : '#f44747');
          const tag   = x.success ? (r.dry_run ? 'PREVIEW' : 'OK') : (x.skipped_reason ? 'SKIP' : 'FAIL');
          const msg   = x.skipped_reason || x.error || (x.extracted.length ? '→ ' + x.extracted.join(', ') : '');
          return `<div style="font-size:12px;color:${color};padding:2px 0">[${tag}] ${x.zip}${msg ? ' — ' + msg : ''}</div>`;
        }).join('');
      }
    }
    if (btnZip) { btnZip.disabled = false; btnZip.textContent = 'Descomprimir ZIPs'; }
  }

  // Health check progress
  const healthWrap = document.getElementById('health-progress-wrap');
  const btnHealth  = document.getElementById('btn-health-check');
  if (s.health_check_running && s.health_progress && s.health_progress.total > 0) {
    const p = s.health_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (healthWrap) healthWrap.style.display = '';
    const bar  = document.getElementById('health-progress-bar');
    const lbl  = document.getElementById('health-progress-label');
    const file = document.getElementById('health-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.health_check_running) {
    if (healthWrap) healthWrap.style.display = 'none';
  }
  if (btnHealth) btnHealth.disabled = s.health_check_running;
  if (!s.health_check_running && s.health_check_result) {
    _renderHealthResult(s.health_check_result);
    if (btnHealth) { btnHealth.disabled = false; btnHealth.textContent = 'Iniciar Health Check'; }
  }

  // RA check progress
  const raWrap  = document.getElementById('ra-progress-wrap');
  const btnRa   = document.getElementById('btn-ra-check');
  if (s.ra_check_running && s.ra_progress && s.ra_progress.total > 0) {
    const p = s.ra_progress;
    const pct = Math.round((p.current / p.total) * 100);
    if (raWrap) raWrap.style.display = '';
    const bar  = document.getElementById('ra-progress-bar');
    const lbl  = document.getElementById('ra-progress-label');
    const file = document.getElementById('ra-progress-file');
    if (bar)  bar.style.width  = pct + '%';
    if (lbl)  lbl.textContent  = `${p.current} / ${p.total} (${pct}%)`;
    if (file) file.textContent = p.current_file;
  } else if (!s.ra_check_running) {
    if (raWrap) raWrap.style.display = 'none';
  }
  if (btnRa) btnRa.disabled = s.ra_check_running;
  if (!s.ra_check_running && s.ra_check_result) {
    _renderRaResult(s.ra_check_result);
    if (btnRa) { btnRa.disabled = false; btnRa.textContent = 'Comprobar compatibilidad RA'; }
  }

  // Cable sync
  const btnCable = document.getElementById('btn-cable-sync');
  const cableWrap = document.getElementById('cable-progress-wrap');
  if (s.cable_sync_running && s.cable_progress) {
    const p = s.cable_progress;
    if (cableWrap) cableWrap.style.display = '';
    const lbl  = document.getElementById('cable-progress-label');
    const file = document.getElementById('cable-progress-file');
    const bar  = document.getElementById('cable-progress-bar');
    if (lbl)  lbl.textContent  = `Copiados: ${p.copied || 0}`;
    if (file) file.textContent = p.current_file || '';
    // Indeterminate animation — bounce bar width 10→90 based on copied count (mod)
    if (bar)  bar.style.width  = (((p.copied || 0) * 7) % 80 + 10) + '%';
  } else if (!s.cable_sync_running) {
    if (cableWrap) cableWrap.style.display = 'none';
  }
  if (btnCable) btnCable.disabled = s.cable_sync_running;
  if (!s.cable_sync_running && s.cable_sync_result) {
    _renderCableSyncResult(s.cable_sync_result);
    if (btnCable) { btnCable.disabled = false; btnCable.textContent = 'Iniciar sincronización'; }
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
    const prunedMsg = result.pruned > 0 ? `  |  Eliminados de BD: ${result.pruned}` : '';
    el.textContent = `Scan completado — ROMs: ${result.roms_detected}  |  Ya escaneados: ${result.roms_skipped}  |  Saves: ${result.saves_detected}  |  Errores: ${result.errors}${prunedMsg}`;
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
  const rawVal = document.getElementById('scan-path').value.trim();
  if (!rawVal) { alert('Introduce al menos una ruta para escanear.'); return; }
  // Split by newlines or commas
  const sourcePaths = rawVal.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
  const btn = document.getElementById('btn-scan');
  btn.disabled = true;
  btn.textContent = 'Escaneando…';
  const resultEl = document.getElementById('job-result-scan');
  resultEl.className = 'job-result';

  try {
    const quick = document.getElementById('scan-quick')?.checked || false;
    const d = await apiPost('/api/scan', { source_paths: sourcePaths, quick });
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

    // ── Apply preview banner ──────────────────────────────────────────────────
    const applyBanner = document.getElementById('apply-preview-banner');
    if (applyBanner) {
      if (d.pending.length > 0) {
        const savesMsg = d.total_saves_affected > 0
          ? `, junto a <strong>${d.total_saves_affected}</strong> save(s) compañeros`
          : ', sin saves compañeros detectados';
        applyBanner.innerHTML =
          `Se renombrarán <strong>${d.pending.length}</strong> ROM(s)${savesMsg}. ` +
          `Si algún save no puede renombrarse, la ROM tampoco cambiará.`;
        applyBanner.style.display = '';
      } else {
        applyBanner.style.display = 'none';
      }
    }

    let html = '';
    if (d.pending.length) {
      html += `<h3 style="color:#569cd6;margin-bottom:12px">Pending renames — ${d.pending.length}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Platform</th><th>From</th><th>To</th><th style="text-align:center">Saves</th></tr></thead><tbody>';
      html += d.pending.map(op => `<tr>
        <td>${op.platform||'<span style="color:#555">Unknown</span>'}</td>
        <td title="${op.source}">${op.source_name}</td>
        <td style="color:#4ec9b0" title="${op.target}">${op.target_name}</td>
        <td style="text-align:center;color:${op.companion_saves > 0 ? '#dcdcaa' : '#555'}">${op.companion_saves > 0 ? op.companion_saves : '—'}</td>
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
  const banner = document.getElementById('apply-preview-banner');
  const msg = banner?.textContent
    ? `${banner.textContent}\n\n¿Continuar? Esta operación mueve archivos en disco.`
    : '¿Aplicar el renombrado? Esta operación mueve archivos en disco.';
  if (!confirm(msg)) return;
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

async function deleteAllDuplicates() {
  const el = document.getElementById('dup-content');
  // Count duplicates to delete
  const rows = document.querySelectorAll('#tab-duplicates .btn.danger');
  const count = rows.length;
  if (count === 0) { alert('No hay duplicados para eliminar.'); return; }
  if (!confirm(`¿Eliminar ${count} archivo(s) duplicado(s) del disco?\n\nSe conservará una copia de cada juego. Esta operación no se puede deshacer.`)) return;
  const btn = document.getElementById('btn-delete-all-dups');
  btn.disabled = true;
  btn.textContent = 'Eliminando…';
  try {
    const d = await apiPost('/api/duplicates/delete-all', {});
    await loadDuplicates();
    loadOverview();
    alert(`Eliminados: ${d.deleted}  |  Fallidos: ${d.failed}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}`);
  } catch(e) {
    alert('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Eliminar todos los duplicados';
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

// ── Extract ZIP ──────────────────────────────────────────────────────────────
async function doCleanupZips() {
  const pathVal = document.getElementById('zip-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  const n = (document.querySelectorAll('#zip-results div').length) || '?';
  if (!confirm(`¿Eliminar TODOS los archivos .zip de:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-zips', { source_path: pathVal });
    const el = document.getElementById('job-result-extract-zip');
    el.className = 'job-result visible success';
    el.textContent = `ZIPs eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message); }
}

async function doCleanupCueBin() {
  const pathVal = document.getElementById('chd-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la carpeta'); return; }
  if (!confirm(`¿Eliminar los archivos .cue y .bin que ya tienen su .chd en:\n${pathVal}\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/cleanup-cue-bin', { source_path: pathVal });
    const el = document.getElementById('job-result-convert-chd');
    el.className = 'job-result visible success';
    el.textContent = `Archivos eliminados: ${d.deleted}  |  Espacio liberado: ${fmtSize(d.freed_bytes)}${d.skipped ? `  |  Sin .chd (no tocados): ${d.skipped}` : ''}${d.failed ? `  |  Fallidos: ${d.failed}` : ''}`;
  } catch(e) { alert('Error: ' + e.message); }
}

async function doExtractZip() {
  const pathVal   = document.getElementById('zip-path').value.trim();
  const dryRun    = document.getElementById('zip-dry-run').checked;
  const delSource = document.getElementById('zip-delete-source').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta con archivos .zip'); return; }
  const btn = document.getElementById('btn-extract-zip');
  const resultEl = document.getElementById('job-result-extract-zip');
  btn.disabled = true; btn.textContent = 'Procesando…';
  resultEl.className = 'job-result';
  document.getElementById('zip-results').innerHTML = '';
  try {
    const d = await apiPost('/api/extract-zip', { source_path: pathVal, dry_run: dryRun, delete_source: delSource });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay una extracción en curso…';
      btn.disabled = false; btn.textContent = 'Descomprimir ZIPs'; return;
    }
    startPolling();
  } catch(e) {
    resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message;
    btn.disabled = false; btn.textContent = 'Descomprimir ZIPs';
  }
}

// ── M3U Generator ─────────────────────────────────────────────────────────────
async function doGenerateM3U() {
  const pathVal = document.getElementById('m3u-path').value.trim();
  const dryRun  = document.getElementById('m3u-dry-run').checked;
  if (!pathVal) { alert('Introduce la ruta de la carpeta de ROMs'); return; }
  const resultEl = document.getElementById('m3u-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Buscando grupos multi-disco…</p>';
  try {
    const d = await apiPost('/api/generate-m3u', { source_path: pathVal, dry_run: dryRun });
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
    const verb = dryRun ? 'Crearía' : 'Creados';
    let html = `<p style="color:#4ec9b0;margin-bottom:12px">${verb}: <strong>${d.created}</strong>  |  Ya existían: <strong>${d.skipped}</strong></p>`;
    if (d.groups.length) {
      html += '<div style="max-height:300px;overflow-y:auto">';
      html += d.groups.map(g => {
        const color = g.discs.length >= 2 ? '#4ec9b0' : '#888';
        return `<div style="font-size:12px;color:${color};padding:2px 0"><strong>${g.m3u}</strong> → ${g.discs.join(', ')}</div>`;
      }).join('');
      html += '</div>';
    } else {
      html += '<p style="color:#555;font-size:12px">No se encontraron grupos multi-disco.</p>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Multi-disc Verifier ───────────────────────────────────────────────────────
async function doVerifyMultidisc() {
  const rawVal = document.getElementById('verify-multidisc-path').value.trim();
  if (!rawVal) { alert('Introduce al menos una carpeta de ROMs'); return; }
  const paths = rawVal.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
  const resultEl = document.getElementById('multidisc-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Verificando…</p>';
  // Aggregate results across all paths
  let totalOk = 0, totalIssues = 0;
  const allIssues = [];
  try {
    for (const pathVal of paths) {
      const d = await apiPost('/api/verify-multidisc', { source_path: pathVal });
      if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
      totalOk += d.groups_ok; totalIssues += d.groups_with_issues;
      allIssues.push(...d.issues);
    }
    const d = { groups_ok: totalOk, groups_with_issues: totalIssues, issues: allIssues };
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }

    const realIssues    = d.issues.filter(i => i.issue_type !== 'unmatched');
    const unmatchedOnly = d.issues.filter(i => i.issue_type === 'unmatched');
    const realBad = new Set(realIssues.map(i => i.base_name));
    // Groups with only "unmatched" and no real structural issues are OK structurally
    const structurallyBad = d.groups_with_issues - [...new Set(unmatchedOnly.map(i => i.base_name))].filter(n => !realBad.has(n)).length;
    const total = d.groups_ok + d.groups_with_issues;

    let html = `<p style="margin-bottom:8px">`;
    html += `<span style="color:#4ec9b0">✓ ${d.groups_ok + (d.groups_with_issues - structurallyBad)} grupos OK estructuralmente</span>`;
    if (structurallyBad > 0) html += `  <span style="color:#f44747">✗ ${structurallyBad} con problemas reales</span>`;
    if (unmatchedOnly.length > 0) html += `  <span style="color:#888">⚠ ${unmatchedOnly.length} sin match en catálogo (normal si no has hecho Match aún)</span>`;
    html += `  <span style="color:#555">(${total} grupos)</span></p>`;

    const issueLabels = { gap: 'Disco faltante', mixed_ext: 'Extensiones mezcladas', missing_file: 'Archivo no encontrado', unmatched: 'Sin match en catálogo' };
    if (realIssues.length) {
      html += `<p style="color:#f44747;font-size:12px;margin:10px 0 6px">Problemas que requieren atención:</p>`;
      html += '<div style="max-height:300px;overflow-y:auto;margin-bottom:12px">';
      html += realIssues.map(i => `<div style="font-size:12px;padding:3px 0;border-bottom:1px solid #1e1e2e">
        <span style="color:#f44747">${issueLabels[i.issue_type] || i.issue_type}</span>
        <span style="color:#888;margin:0 6px">·</span>
        <span style="color:#d4d4d4">${i.base_name}</span>
        <span style="color:#555;margin-left:8px">${i.detail}</span>
      </div>`).join('');
      html += '</div>';
    }
    if (unmatchedOnly.length) {
      html += `<details style="font-size:12px;color:#555"><summary style="cursor:pointer;color:#888">Sin match en catálogo (${unmatchedOnly.length}) — haz Match catálogos para resolverlos</summary>`;
      html += '<div style="max-height:200px;overflow-y:auto;margin-top:6px">';
      html += unmatchedOnly.map(i => `<div style="padding:2px 0;color:#555">${i.base_name} — ${i.detail}</div>`).join('');
      html += '</div></details>';
    }
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Orphaned Saves ────────────────────────────────────────────────────────────
async function doFindOrphans() {
  const pathVal = document.getElementById('orphan-path').value.trim();
  if (!pathVal) { alert('Introduce la ruta de la biblioteca'); return; }
  const resultEl = document.getElementById('orphan-result');
  resultEl.innerHTML = '<p style="color:#888;font-size:12px">Buscando…</p>';
  try {
    const d = await apiFetch('/api/orphaned-saves?path=' + encodeURIComponent(pathVal));
    if (d.error) { resultEl.innerHTML = `<p class="error-msg">${d.error}</p>`; return; }
    if (d.total === 0) { resultEl.innerHTML = '<p class="empty">No se encontraron saves huérfanos.</p>'; return; }
    let html = `<p style="color:#888;margin-bottom:10px">${d.total} save(s) huérfano(s) encontrado(s):</p>`;
    html += '<div style="max-height:350px;overflow-y:auto;margin-bottom:10px">';
    html += d.orphans.map(o => `
      <div style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px" id="orphan-${CSS.escape(o.save_path)}">
        <input type="checkbox" class="orphan-chk" value="${o.save_path.replace(/"/g, '&quot;')}" checked>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#888" title="${o.save_path}">${o.save_path}</span>
        <span style="color:#555;flex-shrink:0">${fmtSize(o.size_bytes)}</span>
      </div>`).join('');
    html += '</div>';
    html += '<button class="btn danger" onclick="doDeleteOrphans()">Eliminar seleccionados</button>';
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

async function doDeleteOrphans() {
  const checked = [...document.querySelectorAll('.orphan-chk:checked')].map(c => c.value);
  if (checked.length === 0) { alert('Selecciona al menos un archivo.'); return; }
  if (!confirm(`¿Eliminar ${checked.length} save(s) huérfano(s)?\n\nEsta operación no se puede deshacer.`)) return;
  try {
    const d = await apiPost('/api/orphaned-saves/delete', { paths: checked });
    alert(`Eliminados: ${d.deleted}  |  Fallidos: ${d.failed}  |  Liberados: ${fmtSize(d.freed_bytes)}`);
    doFindOrphans();
  } catch(e) {
    alert('Error: ' + e.message);
  }
}

// ── Health Check ─────────────────────────────────────────────────────────────
async function doHealthCheck() {
  const btn = document.getElementById('btn-health-check');
  if (!confirm('El Health Check re-hashea todos los ROMs. Puede tardar mucho en bibliotecas grandes.\n\n¿Continuar?')) return;
  btn.disabled = true; btn.textContent = 'Verificando…';
  document.getElementById('health-result').innerHTML = '';
  try {
    const d = await apiPost('/api/health-check', {});
    if (d.status === 'already_running') {
      btn.disabled = false; btn.textContent = 'Iniciar Health Check'; return;
    }
    startPolling();
  } catch(e) {
    btn.disabled = false; btn.textContent = 'Iniciar Health Check';
    document.getElementById('health-result').innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function _renderHealthResult(r) {
  const el = document.getElementById('health-result');
  if (!el) return;
  if (r.error) { el.innerHTML = `<p class="error-msg">${r.error}</p>`; return; }
  const total = r.ok + r.corrupted + r.missing;
  let html = `<p style="margin-bottom:12px">`;
  html += `<span style="color:#4ec9b0">✓ ${r.ok} OK</span>`;
  if (r.corrupted > 0) html += `  <span style="color:#f44747">✗ ${r.corrupted} corruptos</span>`;
  if (r.missing   > 0) html += `  <span style="color:#ce9178">⚠ ${r.missing} no encontrados</span>`;
  html += `  <span style="color:#555">(${total} ROMs verificados)</span></p>`;
  if (r.issues?.length) {
    html += '<div style="max-height:400px;overflow-y:auto">';
    html += r.issues.map(i => {
      const color = i.status === 'corrupted' ? '#f44747' : '#ce9178';
      const label = i.status === 'corrupted' ? 'CORRUPTO' : 'NO ENCONTRADO';
      const name  = i.source_path.split(/[\\/]/).pop();
      return `<div style="font-size:12px;color:${color};padding:2px 0" title="${i.source_path}">[${label}] ${name}</div>`;
    }).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

// ── RetroAchievements ────────────────────────────────────────────────────────
async function doRaCheck() {
  const btn = document.getElementById('btn-ra-check');
  btn.disabled = true;
  btn.textContent = 'Comprobando…';
  document.getElementById('ra-result').innerHTML = '';
  try {
    const d = await apiPost('/api/ra-check', {});
    if (d.error) {
      document.getElementById('ra-result').innerHTML = `<p class="error-msg">${d.error}</p>`;
      btn.disabled = false; btn.textContent = 'Comprobar compatibilidad RA';
      return;
    }
    if (d.status === 'already_running') {
      document.getElementById('ra-result').innerHTML = '<p style="color:#888;font-size:12px">Ya hay una comprobación en curso…</p>';
    }
    startPolling();
  } catch(e) {
    document.getElementById('ra-result').innerHTML = `<p class="error-msg">${e.message}</p>`;
    btn.disabled = false; btn.textContent = 'Comprobar compatibilidad RA';
  }
}

function _renderRaResult(r) {
  const el = document.getElementById('ra-result');
  if (!el) return;
  if (r.error) { el.innerHTML = `<p class="error-msg">${r.error}</p>`; return; }

  const hasAlternatives = r.no_support_alternative > 0;
  const csvLink = hasAlternatives
    ? `<a href="/api/ra-check.csv" download class="btn" style="margin-left:12px;font-size:12px">&#x2193; Descargar CSV (${r.no_support_alternative} juegos)</a>`
    : '';

  let html = `<div style="margin-bottom:12px;display:flex;align-items:center;flex-wrap:wrap;gap:8px">`;
  html += `<span style="color:#4ec9b0">✓ ${r.supported} con logros</span>`;
  if (hasAlternatives)
    html += `  <span style="color:#ce9178">⚠ ${r.no_support_alternative} sin logros (alternativa disponible)</span>`;
  if (r.no_support > 0)
    html += `  <span style="color:#555">✗ ${r.no_support} sin soporte RA</span>`;
  if (r.no_md5 > 0)
    html += `  <span style="color:#555">? ${r.no_md5} sin MD5</span>`;
  if (r.platform_unknown > 0)
    html += `  <span style="color:#555">— ${r.platform_unknown} plataforma no soportada</span>`;
  html += `  <span style="color:#333">(${r.total} total)</span>`;
  html += csvLink;
  html += `</div>`;

  if (r.alternatives?.length) {
    html += `<div style="margin-bottom:8px;color:#ce9178;font-size:12px">`;
    if (hasAlternatives && r.no_support_alternative > 10) {
      html += `⚠ ${r.no_support_alternative} juegos en tu biblioteca no son la versión compatible con RA. `;
      html += `Existe una versión alternativa para cada uno. Descarga el CSV para ver la lista completa.`;
    } else {
      html += `Estos juegos tienen una versión RA-compatible disponible:`;
    }
    html += `</div>`;
    html += '<div style="overflow-x:auto"><table><thead><tr>';
    html += '<th>Plataforma</th><th>Tu archivo</th><th>Título RA</th><th>Logros</th><th>Puntos</th>';
    html += '</tr></thead><tbody>';
    html += r.alternatives.map(a => `<tr>
      <td>${a.platform}</td>
      <td title="${a.filename}" style="max-width:260px">${a.filename}</td>
      <td><a href="https://retroachievements.org/game/${a.ra_id}" target="_blank" style="color:#4ec9b0">${a.ra_title}</a></td>
      <td style="text-align:right;color:#ce9178">${a.ra_achievements}</td>
      <td style="text-align:right;color:#555">${a.ra_points}</td>
    </tr>`).join('');
    html += '</tbody></table></div>';
    if (r.no_support_alternative > r.alternatives.length) {
      html += `<p style="font-size:11px;color:#555;margin-top:6px">Mostrando ${r.alternatives.length} de ${r.no_support_alternative} — descarga el CSV para la lista completa.</p>`;
    }
  }

  el.innerHTML = html;
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
    document.getElementById('cfg-chdman').value        = cfg.chdman || 'chdman';
    document.getElementById('cfg-ra-api-key').value   = cfg.ra_api_key || '';
  } catch(e) { /* silent */ }
}

async function testChdman() {
  const el = document.getElementById('chdman-test-result');
  el.style.color = '#888'; el.textContent = 'Probando…';
  // Save current chdman value first if changed
  const val = document.getElementById('cfg-chdman').value.trim();
  if (val) await apiPost('/api/config', { 'tools.chdman': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/test-chdman');
    if (d.ok) {
      el.style.color = '#4ec9b0';
      el.textContent = '✓ ' + (d.version || 'OK') + '  (' + d.path + ')';
      // Update CHD panel status too
      const st = document.getElementById('chdman-status');
      if (st) { st.style.color = '#4ec9b0'; st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
    } else {
      el.style.color = '#f44747'; el.textContent = '✗ ' + d.error;
      const st = document.getElementById('chdman-status');
      if (st) { st.style.color = '#f44747'; st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
    }
  } catch(e) { el.style.color = '#f44747'; el.textContent = '✗ ' + e.message; }
}

async function loadTools() {
  try {
    const [cfg, discData] = await Promise.all([
      apiFetch('/api/config'),
      apiFetch('/api/disc-folders').catch(() => ({ folders: [], library_root: null })),
    ]);
    const root = cfg.library_root || '';
    // Auto-fill simple tools with library_root
    if (root) {
      _setIfEmpty('zip-path',               root);
      _setIfEmpty('orphan-path',            root);
      _setIfEmpty('verify-multidisc-path',  discData.folders.length ? discData.folders.join('\n') : root);
      _setIfEmpty('m3u-path',               discData.folders.length ? discData.folders[0] : root);
      _setIfEmpty('chd-path',               discData.folders.length ? discData.folders[0] : root);
    }
    // Show multi-disc hint
    if (discData.folders.length > 1) {
      const hint = document.getElementById('multidisc-folder-hint');
      if (hint) {
        hint.textContent = `Detectadas ${discData.folders.length} carpetas de plataformas de disco: ${discData.folders.map(f => f.split(/[\\/]/).pop()).join(', ')}`;
        hint.style.display = '';
      }
    }
    // Test chdman silently and update status
    try {
      const d = await apiFetch('/api/test-chdman');
      const st = document.getElementById('chdman-status');
      if (st) {
        if (d.ok) { st.style.color = '#4ec9b0'; st.textContent = '✓ ' + (d.version || 'chdman disponible'); }
        else      { st.style.color = '#f44747'; st.textContent = '✗ chdman no encontrado — configura la ruta en Settings'; }
      }
    } catch(_) {}
    // Show RA API key status
    const raStatus = document.getElementById('ra-api-key-status');
    if (raStatus) {
      if (cfg.ra_api_key) {
        raStatus.style.color = '#4ec9b0';
        raStatus.textContent = '✓ API key configurada';
      } else {
        raStatus.style.color = '#f44747';
        raStatus.innerHTML = '✗ API key no configurada — <a href="#" onclick="showTab(\'settings\');return false" style="color:#569cd6">ir a Settings</a>';
      }
    }
  } catch(e) { /* silent */ }
}

function _setIfEmpty(id, value) {
  const el = document.getElementById(id);
  if (el && !el.value.trim()) el.value = value;
}

async function saveSettings() {
  const resultEl = document.getElementById('settings-result');
  resultEl.className = 'job-result';
  const updates = {};
  const lr = document.getElementById('cfg-library-root').value.trim();
  const rr = document.getElementById('cfg-rclone-remote').value.trim();
  const su = document.getElementById('cfg-ss-user').value.trim();
  const sp = document.getElementById('cfg-ss-pass').value;
  const ch = document.getElementById('cfg-chdman').value.trim();
  const ra = document.getElementById('cfg-ra-api-key').value.trim();
  if (lr) updates['library.library_root']        = lr;
  if (rr) updates['sync.remote']                 = rr;
  if (su) updates['screenscraper.user']           = su;
  if (sp) updates['screenscraper.pass']           = sp;
  if (ch) updates['tools.chdman']                 = ch;
  if (ra) updates['retroachievements.api_key']    = ra;
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
      resultEl.textContent = 'Guardado: ' + d.saved.join(', ') + '.';
    }
  } catch(e) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

// ── Cable Sync ────────────────────────────────────────────────────────────────
async function loadCableSync() {
  // Auto-fill PC path from config if field is empty
  try {
    const cfg = await apiFetch('/api/config');
    _setIfEmpty('cable-pc-path', cfg.library_root || '');
  } catch(_) {}
}

async function doCableSync() {
  const pcPath = document.getElementById('cable-pc-path').value.trim();
  const abPath = document.getElementById('cable-ab-path').value.trim();
  if (!pcPath) { alert('Introduce la ruta del PC (library_root).'); return; }
  if (!abPath) { alert('Introduce la ruta de la Anbernic en el PC.'); return; }

  const wantSaves = document.getElementById('cable-what-saves').checked;
  const wantRoms  = document.getElementById('cable-what-roms').checked;
  if (!wantSaves && !wantRoms) { alert('Selecciona al menos qué sincronizar: saves o ROMs.'); return; }

  const what = [];
  if (wantSaves) what.push('saves');
  if (wantRoms)  what.push('roms');

  const direction = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const dryRun    = document.getElementById('cable-dry-run').checked;

  const btn      = document.getElementById('btn-cable-sync');
  const resultEl = document.getElementById('cable-result');
  btn.disabled = true;
  btn.textContent = 'Sincronizando…';
  resultEl.className = 'job-result';
  document.getElementById('cable-details-wrap').style.display = 'none';

  // Clear previous result so it doesn't show stale data while job runs
  delete window._lastCableSyncResult;

  try {
    const d = await apiPost('/api/cable-sync', {
      pc_path: pcPath,
      anbernic_path: abPath,
      what,
      direction,
      dry_run: dryRun,
    });
    if (d.status === 'already_running') {
      resultEl.className = 'job-result visible';
      resultEl.textContent = 'Ya hay una sincronización en curso…';
      btn.disabled = false;
      btn.textContent = 'Iniciar sincronización';
      return;
    }
    startPolling();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = 'Iniciar sincronización';
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + e.message;
  }
}

function _renderCableSyncResult(r) {
  const resultEl = document.getElementById('cable-result');
  const detailsWrap = document.getElementById('cable-details-wrap');
  const detailsList = document.getElementById('cable-details-list');
  if (!resultEl) return;

  // Guard: only render once per result
  const key = JSON.stringify({c: r.copied, e: r.errors, d: r.direction});
  if (window._lastCableSyncResult === key) return;
  window._lastCableSyncResult = key;

  if (r.error) {
    resultEl.className = 'job-result visible error-r';
    resultEl.textContent = 'Error: ' + r.error;
    return;
  }

  const verb   = r.dry_run ? 'Copiaría' : 'Copiados';
  const dirMap = { pc_to_anbernic: 'PC → Anbernic', anbernic_to_pc: 'Anbernic → PC', newest: 'Más reciente gana' };
  const dirStr = dirMap[r.direction] || r.direction;
  const dryTag = r.dry_run ? ' [DRY RUN — nada fue copiado]' : '';

  resultEl.className = 'job-result visible success';
  resultEl.textContent = `${verb}: ${r.copied} archivo(s) (${fmtSize(r.copied_bytes)})  |  Omitidos: ${r.skipped}  |  Errores: ${r.errors}  —  ${dirStr}${dryTag}`;

  if (r.details && r.details.length > 0) {
    detailsList.innerHTML = r.details.map(d =>
      `<div style="padding:2px 0;color:#888"><span style="color:#4ec9b0;margin-right:8px">${d.file}</span>${d.path}</div>`
    ).join('');
    detailsWrap.style.display = '';
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
loadOverview();
</script>
</body>
</html>
"""
