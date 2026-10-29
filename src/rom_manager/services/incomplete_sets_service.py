"""PRUNE-INCOMPLETE-1 — detectar sets de disco incompletos y listar los juegos que no funcionaban.

Lógica pura sobre un listado ``{ruta_relativa: tamaño}`` y una función de lectura de texto:
sirve igual para una carpeta local y para la consola por ADB (quien llama aporta el listado).
No toca el disco: devuelve un plan; aplicar el plan (descartar/borrar) es cosa del llamador.

Reglas (una ruta es relativa a la carpeta de la plataforma, separador ``/``):

* Un ``.cue`` con algún ``FILE`` inexistente es un set incompleto (solo cuenta el nombre base,
  como ``converters.chd_converter.parse_bins_from_cue``).
* Si lo que falta existe en otra carpeta, el set es *reparable*: NO se descarta, se informa.
* Un ``.m3u`` con alguna entrada inexistente es una lista rota.
* Una pista ``(Track N).bin`` que ningún ``.cue`` referencia es un resto huérfano.
* Un ``.chd`` vacío, sin firma o truncado (``chd_problem``) es inservible y se retira.
* Lo reparable no se descarta: ``apply_repairs`` mueve las pistas encontradas junto a su ``.cue``
  y regenera el ``.cue`` de los juegos completos que lo han perdido.
* Un set incompleto «perdido» es el que no tiene otra copia que funcione del mismo juego
  y región (``.chd``, ``.cue`` completo o ``.bin`` suelto): esos van a la lista de juegos perdidos.
"""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.services.library_fs import LibraryFS

from rom_manager.sync.chd_header import CHD_V5_HEADER_SIZE, chd_problem

_TRACK_BIN = re.compile(r" \(Track \d+\)\.bin$", re.IGNORECASE)
_FILE_LINE = re.compile(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))', re.IGNORECASE)
_TITLE_REGION = re.compile(r"^(.*?)\s*(\([^)]*\))")
_PLAYABLE_EXT = (".chd", ".iso", ".pbp", ".ecm", ".img", ".mdf")


@dataclass(slots=True)
class IncompleteSet:
    cue: str
    missing: list[str]
    present: list[str]
    recoverable: bool  # lo que falta existe en otro sitio del árbol
    has_alternative: bool  # otra copia que funciona del mismo juego y región
    size_bytes: int = 0


@dataclass(slots=True)
class IncompletePlan:
    sets: list[IncompleteSet] = field(default_factory=list)
    broken_m3u: list[tuple[str, list[str]]] = field(default_factory=list)
    orphan_tracks: list[str] = field(default_factory=list)
    rebuildable: dict[str, list[str]] = field(default_factory=dict)
    bad_chds: list[tuple[str, str]] = field(default_factory=list)  # (ruta, motivo)
    repairs: list[tuple[str, str]] = field(default_factory=list)  # (origen, destino) junto al .cue
    keep: frozenset[str] = frozenset()
    sizes: Mapping[str, int] = field(default_factory=dict)

    @property
    def to_remove(self) -> list[str]:
        """Rutas a descartar: sets irreparables (cue + pistas presentes), m3u rotas y huérfanas."""
        out: list[str] = []
        for s in self.sets:
            if not s.recoverable:
                out.append(s.cue)
                out.extend(s.present)
        out.extend(m for m, _ in self.broken_m3u)
        out.extend(self.orphan_tracks)
        out.extend(p for p, _ in self.bad_chds)
        return [p for p in dict.fromkeys(out) if p not in self.keep]

    @property
    def bytes_to_remove(self) -> int:
        return sum(self.sizes.get(p, 0) for p in self.to_remove)

    @property
    def lost_games(self) -> list[IncompleteSet]:
        return [s for s in self.sets if not s.recoverable and not s.has_alternative]


def _referenced(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        m = _FILE_LINE.match(line)
        if m:
            names.append((m.group(1) or m.group(2)).replace("\\", "/").rsplit("/", 1)[-1])
    return names


def game_key(path: str) -> str:
    """Título + región (primer paréntesis) en minúsculas: ignora disco, revisión y pista."""
    stem = posixpath.basename(path).rsplit(".", 1)[0]
    stem = re.sub(r"\s*\[[^\]]*\]", "", stem)
    m = _TITLE_REGION.match(stem)
    title, region = (m.group(1), m.group(2)) if m else (stem, "")
    return f"{title} {region}".strip().lower()


def plan_incomplete(
    files: Mapping[str, int],
    read_text: Callable[[str], str],
    read_head: Callable[[str, int], bytes] | None = None,
) -> IncompletePlan:
    by_name: dict[str, list[str]] = defaultdict(list)
    for f in files:
        by_name[posixpath.basename(f)].append(f)

    plan = IncompletePlan(sizes=files)
    complete_cues: set[str] = set()
    complete_claimed: set[str] = set()
    claimed: set[str] = set()
    pending: list[tuple[str, list[str], list[str]]] = []

    for f in sorted(files):
        if not f.lower().endswith(".cue"):
            continue
        folder = posixpath.dirname(f)
        refs = _referenced(read_text(f))
        present = [posixpath.join(folder, r) for r in refs if posixpath.join(folder, r) in files]
        missing = [r for r in refs if posixpath.join(folder, r) not in files]
        claimed.update(present)
        if refs and not missing:
            complete_cues.add(f)
            complete_claimed.update(present)
        else:
            pending.append((f, present, missing or ["(el .cue no referencia ningún archivo)"]))

    playable_keys = {game_key(f) for f in files if f.lower().endswith(_PLAYABLE_EXT)}
    playable_keys |= {game_key(c) for c in complete_cues}
    playable_keys |= {
        game_key(f)
        for f in files
        if f.lower().endswith(".bin") and not _TRACK_BIN.search(f) and f not in claimed
    }

    protected: set[str] = set()
    for cue, present, missing in pending:
        found = [m for m in missing if m in by_name and all(p not in present for p in by_name[m])]
        recoverable = bool(missing) and len(found) == len(missing)
        if recoverable:
            for m in found:
                protected.update(by_name[m])
                dst = posixpath.join(posixpath.dirname(cue), m)
                # sin ambigüedad (un solo candidato) y sin que otro .cue ya lo haya pedido
                if len(by_name[m]) == 1 and all(by_name[m][0] != r[0] for r in plan.repairs):
                    plan.repairs.append((by_name[m][0], dst))
        plan.sets.append(
            IncompleteSet(
                cue=cue,
                missing=missing,
                present=present,
                recoverable=recoverable,
                has_alternative=game_key(cue) in playable_keys,
                size_bytes=files.get(cue, 0) + sum(files[p] for p in present),
            )
        )

    if read_head is not None:
        for f in sorted(files):
            if f.lower().endswith(".chd"):
                why = chd_problem(read_head(f, CHD_V5_HEADER_SIZE), files[f])
                if why:
                    plan.bad_chds.append((f, why))

    for f in sorted(files):
        if f.lower().endswith(".m3u"):
            folder = posixpath.dirname(f)
            entries = [
                ln.strip() for ln in read_text(f).splitlines() if ln.strip() and ln[0] != "#"
            ]
            miss = [e for e in entries if posixpath.join(folder, e) not in files]
            if miss or not entries:
                plan.broken_m3u.append((f, miss))

    loose = [
        f for f in sorted(files) if _TRACK_BIN.search(f) and f not in claimed and f not in protected
    ]
    groups: dict[str, list[str]] = defaultdict(list)
    for f in loose:
        groups[_TRACK_BIN.sub("", f.rsplit("/", 1)[-1])].append(f)
    for name, tracks in groups.items():
        nums = sorted(
            int(re.search(r"Track (\d+)", posixpath.basename(f)).group(1)) for f in tracks
        )
        if (
            len(tracks) > 1
            and nums == list(range(1, len(nums) + 1))
            and (game_key(name) not in playable_keys)
        ):
            plan.rebuildable[name] = tracks  # juego completo al que solo le falta el .cue
        else:
            plan.orphan_tracks.extend(tracks)
    # un archivo que usa un .cue completo nunca se retira, aunque otro set roto lo nombre también
    plan.keep = frozenset(complete_claimed)
    return plan


def render_report(plan: IncompletePlan) -> str:
    """Informe Markdown de lo retirado: juegos perdidos, restos de juegos que sí funcionan y huérfanas."""
    lost = plan.lost_games
    rest = [s for s in plan.sets if not s.recoverable and s.has_alternative]
    rep = [s for s in plan.sets if s.recoverable]
    gb = lambda n: f"{n / 1e9:.2f} GB"  # noqa: E731
    out = ["# Juegos eliminados por estar incompletos", ""]
    out += [f"## Juegos que no funcionaban y se han eliminado ({len(lost)})", ""]
    out += [
        f"- `{s.cue}` — faltan {len(s.missing)} archivo(s) ({gb(s.size_bytes)})" for s in lost
    ] or ["- (ninguno)"]
    out += ["", f"## Restos de juegos que sí funcionan por otro archivo ({len(rest)})", ""]
    out += [f"- `{s.cue}` — faltan {len(s.missing)}" for s in rest] or ["- (ninguno)"]
    out += ["", f"## Reparables, NO eliminados ({len(rep)})", ""]
    out += [
        f"- `{s.cue}` — lo que falta está en otra carpeta: {', '.join(s.missing[:3])}" for s in rep
    ] or ["- (ninguno)"]
    out += ["", f"## Completos pero sin .cue, NO eliminados ({len(plan.rebuildable)})", ""]
    out += [f"- `{n}` — {len(tr)} pistas contiguas" for n, tr in plan.rebuildable.items()] or [
        "- (ninguno)"
    ]
    out += ["", f"## CHD vacíos o corruptos eliminados ({len(plan.bad_chds)})", ""]
    out += [f"- `{p}` — {why}" for p, why in plan.bad_chds] or ["- (ninguno)"]
    out += ["", f"## Listas .m3u rotas eliminadas ({len(plan.broken_m3u)})", ""]
    out += [f"- `{m}`" for m, _ in plan.broken_m3u] or ["- (ninguna)"]
    out += ["", f"## Pistas huérfanas eliminadas ({len(plan.orphan_tracks)})", ""]
    out += [f"- `{t}`" for t in plan.orphan_tracks] or ["- (ninguna)"]
    return "\n".join(out) + "\n"


def plan_for(fs: LibraryFS) -> IncompletePlan:
    """Plan sobre cualquier biblioteca (local o consola por ADB) detrás de ``LibraryFS``."""
    return plan_incomplete(fs.list_files(), fs.read_text, fs.read_head)


def _track_no(path: str) -> int:
    return int(re.search(r"Track (\d+)", posixpath.basename(path)).group(1))


def build_cue(names: list[str], mode: int) -> str:
    """``.cue`` para pistas ``.bin`` sueltas: la 1.ª de datos (``mode`` 1 o 2), el resto audio.

    ponytail: las pistas de audio llevan la convención Redump (``INDEX 00 00:00:00`` +
    ``INDEX 01 00:02:00``, 2 s de pregap dentro del archivo); si algún disco tuviera otro pregap el
    audio sonaría desfasado, los datos no. Mejora: leer el pregap real de un DAT Redump.
    """
    out: list[str] = []
    for i, name in enumerate(names, 1):
        out.append(f'FILE "{name}" BINARY')
        if i == 1:
            out += [f"  TRACK 01 MODE{mode}/2352", "    INDEX 01 00:00:00"]
        else:
            out += [f"  TRACK {i:02d} AUDIO", "    INDEX 00 00:00:00", "    INDEX 01 00:02:00"]
    return "\n".join(out) + "\n"


def _data_mode(sector: bytes) -> int | None:
    """Modo (1 o 2) de un sector de datos de 2352 bytes; None si no empieza con la sync CD-ROM."""
    ok = len(sector) >= 16 and sector[:12] == b"\x00" + b"\xff" * 10 + b"\x00"
    return sector[15] if ok and sector[15] in (1, 2) else None


def _is_psx(path: str) -> bool:
    """La regla «datos + audio» de ``build_cue`` solo vale en PSX; un GD-ROM de Dreamcast, por
    ejemplo, tiene datos también en la pista 3 y un .cue así lo estropearía."""
    return "psx" in (part.lower() for part in posixpath.dirname(path).split("/"))


def apply_repairs(fs: LibraryFS, plan: IncompletePlan) -> tuple[int, int]:
    """Repara sin borrar nada: mueve pistas junto a su ``.cue`` y crea los ``.cue`` que faltan.

    Devuelve ``(pistas movidas, .cue creados)``. Un juego cuya 1.ª pista no es un sector de datos
    reconocible se deja como está (no se inventa un ``.cue`` con un modo adivinado).
    """
    for src, dst in plan.repairs:
        fs.move(src, dst)
    created = 0
    for name, tracks in plan.rebuildable.items():
        tracks = sorted(tracks, key=_track_no)
        if not _is_psx(tracks[0]):
            continue
        mode = _data_mode(fs.read_head(tracks[0], 16))
        if mode is None:
            continue
        cue = posixpath.join(posixpath.dirname(tracks[0]), f"{name}.cue")
        fs.write_text(cue, build_cue([posixpath.basename(t) for t in tracks], mode))
        created += 1
    return len(plan.repairs), created


def discard_plan(fs: LibraryFS, plan: IncompletePlan) -> int:
    """Descarta (a ``_descartados/``, purga por edad) lo que el plan retira; nunca borra."""
    for rel in plan.to_remove:
        fs.discard(rel)
    return len(plan.to_remove)


def plan_to_issues(plan: IncompletePlan) -> list[dict]:
    """Incidencias para el Library Doctor. ``removable`` marca lo que «Retirar incompletos» descartaría."""
    issues: list[dict] = []
    for s in plan.sets:
        if s.recoverable:
            kind, sev, action = (
                "repairable_set",
                "info",
                "Reparable: lo que falta está en otra carpeta",
            )
        elif s.has_alternative:
            kind, sev, action = (
                "leftover_set",
                "warning",
                "Resto de un juego que sí funciona por otro archivo",
            )
        else:
            kind, sev, action = (
                "lost_game",
                "error",
                "Juego que no funciona: no queda ninguna copia completa",
            )
        issues.append(
            {
                "type": kind,
                "severity": sev,
                "file": posixpath.basename(s.cue),
                "path": s.cue,
                "platform": None,
                "missing_bins": s.missing[:5],
                "action": f"{action} (faltan {len(s.missing)})",
                "removable": not s.recoverable,
                "repairable": s.recoverable,
            }
        )
    for name, tracks in plan.rebuildable.items():
        issues.append(
            {
                "type": "rebuildable_set",
                "severity": "info",
                "file": name,
                "path": tracks[0],
                "platform": None,
                "action": f"Completo ({len(tracks)} pistas) pero sin .cue: se conserva",
                "removable": False,
                "repairable": _is_psx(tracks[0]),
            }
        )
    for chd, why in plan.bad_chds:
        issues.append(
            {
                "type": "bad_chd",
                "severity": "error",
                "file": posixpath.basename(chd),
                "path": chd,
                "platform": None,
                "action": f"CHD inservible: {why}",
                "removable": True,
            }
        )
    for m3u, missing in plan.broken_m3u:
        issues.append(
            {
                "type": "broken_m3u",
                "severity": "warning",
                "file": posixpath.basename(m3u),
                "path": m3u,
                "platform": None,
                "missing_bins": missing[:5],
                "action": "Lista .m3u rota: apunta a archivos que no existen",
                "removable": True,
            }
        )
    if plan.orphan_tracks:
        size = sum(plan.sizes.get(p, 0) for p in plan.orphan_tracks)
        issues.append(
            {
                "type": "orphan_tracks",
                "severity": "warning",
                "file": f"{len(plan.orphan_tracks)} pistas sueltas",
                "path": plan.orphan_tracks[0],
                "platform": None,
                "action": f"Pistas que ningún .cue usa ({size / 1e9:.2f} GB)",
                "removable": True,
            }
        )
    return issues
