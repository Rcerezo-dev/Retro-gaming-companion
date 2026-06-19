from __future__ import annotations

import html


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.1f} KB"
    if n < 1024**3:
        return f"{n / 1024**2:.1f} MB"
    return f"{n / 1024**3:.2f} GB"


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
            f"<tr><td>{_h(i.get('platform', ''))}</td><td>{_h(i['base_name'])}</td>"
            f"<td>{_h(i['issue_type'])}</td><td>{_h(i['detail'])}</td></tr>"
            for i in issues
        )
        issues_html = f"""
        <h3 style="color:#f44747">Problemas detectados ({len(issues)})</h3>
        <table><thead><tr><th>Plataforma</th><th>Set</th><th>Tipo</th><th>Detalle</th></tr></thead>
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

    summary = (
        f"<p><strong>{pl.get('total_groups', 0)}</strong> sets multi-disco — "
        f"<span style='color:#4ec9b0'>{pl.get('with_m3u', 0)} con M3U</span> / "
        f"<span style='color:#f44747'>{pl.get('without_m3u', 0)} sin M3U</span></p>"
    )

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
        return (
            "<p style='color:#888'>No hay datos de Health Check. "
            "Ejecuta <strong>Health Check</strong> en la pestaña Tools primero.</p>"
        )

    issues = [r for r in hc.get("results", []) if r.get("status") != "ok"]
    ok_count = hc.get("total", 0) - len(issues)

    if not issues:
        return f"<p style='color:#4ec9b0'>{hc.get('total', 0)} ROMs verificadas — todas OK. ✓</p>"

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
    # The RA check job stores results under "alternatives" (not "results")
    alternatives = ra.get("alternatives") if ra else None
    if not ra or alternatives is None:
        return (
            "<p style='color:#888'>No hay datos de RetroAchievements. "
            "Ejecuta <strong>Comprobar RA</strong> en la pestaña Tools primero.</p>"
        )

    if not alternatives:
        total = ra.get("total", 0)
        supported = ra.get("supported", 0)
        return (
            f"<p style='color:#4ec9b0'>No se encontraron versiones sin logros que tengan "
            f"una alternativa en RA. ✓</p>"
            f"<p style='color:#888;font-size:12px'>{total} juegos verificados — "
            f"{supported} con soporte de logros.</p>"
        )

    # Field "filename" in job result (not "original_filename")
    def _ra_row(r: dict) -> str:
        ra_id = _h(r.get("ra_id", ""))
        title = _h(r.get("ra_title", ""))
        plat = _h(r.get("platform", ""))
        fname = _h(r.get("filename") or r.get("original_filename", ""))
        md5 = _h(r.get("our_md5", ""))
        logros = _h(r.get("ra_achievements", ""))
        link = f"https://retroachievements.org/game/{ra_id}" if ra_id else "#"
        return (
            f"<tr>"
            f"<td>{plat}</td>"
            f"<td>{fname}</td>"
            f"<td style='font-family:monospace;font-size:11px'>{md5}</td>"
            f"<td><a href='{link}' target='_blank' style='color:#569cd6'>{title}</a></td>"
            f"<td style='color:#4ec9b0'>{logros}</td>"
            f"</tr>"
        )

    rows = "".join(_ra_row(r) for r in alternatives)
    total = ra.get("total", 0)
    no_alt = ra.get("no_support_alternative", len(alternatives))
    note = f" (mostrando {len(alternatives)} de {no_alt})" if len(alternatives) < no_alt else ""
    return (
        f"<p><strong>{no_alt}</strong> juegos sin soporte RA con versión alternativa disponible{note}.</p>"
        f"<p style='color:#888;font-size:12px'>La columna <em>MD5 nuestro</em> es el hash de tu ROM. "
        "El título RA y sus logros corresponden a la versión con soporte. Haz click en el título para ir a RA.</p>"
        f"<table><thead><tr><th>Plataforma</th><th>Tu archivo</th><th>MD5 nuestro</th>"
        f"<th>Título en RA</th><th>Logros disponibles</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _render_chd(rpt: dict) -> str:
    chd_data = rpt.get("chd", {})
    # chd_data comes from the convert_chd job result — may be empty if not run
    if not chd_data or not chd_data.get("converted") and not chd_data.get("skipped"):
        # Fall back to scanning for .cue files manually using ZIPs data
        zips = rpt.get("zips", {})
        disc_zips = [z for z in zips.get("files", []) if z.get("is_disc_set")]
        if not disc_zips:
            return (
                "<p style='color:#888'>No hay datos de conversión CHD. "
                "Ejecuta <strong>Convertir a CHD</strong> en la pestaña Tools para ver el estado.</p>"
            )
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
            "<h3 style='color:#f44747'>Errores</h3><ul>"
            + "".join(f"<li>{_h(e)}</li>" for e in errors_list)
            + "</ul>"
            if errors_list
            else ""
        )
    )


# ── Main HTML generator ────────────────────────────────────────────────────────


def generate_html_report(rpt: dict) -> str:
    source_path = _h(rpt.get("source_path", ""))
    gen_time = rpt.get("generated_at", "")

    tabs = [
        ("multidisc", "🎮 Multi-disco", _render_multidisc(rpt)),
        ("orphans", "💾 Saves huérfanos", _render_orphans(rpt)),
        ("health", "🔍 Health Check", _render_health(rpt)),
        ("ra", "🏆 Logros (RA)", _render_ra_missing(rpt)),
        ("chd", "💿 CHD pendientes", _render_chd(rpt)),
    ]

    sidebar_items = "".join(
        f'<button class="nav-btn" onclick="showTab(\'{tid}\')" id="btn-{tid}">{_h(label)}</button>'
        for tid, label, _ in tabs
    )
    tab_panels = "".join(
        f'<div class="tab-panel" id="panel-{tid}">'
        f'<h2 style="font-size:16px;font-weight:600;color:#c9bcf5;margin-bottom:20px">{_h(label)}</h2>'
        f"{content}</div>"
        for tid, label, content in tabs
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Informe de biblioteca — ROM Manager</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #1a1a2e; color: #d4d4d4; font-size: 14px; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
  header {{ background: #252537; padding: 14px 24px; border-bottom: 1px solid #3a3a5c; flex-shrink: 0; }}
  header h1 {{ font-size: 17px; color: #c9bcf5; font-weight: 600; }}
  header p {{ color: #666; font-size: 11px; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .layout {{ display: flex; flex: 1; overflow: hidden; }}
  .sidebar {{ width: 200px; background: #252537; border-right: 1px solid #3a3a5c; padding: 12px 0; flex-shrink: 0; overflow-y: auto; }}
  .nav-btn {{ display: block; width: 100%; background: none; border: none; text-align: left; color: #888; padding: 10px 18px; cursor: pointer; font: inherit; font-size: 13px; border-left: 3px solid transparent; transition: color .15s, background .15s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .nav-btn:hover {{ color: #d4d4d4; background: #2d2d44; }}
  .nav-btn.active {{ color: #c9bcf5; border-left-color: #7c5cbf; background: #2d2d44; font-weight: 500; }}
  .content {{ flex: 1; overflow-y: auto; padding: 0; }}
  .tab-panel {{ display: none; padding: 28px 32px; max-width: 1100px; }}
  .tab-panel.active {{ display: block; }}
  h2 {{ font-size: 16px; font-weight: 600; color: #c9bcf5; margin-bottom: 20px; }}
  h3 {{ font-size: 13px; font-weight: 600; margin: 20px 0 8px; }}
  p {{ margin: 8px 0; line-height: 1.5; }}
  a {{ color: #569cd6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 13px; }}
  thead tr {{ background: #2d2d44; position: sticky; top: 0; z-index: 1; }}
  th {{ padding: 6px 10px; text-align: left; color: #888; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #2a2a3e; word-break: break-all; }}
  tr:hover td {{ background: #252537; }}
  strong {{ color: #e0e0e0; }}
  li {{ margin: 4px 0; }}
</style>
</head>
<body>
<header>
  <h1>Informe de salud de biblioteca</h1>
  <p>Ruta: {source_path}{f" &nbsp;·&nbsp; Generado: {_h(gen_time)}" if gen_time else ""}</p>
</header>
<div class="layout">
  <nav class="sidebar">{sidebar_items}</nav>
  <div class="content">{tab_panels}</div>
</div>
<script>
function showTab(id) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  document.getElementById('btn-' + id).classList.add('active');
}}
showTab('{tabs[0][0]}');
</script>
</body>
</html>"""
