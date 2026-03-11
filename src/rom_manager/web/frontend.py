from __future__ import annotations

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ROM Manager</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f0f; color: #d4d4d4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; font-size: 14px; }
  code, .mono { font-family: 'Consolas', 'Courier New', monospace; }
  a { color: #4ec9b0; text-decoration: none; }
  a:hover { text-decoration: underline; }

  header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 14px 24px; border-bottom: 2px solid #4ec9b0; display: flex; align-items: center; gap: 16px; }
  header h1 { color: #4ec9b0; font-size: 20px; letter-spacing: 2px; font-family: 'Consolas', monospace; }
  header .subtitle { color: #888; font-size: 12px; }

  nav { background: #12122a; display: flex; gap: 0; padding: 0 20px; border-bottom: 1px solid #2a2a3a; overflow-x: auto; scrollbar-width: none; }
  nav::-webkit-scrollbar { display: none; }
  nav button { background: none; border: none; color: #666; padding: 11px 18px; cursor: pointer; font: inherit; font-size: 13px; border-bottom: 2px solid transparent; transition: color .15s, border-color .15s; white-space: nowrap; }
  nav button:hover { color: #d4d4d4; }
  nav button.active { color: #4ec9b0; border-bottom-color: #4ec9b0; font-weight: 500; }

  main { padding: 24px; max-width: 1400px; }

  .tab { display: none; }
  .tab.active { display: block; }

  .cards { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; }
  .card { background: #1e1e2e; border: 1px solid #2a2a3a; border-radius: 8px; padding: 16px 20px; min-width: 160px; border-left: 3px solid #4ec9b0; transition: border-color .2s, box-shadow .2s; }
  .card:hover { border-color: #6de0c8; box-shadow: 0 2px 12px rgba(78,201,176,.08); }
  .card.blue { border-left-color: #569cd6; }
  .card.orange { border-left-color: #ce9178; }
  .card.purple { border-left-color: #c586c0; }
  .card.red { border-left-color: #f44747; }
  .card .label { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .card .value { color: #4ec9b0; font-size: 28px; font-weight: bold; font-family: 'Consolas', monospace; }
  .card.blue .value { color: #569cd6; }
  .card.orange .value { color: #ce9178; }
  .card.purple .value { color: #c586c0; }
  .card .sub { color: #666; font-size: 11px; margin-top: 4px; }

  .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
  .toolbar input, .toolbar select { background: #1e1e2e; border: 1px solid #444; color: #d4d4d4; padding: 6px 10px; border-radius: 4px; font: inherit; font-size: 13px; }
  .toolbar input:focus, .toolbar select:focus { outline: none; border-color: #4ec9b0; }
  .btn { background: #1e1e2e; border: 1px solid #4ec9b0; color: #4ec9b0; padding: 6px 14px; border-radius: 5px; cursor: pointer; font: inherit; font-size: 13px; transition: background .15s, color .15s, box-shadow .15s; }
  .btn:hover:not(:disabled) { background: #4ec9b0; color: #0f0f0f; box-shadow: 0 0 8px rgba(78,201,176,.25); }
  .btn:active:not(:disabled) { transform: translateY(1px); }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn.danger { border-color: #f44747; color: #f44747; }
  .btn.danger:hover:not(:disabled) { background: #f44747; color: #fff; box-shadow: 0 0 8px rgba(244,71,71,.25); }
  .btn.primary { border-color: #569cd6; color: #569cd6; }
  .btn.primary:hover:not(:disabled) { background: #569cd6; color: #0f0f0f; box-shadow: 0 0 8px rgba(86,156,214,.25); }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #12122a; color: #666; font-weight: 600; font-size: 11px; text-align: left; padding: 8px 10px; border-bottom: 2px solid #2a2a3a; position: sticky; top: 0; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 8px 10px; border-bottom: 1px solid #1a1a24; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px; }
  tbody tr:nth-child(even) td { background: #0d0d1a; }
  tbody tr:hover td { background: #1e1e2e !important; }
  td.mono, td code { font-family: 'Consolas', monospace; font-size: 12px; }

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

  .actions-panel { background: #1e1e2e; border: 1px solid #2a2a3a; border-radius: 8px; padding: 18px 22px; margin-top: 20px; max-width: 700px; }
  .actions-panel h3 { color: #667; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px; border-bottom: 1px solid #2a2a3a; padding-bottom: 8px; }
  .actions-row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 10px; }
  .actions-row label { color: #888; font-size: 11px; display: block; margin-bottom: 4px; }
  .actions-row input[type="text"] { background: #0f0f0f; border: 1px solid #444; color: #d4d4d4; padding: 6px 10px; border-radius: 4px; font: inherit; font-size: 13px; width: 340px; }
  .actions-row input[type="text"]:focus { outline: none; border-color: #4ec9b0; }
  .job-result { font-size: 12px; margin-top: 10px; padding: 10px 14px; border-radius: 6px; background: #12121e; border: 1px solid #2a2a3a; color: #888; display: none; }
  .job-result.visible { display: block; }
  .job-result.success { background: #0d1f16; border-color: #1a4a2a; color: #4ec9b0; }
  .job-result.error-r { background: #1f0d0d; border-color: #4a1a1a; color: #f44747; }

  .dup-group { background: #1a1a2a; border: 1px solid #2a2a3a; border-radius: 8px; margin-bottom: 12px; padding: 14px 18px; border-left: 3px solid #4ec9b0; }
  .dup-group .title { color: #4ec9b0; margin-bottom: 10px; font-size: 13px; font-weight: 500; }
  .dup-group .entry { color: #666; font-size: 12px; padding: 3px 0; font-family: 'Consolas', monospace; }
  .dup-group .entry span { color: #9cdcfe; }

  .fmt-options { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 14px 16px; margin-bottom: 16px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
  .fmt-options span { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-right: 4px; }
  .fmt-check { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; color: #d4d4d4; }
  .fmt-check input[type="checkbox"] { accent-color: #4ec9b0; width: 14px; height: 14px; cursor: pointer; }

  .empty { color: #555; padding: 40px 0; text-align: center; }
  .loading { color: #555; padding: 24px 0; }
  .error-msg { color: #f44747; padding: 12px; background: #2a1a1a; border-radius: 4px; margin-bottom: 12px; }

  /* ── Progress bars ── */
  .prog-wrap { margin-top: 10px; }
  .prog-info { display: flex; justify-content: space-between; font-size: 11px; color: #888; margin-bottom: 4px; }
  .prog-file { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #555; max-width: 60%; }
  .prog-track { background: #0f0f1a; border-radius: 4px; height: 5px; overflow: hidden; }
  .prog-bar { height: 100%; background: #4ec9b0; border-radius: 4px; transition: width 0.4s; min-width: 0; }
  .prog-bar.indeterminate { width: 35% !important; animation: prog-slide 1.6s ease-in-out infinite; }
  @keyframes prog-slide { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }

  /* ── Platform badges ── */
  .plat { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
  .plat-gba   { background: #1a3a2a; color: #4ec9b0; }
  .plat-snes  { background: #1a2a3a; color: #569cd6; }
  .plat-nes   { background: #3a1a1a; color: #f44747; }
  .plat-gb    { background: #2a2a1a; color: #dcdcaa; }
  .plat-gbc   { background: #2a2a1a; color: #d7ba7d; }
  .plat-nds   { background: #2a1a3a; color: #c586c0; }
  .plat-n64   { background: #1a2a2a; color: #4ec9b0; }
  .plat-psx   { background: #1a1a3a; color: #9cdcfe; }
  .plat-ps2   { background: #1a1a3a; color: #569cd6; }
  .plat-psp   { background: #1a1a2a; color: #79c0ff; }
  .plat-gba   { background: #1a3a2a; color: #4ec9b0; }
  .plat-genesis { background: #2a1a2a; color: #ce9178; }
  .plat-md    { background: #2a1a2a; color: #ce9178; }
  .plat-sms   { background: #1a2a1a; color: #6a9955; }
  .plat-gg    { background: #1a2a1a; color: #4ec9b0; }
  .plat-nds   { background: #2a1a3a; color: #c586c0; }
  .plat-3ds   { background: #1a2a3a; color: #9cdcfe; }
  .plat-other { background: #252525; color: #888; }

  .dev-btn { background:#1a1a2a; border:1px solid #2a2a3a; color:#666; padding:4px 14px; font:inherit; font-size:12px; cursor:pointer; transition:background 0.15s, color 0.15s; }
  .dev-btn:first-of-type { border-radius:4px 0 0 4px; }
  .dev-btn:last-of-type { border-radius:0 4px 4px 0; }
  .dev-btn.active { background:#1a3a2e; border-color:#4ec9b0; color:#4ec9b0; font-weight:600; }
  .dev-btn:not(.active):not(:disabled):hover { background:#222236; color:#aaa; }
  .dev-btn:disabled { opacity:0.35; cursor:not-allowed; }

  .rpt-tab-btn { border-radius:4px 4px 0 0; border-bottom:none; font-size:12px; padding:5px 14px; margin-bottom:-1px; }
  .rpt-tab-btn.active { background:#569cd6; border-color:#569cd6; color:#000; }
  .rpt-stat { display:inline-block; padding:3px 10px; border-radius:4px; font-size:12px; margin:2px 4px 2px 0; }
  .rpt-ok   { background:#1a3a2a; color:#4ec9b0; }
  .rpt-warn { background:#3a3a1a; color:#ce9178; }
  .rpt-bad  { background:#3a1a1a; color:#f44747; }
  .rpt-info { background:#1a2a3a; color:#569cd6; }
  tbody tr:hover { background: #252537; }
  #toast-container { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column-reverse; gap:8px; pointer-events:none; }
  .toast { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px 18px; font-size:13px; color:#d4d4d4; max-width:360px; box-shadow:0 8px 24px rgba(0,0,0,.5); animation:toast-in .25s cubic-bezier(.34,1.56,.64,1); pointer-events:auto; border-left:4px solid #444; }
  .toast.ok  { border-left-color:#4ec9b0; }
  .toast.err { border-left-color:#f44747; }
  .toast.info { border-left-color:#569cd6; }
  @keyframes toast-in { from { opacity:0; transform:translateX(20px) scale(.95); } to { opacity:1; transform:translateX(0) scale(1); } }
</style>
</head>
<body>

<header>
  <h1>&#x1F3AE; ROM Manager</h1>
  <span class="subtitle">local library</span>
</header>

<nav>
  <button class="active" id="nav-overview" onclick="showTab('overview')">Overview</button>
  <button id="nav-games" onclick="showTab('games')">Games</button>
  <button id="nav-plan" onclick="showTab('plan')">Plan</button>
  <button id="nav-duplicates" onclick="showTab('duplicates')">Duplicates</button>
  <button id="nav-assets" onclick="showTab('assets')">Assets</button>
  <button id="nav-sync" onclick="showTab('sync')">Sync</button>
  <button id="nav-cable" onclick="showTab('cable')">Cable Sync</button>
  <button id="nav-scraper" onclick="showTab('scraper')">Scraper</button>
  <button id="nav-tools" onclick="showTab('tools')">Tools</button>
  <button id="nav-settings" onclick="showTab('settings')">Settings</button>
</nav>

<div id="device-selector" style="display:flex;align-items:center;gap:0;padding:6px 20px;background:#161626;border-bottom:1px solid #2a2a2a">
  <span style="color:#555;font-size:11px;margin-right:10px">Dispositivo activo:</span>
  <button class="dev-btn active" id="dev-pc" onclick="setDevice('pc')">PC</button>
  <button class="dev-btn" id="dev-both" onclick="setDevice('both')">Sistema completo</button>
  <button class="dev-btn" id="dev-anbernic" onclick="setDevice('anbernic')" disabled>Anbernic</button>
</div>

<main>

<!-- OVERVIEW -->
<div id="tab-overview" class="tab active">

  <!-- Stats: dual column PC / Anbernic -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
    <!-- PC column -->
    <div>
      <div style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;display:flex;align-items:center;gap:8px">
        <span style="color:#4ec9b0">&#x25CF;</span> PC
        <span id="ov-pc-path-label" style="color:#555;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px"></span>
      </div>
      <div id="ov-pc-cards" class="cards" style="margin-bottom:0"><p class="loading" style="font-size:12px">Loading…</p></div>
    </div>
    <!-- Anbernic column -->
    <div>
      <div style="color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;display:flex;align-items:center;gap:8px">
        <span id="ov-ab-dot" style="color:#555">&#x25CF;</span> Anbernic
        <span id="ov-ab-path-label" style="color:#555;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px"></span>
      </div>
      <div id="ov-ab-cards" class="cards" style="margin-bottom:0">
        <p id="ov-ab-empty-msg" style="color:#555;font-size:12px;padding:10px 0">Configura la ruta de la Anbernic abajo y escanea para ver datos.</p>
      </div>
    </div>
  </div>

  <!-- Config summary -->
  <div id="ov-config-summary" style="margin-bottom:20px"></div>

  <!-- Rutas principales -->
  <div class="actions-panel" style="margin-bottom:16px">
    <h3>Rutas</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px">
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Carpeta del ordenador</label>
        <input id="ov-pc-path" type="text" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="E:/Carpetas anbernic">
      </div>
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Anbernic — SD card o red local
          <span style="color:#555;font-weight:normal"> (no MTP directo)</span>
        </label>
        <input id="ov-ab-path" type="text" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="F:/ o \\192.168.1.x\share">
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px">
      <button class="btn" onclick="saveOvPaths()">Guardar rutas</button>
      <span id="ov-paths-result" class="job-result"></span>
    </div>
    <div style="margin-top:10px;padding:8px 10px;background:#161616;border:1px solid #2a2a2a;border-radius:4px;font-size:11px;color:#555;line-height:1.7">
      <strong style="color:#888">Opciones para acceder a la Anbernic desde Windows:</strong><br>
      <span style="color:#4ec9b0">A)</span> SD card en lector USB → letra de unidad (<code style="color:#ce9178">F:\</code>) — recomendado<br>
      <span style="color:#4ec9b0">B)</span> Termux + SFTP en la Anbernic → accesible por red (<code style="color:#ce9178">\\192.168.1.x\share</code>)<br>
      <span style="color:#4ec9b0">C)</span> WinFsp + MTPDrive → monta el MTP como unidad (herramienta gratuita)<br>
      <span style="color:#555">⚠ La ruta "Este equipo\RG556\Ambernic" de Windows MTP <strong style="color:#888">no es compatible</strong> con acceso por ruta de carpeta.</span>
    </div>
  </div>

  <!-- Gestión de biblioteca -->
  <div class="actions-panel">
    <h3>Gestión de biblioteca</h3>

    <div class="actions-row" style="flex-wrap:wrap;gap:12px;align-items:center">
      <div>
        <div style="color:#888;font-size:11px;margin-bottom:6px">¿Qué escanear?</div>
        <label class="fmt-check">
          <input type="checkbox" id="scan-include-pc" checked>
          PC — <span id="scan-pc-label" style="color:#555;font-size:11px">(configura la ruta arriba)</span>
        </label>
        <label class="fmt-check" style="margin-top:4px">
          <input type="checkbox" id="scan-include-ab" disabled>
          Anbernic (SD card / red) — <span id="scan-ab-label" style="color:#555;font-size:11px">(configura la ruta arriba)</span>
        </label>
        <label class="fmt-check" style="margin-top:4px" id="scan-adb-row" title="Escanea la Anbernic por USB sin sacar la SD card — requiere ADB configurado en Settings">
          <input type="checkbox" id="scan-include-adb" onchange="_onScanAdbChange()">
          <span style="color:#4ec9b0">Anbernic por ADB</span> <span style="color:#555;font-size:11px">(cable USB, sin montar como unidad)</span>
        </label>
      </div>
      <label class="fmt-check" style="margin-left:auto" title="No calcula hashes — mucho más rápido, pero Match y Sync no funcionarán hasta hacer un scan completo">
        <input type="checkbox" id="scan-quick"> Quick (sin hash)
      </label>
      <button id="btn-scan" class="btn" onclick="doScan()">Scan</button>
    </div>
    <div id="scan-progress-wrap" class="prog-wrap" style="display:none">
      <div class="prog-info">
        <span id="scan-progress-counts" style="color:#888"></span>
        <span id="scan-progress-file" class="prog-file"></span>
      </div>
      <div class="prog-track">
        <div id="scan-progress-bar" class="prog-bar indeterminate"></div>
      </div>
    </div>

    <!-- ADB scan options (inline, hidden by default) -->
    <div id="scan-adb-options" style="display:none;margin-top:8px;padding:10px 12px;background:#161626;border:1px solid #2a3a4a;border-radius:4px;font-size:12px">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <label style="color:#888;font-size:11px">Dispositivo ADB:</label>
        <select id="scan-adb-device" style="background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:4px 8px;border-radius:4px;font:inherit;font-size:12px;min-width:200px">
          <option value="">— Detectar primero —</option>
        </select>
        <button class="btn" style="padding:4px 10px;font-size:11px" onclick="detectAdbDevicesForScan()">Detectar</button>
        <label style="color:#888;font-size:11px;margin-left:8px">Ruta Android:</label>
        <input id="scan-android-path" type="text" value="/storage/emulated/0" style="background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:4px 8px;border-radius:4px;font:inherit;font-size:12px;width:260px">
        <span id="scan-adb-status" style="color:#555;font-size:11px"></span>
      </div>
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

  <!-- Workflow guide (collapsible) -->
  <details id="ov-guide" style="margin-top:24px;max-width:760px">
    <summary style="cursor:pointer;color:#888;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;list-style:none;display:flex;align-items:center;gap:6px;user-select:none">
      <span id="ov-guide-arrow" style="color:#4ec9b0;font-size:10px">&#x25B6;</span>
      Cómo usar ROM Manager
    </summary>

    <div style="margin-top:10px">
    <!-- Primera vez -->
    <div style="background:#161626;border:1px solid #2a2a4a;border-radius:4px;padding:10px 14px;margin-bottom:14px;font-size:12px;color:#888;line-height:1.7">
      <strong style="color:#569cd6">Primera vez:</strong>
      configura las rutas en el panel de arriba y pulsa <strong style="color:#d4d4d4">Guardar rutas</strong>.
      La <em>Carpeta del ordenador</em> es donde viven tus ROMs y saves en el PC.
      La <em>Anbernic</em> solo es necesaria si quieres escanear o copiar archivos de la consola.
      Si tienes catálogos DAT (No-Intro / Redump), colócalos en <code style="color:#ce9178">catalogs/</code> para poder hacer Match.
    </div>

    <!-- Pasos -->
    <div style="display:flex;gap:0">
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#4ec9b0;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">① Scan</div>
        <div style="color:#888;font-size:12px;line-height:1.6">Activa los checkboxes de qué escanear y pulsa <strong style="color:#d4d4d4">Scan</strong>. Se calcula el hash SHA1/MD5 de cada ROM y se indexa en la base de datos local.<br><span style="color:#555;font-size:11px">Usa Quick para solo actualizar el inventario sin hashear.</span></div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#569cd6;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">② Match</div>
        <div style="color:#888;font-size:12px;line-height:1.6">Pulsa <strong style="color:#d4d4d4">Match catálogos</strong>. Cada ROM se compara contra los DAT de No-Intro y Redump para obtener su título canónico, región y revisión.<br><span style="color:#555;font-size:11px">Requiere catálogos DAT en catalogs/.</span></div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;border-right:none;padding:14px 16px">
        <div style="color:#ce9178;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">③ Plan</div>
        <div style="color:#888;font-size:12px;line-height:1.6">Ve a <strong style="color:#d4d4d4">Plan</strong> para previsualizar los renombrados. Elige qué incluir en el nombre (región, revisión…) y revisa antes de tocar ningún archivo.<br><span style="color:#555;font-size:11px">Los saves se renombran junto al ROM automáticamente.</span></div>
      </div>
      <div style="flex:1;background:#1e1e2e;border:1px solid #333;padding:14px 16px">
        <div style="color:#4ec9b0;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">④ Apply</div>
        <div style="color:#888;font-size:12px;line-height:1.6">Pulsa <strong style="color:#d4d4d4">Aplicar renombrado</strong> cuando estés conforme. El rename es atómico: si algo falla a mitad, todo vuelve al estado anterior.<br><span style="color:#555;font-size:11px">Después, usa Cable Sync para volcar los cambios a la Anbernic.</span></div>
      </div>
    </div>
    </div>
  </details>
</div>

<!-- GAMES -->
<div id="tab-games" class="tab">
  <div id="games-root-banner" style="display:none;margin-bottom:8px;padding:6px 10px;background:#1e1e2e;border:1px solid #333;border-radius:4px;align-items:center;gap:10px"></div>
  <div class="toolbar">
    <input id="games-search" type="text" placeholder="Search title or filename…" oninput="onGamesSearchChange()">
    <select id="games-platform" onchange="onGamesFilterChange()"><option value="">All platforms</option></select>
    <select id="games-matched" onchange="onGamesFilterChange()">
      <option value="">All</option>
      <option value="matched">Matched only</option>
      <option value="unmatched">Unmatched only</option>
    </select>
    <select id="games-filetype" onchange="onGamesFilterChange()" style="background:#1e1e2e;border:1px solid #444;color:#d4d4d4;padding:5px 9px;border-radius:4px;font:inherit;font-size:13px">
      <option value="rom">Solo ROMs</option>
      <option value="">ROMs + saves</option>
      <option value="all">Todo</option>
    </select>
    <span id="games-count" style="color:#666;margin-left:8px;"></span>
    <a href="/api/report.csv" class="btn" style="margin-left:auto">&#x2193; CSV</a>
    <a href="/api/report.json" class="btn">&#x2193; JSON</a>
  </div>
  <div style="overflow-x:auto">
    <table id="games-table">
      <thead><tr>
        <th>Platform</th><th>Canonical title</th><th>Original filename</th>
        <th id="gcol-region">Region</th><th id="gcol-match">Match</th><th id="gcol-size">Size</th><th id="gcol-sha1">SHA1
          <button title="Configurar columnas" onclick="toggleColPicker(event)" style="background:none;border:none;color:#888;cursor:pointer;font-size:14px;padding:0 2px;vertical-align:middle">&#x2699;</button>
          <div id="col-picker" style="display:none;position:absolute;background:#252535;border:1px solid #444;border-radius:6px;padding:10px 14px;z-index:100;min-width:160px;font-size:13px;font-weight:normal">
            <div style="color:#888;font-size:11px;margin-bottom:8px">Mostrar columnas</div>
            <label style="display:block;margin-bottom:6px;cursor:pointer"><input type="checkbox" id="gcol-check-region" onchange="applyColVisibility()"> Region</label>
            <label style="display:block;margin-bottom:6px;cursor:pointer"><input type="checkbox" id="gcol-check-match" onchange="applyColVisibility()"> Match</label>
            <label style="display:block;margin-bottom:6px;cursor:pointer"><input type="checkbox" id="gcol-check-size" onchange="applyColVisibility()"> Size</label>
            <label style="display:block;cursor:pointer"><input type="checkbox" id="gcol-check-sha1" onchange="applyColVisibility()"> SHA1</label>
          </div>
        </th>
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
  <div id="plan-context-bar" style="display:none;margin-bottom:10px;padding:7px 12px;background:#1e1e2e;border:1px solid #333;border-radius:4px;font-size:12px;color:#888"></div>
  <div id="plan-content"><p class="loading">Loading…</p></div>
</div>

<!-- DUPLICATES -->
<div id="tab-duplicates" class="tab">
  <div class="toolbar" style="justify-content:space-between;align-items:center">
    <span style="color:#888;font-size:12px">Se conserva la primera copia de cada grupo; se eliminan las demás.</span>
    <button id="btn-delete-all-dups" class="btn danger" onclick="deleteAllDuplicates()">Eliminar todos los duplicados</button>
  </div>
  <div id="dup-context-bar" style="display:none;margin-bottom:10px;padding:7px 12px;background:#1e1e2e;border:1px solid #333;border-radius:4px;font-size:12px;color:#888"></div>
  <div id="dup-content"><p class="loading">Loading…</p></div>

  <!-- ── RA-based duplicates (same title, different version, one lacks RA support) ── -->
  <div style="margin-top:28px;border-top:1px solid #2a2a3e;padding-top:20px">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
      <h3 style="margin:0;font-size:13px;color:#c9bcf5">Duplicados por versión — sin logros RA</h3>
      <button class="btn" onclick="loadRaDuplicates()" id="btn-ra-dups" style="font-size:12px;padding:3px 10px">Comprobar</button>
    </div>
    <p style="color:#555;font-size:11px;margin-bottom:12px">Detecta juegos con ≥2 versiones (mismo título normalizado, distinto MD5) donde una versión tiene logros en RetroAchievements y otra no. La versión sin logros es candidata a eliminar.<br>Requiere que hayas ejecutado la comprobación RA en <strong>Tools</strong> al menos una vez.</p>
    <div id="ra-dup-content"></div>
  </div>
</div>

<!-- SYNC -->
<div id="tab-sync" class="tab">
  <div id="sync-context-bar" style="display:none;margin-bottom:12px;padding:7px 12px;background:#1e1e2e;border:1px solid #333;border-radius:4px;font-size:12px;color:#888"></div>
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
    <h3 style="color:#4ec9b0;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Cómo hacer accesible la Anbernic desde el PC</h3>

    <!-- MTP warning -->
    <div style="padding:9px 12px;background:#2a1a1a;border:1px solid #5a2a2a;border-radius:4px;margin-bottom:14px;font-size:12px;line-height:1.6">
      <strong style="color:#f44747">⚠ La ruta "Este equipo\RG556\Ambernic" NO es compatible.</strong>
      <span style="color:#888;margin-left:6px">Windows MTP expone el dispositivo como objeto shell, no como ruta del sistema de archivos. Python no puede acceder a ella directamente.</span>
    </div>

    <!-- Three options -->
    <div style="display:flex;flex-direction:column;gap:8px">

      <!-- Opción A -->
      <details open style="background:#161626;border:1px solid #2a4a2a;border-radius:4px;padding:0">
        <summary style="cursor:pointer;padding:10px 14px;font-size:13px;color:#4ec9b0;list-style:none;display:flex;align-items:center;gap:8px;user-select:none">
          <span style="font-weight:bold">A)</span> SD card en lector USB
          <span style="background:#1a3a2a;color:#4ec9b0;font-size:10px;padding:1px 6px;border-radius:3px;margin-left:4px">RECOMENDADO</span>
          <span style="color:#555;font-size:11px;margin-left:auto">Sin configuración extra</span>
        </summary>
        <div style="padding:0 14px 12px;font-size:12px;color:#888;line-height:1.8">
          <span style="color:#d4d4d4">①</span> Apaga la Anbernic o ve a Ajustes → Apagar.<br>
          <span style="color:#d4d4d4">②</span> Extrae la tarjeta SD de la Anbernic.<br>
          <span style="color:#d4d4d4">③</span> Insértala en un lector de tarjetas USB conectado al PC.<br>
          <span style="color:#d4d4d4">④</span> Windows la monta automáticamente como letra de unidad (ej. <code style="color:#ce9178">F:\</code> o <code style="color:#ce9178">G:\</code>).<br>
          <span style="color:#d4d4d4">⑤</span> Usa esa letra como ruta de la Anbernic en el formulario de abajo.
        </div>
      </details>

      <!-- Opción B -->
      <details style="background:#161626;border:1px solid #333;border-radius:4px;padding:0">
        <summary style="cursor:pointer;padding:10px 14px;font-size:13px;color:#d4d4d4;list-style:none;display:flex;align-items:center;gap:8px;user-select:none">
          <span style="font-weight:bold;color:#569cd6">B)</span> Termux + SFTP <span style="color:#555;font-size:11px;margin-left:6px">(vía red Wi-Fi local, sin sacar la SD)</span>
        </summary>
        <div style="padding:0 14px 12px;font-size:12px;color:#888;line-height:1.8">
          Requiere <strong style="color:#d4d4d4">Termux instalado</strong> en la Anbernic. Consulta la guía completa en <code style="color:#ce9178">Tareas/Guia-Termux-Anbernic.md</code>.<br><br>
          <span style="color:#d4d4d4">①</span> Instala openssh en Termux: <code style="color:#ce9178">pkg install openssh</code><br>
          <span style="color:#d4d4d4">②</span> Arranca el servidor SSH: <code style="color:#ce9178">sshd</code><br>
          <span style="color:#d4d4d4">③</span> Mira la IP de la Anbernic: Ajustes → Wi-Fi → (nombre de red) → IP<br>
          <span style="color:#d4d4d4">④</span> En el PC, monta la carpeta con <strong style="color:#d4d4d4">WinFsp + SSHFS-Win</strong> o accede vía <code style="color:#ce9178">rclone</code>:<br>
          <code style="color:#ce9178;margin-left:16px;display:block">rclone copy anbernic-sftp:/storage/emulated/0/ F:/Anbernic/ --progress</code>
          <span style="color:#d4d4d4">⑤</span> O usa la ruta de red directamente si está montada: <code style="color:#ce9178">\\192.168.1.X\storage</code>
        </div>
      </details>

      <!-- Opción C -->
      <details style="background:#161626;border:1px solid #333;border-radius:4px;padding:0">
        <summary style="cursor:pointer;padding:10px 14px;font-size:13px;color:#d4d4d4;list-style:none;display:flex;align-items:center;gap:8px;user-select:none">
          <span style="font-weight:bold;color:#569cd6">C)</span> WinFsp + MTPDrive <span style="color:#555;font-size:11px;margin-left:6px">(mantiene el cable USB, herramienta de terceros)</span>
        </summary>
        <div style="padding:0 14px 12px;font-size:12px;color:#888;line-height:1.8">
          <span style="color:#d4d4d4">①</span> Descarga e instala <strong style="color:#d4d4d4">WinFsp</strong> (winfsp.dev) y <strong style="color:#d4d4d4">MTPDrive</strong> (mtpdrive.com).<br>
          <span style="color:#d4d4d4">②</span> Conecta la Anbernic en modo MTP (Transferencia de archivos).<br>
          <span style="color:#d4d4d4">③</span> MTPDrive monta el dispositivo como letra de unidad (ej. <code style="color:#ce9178">M:\</code>).<br>
          <span style="color:#d4d4d4">④</span> Usa esa letra en el formulario de abajo.<br>
          <span style="color:#ce9178;font-size:11px">⚠ La velocidad puede ser inferior a la SD card con lector USB.</span>
        </div>
      </details>

      <!-- Opción D -->
      <details style="background:#161626;border:1px solid #2a3a4a;border-radius:4px;padding:0">
        <summary style="cursor:pointer;padding:10px 14px;font-size:13px;color:#d4d4d4;list-style:none;display:flex;align-items:center;gap:8px;user-select:none">
          <span style="font-weight:bold;color:#4ec9b0">D)</span> ADB (Android Debug Bridge)
          <span style="background:#1a2a3a;color:#4ec9b0;font-size:10px;padding:1px 6px;border-radius:3px;margin-left:4px">SIN SACAR LA SD</span>
          <span style="color:#555;font-size:11px;margin-left:auto">Herramienta gratuita de Google</span>
        </summary>
        <div style="padding:0 14px 12px;font-size:12px;color:#888;line-height:1.8">
          ADB se comunica con Android directamente por USB. No necesita montar como unidad, no necesita Wi-Fi.<br><br>
          <strong style="color:#d4d4d4">① Activar depuración USB en la Anbernic:</strong><br>
          <span style="margin-left:16px;display:block">Ajustes → Información del teléfono → pulsa <em>Número de compilación</em> 7 veces</span>
          <span style="margin-left:16px;display:block">Ajustes → Opciones de desarrollador → <strong style="color:#d4d4d4">Depuración USB ✓</strong></span><br>
          <strong style="color:#d4d4d4">② Descargar Android Platform Tools:</strong><br>
          <span style="margin-left:16px;display:block">developer.android.com/tools/releases/platform-tools → descomprimir → copia <code style="color:#ce9178">adb.exe</code> en <code style="color:#ce9178">tools/</code></span><br>
          <strong style="color:#d4d4d4">③ Configurar ruta en Settings:</strong>
          <code style="color:#ce9178;margin-left:6px">tools/adb.exe</code><br><br>
          <strong style="color:#d4d4d4">④ Conecta el cable y elige modo USB:</strong>
          <span style="color:#d4d4d4;margin-left:6px">cualquier modo funciona; recomendado "Transferencia de archivos"</span><br>
          <span style="margin-left:16px;display:block;color:#569cd6">Acepta el diálogo "¿Permitir depuración USB?" en la pantalla de la Anbernic.</span><br>
          <strong style="color:#d4d4d4">⑤ En el formulario de abajo:</strong>
          activa el toggle <strong style="color:#d4d4d4">Modo ADB</strong>, haz clic en <strong style="color:#d4d4d4">Detectar dispositivos</strong>.
        </div>
      </details>

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
          <input type="radio" name="cable-direction" value="pc_to_anbernic" checked style="margin-top:2px;accent-color:#4ec9b0" onchange="_onCableDirectionChange()">
          <span>
            <strong style="color:#d4d4d4">PC → Anbernic</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Copia del PC a la consola. Sobrescribe los archivos de la Anbernic.</span><br>
            <span style="color:#569cd6;font-size:11px">✓ Recomendado después de renombrar archivos en el PC</span>
          </span>
        </label>
        <label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px">
          <input type="radio" name="cable-direction" value="anbernic_to_pc" style="margin-top:2px;accent-color:#4ec9b0" onchange="_onCableDirectionChange()">
          <span>
            <strong style="color:#d4d4d4">Anbernic → PC</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Copia todo de la consola al PC. Archivos solo en Anbernic pasan al PC.</span><br>
            <span style="color:#569cd6;font-size:11px">✓ Útil para importar juegos nuevos de la SD card al PC. Luego haz Scan para indexarlos.</span>
          </span>
        </label>
        <label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px">
          <input type="radio" name="cable-direction" value="newest" style="margin-top:2px;accent-color:#4ec9b0" onchange="_onCableDirectionChange()">
          <span>
            <strong style="color:#4ec9b0">&#x21C4; Igualar ambos dispositivos</strong>
            <span style="color:#555;font-size:12px;margin-left:6px">Compara mtime y copia en la dirección correcta. Archivos exclusivos de un lado se copian al otro.</span><br>
            <span style="color:#4ec9b0;font-size:11px">✓ Al terminar, PC y Anbernic tienen exactamente los mismos archivos</span><br>
            <span style="color:#ce9178;font-size:11px">⚠ Tras renombrar en el PC, las fechas cambian — usa "PC → Anbernic" en ese caso para no perder cambios</span>
          </span>
        </label>
      </div>
    </div>

    <!-- Modo Anbernic toggle -->
    <div style="margin-bottom:14px;display:flex;align-items:center;gap:12px">
      <span style="color:#888;font-size:12px">Modo Anbernic:</span>
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
        <input type="radio" name="cable-ab-mode" value="fs" checked style="accent-color:#4ec9b0" onchange="_onCableModeChange()">
        <span style="color:#d4d4d4">SD card / Red</span>
        <span style="color:#555;font-size:11px">(letra de unidad o ruta de red)</span>
      </label>
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
        <input type="radio" name="cable-ab-mode" value="adb" style="accent-color:#4ec9b0" onchange="_onCableModeChange()">
        <span style="color:#4ec9b0">ADB</span>
        <span style="color:#555;font-size:11px">(cable USB, sin montar como unidad)</span>
      </label>
    </div>

    <!-- Rutas: modo FS -->
    <div id="cable-fs-section" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Ruta del PC (library_root)</label>
        <div style="display:flex;gap:6px">
          <input id="cable-pc-path" type="text" style="flex:1;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="E:/Carpetas anbernic">
          <button class="btn" style="padding:6px 10px;font-size:12px;flex-shrink:0" onclick="testCablePath('pc')" title="Verificar que la ruta existe y es accesible">Probar</button>
        </div>
        <div id="cable-pc-path-status" style="font-size:11px;margin-top:4px;min-height:16px"></div>
      </div>
      <div>
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">
          Ruta de la Anbernic (SD card, red…)
          <button class="btn" style="padding:2px 8px;font-size:10px;margin-left:6px" onclick="detectDrives()" title="Listar letras de unidad disponibles">Detectar drives</button>
        </label>
        <div style="display:flex;gap:6px">
          <input id="cable-ab-path" type="text" style="flex:1;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="F:\ o \\192.168.1.x\share">
          <button class="btn" style="padding:6px 10px;font-size:12px;flex-shrink:0" onclick="testCablePath('ab')" title="Verificar que la ruta existe y es accesible">Probar</button>
        </div>
        <div id="cable-ab-path-status" style="font-size:11px;margin-top:4px;min-height:16px"></div>
        <div id="cable-drives-list" style="display:none;margin-top:6px;background:#0f0f0f;border:1px solid #333;border-radius:4px;padding:6px 8px;font-size:12px"></div>
      </div>
    </div>

    <!-- Rutas: modo ADB -->
    <div id="cable-adb-section" style="display:none;margin-bottom:16px">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px">
        <div>
          <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Ruta del PC (library_root)</label>
          <div style="display:flex;gap:6px">
            <input id="cable-adb-pc-path" type="text" style="flex:1;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px" placeholder="E:/Carpetas anbernic">
          </div>
        </div>
        <div>
          <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Ruta en Android</label>
          <input id="cable-android-path" type="text" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:6px 10px;border-radius:4px;font:inherit;font-size:13px;box-sizing:border-box" value="/storage/emulated/0/RetroArch">
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <label style="color:#888;font-size:11px">Dispositivo ADB:</label>
        <select id="cable-adb-device" style="background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:5px 8px;border-radius:4px;font:inherit;font-size:13px;min-width:220px">
          <option value="">— Detectar primero —</option>
        </select>
        <button class="btn" style="padding:5px 12px;font-size:12px" onclick="detectAdbDevices()">Detectar dispositivos</button>
        <span id="cable-adb-status" style="font-size:11px;color:#888;min-height:16px"></span>
      </div>
      <div id="cable-adb-path-status" style="font-size:11px;margin-top:6px;min-height:16px"></div>
    </div>

    <!-- Opciones adicionales (condicionales según dirección) -->
    <div id="cable-sha1-row" style="display:none;margin-bottom:12px;padding:10px 12px;background:#161626;border:1px solid #2a2a4a;border-radius:4px">
      <label class="fmt-check" title="Requiere que la SD card haya sido escaneada previamente desde Overview">
        <input type="checkbox" id="cable-skip-sha1">
        <span>Omitir ROMs duplicados <span style="color:#555;font-size:11px">(comprueba SHA1 en BD — requiere scan previo de la Anbernic)</span></span>
      </label>
      <div style="color:#555;font-size:11px;margin-top:6px;margin-left:20px">
        Antes de copiar cada ROM, se calcula su SHA1 y se compara con la biblioteca del PC.
        Si ya existe (aunque tenga otro nombre), se omite. Los saves no se filtran.
      </div>
    </div>

    <!-- Dry run + botón -->
    <div class="actions-row" style="flex-wrap:wrap;gap:16px">
      <label class="fmt-check" title="Muestra qué se copiaría sin mover ningún archivo. Desmarca para copiar de verdad.">
        <input type="checkbox" id="cable-dry-run" onchange="_onCableDryRunChange()"> <span id="cable-dry-run-label">Dry run <span style="color:#555;font-size:11px">(solo previsualizar)</span></span>
      </label>
      <label class="fmt-check" title="Salta archivos que ya existen en destino con el mismo tamaño — evita re-copiar lo que ya está sincronizado">
        <input type="checkbox" id="cable-skip-existing" checked> Omitir si ya existe
        <span style="color:#555;font-size:11px;margin-left:4px">(mismo tamaño)</span>
      </label>
      <button id="btn-cable-sync" class="btn primary" onclick="doCableSync()" style="margin-left:auto">Iniciar sincronización</button>
    </div>
    <div id="cable-dry-run-warning" style="display:none;margin-top:6px;padding:6px 12px;background:#1a1f1a;border:1px solid #2a4a2a;border-left:3px solid #4ec9b0;border-radius:4px;font-size:12px;color:#4ec9b0">
      Dry run desactivado — los archivos se <strong>copiarán realmente</strong>. Asegúrate de que las rutas son correctas antes de continuar.
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
  <div id="assets-context-bar" style="display:none;margin-bottom:10px;padding:7px 12px;background:#1e1e2e;border:1px solid #333;border-radius:4px;font-size:12px;color:#888"></div>
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
    <div class="actions-row" style="flex-wrap:wrap;gap:8px;align-items:flex-end">
      <div style="flex:1;min-width:200px">
        <label>Carpeta de ROMs</label>
        <input id="m3u-path" type="text" placeholder="C:/ROMs/psx" style="width:100%">
      </div>
      <button class="btn" onclick="autodetectM3UFolders()" id="btn-m3u-autodetect" title="Detecta automáticamente las carpetas de plataformas de disco">Autodetectar carpetas</button>
    </div>
    <div id="m3u-folder-select-wrap" style="display:none;margin-top:8px">
      <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">Carpetas detectadas — haz clic para seleccionar:</label>
      <div id="m3u-folder-list" style="display:flex;flex-wrap:wrap;gap:6px"></div>
    </div>
    <div class="actions-row" style="gap:20px;align-items:center;margin-top:10px">
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

  <!-- ── Informe de biblioteca ── -->
  <div class="actions-panel" style="margin-top:20px" id="report-panel">
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
      <h3 style="margin:0">Informe de biblioteca</h3>
      <div style="flex:1;min-width:200px">
        <input id="report-path" type="text" placeholder="Ruta (vacío = library_root)" style="width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:5px 9px;border-radius:4px;font:inherit;font-size:13px">
      </div>
      <button class="btn primary" onclick="generateReport()">Generar informe</button>
      <button class="btn" id="btn-export-report" style="display:none" onclick="exportReportHtml()">&#x2193; Exportar HTML</button>
      <button class="btn" id="btn-open-html-report" onclick="openHtmlReport()" title="Abre el informe en una nueva pestaña con navegación por pestañas">&#x2197; Ver informe HTML</button>
    </div>
    <p style="color:#555;font-size:11px;margin-top:8px">Recopila el estado de ZIPs, playlists, sets multi-disco, saves huérfanos, RetroAchievements y conversiones CHD.</p>

    <div id="report-loading" style="display:none;color:#555;font-size:12px;padding:12px 0">Generando informe…</div>

    <div id="report-content" style="display:none;margin-top:16px">
      <!-- Sub-tab nav -->
      <div style="display:flex;gap:2px;border-bottom:1px solid #333;margin-bottom:16px;flex-wrap:wrap">
        <button class="btn rpt-tab-btn active" id="rpt-tab-btn-zips"       onclick="showReportTab('zips')">ZIPs</button>
        <button class="btn rpt-tab-btn"        id="rpt-tab-btn-playlists"  onclick="showReportTab('playlists')">Playlists</button>
        <button class="btn rpt-tab-btn"        id="rpt-tab-btn-multidisc"  onclick="showReportTab('multidisc')">Multi-disco</button>
        <button class="btn rpt-tab-btn"        id="rpt-tab-btn-orphans"    onclick="showReportTab('orphans')">Saves huérfanos</button>
        <button class="btn rpt-tab-btn"        id="rpt-tab-btn-ra"         onclick="showReportTab('ra')">RetroAchievements</button>
        <button class="btn rpt-tab-btn"        id="rpt-tab-btn-chd"        onclick="showReportTab('chd')">CHD</button>
      </div>

      <div id="rpt-tab-zips"      class="rpt-tab"></div>
      <div id="rpt-tab-playlists" class="rpt-tab" style="display:none"></div>
      <div id="rpt-tab-multidisc" class="rpt-tab" style="display:none"></div>
      <div id="rpt-tab-orphans"   class="rpt-tab" style="display:none"></div>
      <div id="rpt-tab-ra"        class="rpt-tab" style="display:none"></div>
      <div id="rpt-tab-chd"       class="rpt-tab" style="display:none"></div>
    </div>
  </div>

  <!-- ── Análisis de carpeta ── -->
  <div class="actions-panel" style="margin-top:20px">
    <h3>Análisis de carpeta</h3>
    <p style="color:#888;font-size:12px;margin-bottom:12px">Inspecciona una carpeta y muestra extensiones encontradas, sets PSX con .bin faltante, y formatos que necesitan conversión.</p>
    <div class="actions-row">
      <div><label>Carpeta a analizar</label><input id="folder-analysis-path" type="text" placeholder="H:\\psx  o  E:\\Carpetas anbernic\\psx"></div>
    </div>
    <div class="actions-row">
      <button class="btn primary" onclick="doFolderAnalysis()">Analizar carpeta</button>
    </div>
    <div id="folder-analysis-result" style="margin-top:12px"></div>
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
        <label style="color:#888;font-size:11px;display:block;margin-bottom:4px">adb — ruta al binario (para Cable Sync por ADB) <span style="color:#555">— descargar Android Platform Tools de developer.android.com</span></label>
        <div style="display:flex;gap:8px">
          <input id="cfg-adb" type="text" style="flex:1" placeholder="adb  o  tools/adb.exe">
          <button class="btn" onclick="testAdbBinary()" style="flex-shrink:0">Probar</button>
        </div>
        <div id="adb-test-result" style="font-size:11px;margin-top:4px;color:#555"></div>
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
let gamesState = { offset: 0, limit: 100, total: 0, platform: '', status: '', root: null };
let platformsLoaded = false;

// ── Column visibility ─────────────────────────────────────────────────────────
const _COL_DEFAULTS = { region: true, match: true, size: false, sha1: false };
function _loadColPrefs() {
  try { return JSON.parse(localStorage.getItem('games_cols') || 'null') || _COL_DEFAULTS; }
  catch { return _COL_DEFAULTS; }
}
function _saveColPrefs(prefs) {
  localStorage.setItem('games_cols', JSON.stringify(prefs));
}
function applyColVisibility() {
  const prefs = {
    region: document.getElementById('gcol-check-region')?.checked ?? _COL_DEFAULTS.region,
    match:  document.getElementById('gcol-check-match')?.checked  ?? _COL_DEFAULTS.match,
    size:   document.getElementById('gcol-check-size')?.checked   ?? _COL_DEFAULTS.size,
    sha1:   document.getElementById('gcol-check-sha1')?.checked   ?? _COL_DEFAULTS.sha1,
  };
  _saveColPrefs(prefs);
  const show = (id, vis) => { const el = document.getElementById(id); if (el) el.style.display = vis ? '' : 'none'; };
  show('gcol-region', prefs.region);
  show('gcol-match',  prefs.match);
  show('gcol-size',   prefs.size);
  show('gcol-sha1',   prefs.sha1);
  // Update row cells (col index: 0=platform,1=title,2=filename,3=region,4=match,5=size,6=sha1)
  const COL = { region: 3, match: 4, size: 5, sha1: 6 };
  document.querySelectorAll('#games-tbody tr').forEach(tr => {
    Object.entries(COL).forEach(([key, idx]) => {
      const td = tr.cells[idx];
      if (td) td.style.display = prefs[key] ? '' : 'none';
    });
  });
}
function _initColPicker() {
  const prefs = _loadColPrefs();
  ['region','match','size','sha1'].forEach(key => {
    const cb = document.getElementById('gcol-check-' + key);
    if (cb) cb.checked = prefs[key];
  });
  applyColVisibility();
}
function toggleColPicker(event) {
  event.stopPropagation();
  const picker = document.getElementById('col-picker');
  if (!picker) return;
  picker.style.display = picker.style.display === 'none' ? '' : 'none';
  if (picker.style.display !== 'none') {
    // Close when clicking outside
    const close = (e) => { if (!picker.contains(e.target)) { picker.style.display = 'none'; document.removeEventListener('click', close); }};
    setTimeout(() => document.addEventListener('click', close), 0);
  }
}
let _pollingTimer = null;
// Track result timestamps already shown, so toasts/banners fire only once per result
const _shownResultTs = {};

// ── Device selector ───────────────────────────────────────────────────────────
let _activeDevice = 'pc';  // 'pc' | 'both' | 'anbernic'

function setDevice(d) {
  _activeDevice = d;
  ['pc','both','anbernic'].forEach(id => {
    const b = document.getElementById('dev-' + id);
    if (b) b.classList.toggle('active', id === d);
  });
  // Reload current active tab
  const activeTab = document.querySelector('nav button.active')?.id?.replace('nav-','');
  if (activeTab) {
    if (activeTab === 'games')      loadGames(0);
    if (activeTab === 'plan')       loadPlan();
    if (activeTab === 'duplicates') loadDuplicates();
    if (activeTab === 'assets')     loadAssets();
  }
}

function _deviceRoot() {
  if (_activeDevice === 'pc')       return document.getElementById('ov-pc-path')?.value.trim() || null;
  if (_activeDevice === 'anbernic') return document.getElementById('ov-ab-path')?.value.trim() || null;
  return null; // 'both' = sin filtro
}

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  const navBtn = document.getElementById('nav-' + name);
  if (navBtn) navBtn.classList.add('active');
  else if (event?.currentTarget) event.currentTarget.classList.add('active');
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

// ── Guide toggle (update arrow icon) ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const guide = document.getElementById('ov-guide');
  if (guide) {
    const updateArrow = () => {
      const arrow = document.getElementById('ov-guide-arrow');
      if (arrow) arrow.innerHTML = guide.open ? '&#x25BC;' : '&#x25B6;';
      localStorage.setItem('guide_closed', guide.open ? '0' : '1');
    };
    guide.addEventListener('toggle', updateArrow);
    // Restore saved state
    if (localStorage.getItem('guide_closed') === '1') guide.removeAttribute('open');
    updateArrow();
  }
});

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

const _PLAT_CLASS = {
  gba:'gba', 'game boy advance':'gba',
  snes:'snes', 'super nintendo':'snes',
  nes:'nes', 'nintendo':'nes',
  gb:'gb', 'game boy':'gb',
  gbc:'gbc', 'game boy color':'gbc',
  nds:'nds', 'nintendo ds':'nds',
  '3ds':'3ds', 'nintendo 3ds':'3ds',
  n64:'snes', 'nintendo 64':'snes',
  psx:'psx', 'playstation':'psx',
  ps2:'ps2', 'playstation 2':'ps2',
  psp:'psp', 'playstation portable':'psp',
  genesis:'genesis', 'mega drive':'md', md:'md',
  sms:'sms', 'master system':'sms',
  gg:'gg', 'game gear':'gg',
};
function _platBadge(plat) {
  if (!plat) return '<span class="plat plat-other">?</span>';
  const key = plat.toLowerCase();
  const cls = _PLAT_CLASS[key] || 'other';
  return `<span class="plat plat-${cls}">${_h(plat)}</span>`;
}

function _h(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function stopJob(name) {
  try {
    await apiPost('/api/stop-job', { job: name });
  } catch(_) {}
}

function openHtmlReport() {
  const path = document.getElementById('report-path')?.value.trim() || '';
  const url = '/api/report/html' + (path ? '?path=' + encodeURIComponent(path) : '');
  window.open(url, '_blank');
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
  try {
    const _t = Date.now();
    const cfg = await apiFetch('/api/config?t=' + _t);

    // Populate path inputs (only if empty)
    const pcInput = document.getElementById('ov-pc-path');
    const abInput = document.getElementById('ov-ab-path');
    const pcPath  = pcInput?.value.trim() || cfg.library_root || '';
    const abStored = localStorage.getItem('anbernic_path') || '';
    // If ADB scan was used, the stored android path acts as the Anbernic root
    const abAdbPath = localStorage.getItem('anbernic_adb_path') || '';
    const abPath   = abInput?.value.trim() || abStored || abAdbPath;
    if (pcInput && !pcInput.value) pcInput.value = pcPath;
    if (abInput && !abInput.value) abInput.value = abPath;

    // Update path labels in stats columns
    const pcLbl = document.getElementById('ov-pc-path-label');
    const abLbl = document.getElementById('ov-ab-path-label');
    if (pcLbl) pcLbl.textContent = pcPath ? '— ' + pcPath : '';
    if (abLbl) abLbl.textContent = abPath ? '— ' + abPath : '';

    // Update scan checkboxes
    const pcLabel = document.getElementById('scan-pc-label');
    const abLabel = document.getElementById('scan-ab-label');
    const abCb    = document.getElementById('scan-include-ab');
    if (pcLabel) pcLabel.textContent = pcPath || '(configura la ruta arriba)';
    if (abLabel) abLabel.textContent = abPath || '(configura la ruta arriba)';
    if (abCb) { abCb.disabled = !abPath; if (abPath && !abCb.checked) abCb.checked = true; }

    // Enable/disable Anbernic device button
    const devAb = document.getElementById('dev-anbernic');
    if (devAb) devAb.disabled = !abPath;

    // Config summary
    const cfgEl = document.getElementById('ov-config-summary');
    if (cfgEl) {
      cfgEl.innerHTML = `<div class="config-grid" style="max-width:560px">
        <span class="cfg-key">library_root</span>
        <span class="cfg-val ${cfg.library_root ? '' : 'missing'}">${cfg.library_root || '(not set — configura en Settings)'}</span>
        <span class="cfg-key">rclone remote</span>
        <span class="cfg-val ${cfg.rclone_remote ? '' : 'missing'}">${cfg.rclone_remote || '(not set)'}</span>
        <span class="cfg-key">ScreenScraper</span>
        <span class="cfg-val ${cfg.screenscraper_user ? '' : 'missing'}">${cfg.screenscraper_user || '(not set)'}</span>
        <span class="cfg-key">web</span>
        <span class="cfg-val">${cfg.web_host}:${cfg.web_port}</span>
      </div>`;
    }

    // Fetch PC stats (filter by library_root)
    const pcCardsEl = document.getElementById('ov-pc-cards');
    try {
      const pcParam = (pcPath ? '?root=' + encodeURIComponent(pcPath) + '&' : '?') + 't=' + _t;
      const d = await apiFetch('/api/status' + pcParam);
      const matchPct = d.total_games > 0 ? Math.round(d.matched_games / d.total_games * 100) : 0;
      if (pcCardsEl) pcCardsEl.innerHTML =
        card('Games',      d.total_games,     null, () => goToGames(pcPath, ''), '')          +
        card('Matched',    d.matched_games,    matchPct + '% matched', () => goToGames(pcPath, 'matched'), 'blue')    +
        card('Unmatched',  d.unmatched_games,  null, () => goToGames(pcPath, 'unmatched'), 'orange')  +
        card('Saves',      d.total_saves,      null, null, 'purple')      +
        card('Assets',     d.total_assets)     +
        card('Duplicados', d.duplicate_groups, fmtSize(d.wasted_bytes) + ' wasted', null, d.duplicate_groups > 0 ? 'red' : '') +
        card('Último scan', d.last_scan_at ? d.last_scan_at.replace('T',' ').slice(0,16) : 'nunca');
      // Auto-collapse guide when library already has data
      const guide = document.getElementById('ov-guide');
      if (guide && d.total_games > 0 && localStorage.getItem('guide_closed') !== '0') {
        guide.removeAttribute('open');
      } else if (guide && d.total_games === 0) {
        guide.setAttribute('open', '');
      }
    } catch(e) {
      if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
    }

    // Fetch Anbernic stats (if path configured)
    const abCardsEl  = document.getElementById('ov-ab-cards');
    const abDot      = document.getElementById('ov-ab-dot');
    const abEmptyMsg = document.getElementById('ov-ab-empty-msg');
    if (abPath && abCardsEl) {
      try {
        const ab = await apiFetch('/api/status?root=' + encodeURIComponent(abPath) + '&t=' + _t);
        const abMatchPct = ab.total_games > 0 ? Math.round(ab.matched_games / ab.total_games * 100) : 0;
        if (abDot) abDot.style.color = ab.total_games > 0 ? '#4ec9b0' : '#555';
        if (ab.total_games === 0) {
          if (abCardsEl) abCardsEl.innerHTML = `<p id="ov-ab-empty-msg" style="color:#555;font-size:12px;padding:10px 0">Ruta configurada pero sin datos escaneados. Activa el checkbox de Anbernic en <em>Gestión de biblioteca</em> y lanza un Scan.</p>`;
        } else {
          if (abCardsEl) abCardsEl.innerHTML =
            card('Games',      ab.total_games,    null, () => goToGames(abPath, ''), '')          +
            card('Matched',    ab.matched_games,   abMatchPct + '% matched', () => goToGames(abPath, 'matched'), 'blue')  +
            card('Unmatched',  ab.unmatched_games, null, () => goToGames(abPath, 'unmatched'), 'orange')  +
            card('Saves',      ab.total_saves,     null, null, 'purple')     +
            card('Assets',     ab.total_assets);
        }
      } catch(e) {
        if (abCardsEl) abCardsEl.innerHTML = `<p class="error-msg" style="font-size:12px">${e.message}</p>`;
      }
    }

  } catch(e) {
    const pcCardsEl = document.getElementById('ov-pc-cards');
    if (pcCardsEl) pcCardsEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function card(label, value, sub, onclick, colorCls) {
  const clickStyle = onclick ? 'cursor:pointer' : '';
  const clickAttr  = onclick ? `onclick="(${onclick.toString()})()"` : '';
  const cls = colorCls ? ` ${colorCls}` : '';
  return `<div class="card${cls}" style="${clickStyle}" ${clickAttr} title="${onclick ? 'Ver lista' : ''}">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    ${sub ? `<div class="sub">${sub}</div>` : ''}
  </div>`;
}

// Navigate to Games tab pre-filtered by device root and match status
function goToGames(root, status) {
  gamesState.root   = root   || null;
  gamesState.status = status || '';
  gamesState.platform = '';
  platformsLoaded = false;
  const statusSel = document.getElementById('games-matched');
  if (statusSel) statusSel.value = status || '';
  showTab('games');
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
    if (s.scan_running) {
      btnScan.disabled = false;
      btnScan.textContent = 'Detener scan';
      btnScan.onclick = () => stopJob('scan');
      btnScan.classList.add('danger');
    } else {
      btnScan.disabled = false;
      btnScan.textContent = 'Scan';
      btnScan.onclick = doScan;
      btnScan.classList.remove('danger');
    }
  }
  const scanProgWrap = document.getElementById('scan-progress-wrap');
  if (scanProgWrap) {
    if (s.scan_running && s.scan_progress) {
      const p = s.scan_progress;
      scanProgWrap.style.display = '';
      const counts = document.getElementById('scan-progress-counts');
      const file   = document.getElementById('scan-progress-file');
      if (counts) counts.textContent = `${p.files_seen || 0} archivos — ${p.roms_detected || 0} ROMs`;
      if (file)   file.textContent   = p.current_file || p.current_path || '';
    } else {
      scanProgWrap.style.display = 'none';
    }
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
    const ts = s.scan_result.result_ts || JSON.stringify(s.scan_result);
    if (_shownResultTs.scan !== ts) {
      _shownResultTs.scan = ts;
      _showJobResult('scan', s.scan_result);
      loadOverview();
    }
  }
  if (!s.match_running && s.match_result) {
    const ts = s.match_result.result_ts || JSON.stringify(s.match_result);
    if (_shownResultTs.match !== ts) {
      _shownResultTs.match = ts;
      _showJobResult('match', s.match_result);
      loadOverview();
    }
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
        const discMsg = r.disc_sets > 0 ? `  |  Sets multi-disco (omitidos): ${r.disc_sets}` : '';
        el.className = 'job-result visible success';
        el.textContent = `${verb}: ${r.extracted}  |  Omitidos: ${r.skipped}  |  Fallidos: ${r.failed}${discMsg}`;
      }
      const div = document.getElementById('zip-results');
      if (div && r.results?.length) {
        div.innerHTML = r.results.map(x => {
          const isDisc = x.is_disc_set;
          const color = x.success ? '#4ec9b0' : (isDisc ? '#569cd6' : (x.skipped_reason ? '#888' : '#f44747'));
          const tag   = x.success ? (r.dry_run ? 'PREVIEW' : 'OK') : (isDisc ? 'DISC' : (x.skipped_reason ? 'SKIP' : 'FAIL'));
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
    const srcMsg = result.source === 'adb' ? ` [ADB — ${result.android_path}]` : '';
    // If ADB scan, store the android path so the Overview Anbernic column filters by it
    if (result.source === 'adb' && result.android_path) {
      localStorage.setItem('anbernic_adb_path', result.android_path);
      // Also pre-fill the ov-ab-path field so stats show immediately
      const abInput = document.getElementById('ov-ab-path');
      if (abInput && !abInput.value) abInput.value = result.android_path;
    }
    el.textContent = `Scan completado${srcMsg} — ROMs: ${result.roms_detected}  |  Ya escaneados: ${result.roms_skipped}  |  Saves: ${result.saves_detected}  |  Errores: ${result.errors}${prunedMsg}`;
    showToast(`Scan completado — ${result.roms_detected} ROMs${result.errors ? ', ' + result.errors + ' errores' : ''}`, result.errors ? 'err' : 'ok');
  } else if (type === 'match') {
    el.className = 'job-result visible success';
    el.textContent = `Match completado — SHA1: ${result.matched_high}  |  Nombre: ${result.matched_low}  |  Sin match: ${result.unmatched}  (de ${result.total} ROMs)`;
  } else if (type === 'convert-chd') {
    el.className = 'job-result visible success';
    const verb = result.dry_run ? 'Convertiría' : 'Convertidos';
    el.textContent = `${verb}: ${result.converted}  |  Omitidos: ${result.skipped}  |  Fallidos: ${result.failed}`;
  }
}

// ── ADB scan helpers ──────────────────────────────────────────────────────────
function _onScanAdbChange() {
  const cb  = document.getElementById('scan-include-adb');
  const box = document.getElementById('scan-adb-options');
  if (box) box.style.display = cb?.checked ? '' : 'none';
}

async function detectAdbDevicesForScan() {
  const sel    = document.getElementById('scan-adb-device');
  const status = document.getElementById('scan-adb-status');
  if (status) { status.style.color = '#555'; status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) { if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + d.error; } return; }
    if (!d.devices?.length) {
      if (status) { status.style.color = '#ce9178'; status.textContent = 'No se encontraron dispositivos — conecta la Anbernic y activa Depuración USB'; }
      return;
    }
    if (sel) {
      sel.innerHTML = d.devices.map(dev =>
        `<option value="${dev.serial}" ${!dev.ready ? 'disabled' : ''}>${dev.display}${!dev.ready ? ' [NO LISTO]' : ''}</option>`
      ).join('');
      const ready = d.devices.find(dv => dv.ready);
      if (ready) sel.value = ready.serial;
    }
    const readyCount = d.devices.filter(dv => dv.ready).length;
    if (status) {
      status.style.color = readyCount ? '#4ec9b0' : '#ce9178';
      status.textContent = readyCount ? `✓ ${readyCount} dispositivo(s) listo(s)` : '⚠ Acepta el diálogo de depuración USB en la Anbernic';
    }
  } catch(e) { if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + e.message; } }
}

// ── Scan action ───────────────────────────────────────────────────────────────
async function doScan() {
  const includePc  = document.getElementById('scan-include-pc')?.checked;
  const includeAb  = document.getElementById('scan-include-ab')?.checked;
  const includeAdb = document.getElementById('scan-include-adb')?.checked;
  const pcPath = document.getElementById('ov-pc-path')?.value.trim() || '';
  const abPath = document.getElementById('ov-ab-path')?.value.trim() || '';
  const sourcePaths = [];
  if (includePc && pcPath) sourcePaths.push(pcPath);
  if (includeAb && abPath) sourcePaths.push(abPath);

  // ADB scan runs separately
  if (includeAdb) {
    const serial      = document.getElementById('scan-adb-device')?.value.trim();
    const androidPath = document.getElementById('scan-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    const resultEl = document.getElementById('job-result-scan');
    const btn      = document.getElementById('btn-scan');
    btn.disabled = true; btn.textContent = 'Escaneando ADB…';
    resultEl.className = 'job-result';
    try {
      const d = await apiPost('/api/adb-scan', { adb_serial: serial, android_path: androidPath });
      if (d.status === 'already_running') {
        resultEl.className = 'job-result visible'; resultEl.textContent = 'Ya hay un scan en curso…';
        btn.disabled = false; btn.textContent = 'Scan'; return;
      }
      // Also run FS scan if any FS paths selected
      if (sourcePaths.length > 0) {
        await apiPost('/api/scan', { source_paths: sourcePaths, quick: document.getElementById('scan-quick')?.checked || false });
      }
      startPolling();
    } catch(e) {
      btn.disabled = false; btn.textContent = 'Scan';
      resultEl.className = 'job-result visible error-r'; resultEl.textContent = 'Error: ' + e.message;
    }
    return;
  }

  if (sourcePaths.length === 0) {
    alert('Configura al menos una ruta en el panel "Rutas" y activa el checkbox correspondiente.');
    return;
  }
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
let _gamesSearchTimer = null;
function onGamesSearchChange() {
  clearTimeout(_gamesSearchTimer);
  _gamesSearchTimer = setTimeout(() => { loadGames(0); }, 300);
}
function onGamesFilterChange() {
  gamesState.platform = document.getElementById('games-platform').value;
  gamesState.status   = document.getElementById('games-matched').value;
  gamesState.filetype = document.getElementById('games-filetype').value;
  loadGames(0);
}

async function loadGames(offset) {
  gamesState.offset = offset ?? 0;
  const tbody = document.getElementById('games-tbody');
  tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading…</td></tr>';

  // Show active root filter if set
  const rootBanner = document.getElementById('games-root-banner');
  if (rootBanner) {
    if (gamesState.root) {
      rootBanner.style.display = 'flex';
      rootBanner.innerHTML = `<span style="color:#888;font-size:12px">Filtrando por: <code style="color:#ce9178">${gamesState.root}</code></span> <button class="btn" style="padding:2px 8px;font-size:11px" onclick="gamesState.root=null;document.getElementById('games-root-banner').style.display='none';loadGames(0)">&#x2715; Quitar filtro</button>`;
    } else {
      rootBanner.style.display = 'none';
    }
  }

  const q = document.getElementById('games-search').value.trim();
  const params = new URLSearchParams({
    offset: gamesState.offset,
    limit:  gamesState.limit,
  });
  if (gamesState.platform) params.set('platform', gamesState.platform);
  if (gamesState.status)   params.set('status',   gamesState.status);
  if (q)                   params.set('search',   q);
  const ft = document.getElementById('games-filetype')?.value;
  if (ft !== undefined && ft !== 'all') params.set('filetype', ft);
  const _gamesRoot = gamesState.root || _deviceRoot();
  if (_gamesRoot)          params.set('root',      _gamesRoot);

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

    const rows = d.games;

    const empty = document.getElementById('games-empty');
    if (rows.length === 0) {
      tbody.innerHTML = '';
      if (d.total === 0 && _activeDevice === 'anbernic' && !gamesState.root) {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        empty.innerHTML = `No hay ROMs de la Anbernic en la base de datos.<br><span style="color:#888;font-size:12px">Ruta: <code>${ab}</code> — Escanea la Anbernic primero (Overview → Escanear → Anbernic por ADB).</span>`;
      } else {
        empty.innerHTML = 'No games match the filter.';
      }
      empty.style.display = '';
    }
    else {
      empty.style.display = 'none';
      tbody.innerHTML = rows.map(g => `<tr>
        <td>${_platBadge(g.platform)}</td>
        <td title="${_h(g.canonical_title||'')}">${g.canonical_title || '<span style="color:#444">—</span>'}</td>
        <td class="mono" title="${_h(g.original_filename)}" style="color:#9cdcfe;font-size:12px">${_h(g.original_filename)}</td>
        <td><span style="font-size:11px;color:#888">${_h(g.region || '')}</span></td>
        <td>${g.match_confidence ? badge(g.match_confidence, g.match_confidence) : badge('none','—')}</td>
        <td style="color:#666;font-size:12px">${fmtSize(g.size_bytes)}</td>
        <td class="mono" style="color:#444;font-size:11px">${(g.sha1||'').slice(0,10)}…</td>
      </tr>`).join('');
      applyColVisibility();
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
    const root = _deviceRoot();
    const rootParam = root ? `&source_root=${encodeURIComponent(root)}` : '';
    const [d, cfg] = await Promise.all([apiFetch('/api/plan' + _planQueryString() + rootParam), apiFetch('/api/config')]);
    const planBar = document.getElementById('plan-context-bar');
    if (planBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        const r = cfg.library_root || '(no configurado)';
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${r}</span> &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      } else if (_activeDevice === 'anbernic') {
        const r = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">Anbernic — ${r}</span> &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      } else {
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> (PC + Anbernic) &nbsp;·&nbsp; <span style="color:#555">Los saves se renombran junto al ROM · Los cambios son reversibles</span>`;
      }
      planBar.innerHTML = barHtml;
      planBar.style.display = '';
    }

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
      if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || '(no configurado)';
        el.innerHTML = `<p class="empty">No hay ROMs de esta ruta en la base de datos.<br><span style="color:#888;font-size:12px">Ruta Anbernic: <code>${ab}</code><br>Escanea la Anbernic primero (Overview → Escanear → Anbernic por ADB).</span></p>`;
      } else {
        el.innerHTML = '<p class="empty">No matched games found. Run <strong>Match catálogos</strong> primero.</p>';
      }
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
      const collisions = d.conflicts.filter(c => c.reason === 'collision');
      const diskConflicts = d.conflicts.filter(c => c.reason === 'disk');
      const unknown = d.conflicts.filter(c => !c.reason || (c.reason !== 'collision' && c.reason !== 'disk'));

      html += `<h3 style="color:#f44747;margin:20px 0 8px">Conflicts — ${d.conflicts.length}</h3>`;

      if (collisions.length) {
        html += `<div style="background:#1a1218;border:1px solid #3a2030;border-left:3px solid #ce9178;border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:#ce9178;font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26A0; Colisión de plan (${collisions.length}) — dos ROMs quieren el mismo nombre canónico`;
        html += `</div>`;
        html += `<div style="color:#888;font-size:11px;margin-bottom:10px">`;
        html += `Causa habitual: tienes múltiples versiones del mismo juego (regional, revisión) y la opción <strong>Región</strong> o <strong>Revisión</strong> está desactivada en el formato. Actívalas para que cada versión obtenga un nombre único.<br>`;
        html += `O usa <button class="btn" style="padding:2px 10px;font-size:11px;margin:0 4px" onclick="applyKeepBoth()">Resolver automáticamente (añadir sufijo _1 _2)</button> para aplicar ambas con nombres distintos.`;
        html += `</div>`;
        html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Nombre bloqueado</th></tr></thead><tbody>';
        html += collisions.map(op => `<tr>
          <td class="mono" style="color:#9cdcfe">${_h(op.source_name)}</td>
          <td class="mono" style="color:#ce9178">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div></div>';
      }

      if (diskConflicts.length) {
        html += `<div style="background:#1a1212;border:1px solid #3a2020;border-left:3px solid #f44747;border-radius:6px;padding:12px 16px;margin-bottom:12px">`;
        html += `<div style="color:#f44747;font-size:12px;font-weight:600;margin-bottom:6px">`;
        html += `&#x26D4; Conflicto de disco (${diskConflicts.length}) — ya existe un archivo diferente en el destino`;
        html += `</div>`;
        html += `<div style="color:#888;font-size:11px;margin-bottom:10px">`;
        html += `El nombre canónico al que quieres renombrar ya está ocupado por otro archivo. Puede que hayas renombrado manualmente, o que haya dos ROMs distintas con el mismo título. Comprueba qué archivo ocupa ese nombre y elimínalo o muévelo manualmente.`;
        html += `</div>`;
        html += '<div style="overflow-x:auto"><table><thead><tr><th>ROM</th><th>Destino bloqueado</th></tr></thead><tbody>';
        html += diskConflicts.map(op => `<tr>
          <td class="mono" style="color:#9cdcfe">${_h(op.source_name)}</td>
          <td class="mono" style="color:#f44747">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div></div>';
      }

      if (unknown.length) {
        html += '<div style="overflow-x:auto"><table><thead><tr><th>From</th><th>To (blocked)</th></tr></thead><tbody>';
        html += unknown.map(op => `<tr>
          <td class="mono">${_h(op.source_name)}</td>
          <td class="mono" style="color:#f44747">${_h(op.target_name)}</td>
        </tr>`).join('');
        html += '</tbody></table></div>';
      }
    }
    if (d.already_correct > 0) {
      html += `<p style="color:#555;margin-top:16px">${d.already_correct} file(s) already have the correct name.</p>`;
    }
    if (d.unmatched_count > 0) {
      html += `<details style="margin-top:20px;border:1px solid #333;border-radius:6px;padding:10px 14px;background:#161620">`;
      html += `<summary style="cursor:pointer;color:#888;font-size:13px;user-select:none">`;
      html += `${d.unmatched_count} ROM${d.unmatched_count !== 1 ? 's' : ''} sin match en catálogo (no se renombrarán) `;
      html += `— <a href="#" style="color:#569cd6;font-size:12px" onclick="event.preventDefault();goToGames(null,'unmatched')">Ver en Games →</a>`;
      html += `</summary>`;
      html += `<div style="margin-top:10px;overflow-x:auto"><table><thead><tr><th>Platform</th><th>Filename</th></tr></thead><tbody>`;
      html += d.unmatched.map(g => `<tr>
        <td>${_platBadge(g.platform)}</td>
        <td class="mono" style="color:#9cdcfe;font-size:12px">${_h(g.original_filename)}</td>
      </tr>`).join('');
      html += `</tbody></table></div></details>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Apply action ──────────────────────────────────────────────────────────────
async function applyKeepBoth() {
  if (!confirm('¿Resolver colisiones añadiendo sufijo _1 _2 a los nombres? Se renombrarán todas las ROMs en colisión con nombres únicos.')) return;
  const applyBody = {
    keep_both: true,
    format_opts: {
      include_region:   document.getElementById('fmt-region').checked,
      include_revision: document.getElementById('fmt-revision').checked,
      include_platform: document.getElementById('fmt-platform').checked,
      include_sha:      document.getElementById('fmt-sha').checked,
      sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
    }
  };
  const applyRoot = _deviceRoot();
  if (applyRoot) applyBody.source_root = applyRoot;
  try {
    const d = await apiPost('/api/apply', applyBody);
    showToast(`Resueltos: ${d.renamed} renombrados, ${d.conflicts} conflictos restantes`, d.conflicts > 0 ? 'info' : 'ok');
    await loadPlan();
    loadOverview();
  } catch(e) {
    showToast('Error: ' + e.message, 'err');
  }
}

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
    const applyBody = {
      format_opts: {
        include_region:   document.getElementById('fmt-region').checked,
        include_revision: document.getElementById('fmt-revision').checked,
        include_platform: document.getElementById('fmt-platform').checked,
        include_sha:      document.getElementById('fmt-sha').checked,
        sha_length:       parseInt(document.getElementById('fmt-sha-length')?.value || '8'),
      }
    };
    const applyRoot = _deviceRoot();
    if (applyRoot) applyBody.source_root = applyRoot;
    const d = await apiPost('/api/apply', applyBody);
    const el = document.getElementById('plan-content');
    const msg = document.createElement('p');
    msg.style.cssText = 'margin-top:16px;color:#4ec9b0;font-size:13px';
    const savesInfo = d.saves_renamed > 0 ? `  |  Saves renombrados: ${d.saves_renamed}` : '';
    const skippedInfo = d.skipped > 0 ? `  |  Omitidos: ${d.skipped}` : '';
    msg.textContent = `Renombrados: ${d.renamed}  |  Fallidos: ${d.failed}${skippedInfo}  |  Conflictos: ${d.conflicts}${savesInfo}`;
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
    const root = _deviceRoot();
    let url;
    if (root) {
      url = `/api/duplicates?source_root=${encodeURIComponent(root)}`;
    } else {
      // Sistema completo: pass both roots so the server can exclude intentional cross-device copies
      const pcPath = localStorage.getItem('pc_path') || '';
      const abPath = localStorage.getItem('anbernic_path') || '';
      url = '/api/duplicates';
      const params = new URLSearchParams();
      if (pcPath) params.set('pc_root', pcPath);
      if (abPath) params.set('ab_root', abPath);
      if (params.toString()) url += '?' + params.toString();
    }
    const [d, cfg] = await Promise.all([apiFetch(url), apiFetch('/api/config')]);
    const dupBar = document.getElementById('dup-context-bar');
    if (dupBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${cfg.library_root || '(no configurado)'}</span> &nbsp;·&nbsp; <span style="color:#555">Duplicado = mismo SHA1 exacto</span>`;
      } else if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">Anbernic — ${ab}</span> &nbsp;·&nbsp; <span style="color:#555">Duplicado = mismo SHA1 exacto</span>`;
      } else {
        const parts = [`PC: <span style="color:#4ec9b0">${cfg.library_root || '(no configurado)'}</span>`];
        const ab = localStorage.getItem('anbernic_path');
        if (ab) parts.push(`Anbernic: <span style="color:#ce9178">${ab}</span>`);
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> → ${parts.join(' &nbsp;+&nbsp; ')} &nbsp;·&nbsp; <span style="color:#555">Duplicados <em>dentro</em> del mismo dispositivo — las copias PC↔Anbernic se excluyen</span>`;
      }
      dupBar.innerHTML = barHtml;
      dupBar.style.display = '';
    }
    if (d.groups.length === 0) {
      if (_activeDevice === 'anbernic') {
        el.innerHTML = '<p class="empty">No se encontraron duplicados en la Anbernic.<br><span style="color:#888;font-size:12px">Nota: Los duplicados <em>cruzados</em> entre PC y Anbernic (mismo SHA1 en ambos dispositivos) solo aparecen en modo <strong>Sistema completo</strong>.</span></p>';
      } else {
        el.innerHTML = '<p class="empty">No duplicates found.</p>';
      }
      return;
    }
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

// ── RA Duplicates ─────────────────────────────────────────────────────────────
async function loadRaDuplicates() {
  const el = document.getElementById('ra-dup-content');
  const btn = document.getElementById('btn-ra-dups');
  el.innerHTML = '<p style="color:#555;font-size:12px">Cargando…</p>';
  if (btn) btn.disabled = true;
  try {
    const d = await apiFetch('/api/ra-duplicates');
    if (d.note) {
      el.innerHTML = `<p style="color:#888;font-size:12px">${d.note}</p>`;
      return;
    }
    if (d.total_groups === 0) {
      el.innerHTML = '<p style="color:#4ec9b0;font-size:13px">No se encontraron versiones candidatas a eliminar. ✓</p>';
      return;
    }
    let html = `<p style="color:#888;font-size:12px;margin-bottom:12px">
      <strong style="color:#e0e0e0">${d.total_groups}</strong> grupos encontrados —
      <strong style="color:#f44747">${fmtSize(d.wasted_bytes)}</strong> recuperables eliminando versiones sin logros.
    </p>`;
    for (const g of d.groups) {
      html += `<div style="border:1px solid #2a2a3e;border-radius:4px;margin-bottom:10px;overflow:hidden">
        <div style="background:#252537;padding:7px 12px;display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:13px;font-weight:600;color:#c9bcf5">${_h(g.normalized_title)}</span>
          <span style="font-size:11px;color:#888">${_h(g.platform)} — ${fmtSize(g.wasted_bytes)} recuperables</span>
        </div>
        <table style="width:100%;font-size:12px">
          <thead><tr>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Archivo</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Tamaño</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Logros RA</th>
            <th style="padding:5px 10px;text-align:left;color:#555;font-size:11px">Recomendación</th>
          </tr></thead>
          <tbody>`;
      for (const e of g.entries) {
        const raLabel = e.ra_supported
          ? `<span style="color:#4ec9b0">✓ ${e.ra_achievements} logros</span>`
          : `<span style="color:#f44747">✗ Sin logros</span>`;
        const rec = e.ra_supported
          ? '<span style="color:#4ec9b0">Conservar</span>'
          : '<span style="color:#f44747">Candidata a eliminar</span>';
        const rowBg = e.ra_supported ? '' : 'style="background:#1a1015"';
        html += `<tr ${rowBg}>
          <td style="padding:5px 10px;word-break:break-all">${_h(e.filename)}</td>
          <td style="padding:5px 10px">${fmtSize(e.size_bytes)}</td>
          <td style="padding:5px 10px">${raLabel}</td>
          <td style="padding:5px 10px">${rec}</td>
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

// ── Sync ──────────────────────────────────────────────────────────────────────
async function loadSync() {
  const el = document.getElementById('sync-content');
  try {
    const [sl, cfg] = await Promise.all([apiFetch('/api/sync-log'), apiFetch('/api/config')]);
    let html = '';
    const syncBar = document.getElementById('sync-context-bar');
    if (syncBar) {
      const local  = cfg.library_root  || '(no configurado)';
      const remote = cfg.rclone_remote || '(no configurado)';
      const remoteColor = cfg.rclone_remote ? '#4ec9b0' : '#f48771';
      syncBar.innerHTML = `Sincronizando saves de <span style="color:#4ec9b0">${local}</span> &nbsp;↔&nbsp; nube: <span style="color:${remoteColor}">${remote}</span> &nbsp;·&nbsp; <span style="color:#555">Solo archivos .sav .srm .state y similares</span>`;
      syncBar.style.display = '';
    }
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
    const _assetsRoot = _deviceRoot();
    const assetsUrl = _assetsRoot ? `/api/assets?root=${encodeURIComponent(_assetsRoot)}` : '/api/assets';
    const [d, cfg] = await Promise.all([apiFetch(assetsUrl), apiFetch('/api/config')]);
    const assetsBar = document.getElementById('assets-context-bar');
    if (assetsBar) {
      let barHtml = '';
      if (_activeDevice === 'pc') {
        barHtml = `Viendo: <span style="color:#4ec9b0">PC — ${cfg.library_root || '(no configurado)'}</span> &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      } else if (_activeDevice === 'anbernic') {
        const ab = document.getElementById('ov-ab-path')?.value.trim() || localStorage.getItem('anbernic_path') || '(no configurado)';
        barHtml = `Viendo: <span style="color:#ce9178">Anbernic — ${ab}</span> &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      } else {
        barHtml = `Viendo: <span style="color:#569cd6">Sistema completo</span> (PC + Anbernic) &nbsp;·&nbsp; <span style="color:#555">Portadas, videos y otros archivos de frontend detectados en el scan</span>`;
      }
      assetsBar.innerHTML = barHtml;
      assetsBar.style.display = '';
    }
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
        if (r.success) {
          const tag = result.dry_run ? 'PREVIEW' : 'OK';
          return `<div style="font-size:12px;color:#4ec9b0;padding:2px 0">[${tag}] ${r.cue} → ${r.chd}</div>`;
        } else {
          const errMsg = r.error ? `<span style="color:#f44747;margin-left:6px;font-style:italic">${r.error}</span>` : '';
          return `<div style="font-size:12px;color:#f44747;padding:4px 0;border-bottom:1px solid #2a1a1a"><strong>[FAIL]</strong> ${r.cue}${errMsg}</div>`;
        }
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

async function autodetectM3UFolders() {
  const btn = document.getElementById('btn-m3u-autodetect');
  const wrap = document.getElementById('m3u-folder-select-wrap');
  const listEl = document.getElementById('m3u-folder-list');
  if (btn) { btn.disabled = true; btn.textContent = 'Detectando…'; }
  try {
    const d = await apiFetch('/api/disc-folders');
    const folders = d.folders || [];
    if (folders.length === 0) {
      alert('No se detectaron carpetas de plataformas de disco en library_root.');
    } else if (folders.length === 1) {
      document.getElementById('m3u-path').value = folders[0];
      if (wrap) wrap.style.display = 'none';
    } else {
      // Show folder buttons to pick one
      listEl.innerHTML = folders.map(f => {
        const name = f.split(/[\\/]/).pop();
        return `<button class="btn" style="font-size:12px;padding:3px 10px" onclick="document.getElementById('m3u-path').value='${f.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}';document.getElementById('m3u-folder-select-wrap').style.display='none'">${name}</button>`;
      }).join('');
      if (wrap) wrap.style.display = '';
    }
  } catch(e) {
    alert('Error al detectar carpetas: ' + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Autodetectar carpetas'; }
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
    const totalBytes = d.orphans.reduce((s, o) => s + o.size_bytes, 0);
    let html = `<p style="color:#888;margin-bottom:8px">${d.total} save(s) huérfano(s) — ${fmtSize(totalBytes)} en total:</p>`;
    html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:12px">
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#888">
        <input type="checkbox" id="orphan-select-all" checked onchange="document.querySelectorAll('.orphan-chk').forEach(c=>c.checked=this.checked)">
        Seleccionar todos
      </label>
    </div>`;
    html += '<div style="max-height:350px;overflow-y:auto;margin-bottom:10px">';
    html += d.orphans.map(o => `
      <div style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px">
        <input type="checkbox" class="orphan-chk" value="${o.save_path.replace(/"/g, '&quot;')}" data-size="${o.size_bytes}" checked onchange="_updateOrphanSelectAll()">
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#888" title="${o.save_path}">${o.save_path}</span>
        <span style="color:#555;flex-shrink:0">${fmtSize(o.size_bytes)}</span>
      </div>`).join('');
    html += '</div>';
    html += '<button class="btn danger" onclick="doDeleteOrphans()">Borrar seleccionados</button>';
    resultEl.innerHTML = html;
  } catch(e) {
    resultEl.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

function _updateOrphanSelectAll() {
  const all = [...document.querySelectorAll('.orphan-chk')];
  const allChecked = all.every(c => c.checked);
  const noneChecked = all.every(c => !c.checked);
  const sa = document.getElementById('orphan-select-all');
  if (sa) { sa.checked = allChecked; sa.indeterminate = !allChecked && !noneChecked; }
}

async function doDeleteOrphans() {
  const checkedEls = [...document.querySelectorAll('.orphan-chk:checked')];
  const checked = checkedEls.map(c => c.value);
  if (checked.length === 0) { alert('Selecciona al menos un archivo.'); return; }
  const totalBytes = checkedEls.reduce((s, c) => s + parseInt(c.dataset.size || '0'), 0);
  if (!confirm(`¿Eliminar ${checked.length} save(s) huérfano(s)?\nEspacio a liberar: ${fmtSize(totalBytes)}\n\nEsta operación no se puede deshacer.`)) return;
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

// ── Análisis de carpeta ───────────────────────────────────────────────────────
async function doFolderAnalysis() {
  const path = document.getElementById('folder-analysis-path').value.trim();
  const el   = document.getElementById('folder-analysis-result');
  if (!path) { el.innerHTML = '<p class="error-msg">Introduce una ruta.</p>'; return; }
  el.innerHTML = '<p class="loading">Analizando…</p>';
  try {
    const d = await apiFetch('/api/folder-analysis?path=' + encodeURIComponent(path));
    let html = '';

    // Extensions table
    if (d.extensions && d.extensions.length > 0) {
      html += '<h4 style="color:#569cd6;margin-bottom:8px">Extensiones encontradas</h4>';
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Extensión</th><th>Archivos</th><th>Categoría</th></tr></thead><tbody>';
      html += d.extensions.map(e => {
        const color = e.category === 'rom' ? '#4ec9b0' : e.category === 'unknown' ? '#f44747' : '#888';
        return `<tr><td class="mono" style="color:${color}">${_h(e.ext)}</td><td>${e.count}</td><td style="color:${color}">${_h(e.category)}</td></tr>`;
      }).join('');
      html += '</tbody></table></div>';
    }

    // CUE sets with missing BIN
    if (d.cue_missing_bin && d.cue_missing_bin.length > 0) {
      html += `<h4 style="color:#f44747;margin:16px 0 8px">&#x26D4; .cue sin .bin (${d.cue_missing_bin.length})</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.cue_missing_bin.map(f => `<li class="mono" style="color:#ce9178;font-size:12px">${_h(f)}</li>`).join('');
      html += '</ul>';
    }

    // Orphan BIN (no CUE)
    if (d.bin_orphan && d.bin_orphan.length > 0) {
      html += `<h4 style="color:#ce9178;margin:16px 0 8px">&#x26A0; .bin sin .cue (${d.bin_orphan.length})</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.bin_orphan.map(f => `<li class="mono" style="font-size:12px">${_h(f)}</li>`).join('');
      html += '</ul>';
    }

    // Formats needing conversion
    if (d.needs_conversion && d.needs_conversion.length > 0) {
      html += `<h4 style="color:#dcdcaa;margin:16px 0 8px">Formatos que necesitan soporte/conversión</h4>`;
      html += '<ul style="margin:0;padding-left:20px">';
      html += d.needs_conversion.map(e => `<li style="color:#888;font-size:12px"><code>${_h(e.ext)}</code> — ${_h(e.note)}</li>`).join('');
      html += '</ul>';
    }

    if (!html) html = '<p style="color:#555">No se encontraron archivos en la carpeta.</p>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${_h(e.message)}</p>`;
  }
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
    document.getElementById('cfg-adb').value           = cfg.adb || 'adb';
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

async function testAdbBinary() {
  const el = document.getElementById('adb-test-result');
  el.style.color = '#888'; el.textContent = 'Probando…';
  const val = document.getElementById('cfg-adb').value.trim();
  if (val) await apiPost('/api/config', { 'tools.adb': val }).catch(() => {});
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      el.style.color = '#f44747'; el.textContent = '✗ ' + d.error;
    } else {
      el.style.color = '#4ec9b0';
      el.textContent = `✓ adb accesible — ${d.devices?.length ?? 0} dispositivo(s) detectado(s)  (${d.adb_path})`;
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
      _setIfEmpty('report-path',            root);
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
  if (el && !el.value.trim() && value) { el.value = value; return true; }
  return false;
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
  const ab = document.getElementById('cfg-adb').value.trim();
  const ra = document.getElementById('cfg-ra-api-key').value.trim();
  if (lr) updates['library.library_root']        = lr;
  if (rr) updates['sync.remote']                 = rr;
  if (su) updates['screenscraper.user']           = su;
  if (sp) updates['screenscraper.pass']           = sp;
  if (ch) updates['tools.chdman']                 = ch;
  if (ab) updates['tools.adb']                    = ab;
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

async function saveOvPaths() {
  const pcPath = document.getElementById('ov-pc-path').value.trim();
  const abPath = document.getElementById('ov-ab-path').value.trim();
  const resultEl = document.getElementById('ov-paths-result');
  if (abPath) localStorage.setItem('anbernic_path', abPath);
  if (pcPath) {
    try {
      const d = await apiPost('/api/config', {'library.library_root': pcPath});
      if (d.error) {
        resultEl.className = 'job-result visible error-r';
        resultEl.textContent = 'Error: ' + d.error;
        return;
      }
    } catch(e) {
      resultEl.className = 'job-result visible error-r';
      resultEl.textContent = 'Error: ' + e.message;
      return;
    }
  }
  // Update UI elements that depend on abPath
  const abCb    = document.getElementById('scan-include-ab');
  const devAb   = document.getElementById('dev-anbernic');
  const abLabel = document.getElementById('scan-ab-label');
  const abLbl   = document.getElementById('ov-ab-path-label');
  if (abCb)    { abCb.disabled = !abPath; if (abPath && !abCb.checked) abCb.checked = true; }
  if (devAb)   devAb.disabled = !abPath;
  if (abLabel) abLabel.textContent = abPath || '(configura la ruta arriba)';
  if (abLbl)   abLbl.textContent = abPath ? '— ' + abPath : '';
  // Reload Anbernic stats in Overview if path changed
  if (abPath) loadOverview();

  resultEl.className = 'job-result visible ok-r';
  resultEl.textContent = 'Rutas guardadas.';
  setTimeout(() => { resultEl.className = 'job-result'; }, 3000);
}

// ── Cable Sync ────────────────────────────────────────────────────────────────

function _isAdbMode() {
  return document.querySelector('input[name="cable-ab-mode"]:checked')?.value === 'adb';
}

function _onCableModeChange() {
  const adb = _isAdbMode();
  const fsEl  = document.getElementById('cable-fs-section');
  const adbEl = document.getElementById('cable-adb-section');
  if (fsEl)  fsEl.style.display  = adb ? 'none' : '';
  if (adbEl) adbEl.style.display = adb ? '' : 'none';
}

function _onCableDryRunChange() {
  const cb = document.getElementById('cable-dry-run');
  const warn = document.getElementById('cable-dry-run-warning');
  if (warn) warn.style.display = cb?.checked ? 'none' : '';
}

function _onCableDirectionChange() {
  const dir = document.querySelector('input[name="cable-direction"]:checked')?.value;
  const row = document.getElementById('cable-sha1-row');
  if (row) row.style.display = (dir === 'anbernic_to_pc') ? '' : 'none';
}

async function testCablePath(which) {
  const inputId  = which === 'pc' ? 'cable-pc-path' : 'cable-ab-path';
  const statusId = which === 'pc' ? 'cable-pc-path-status' : 'cable-ab-path-status';
  const path = document.getElementById(inputId)?.value.trim();
  const statusEl = document.getElementById(statusId);
  if (!path) { if (statusEl) { statusEl.style.color = '#888'; statusEl.textContent = 'Introduce una ruta primero.'; } return; }
  if (statusEl) { statusEl.style.color = '#555'; statusEl.textContent = 'Verificando…'; }
  try {
    const d = await apiFetch('/api/test-path?path=' + encodeURIComponent(path));
    if (d.accessible) {
      statusEl.style.color = '#4ec9b0';
      statusEl.textContent = `✓ Accesible — ${d.entries} entradas en la carpeta`;
    } else {
      statusEl.style.color = '#f44747';
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { statusEl.style.color = '#f44747'; statusEl.textContent = '✗ ' + e.message; }
  }
}

async function detectDrives() {
  const listEl = document.getElementById('cable-drives-list');
  if (!listEl) return;
  listEl.style.display = '';
  listEl.textContent = 'Buscando…';
  try {
    const d = await apiFetch('/api/list-drives');
    if (!d.drives?.length) { listEl.textContent = 'No se encontraron unidades.'; return; }
    listEl.innerHTML = d.drives.map(dr => {
      const label = dr.label ? ` — ${dr.label}` : '';
      const size  = dr.total_bytes > 0 ? ` (${fmtSize(dr.free_bytes)} libres de ${fmtSize(dr.total_bytes)})` : '';
      return `<div style="display:flex;align-items:center;gap:8px;padding:2px 0">
        <code style="color:#ce9178;min-width:36px">${dr.letter}</code>
        <span style="color:#888">${label}${size}</span>
        <button class="btn" style="padding:1px 8px;font-size:11px;margin-left:auto" onclick="document.getElementById('cable-ab-path').value='${dr.letter.replace(/\\/g, '\\\\')}';testCablePath('ab');document.getElementById('cable-drives-list').style.display='none'">Usar</button>
      </div>`;
    }).join('');
  } catch(e) {
    listEl.textContent = 'Error: ' + e.message;
  }
}

async function detectAdbDevices() {
  const sel    = document.getElementById('cable-adb-device');
  const status = document.getElementById('cable-adb-status');
  const pathStatus = document.getElementById('cable-adb-path-status');
  if (status) { status.style.color = '#555'; status.textContent = 'Buscando…'; }
  try {
    const d = await apiFetch('/api/adb-devices');
    if (d.error) {
      if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + d.error; }
      return;
    }
    if (!d.devices?.length) {
      if (status) { status.style.color = '#ce9178'; status.textContent = 'No se encontraron dispositivos. ¿Cable conectado? ¿Depuración USB activada?'; }
      return;
    }
    if (sel) {
      sel.innerHTML = d.devices.map(dev =>
        `<option value="${dev.serial}" ${!dev.ready ? 'disabled' : ''}>
          ${dev.display}${!dev.ready ? ' — NO LISTO' : ''}
        </option>`
      ).join('');
    }
    const ready = d.devices.filter(dv => dv.ready);
    if (status) {
      status.style.color = ready.length ? '#4ec9b0' : '#ce9178';
      status.textContent = ready.length
        ? `✓ ${ready.length} dispositivo(s) listo(s)`
        : '⚠ Dispositivo detectado pero no listo — acepta el diálogo de depuración USB en la pantalla';
    }
    // Auto-test the Android path if a ready device is selected
    if (ready.length) {
      sel.value = ready[0].serial;
      testAdbPath();
    }
  } catch(e) {
    if (status) { status.style.color = '#f44747'; status.textContent = '✗ ' + e.message; }
  }
}

async function testAdbPath() {
  const serial  = document.getElementById('cable-adb-device')?.value.trim();
  const ap      = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
  const statusEl = document.getElementById('cable-adb-path-status');
  if (!serial) { if (statusEl) { statusEl.style.color = '#888'; statusEl.textContent = 'Selecciona un dispositivo primero.'; } return; }
  if (statusEl) { statusEl.style.color = '#555'; statusEl.textContent = 'Verificando ruta en el dispositivo…'; }
  try {
    const d = await apiFetch(`/api/test-adb-path?serial=${encodeURIComponent(serial)}&path=${encodeURIComponent(ap)}`);
    if (d.accessible) {
      statusEl.style.color = '#4ec9b0';
      statusEl.textContent = `✓ Ruta accesible — ${d.entries} entradas`;
    } else {
      statusEl.style.color = '#f44747';
      statusEl.textContent = '✗ ' + d.error;
    }
  } catch(e) {
    if (statusEl) { statusEl.style.color = '#f44747'; statusEl.textContent = '✗ ' + e.message; }
  }
}

async function loadCableSync() {
  try {
    const cfg = await apiFetch('/api/config');
    const ovPc = document.getElementById('ov-pc-path')?.value.trim();
    const ovAb = document.getElementById('ov-ab-path')?.value.trim();
    // Fill both fs and adb pc-path inputs
    _setIfEmpty('cable-pc-path',     ovPc || cfg.library_root || '');
    _setIfEmpty('cable-adb-pc-path', ovPc || cfg.library_root || '');
    _setIfEmpty('cable-ab-path', ovAb || localStorage.getItem('anbernic_path') || '');
    if (document.getElementById('cable-pc-path')?.value) testCablePath('pc');
    if (document.getElementById('cable-ab-path')?.value) testCablePath('ab');
  } catch(_) {}
}

async function doCableSync() {
  const adb = _isAdbMode();
  const pcPath = (adb
    ? document.getElementById('cable-adb-pc-path')
    : document.getElementById('cable-pc-path'))?.value.trim();
  if (!pcPath) { alert('Introduce la ruta del PC (library_root).'); return; }

  const wantSaves = document.getElementById('cable-what-saves').checked;
  const wantRoms  = document.getElementById('cable-what-roms').checked;
  if (!wantSaves && !wantRoms) { alert('Selecciona al menos qué sincronizar: saves o ROMs.'); return; }

  const what = [];
  if (wantSaves) what.push('saves');
  if (wantRoms)  what.push('roms');

  const direction    = document.querySelector('input[name="cable-direction"]:checked')?.value || 'pc_to_anbernic';
  const dryRun       = document.getElementById('cable-dry-run').checked;
  const skipExisting = document.getElementById('cable-skip-existing')?.checked ?? true;
  const skipSha1Dups = direction === 'anbernic_to_pc' && (document.getElementById('cable-skip-sha1')?.checked ?? false);

  let body;
  if (adb) {
    const serial      = document.getElementById('cable-adb-device')?.value.trim();
    const androidPath = document.getElementById('cable-android-path')?.value.trim() || '/storage/emulated/0';
    if (!serial) { alert('Detecta y selecciona un dispositivo ADB primero.'); return; }
    body = { pc_path: pcPath, use_adb: true, adb_serial: serial, android_path: androidPath,
             what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups };
  } else {
    const abPath = document.getElementById('cable-ab-path')?.value.trim();
    if (!abPath) { alert('Introduce la ruta de la Anbernic en el PC.'); return; }
    body = { pc_path: pcPath, anbernic_path: abPath, what, direction, dry_run: dryRun, skip_existing: skipExisting, skip_sha1_dups: skipSha1Dups };
  }

  const btn      = document.getElementById('btn-cable-sync');
  const resultEl = document.getElementById('cable-result');
  btn.disabled = true;
  btn.textContent = 'Sincronizando…';
  resultEl.className = 'job-result';
  document.getElementById('cable-details-wrap').style.display = 'none';
  delete window._lastCableSyncResult;

  try {
    const d = await apiPost('/api/cable-sync', body);
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
  const sha1Msg     = r.sha1_skipped > 0 ? `  |  Dups SHA1: ${r.sha1_skipped}` : '';
  const existsCount = r.details ? r.details.filter(d => d.file === 'EXISTS').length : 0;
  const existsMsg   = existsCount > 0 ? `  |  Ya existen: ${existsCount}` : '';

  const needsScan = !r.dry_run && r.copied > 0 && (r.direction === 'anbernic_to_pc' || r.direction === 'newest');
  resultEl.className = 'job-result visible success';
  resultEl.innerHTML = `${verb}: <strong>${r.copied}</strong> archivo(s) (${fmtSize(r.copied_bytes)})  |  Omitidos: ${r.skipped}  |  Errores: ${r.errors}${existsMsg}${sha1Msg}  —  ${dirStr}${dryTag}`
    + (needsScan ? `<br><span style="color:#dcdcaa;font-size:11px">&#x26A0; Se han copiado archivos al PC — haz un <strong>Scan</strong> en Overview para indexarlos en la base de datos.</span>` : '');

  if (r.details && r.details.length > 0) {
    detailsList.innerHTML = r.details.map(d => {
      const isDup    = d.file === 'DUP';
      const isExists = d.file === 'EXISTS';
      const isErr    = d.file.startsWith('ERROR');
      const tagColor = isDup ? '#569cd6' : isExists ? '#444' : isErr ? '#f44747' : '#4ec9b0';
      return `<div style="padding:2px 0;color:#888"><span style="color:${tagColor};margin-right:8px">${d.file}</span>${d.path}</div>`;
    }).join('');
    detailsWrap.style.display = '';
  }
}

// ── Library Report ───────────────────────────────────────────────────────────
let _reportData = null;

function showReportTab(name) {
  document.querySelectorAll('.rpt-tab').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.rpt-tab-btn').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById('rpt-tab-' + name);
  const btn = document.getElementById('rpt-tab-btn-' + name);
  if (tab) tab.style.display = '';
  if (btn) btn.classList.add('active');
}

async function generateReport() {
  const pathInput = document.getElementById('report-path');
  const path = pathInput?.value.trim() || '';
  const loadingEl  = document.getElementById('report-loading');
  const contentEl  = document.getElementById('report-content');
  const exportBtn  = document.getElementById('btn-export-report');

  if (loadingEl) loadingEl.style.display = '';
  if (contentEl) contentEl.style.display = 'none';
  if (exportBtn) exportBtn.style.display = 'none';

  try {
    const params = path ? '?path=' + encodeURIComponent(path) : '';
    _reportData = await apiFetch('/api/library-report' + params);

    _renderReportZips(_reportData);
    _renderReportPlaylists(_reportData);
    _renderReportMultidisc(_reportData);
    _renderReportOrphans(_reportData);
    _renderReportRa(_reportData);
    _renderReportChd(_reportData);

    if (contentEl) contentEl.style.display = '';
    if (exportBtn) exportBtn.style.display = '';
    showReportTab('zips');
  } catch(e) {
    const el = document.getElementById('rpt-tab-zips');
    if (el) el.innerHTML = `<p class="error-msg">${e.message}</p>`;
    if (contentEl) contentEl.style.display = '';
    showReportTab('zips');
  } finally {
    if (loadingEl) loadingEl.style.display = 'none';
  }
}

function _rptStat(cls, text) {
  return `<span class="rpt-stat ${cls}">${text}</span>`;
}

function _renderReportZips(d) {
  const el = document.getElementById('rpt-tab-zips');
  if (!el) return;
  const z = d.zips;
  const normal    = z.files.filter(f => !f.is_disc_set);
  const discSets  = z.files.filter(f => f.is_disc_set);
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-info', z.total + ' ZIPs encontrados')}
    ${discSets.length ? _rptStat('rpt-warn', discSets.length + ' sets multi-disco (usar CHD)') : ''}
    ${normal.length   ? _rptStat('rpt-ok',   normal.length + ' ROMs comprimidos pendientes') : _rptStat('rpt-ok', 'Sin ZIPs pendientes')}
  </div>`;
  if (normal.length) {
    const totalBytes = normal.reduce((s, f) => s + f.size_bytes, 0);
    html += `<p style="color:#888;font-size:12px;margin-bottom:8px">Espacio total: ${fmtSize(totalBytes)}</p>`;
    html += '<div style="max-height:350px;overflow-y:auto;font-size:12px">';
    html += normal.map(f => `<div style="padding:2px 0;color:#d4d4d4">${f.path} <span style="color:#555">(${fmtSize(f.size_bytes)})</span></div>`).join('');
    html += '</div>';
  }
  if (discSets.length) {
    html += `<p style="color:#ce9178;font-size:11px;margin-top:12px;margin-bottom:4px">Sets multi-disco (omitidos por el extractor — usar conversor CHD):</p>`;
    html += '<div style="max-height:200px;overflow-y:auto;font-size:12px">';
    html += discSets.map(f => `<div style="padding:2px 0;color:#555">${f.path}</div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html || '<p class="empty">No hay archivos ZIP en la carpeta.</p>';
}

function _renderReportPlaylists(d) {
  const el = document.getElementById('rpt-tab-playlists');
  if (!el) return;
  const p = d.playlists;
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-info',  p.total_groups + ' grupos multi-disco')}
    ${_rptStat('rpt-ok',    p.with_m3u    + ' con playlist M3U')}
    ${p.without_m3u ? _rptStat('rpt-warn', p.without_m3u + ' sin playlist') : ''}
  </div>`;
  if (!p.groups.length) { el.innerHTML = '<p class="empty">No hay juegos multi-disco.</p>'; return; }
  html += '<div style="max-height:450px;overflow-y:auto">';
  html += p.groups.map(g => {
    const tag = g.m3u_exists
      ? `<span style="color:#4ec9b0;font-size:11px">✓ M3U</span>`
      : `<span style="color:#ce9178;font-size:11px">⚠ Sin M3U</span>`;
    return `<div style="padding:5px 0;border-bottom:1px solid #1e1e2e">
      <div style="display:flex;align-items:center;gap:8px">
        ${tag}
        <span style="color:#d4d4d4;font-size:13px">${g.base_name}</span>
        <span style="color:#555;font-size:11px">${g.disc_count} discos</span>
      </div>
      <div style="color:#555;font-size:11px;margin-top:2px;padding-left:4px">${g.discs.join(' · ')}</div>
    </div>`;
  }).join('');
  html += '</div>';
  el.innerHTML = html;
}

function _renderReportMultidisc(d) {
  const el = document.getElementById('rpt-tab-multidisc');
  if (!el) return;
  const m = d.multidisc;
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-ok',  m.groups_ok + ' sets completos')}
    ${m.groups_with_issues ? _rptStat('rpt-bad', m.groups_with_issues + ' sets con problemas') : ''}
  </div>`;
  if (!m.issues.length) {
    html += '<p style="color:#4ec9b0;font-size:12px">Todos los sets multi-disco están completos.</p>';
  } else {
    const typeLabels = { gap: 'Discos faltantes', mixed_ext: 'Extensiones mezcladas', missing_file: 'Archivo no encontrado', unmatched: 'Sin match en catálogo' };
    html += '<div style="max-height:450px;overflow-y:auto">';
    const grouped = {};
    m.issues.forEach(i => { (grouped[i.base_name] = grouped[i.base_name] || []).push(i); });
    html += Object.entries(grouped).map(([name, issues]) => `
      <div style="padding:8px 0;border-bottom:1px solid #1e1e2e">
        <div style="color:#ce9178;font-size:13px;margin-bottom:4px">${name}</div>
        ${issues.map(i => `<div style="font-size:12px;color:#888;padding:1px 0">
          <span style="color:#f44747">${typeLabels[i.issue_type] || i.issue_type}:</span> ${i.detail}
        </div>`).join('')}
      </div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

function _renderReportOrphans(d) {
  const el = document.getElementById('rpt-tab-orphans');
  if (!el) return;
  const o = d.orphans;
  let html = `<div style="margin-bottom:12px">
    ${o.total ? _rptStat('rpt-warn', o.total + ' saves huérfanos') : _rptStat('rpt-ok', 'Sin saves huérfanos')}
    ${o.total ? _rptStat('rpt-info', fmtSize(o.total_bytes) + ' recuperables') : ''}
  </div>`;
  if (!o.saves.length) { el.innerHTML = html + '<p style="color:#4ec9b0;font-size:12px">No hay saves huérfanos.</p>'; return; }
  html += '<div style="max-height:400px;overflow-y:auto;font-size:12px">';
  html += o.saves.map(s => {
    const name = s.path.split(/[\\/]/).pop();
    return `<div style="padding:2px 0;color:#888">${name} <span style="color:#555">(${fmtSize(s.size_bytes)})</span> <span style="color:#444;font-size:10px">${s.path}</span></div>`;
  }).join('');
  html += '</div>';
  el.innerHTML = html;
}

function _renderReportRa(d) {
  const el = document.getElementById('rpt-tab-ra');
  if (!el) return;
  const ra = d.retroachievements;
  if (ra?.note) { el.innerHTML = `<p style="color:#555;font-size:12px">${ra.note}</p>`; return; }
  if (ra?.error) { el.innerHTML = `<p class="error-msg">${ra.error}</p>`; return; }
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-ok',   ra.supported + ' con logros')}
    ${ra.no_support_alternative ? _rptStat('rpt-warn', ra.no_support_alternative + ' versión sin logros (alternativa disponible)') : ''}
    ${_rptStat('rpt-info', ra.no_support + ' sin soporte RA')}
    ${ra.no_md5 ? _rptStat('rpt-info', ra.no_md5 + ' sin MD5 (scan completo necesario)') : ''}
  </div>`;
  if (ra.alternatives?.length) {
    html += `<p style="color:#888;font-size:12px;margin-bottom:8px">Juegos con versión alternativa compatible:</p>`;
    html += '<div style="max-height:350px;overflow-y:auto;font-size:12px">';
    html += ra.alternatives.map(a => `<div style="padding:3px 0;border-bottom:1px solid #1e1e2e">
      <span style="color:#ce9178">${a.our_filename}</span>
      <span style="color:#555;font-size:11px;margin-left:8px">→ RA: ${a.ra_title} (${a.ra_achievements} logros, ${a.ra_points} pts)</span>
    </div>`).join('');
    html += '</div>';
    if (ra.no_support_alternative > 0) {
      html += `<p style="margin-top:8px"><a href="/api/ra-check.csv" download class="btn" style="font-size:12px">&#x2193; Descargar CSV completo (${ra.no_support_alternative} juegos)</a></p>`;
    }
  }
  el.innerHTML = html;
}

function _renderReportChd(d) {
  const el = document.getElementById('rpt-tab-chd');
  if (!el) return;
  const chd = d.chd;
  if (chd?.note) { el.innerHTML = `<p style="color:#555;font-size:12px">${chd.note}</p>`; return; }
  if (chd?.error) { el.innerHTML = `<p class="error-msg">${chd.error}</p>`; return; }
  const ok   = (chd.results || []).filter(r => r.success);
  const fail = (chd.results || []).filter(r => !r.success && r.error);
  const skip = (chd.results || []).filter(r => !r.success && !r.error);
  let html = `<div style="margin-bottom:12px">
    ${_rptStat('rpt-ok',   ok.length   + ' convertidos')}
    ${fail.length ? _rptStat('rpt-bad', fail.length + ' fallidos') : ''}
    ${skip.length ? _rptStat('rpt-info', skip.length + ' omitidos') : ''}
    ${chd.dry_run ? '<span style="color:#569cd6;font-size:11px">[DRY RUN]</span>' : ''}
  </div>`;
  if (fail.length) {
    html += '<p style="color:#f44747;font-size:12px;margin-bottom:8px">Fallos de conversión:</p>';
    html += '<div style="max-height:350px;overflow-y:auto">';
    html += fail.map(r => `<div style="padding:3px 0;border-bottom:1px solid #1e1e2e">
      <strong style="color:#d4d4d4;font-size:12px">${r.cue}</strong>
      <em style="display:block;color:#f44747;font-size:11px;margin-top:2px">${r.error}</em>
    </div>`).join('');
    html += '</div>';
  }
  el.innerHTML = html;
}

function exportReportHtml() {
  if (!_reportData) return;
  const d = _reportData;
  const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const lines = [
    `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Informe Biblioteca — ${ts}</title>`,
    `<style>body{font-family:monospace;background:#0f0f0f;color:#d4d4d4;padding:20px;font-size:13px}`,
    `h1{color:#4ec9b0}h2{color:#888;border-bottom:1px solid #333;padding-bottom:4px}`,
    `.ok{color:#4ec9b0}.warn{color:#ce9178}.bad{color:#f44747}.dim{color:#555}</style></head><body>`,
    `<h1>Informe de biblioteca</h1><p class="dim">Generado: ${ts} | Ruta: ${d.source_path}</p>`,
    `<h2>ZIPs (${d.zips.total})</h2>`,
    d.zips.files.filter(f => !f.is_disc_set).map(f => `<div>${f.path} <span class="dim">(${fmtSize(f.size_bytes)})</span></div>`).join('') || '<p class="ok">Sin ZIPs pendientes</p>',
    `<h2>Playlists M3U</h2>`,
    d.playlists.groups.map(g => `<div>${g.m3u_exists ? '<span class="ok">✓</span>' : '<span class="warn">⚠</span>'} ${g.base_name} (${g.disc_count} discos)</div>`).join('') || '<p class="ok">Sin grupos multi-disco</p>',
    `<h2>Sets multi-disco — problemas (${d.multidisc.groups_with_issues})</h2>`,
    d.multidisc.issues.map(i => `<div class="bad">${i.base_name}: ${i.detail}</div>`).join('') || '<p class="ok">Todos los sets completos</p>',
    `<h2>Saves huérfanos (${d.orphans.total}) — ${fmtSize(d.orphans.total_bytes)}</h2>`,
    d.orphans.saves.map(s => `<div class="warn">${s.path}</div>`).join('') || '<p class="ok">Sin saves huérfanos</p>',
    `</body></html>`,
  ];
  const blob = new Blob([lines.join('\n')], {type: 'text/html;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `informe-biblioteca-${ts.replace(/[: ]/g,'-')}.html`;
  a.click();
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(msg, type='ok', duration=3000) {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity='0'; t.style.transition='opacity .3s'; setTimeout(() => t.remove(), 320); }, duration);
}

// ── Init ─────────────────────────────────────────────────────────────────────
_initColPicker();
loadOverview();
</script>
<div id="toast-container"></div>
</body>
</html>
"""
