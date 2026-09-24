"""GAME-BLOCKLIST-1/2: marca permanente por SHA1 + borrado en ambas bibliotecas.

Paso 5 del roadmap 18:
  - Marca + borrado: el juego desaparece de ambas bibliotecas, la marca persiste.
  - Reaparición: un archivo con SHA1 bloqueado que vuelve a aparecer (nueva fila,
    nuevo game_id) no se re-cuenta como pendiente ni se re-matchea.
  - Renombrado: el mismo SHA1 con nombre distinto sigue reconociéndose como bloqueado.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.storage_service import block_and_delete_game

TS = "2026-01-01T00:00:00"


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
    canonical_title: str | None = None,
) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=0,
        sha1=sha1,
        md5=(sha1 * 32)[:32],
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    if canonical_title:
        with repo.connect() as conn:
            conn.execute(
                "UPDATE games SET canonical_title=?, match_confidence='high' WHERE source_path=?",
                (canonical_title, source_path),
            )
            conn.commit()


def _count(repo: LibraryRepository) -> int:
    with repo.connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"])


# ── Marca + borrado ──────────────────────────────────────────────────────────


def test_block_and_delete_marks_both_dbs_and_trashes_pc_file(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    roms.mkdir()
    rom = roms / "Barbie.gba"
    rom.write_bytes(b"data")
    sha1 = "A" * 40

    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    _insert_game(repo_pc, source_path=str(rom), sha1=sha1)

    result = block_and_delete_game(repo_pc, repo_android, sha1, canonical_title="Barbie")

    assert result["blocked"] is True
    assert result["trashed"] is True
    assert result["deleted_device"] is False
    assert not rom.exists()
    assert (roms / "_descartados" / "Barbie.gba").exists()
    assert _count(repo_pc) == 0
    # La marca vive en AMBAS bases de datos, no solo en la que tenía el archivo.
    assert repo_pc.is_blocked(sha1) is True
    assert repo_android.is_blocked(sha1) is True


def test_block_and_delete_deletes_android_via_adb(tmp_path: Path) -> None:
    sha1 = "B" * 40
    device_path = "/storage/emulated/0/RetroArch/roms/gba/Barbie.gba"
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    _insert_game(repo_android, source_path=device_path, sha1=sha1)
    adb = SimpleNamespace(removed=[])
    adb.remove = lambda p: adb.removed.append(p)

    result = block_and_delete_game(repo_pc, repo_android, sha1, adb_transport=adb)

    assert result["deleted_device"] is True
    assert adb.removed == [device_path]
    assert _count(repo_android) == 0
    assert repo_pc.is_blocked(sha1) is True


def test_block_and_delete_without_device_still_marks_both_sides(tmp_path: Path) -> None:
    """Sin cable conectado: la marca se aplica igual en ambas BDs (Paso 2:
    marcar ANTES de borrar), el lado PC se borra si estaba presente, y el lado
    Android queda pendiente de borrado -- pero ya bloqueado, así que un sync
    posterior no lo trae de vuelta."""
    sha1 = "C" * 40
    device_path = "/storage/emulated/0/RetroArch/roms/gba/Barbie.gba"
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    _insert_game(repo_android, source_path=device_path, sha1=sha1)

    result = block_and_delete_game(repo_pc, repo_android, sha1, adb_transport=None)

    assert result["blocked"] is True
    assert result["deleted_device"] is False
    assert len(result["errors"]) == 1
    assert repo_android.is_blocked(sha1) is True
    assert repo_pc.is_blocked(sha1) is True
    # La fila Android sigue existiendo (no se pudo borrar sin cable).
    assert _count(repo_android) == 1


def test_block_and_delete_empty_sha1_is_rejected(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")

    result = block_and_delete_game(repo_pc, repo_android, "")

    assert result["blocked"] is False
    assert len(result["errors"]) == 1


# ── Reaparición ──────────────────────────────────────────────────────────────


def test_reappeared_file_excluded_from_unresolved_games(tmp_path: Path) -> None:
    """Un SHA1 bloqueado que vuelve a aparecer como fila NUEVA (game_id nuevo,
    sin matchear todavía -- el caso real tras un sync/adb pull) no debe
    re-entrar en la cola de matching."""
    sha1 = "D" * 40
    repo = LibraryRepository(tmp_path / "lib.db")
    repo.block_sha1(sha1, "Barbie")

    # Reaparece: fila nueva, mismo sha1, sin match_confidence todavía.
    _insert_game(repo, source_path=str(tmp_path / "inbox" / "Barbie.gba"), sha1=sha1)

    unresolved = repo.get_unresolved_games()
    assert all(g.sha1 != sha1 for g in unresolved)


def test_reappeared_file_excluded_from_matched_games(tmp_path: Path) -> None:
    """Igual que arriba pero para el plan de renombrado: si de algún modo
    la fila reaparecida ya tiene canonical_title, tampoco debe contar como
    pendiente en build_plan (que lee get_matched_games)."""
    sha1 = "E" * 40
    repo = LibraryRepository(tmp_path / "lib.db")
    repo.block_sha1(sha1, "Barbie")

    _insert_game(
        repo,
        source_path=str(tmp_path / "inbox" / "Barbie.gba"),
        sha1=sha1,
        canonical_title="Barbie",
    )

    matched = repo.get_matched_games()
    assert all(g.sha1 != sha1 for g in matched)


def test_unrelated_games_still_appear_after_a_block(tmp_path: Path) -> None:
    """El filtro por sha1 bloqueado no debe tragarse juegos no relacionados."""
    blocked_sha1 = "F" * 40
    other_sha1 = "1" * 40
    repo = LibraryRepository(tmp_path / "lib.db")
    repo.block_sha1(blocked_sha1)

    _insert_game(repo, source_path=str(tmp_path / "Blocked.gba"), sha1=blocked_sha1)
    _insert_game(repo, source_path=str(tmp_path / "Other.gba"), sha1=other_sha1)

    unresolved_sha1s = {g.sha1 for g in repo.get_unresolved_games()}
    assert other_sha1 in unresolved_sha1s
    assert blocked_sha1 not in unresolved_sha1s


# ── Renombrado ───────────────────────────────────────────────────────────────


def test_renamed_file_same_sha1_still_recognized_as_blocked(tmp_path: Path) -> None:
    """El mismo archivo (mismo SHA1) con un nombre distinto sigue bloqueado --
    la marca es por contenido, no por ruta/nombre."""
    sha1 = "A1B2C3D4" * 5
    repo = LibraryRepository(tmp_path / "lib.db")
    repo.block_sha1(sha1, canonical_title="Barbie (Original Name)")

    assert repo.is_blocked(sha1) is True
    # sha1 en minúsculas también debe reconocerse (normalización a mayúsculas).
    assert repo.is_blocked(sha1.lower()) is True

    _insert_game(repo, source_path=str(tmp_path / "Barbie - Renamed Copy (Europe).gba"), sha1=sha1)

    unresolved_sha1s = {g.sha1 for g in repo.get_unresolved_games()}
    assert sha1 not in unresolved_sha1s
