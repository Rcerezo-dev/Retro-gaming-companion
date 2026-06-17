"""Response-builder functions for the Retro Vault web server, split by domain.

Each module holds pure functions (typed params → JSON-ready dicts) for one
domain. Import directly from the relevant module, e.g.
``from rom_manager.web.builders.library import _build_status``.

Modules (SRP-1a):
    common      — HTTP/path utilities and shared helpers
    library     — library report, status, games, plan
    duplicates  — duplicate detection + RetroAchievements annotation
    diff        — two-repo (PC ↔ Android) library diff
    folders     — junk scan + folder analysis
    misc        — assets, sync log, config, scrape summary, cable-sync preview
"""
