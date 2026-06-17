"""Response-builder functions for the Retro Vault web server, split by domain.

Each module here holds pure functions (typed params → JSON-ready dicts) for one
domain. ``web/response_builders.py`` re-exports them as a thin façade so existing
imports (``from rom_manager.web.response_builders import _build_X``) keep working.

Migration in progress (SRP-1a):
    common      — HTTP/path utilities and shared helpers
    library     — library report, status, games, plan
    duplicates  — duplicate detection + RetroAchievements annotation
    diff        — two-repo (PC ↔ Android) library diff
    folders     — junk scan + folder analysis
    misc        — assets, sync log, config, scrape summary, cable-sync preview
"""
