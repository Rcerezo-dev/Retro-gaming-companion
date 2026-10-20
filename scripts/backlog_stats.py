"""Resumen del backlog partido (Tareas/backlog/*.md + hecho/). Solo stdlib.

Uso: python scripts/backlog_stats.py [--detalle]
Una sección ``###`` es 'hecho' si todas sus celdas de estado empiezan por ✅,
'pendiente' si alguna no, y 'revisar' si no tiene tabla de estado (prosa).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "Tareas" / "backlog"
_EMOJI = re.compile(r"^(✅|⬜|⏳|🔴|🟡|🔲|❌|⚠️|🚫)")
_SEP = re.compile(r"^\|[\s\-|:]+\|$")


def sections(text: str):
    """Devuelve [(título, líneas)] de las secciones ``###`` (ignora bloques de código)."""
    out, cur, fence = [], None, False
    for line in text.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("### "):
            cur = (line[4:], [])
            out.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return out


def classify(lines: list[str]) -> tuple[str, int, int]:
    """(estado, filas ✅, filas no ✅) de una sección."""
    done = todo = 0
    for line in lines:
        if line.startswith("|") and not _SEP.match(line):
            for c in (x.strip() for x in line.strip().strip("|").split("|")):
                if _EMOJI.match(c):
                    done, todo = (done + 1, todo) if c.startswith("✅") else (done, todo + 1)
    if not done and not todo:
        return "revisar", 0, 0
    return ("pendiente" if todo else "hecho"), done, todo


def main(argv: list[str]) -> int:
    if not ROOT.is_dir():
        print(f"No existe {ROOT}", file=sys.stderr)
        return 1
    rows, pend = [], []
    for f in sorted(ROOT.glob("*.md")) + sorted((ROOT / "hecho").glob("*.md")):
        hecho_dir = f.parent.name == "hecho"
        n = {"hecho": 0, "pendiente": 0, "revisar": 0}
        d = t = 0
        for title, lines in sections(f.read_text(encoding="utf-8")):
            st, a, b = classify(lines)
            n["hecho" if hecho_dir else st] += 1
            d, t = d + a, t + b
            if st == "pendiente" and not hecho_dir:
                pend.append((f.stem, title, b))
        rows.append((("hecho/" if hecho_dir else "") + f.stem, n, d, t))
    print(f"{'archivo':34} {'hecho':>5} {'pend.':>5} {'revisar':>7} {'filas ✅':>9} {'filas abiertas':>14}")
    for name, n, d, t in rows:
        print(f"{name:34} {n['hecho']:5} {n['pendiente']:5} {n['revisar']:7} {d:9} {t:14}")
    tot = [sum(r[1][k] for r in rows) for k in ("hecho", "pendiente", "revisar")]
    print(f"\nTOTAL secciones: {tot[0]} hechas, {tot[1]} pendientes, {tot[2]} por revisar")
    if "--detalle" in argv:
        print("\nPendientes (sección — filas abiertas):")
        for stem, title, b in sorted(pend, key=lambda x: -x[2]):
            print(f"  [{stem}] {title[:90]} — {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
