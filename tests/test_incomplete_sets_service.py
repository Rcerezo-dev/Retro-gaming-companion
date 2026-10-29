"""PRUNE-INCOMPLETE-1: planificación de sets de disco incompletos."""

from rom_manager.services.incomplete_sets_service import plan_incomplete, render_report


def _cue(*names: str) -> str:
    return "\n".join(f'FILE "{n}" BINARY\n  TRACK 01 MODE2/2352' for n in names)


def _plan(files: dict[str, str]):
    sizes = {k: 10 for k in files}
    return plan_incomplete(sizes, lambda p: files[p])


def test_complete_set_is_untouched():
    plan = _plan({"A (USA).cue": _cue("A (USA) (Track 1).bin"), "A (USA) (Track 1).bin": ""})
    assert plan.sets == [] and plan.to_remove == []


def test_lost_game_listed_and_removed_with_its_present_tracks():
    plan = _plan(
        {
            "B (Europe).cue": _cue("B (Europe) (Track 1).bin", "B (Europe) (Track 2).bin"),
            "B (Europe) (Track 2).bin": "",
        }
    )
    assert [s.cue for s in plan.lost_games] == ["B (Europe).cue"]
    assert set(plan.to_remove) == {"B (Europe).cue", "B (Europe) (Track 2).bin"}
    assert "B (Europe).cue" in render_report(plan)


def test_incomplete_cue_with_working_chd_is_a_leftover_not_a_lost_game():
    plan = _plan({"C (USA).cue": _cue("C (USA) (Track 1).bin"), "C (USA).chd": ""})
    assert plan.lost_games == []
    assert plan.to_remove == ["C (USA).cue"]


def test_other_region_chd_does_not_count_as_alternative():
    plan = _plan({"D (Europe).cue": _cue("D (Europe) (Track 1).bin"), "D (USA).chd": ""})
    assert [s.cue for s in plan.lost_games] == ["D (Europe).cue"]


def test_recoverable_set_is_kept_with_the_loose_track_it_needs():
    plan = _plan(
        {
            "E (Europe)/E (Europe).cue": _cue(
                "E (Europe) (Track 1).bin", "E (Europe) (Track 2).bin"
            ),
            "E (Europe)/E (Europe) (Track 2).bin": "",
            "E (Europe) (Track 1).bin": "",
        }
    )
    assert plan.sets[0].recoverable
    assert plan.to_remove == [] and plan.lost_games == []


def test_orphan_track_and_broken_m3u_removed():
    plan = _plan(
        {
            "F (Track 9).bin": "",
            "G.m3u": "G (Disc 1).chd\nG (Disc 2).chd\n",
            "G (Disc 1).chd": "",
        }
    )
    assert plan.orphan_tracks == ["F (Track 9).bin"]
    assert plan.broken_m3u == [("G.m3u", ["G (Disc 2).chd"])]


def test_track_used_by_a_complete_cue_is_never_removed():
    plan = _plan(
        {
            "H.cue": _cue("H (Track 1).bin"),
            "H (Track 1).bin": "",
            "X.cue": _cue("H (Track 1).bin", "X (Track 2).bin"),
        }
    )
    assert "H (Track 1).bin" not in plan.to_remove


def test_contiguous_tracks_without_cue_are_rebuildable_not_orphans():
    plan = _plan({"I (Track 1).bin": "", "I (Track 2).bin": "", "I (Track 3).bin": ""})
    assert list(plan.rebuildable) == ["I"] and plan.orphan_tracks == []


def test_gapped_tracks_without_cue_are_orphans():
    plan = _plan({"J (Track 1).bin": "", "J (Track 3).bin": ""})
    assert plan.rebuildable == {} and len(plan.orphan_tracks) == 2


def test_directory_roundtrip_moves_only_what_the_plan_removes(tmp_path):
    from rom_manager.services.incomplete_sets_service import discard_plan, plan_for
    from rom_manager.services.library_fs import LocalLibraryFS

    (tmp_path / "K (Europe).cue").write_text(_cue("K (Europe) (Track 1).bin"))
    (tmp_path / "L (USA).chd").write_bytes(_chd_header().ljust(600, bytes(1)))
    (tmp_path / "M (Track 4).bin").write_bytes(b"x")
    fs = LocalLibraryFS(tmp_path)
    plan = plan_for(fs)
    assert discard_plan(fs, plan) == 2
    assert (tmp_path / "L (USA).chd").exists()
    assert not (tmp_path / "K (Europe).cue").exists()
    assert (tmp_path / "_descartados" / "M (Track 4).bin").exists()


# ── PRUNE-INCOMPLETE-1d: CHD inservibles, reparación y .cue regenerados ──────────────────────


def _chd_header(*, size_ok: bool = True, logical: int = 1000) -> bytes:
    h = bytearray(124)
    h[:8] = b"MComprHD"
    h[8:12] = (124).to_bytes(4, "big")
    h[12:16] = (5).to_bytes(4, "big")
    h[32:40] = logical.to_bytes(8, "big")
    h[40:48] = (200 if size_ok else 10_000).to_bytes(8, "big")
    h[48:56] = (300 if size_ok else 10_000).to_bytes(8, "big")
    return bytes(h)


def test_bad_chds_are_detected_and_removed():
    heads = {
        "ok.chd": _chd_header(),
        "blank.chd": bytes(124),
        "cut.chd": _chd_header(size_ok=False),
        "empty.chd": b"",
    }
    sizes = {"ok.chd": 5000, "blank.chd": 5000, "cut.chd": 5000, "empty.chd": 0}
    plan = plan_incomplete(sizes, lambda p: "", lambda p, n: heads[p])
    assert {p for p, _ in plan.bad_chds} == {"blank.chd", "cut.chd", "empty.chd"}
    assert "ok.chd" not in plan.to_remove and "blank.chd" in plan.to_remove


def test_repair_moves_track_next_to_its_cue_and_never_overwrites():
    plan = _plan({"Dir/G.cue": _cue("G (Track 1).bin"), "G (Track 1).bin": ""})
    assert plan.repairs == [("G (Track 1).bin", "Dir/G (Track 1).bin")]


def test_apply_repairs_moves_and_rebuilds_cue(tmp_path):
    from rom_manager.services.incomplete_sets_service import apply_repairs, plan_for
    from rom_manager.services.library_fs import LocalLibraryFS

    (tmp_path / "Dir").mkdir()
    (tmp_path / "psx").mkdir()
    (tmp_path / "Dir" / "G.cue").write_text(_cue("G (Track 1).bin"))
    (tmp_path / "G (Track 1).bin").write_bytes(b"x")
    data = b"\x00" + b"\xff" * 10 + b"\x00" + b"\x00\x00\x00\x02" + b"\x00" * 20
    for n in range(1, 11):
        (tmp_path / "psx" / f"I (Track {n}).bin").write_bytes(data)
    fs = LocalLibraryFS(tmp_path)

    assert apply_repairs(fs, plan_for(fs)) == (1, 1)

    assert (tmp_path / "Dir" / "G (Track 1).bin").exists()
    cue = (tmp_path / "psx" / "I.cue").read_text()
    assert "TRACK 01 MODE2/2352" in cue and "TRACK 10 AUDIO" in cue
    assert cue.index("Track 2") < cue.index("Track 10")  # orden numérico, no alfabético
    assert plan_for(fs).repairs == [] and plan_for(fs).rebuildable == {}


def test_rebuild_is_skipped_when_first_track_is_not_a_data_sector(tmp_path):
    from rom_manager.services.incomplete_sets_service import apply_repairs, plan_for
    from rom_manager.services.library_fs import LocalLibraryFS

    for n in (1, 2):
        (tmp_path / f"J (Track {n}).bin").write_bytes(b"x" * 32)
    fs = LocalLibraryFS(tmp_path)
    assert apply_repairs(fs, plan_for(fs)) == (0, 0)
    assert not (tmp_path / "J.cue").exists()


def test_rebuild_is_only_for_psx(tmp_path):
    from rom_manager.services.incomplete_sets_service import apply_repairs, plan_for
    from rom_manager.services.library_fs import LocalLibraryFS

    (tmp_path / "dreamcast").mkdir()
    data = b"\x00" + b"\xff" * 10 + b"\x00" + b"\x00\x00\x00\x01" + b"\x00" * 20
    for n in (1, 2, 3):
        (tmp_path / "dreamcast" / f"K (Track {n}).bin").write_bytes(data)
    fs = LocalLibraryFS(tmp_path)
    assert apply_repairs(fs, plan_for(fs)) == (0, 0)


def test_rebuild_gathers_tracks_split_across_folders(tmp_path):
    from rom_manager.services.incomplete_sets_service import apply_repairs, plan_for
    from rom_manager.services.library_fs import LocalLibraryFS

    (tmp_path / "psx" / "L").mkdir(parents=True)
    data = b"\x00" + b"\xff" * 10 + b"\x00" + b"\x00\x00\x00\x02" + b"\x00" * 20
    (tmp_path / "psx" / "L (Track 1).bin").write_bytes(data)
    for n in (2, 3):
        (tmp_path / "psx" / "L" / f"L (Track {n}).bin").write_bytes(data)
    fs = LocalLibraryFS(tmp_path)

    assert apply_repairs(fs, plan_for(fs)) == (0, 1)

    assert (tmp_path / "psx" / "L" / "L.cue").exists()
    assert (tmp_path / "psx" / "L" / "L (Track 1).bin").exists()
    assert plan_for(fs).sets == []


def test_gdi_tracks_are_neither_orphans_nor_rebuildable():
    q = chr(34)
    rows = ["3"] + [f"{n} 0 4 2352 {q}M (Track {n}).bin{q} 0" for n in (1, 2, 3)]
    gdi = chr(10).join(rows) + chr(10)
    plan = _plan(
        {"D/M.gdi": gdi, "D/M (Track 1).bin": "", "D/M (Track 2).bin": "", "D/M (Track 3).bin": ""}
    )
    assert plan.orphan_tracks == [] and plan.rebuildable == {} and plan.to_remove == []
