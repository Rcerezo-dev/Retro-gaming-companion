from __future__ import annotations

import html
from pathlib import Path


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    if n < 1024 ** 3:
        return f"{n / 1024 ** 2:.1f} MB"
    return f"{n / 1024 ** 3:.2f} GB"


def _h(s: object) -> str:
    return html.escape(str(s))


# ── Per-section renderers ──────────────────────────────────────────────────────

def _render_multidisc(rpt: dict) -> str:
    pl = rpt.get("playlists", {})
    md = rpt.get("multidisc", {})
    groups = pl.get("groups", [])
    issues = md.get("issues", [])

    rows_ok = []
    rows_missing = []
    for g in groups:
        if g["m3u_exists"]:
            rows_ok.append(
                f"<tr><td>{_h(g['base_name'])}</td>"
                f"<td>{_h(g['disc_count'])}</td>"
                f"<td style='color:#4ec9b0'>{_h(g['m3u_name'])}</td></tr>"
            )
        else:
            rows_missing.append(
                f"<tr><td>{_h(g['base_name'])}</td>"
                f"<td>{_h(g['disc_count'])}</td>"
                f"<td style='color:#f44747'>Falta</td></tr>"
            )

    issues_html = ""
    if issues:
        issue_rows = "".join(
            f"<tr><td>{_h(i['base_name'])}</td><td>{_h(i['issue_type'])}</td>"
            f"<td>{_h(i['detail'])}</td></tr>"
            for i in issues
        )
        issues_html = f"""
        <h3 style="color:#f44747">Problemas detectados ({len(issues)})</h3>
        <table><thead><tr><th>Set</th><th>Tipo</th><th>Detalle</th></tr></thead>
        <tbody>{issue_rows}</tbody></table>"""

    table_ok = ""
    if rows_ok:
        table_ok = f"""
        <h3 style="color:#4ec9b0">Con playlist .m3u ({len(rows_ok)})</h3>
        <table><thead><tr><th>Nombre base</th><th>Discos</th><th>Archivo M3U</th></tr></thead>
        <tbody>{"".join(rows_ok)}</tbody></table>"""

    table_missing = ""
    if rows_missing:
        table_missing = f"""
        <h3 style="color:#f44747">Sin playlist .m3u ({len(rows_missing)})</h3>
        <table><thead><tr><th>Nombre base</th><th>Discos</th><th>Estado</th></tr></thead>
        <tbody>{"".join(rows_missing)}</tbody></table>"""

    summary = (f"<p><strong>{pl.get('total_groups', 0)}</strong> sets multi-disco — "
               f"<span style='color:#4ec9b0'>{pl.get('with_m3u', 0)} con M3U</span> / "
               f"<span style='color:#f44747'>{pl.get('without_m3u', 0)} sin M3U</span></p>")

    return summary + issues_html + table_missing + table_ok


def _render_orphans(rpt: dict) -> str:
    orphan_data = rpt.get("orphans", {})
    saves = orphan_data.get("saves", [])
    if not saves:
        return "<p style='color:#4ec9b0'>No hay saves huérfanos. ✓</p>"

    rows = "".join(
        f"<tr><td>{_h(s['path'])}</td><td>{_h(s['extension'])}</td>"
        f"<td>{_h(_fmt_bytes(s['size_bytes']))}</td></tr>"
        for s in saves
    )
    return (
        f"<p><strong>{orphan_data.get('total', 0)}</strong> saves huérfanos — "
        f"{_h(_fmt_bytes(orphan_data.get('total_bytes', 0)))} total</p>"
        f"<table><thead><tr><th>Ruta</th><th>Extensión</th><th>Tamaño</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _render_health(rpt: dict) -> str:
    hc = rpt.get("health_check", {})
    if not hc:
        return ("<p style='color:#888'>No hay datos de Health Check. "
                "Ejecuta <strong>Health Check</strong> en la pestaña Tools primero.</p>")

    issues = [r for r in hc.get("results", []) if r.get("status") != "ok"]
    ok_count = hc.get("total", 0) - len(issues)

    if not issues:
        return (f"<p style='color:#4ec9b0'>{hc.get('total', 0)} ROMs verificadas — "
                "todas OK. ✓</p>")

    rows = "".join(
        f"<tr><td>{_h(r.get('filename', ''))}</td>"
        f"<td>{_h(r.get('platform', ''))}</td>"
        f"<td style='color:#f44747'>{_h(r.get('status', ''))}</td>"
        f"<td style='font-family:monospace;font-size:11px'>{_h(r.get('stored_sha1', ''))}</td>"
        f"<td style='font-family:monospace;font-size:11px'>{_h(r.get('current_sha1', ''))}</td></tr>"
        for r in issues
    )
    return (
        f"<p><strong>{hc.get('total', 0)}</strong> ROMs verificadas — "
        f"<span style='color:#4ec9b0'>{ok_count} OK</span> / "
        f"<span style='color:#f44747'>{len(issues)} con problema</span></p>"
        f"<table><thead><tr><th>Archivo</th><th>Plataforma</th><th>Estado</th>"
        f"<th>SHA1 almacenado</th><th>SHA1 actual</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _render_ra_missing(rpt: dict) -> str:
    ra = rpt.get("retroachievements", {})
    if not ra or "results" not in ra:
        return ("<p style='color:#888'>No hay datos de RetroAchievements. "
                "Ejecuta <strong>Comprobar RA</strong> en la pestaña Tools primero.</p>")

    alternatives = [r for r in ra.get("results", []) if r.get("status") == "no_support_alternative"]
    if not alternatives:
        return ("<p style='color:#4ec9b0'>No se encontraron versiones sin logros que tengan "
                "una alternativa con logros en RA. ✓</p>")

    rows = "".join(
        f"<tr>"
        f"<td>{_h(r.get('platform', ''))}</td>"
        f"<td>{_h(r.get('original_filename', ''))}</td>"
        f"<td style='font-family:monospace;font-size:11px'>{_h(r.get('our_md5', ''))}</td>"
        f"<td>{_h(r.get('ra_title', ''))}</td>"
        f"<td style='color:#4ec9b0'>{_h(r.get('ra_achievements', ''))}</td>"
        f"</tr>"
        for r in alternatives
    )
    return (
        f"<p><strong>{len(alternatives)}</strong> juegos sin soporte RA pero con versión alternativa disponible.</p>"
        f"<p style='color:#888;font-size:12px'>La columna <em>MD5 nuestro</em> es el hash de tu ROM. "
        "El título RA y sus logros corresponden a la versión con soporte.</p>"
        f"<table><thead><tr><th>Plataforma</th><th>Tu archivo</th><th>MD5 nuestro</th>"
        f"<th>Título en RA</th><th>Logros disponibles</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _render_chd(rpt: dict) -> str:
    chd_data = rpt.get("chd", {})
    # chd_data comes from _job_results["convert_chd"] — may be empty if not run
    if not chd_data or not chd_data.get("converted") and not chd_data.get("skipped"):
        # Fall back to scanning for .cue files manually using ZIPs data
        zips = rpt.get("zips", {})
        disc_zips = [z for z in zips.get("files", []) if z.get("is_disc_set")]
        if not disc_zips:
            return ("<p style='color:#888'>No hay datos de conversión CHD. "
                    "Ejecuta <strong>Convertir a CHD</strong> en la pestaña Tools para ver el estado.</p>")
        rows = "".join(
            f"<tr><td>{_h(z['name'])}</td><td>{_h(_fmt_bytes(z['size_bytes']))}</td></tr>"
            for z in disc_zips
        )
        return (
            f"<p><strong>{len(disc_zips)}</strong> sets de disco encontrados como ZIP (candidatos a CHD).</p>"
            f"<table><thead><tr><th>Archivo</th><th>Tamaño</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    converted = chd_data.get("converted", 0)
    skipped = chd_data.get("skipped", 0)
    errors_list = chd_data.get("errors", [])
    return (
        f"<p><span style='color:#4ec9b0'>{converted} convertidos a CHD</span> / "
        f"<span style='color:#888'>{skipped} omitidos (ya existen)</span> / "
        f"<span style='color:#f44747'>{len(errors_list)} errores</span></p>"
        + (
            "<h3 style='color:#f44747'>Errores</h3><ul>" +
            "".join(f"<li>{_h(e)}</li>" for e in errors_list) + "</ul>"
            if errors_list else ""
        )
    )


# ── Main HTML generator ────────────────────────────────────────────────────────

def generate_html_report(rpt: dict) -> str:
    source_path = _h(rpt.get("source_path", ""))

    tabs = [
        ("multidisc", "Multi-disco", _render_multidisc(rpt)),
        ("orphans",   "Saves huérfanos", _render_orphans(rpt)),
        ("health",    "Health Check", _render_health(rpt)),
        ("ra",        "Logros faltantes", _render_ra_missing(rpt)),
        ("chd",       "CHD pendientes", _render_chd(rpt)),
    ]

    tab_buttons = "".join(
        f'<button class="tab-btn" onclick="showTab(\'{tid}\')" id="btn-{tid}">{_h(label)}</button>'
        for tid, label, _ in tabs
    )
    tab_panels = "".join(
        f'<div class="tab-panel" id="panel-{tid}">{content}</div>'
        for tid, _, content in tabs
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Informe de biblioteca — ROM Manager</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #1e1e2e; color: #d4d4d4; font-size: 14px; }}
  header {{ background: #252537; padding: 16px 24px; border-bottom: 1px solid #3a3a5c; }}
  header h1 {{ font-size: 18px; color: #c9bcf5; font-weight: 600; }}
  header p {{ color: #888; font-size: 12px; margin-top: 4px; }}
  .tabs {{ display: flex; gap: 2px; padding: 12px 24px 0; background: #252537; border-bottom: 1px solid #3a3a5c; flex-wrap: wrap; }}
  .tab-btn {{ background: transparent; border: none; color: #888; padding: 8px 16px; cursor: pointer; font: inherit; font-size: 13px; border-bottom: 2px solid transparent; transition: color .15s; }}
  .tab-btn:hover {{ color: #d4d4d4; }}
  .tab-btn.active {{ color: #c9bcf5; border-bottom-color: #7c5cbf; }}
  .tab-panel {{ display: none; padding: 24px; max-width: 1200px; }}
  .tab-panel.active {{ display: block; }}
  h3 {{ font-size: 13px; font-weight: 600; margin: 20px 0 8px; }}
  p {{ margin: 8px 0; line-height: 1.5; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 13px; }}
  thead tr {{ background: #2d2d44; }}
  th {{ padding: 6px 10px; text-align: left; color: #888; font-weight: 500; font-size: 11px; text-transform: uppercase; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #2a2a3e; word-break: break-all; }}
  tr:hover td {{ background: #252537; }}
  strong {{ color: #e0e0e0; }}
</style>
</head>
<body>
<header>
  <h1>Informe de salud de biblioteca</h1>
  <p>Ruta: {source_path}</p>
</header>
<nav class="tabs">{tab_buttons}</nav>
{tab_panels}
<script>
function showTab(id) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  document.getElementById('btn-' + id).classList.add('active');
}}
showTab('{tabs[0][0]}');
</script>
</body>
</html>"""
