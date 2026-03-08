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
  .btn { background: #1e1e2e; border: 1px solid #4ec9b0; color: #4ec9b0; padding: 6px 14px; border-radius: 4px; cursor: pointer; font: inherit; font-size: 13px; }
  .btn:hover { background: #4ec9b0; color: #0f0f0f; }
  .btn.danger { border-color: #f44747; color: #f44747; }
  .btn.danger:hover { background: #f44747; color: #0f0f0f; }

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
  .badge.conflict { background: #3a2a1a; color: #ce9178; }

  .config-grid { display: grid; grid-template-columns: auto 1fr; gap: 6px 16px; font-size: 13px; background: #1e1e2e; border: 1px solid #333; border-radius: 6px; padding: 14px 16px; margin-top: 16px; max-width: 600px; }
  .config-grid .cfg-key { color: #888; }
  .config-grid .cfg-val { color: #d4d4d4; }
  .config-grid .cfg-val.missing { color: #555; font-style: italic; }

  .dup-group { background: #1e1e2e; border: 1px solid #333; border-radius: 6px; margin-bottom: 12px; padding: 14px 16px; }
  .dup-group .title { color: #4ec9b0; margin-bottom: 8px; }
  .dup-group .entry { color: #888; font-size: 12px; padding: 2px 0; }
  .dup-group .entry span { color: #d4d4d4; }

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
  <button onclick="showTab('sync')">Sync</button>
</nav>

<main>

<!-- OVERVIEW -->
<div id="tab-overview" class="tab active">
  <div id="overview-cards" class="cards"><p class="loading">Loading…</p></div>
</div>

<!-- GAMES -->
<div id="tab-games" class="tab">
  <div class="toolbar">
    <input id="games-search" type="text" placeholder="Search title or filename…" oninput="filterGames()">
    <select id="games-platform" onchange="filterGames()"><option value="">All platforms</option></select>
    <select id="games-matched" onchange="filterGames()">
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
</div>

<!-- PLAN -->
<div id="tab-plan" class="tab">
  <div id="plan-content"><p class="loading">Loading…</p></div>
</div>

<!-- DUPLICATES -->
<div id="tab-duplicates" class="tab">
  <div id="dup-content"><p class="loading">Loading…</p></div>
</div>

<!-- SYNC -->
<div id="tab-sync" class="tab">
  <div id="sync-content"><p class="loading">Loading…</p></div>
</div>

</main>

<script>
"use strict";

let allGames = [];

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.currentTarget.classList.add('active');
  if (name === 'overview') loadOverview();
  if (name === 'games')    loadGames();
  if (name === 'plan')     loadPlan();
  if (name === 'duplicates') loadDuplicates();
  if (name === 'sync')       loadSync();
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

// ── Overview ─────────────────────────────────────────────────────────────────
async function loadOverview() {
  const el = document.getElementById('overview-cards');
  try {
    const [d, cfg] = await Promise.all([apiFetch('/api/status'), apiFetch('/api/config')]);
    const matchPct = d.total_games > 0 ? Math.round(d.matched_games / d.total_games * 100) : 0;
    const cfgHtml = `
      <div class="config-grid" style="margin-top:24px">
        <span class="cfg-key">saves_dir</span>
        <span class="cfg-val ${cfg.saves_dir ? '' : 'missing'}">${cfg.saves_dir || '(not set)'}</span>
        <span class="cfg-key">rclone remote</span>
        <span class="cfg-val ${cfg.rclone_remote ? '' : 'missing'}">${cfg.rclone_remote || '(not set)'}</span>
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

// ── Games ────────────────────────────────────────────────────────────────────
async function loadGames() {
  if (allGames.length > 0) { filterGames(); return; }
  const tbody = document.getElementById('games-tbody');
  tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading…</td></tr>';
  try {
    const d = await apiFetch('/api/games');
    allGames = d.games;
    // Populate platform filter
    const platforms = [...new Set(allGames.map(g => g.platform || 'Unknown'))].sort();
    const sel = document.getElementById('games-platform');
    platforms.forEach(p => { const o = document.createElement('option'); o.value = p; o.text = p; sel.add(o); });
    filterGames();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" class="error-msg">${e.message}</td></tr>`;
  }
}

function filterGames() {
  const q = document.getElementById('games-search').value.toLowerCase();
  const plat = document.getElementById('games-platform').value;
  const mf = document.getElementById('games-matched').value;
  let rows = allGames.filter(g => {
    if (plat && (g.platform || 'Unknown') !== plat) return false;
    if (mf === 'matched' && !g.canonical_title) return false;
    if (mf === 'unmatched' && g.canonical_title) return false;
    if (q && !((g.canonical_title||'').toLowerCase().includes(q) || g.original_filename.toLowerCase().includes(q))) return false;
    return true;
  });
  document.getElementById('games-count').textContent = rows.length + ' game' + (rows.length !== 1 ? 's' : '');
  const tbody = document.getElementById('games-tbody');
  const empty = document.getElementById('games-empty');
  if (rows.length === 0) { tbody.innerHTML = ''; empty.style.display = ''; return; }
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

// ── Plan ─────────────────────────────────────────────────────────────────────
async function loadPlan() {
  const el = document.getElementById('plan-content');
  try {
    const d = await apiFetch('/api/plan');
    if (d.total === 0) { el.innerHTML = '<p class="empty">No matched games found. Run <code>rommgr match</code> first.</p>'; return; }
    let html = '';
    if (d.pending.length) {
      html += `<h3 style="color:#569cd6;margin-bottom:12px">Pending renames — ${d.pending.length}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>Platform</th><th>From</th><th>To</th></tr></thead><tbody>';
      html += d.pending.map(op => `<tr><td>${op.platform||''}</td><td title="${op.source}">${op.source_name}</td><td style="color:#4ec9b0" title="${op.target}">${op.target_name}</td></tr>`).join('');
      html += '</tbody></table></div>';
    }
    if (d.conflicts.length) {
      html += `<h3 style="color:#f44747;margin:20px 0 12px">Conflicts — ${d.conflicts.length}</h3>`;
      html += '<div style="overflow-x:auto"><table><thead><tr><th>From</th><th>To (blocked)</th></tr></thead><tbody>';
      html += d.conflicts.map(op => `<tr><td>${op.source_name}</td><td style="color:#f44747">${op.target_name}</td></tr>`).join('');
      html += '</tbody></table></div>';
    }
    if (d.already_correct > 0) {
      html += `<p style="color:#555;margin-top:16px">${d.already_correct} file(s) already have the correct name.</p>`;
    }
    html += `<p style="margin-top:20px;color:#555">Run <code>rommgr apply</code> in the terminal to execute the renames.</p>`;
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
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
      <div class="dup-group">
        <div class="title">${g.canonical_title || '(unmatched)'}
          <span style="color:#555;font-size:11px;margin-left:8px">${g.platform||''} · SHA1: ${g.sha1.slice(0,12)}…</span>
        </div>
        ${g.entries.map(e => `<div class="entry"><span>${e.source_path}</span>  <span style="color:#555">${fmtSize(e.size_bytes)}</span></div>`).join('')}
      </div>`).join('');
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Sync ──────────────────────────────────────────────────────────────────────
async function loadSync() {
  const el = document.getElementById('sync-content');
  try {
    const [sl, cfg] = await Promise.all([apiFetch('/api/sync-log'), apiFetch('/api/config')]);
    let html = '';
    // Config info
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
      const msg = e.message ? `<span style="color:#888">${e.message}</span>` : '';
      const date = e.created_at ? e.created_at.replace('T', ' ') : '';
      return `<tr><td>${date}</td><td>${dirBadge}</td><td>${resBadge}</td><td title="${e.local_path}">${e.local_path.split(/[\\/]/).pop()}</td><td title="${e.remote_path}">${e.remote_path}</td><td>${msg}</td></tr>`;
    }).join('');
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<p class="error-msg">${e.message}</p>`;
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
loadOverview();
</script>
</body>
</html>
"""
