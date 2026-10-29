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
    (tmp_path / "L (USA).chd").write_bytes(b"x")
    (tmp_path / "M (Track 4).bin").write_bytes(b"x")
    fs = LocalLibraryFS(tmp_path)
    plan = plan_for(fs)
    assert discard_plan(fs, plan) == 2
    assert (tmp_path / "L (USA).chd").exists()
    assert not (tmp_path / "K (Europe).cue").exists()
    assert (tmp_path / "_descartados" / "M (Track 4).bin").exists()
