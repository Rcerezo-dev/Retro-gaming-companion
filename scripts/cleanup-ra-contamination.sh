#!/usr/bin/env bash
# cleanup-ra-contamination.sh
#
# Removes non-gaming content that a third-party sync app (Syncthing) mirrored
# onto the Anbernic RG556, and consolidates duplicate PS1 memory-card copies
# down to the single authoritative location (DuckStation).
#
# See docs/sync/android-save-paths-RG556.md → "Known contamination / caveats".
#
# ASSUMPTIONS:
#   - Personal documents in /sdcard/ra-saves/ are backed up on PC (via Syncthing).
#   - /sdcard/ra-saves/memcards psx/ saves are ALL present in DuckStation memcards
#     with identical or newer timestamps — deleting them loses no data.
#   - RetroArch/saves/Beetle PSX/ is a stale 3-file subset of DuckStation — same.
#   - /sdcard/ra-states/ contains a REAL save state (Kirby .state) — it is kept;
#     only the steam_autocloud.vdf marker inside it is removed.
#
# Run this LOCALLY with the RG556 attached over USB and ADB authorized.
# Via Git Bash on Windows:
#   bash scripts/cleanup-ra-contamination.sh tools/adb.exe
#
# Usage: ./scripts/cleanup-ra-contamination.sh [path-to-adb]

set -euo pipefail

ADB="${1:-adb}"

# ── ADB detection ──────────────────────────────────────────────────────────────
if ! command -v "$ADB" >/dev/null 2>&1 && [ ! -x "$ADB" ]; then
    echo "adb not found at '$ADB'. Pass the path explicitly, e.g.:" >&2
    echo "  bash scripts/cleanup-ra-contamination.sh tools/adb.exe" >&2
    exit 1
fi

DEVICE=$("$ADB" devices 2>/dev/null | awk '/device$/{print $1; exit}')
if [ -z "$DEVICE" ]; then
    echo "No ADB device found. Attach the RG556 and ensure USB debugging is authorized." >&2
    exit 1
fi
echo "Device: $DEVICE"
echo

# ── Confirmation helper ─────────────────────────────────────────────────────────
confirm() {
    printf '%s [y/N] ' "${1:-Continue?}" >/dev/tty
    local answer
    read -r answer </dev/tty
    [[ "$answer" =~ ^[Yy]$ ]]
}

RA_SAVES="/sdcard/ra-saves"
RA_STATES="/sdcard/ra-states"
RA_ROOT="/storage/emulated/0/RetroArch/saves"
BEETLE_PSX="$RA_ROOT/Beetle PSX"

# ── Step 1: ra-saves — delete everything (personal docs + stale PS1 copies) ────
echo "════════════════════════════════════════════════════════════"
echo " STEP 1 — $RA_SAVES"
echo " Contains personal documents (backed up on PC) AND a stale"
echo " 'memcards psx/' subfolder whose PS1 memory cards are fully"
echo " covered by DuckStation with more recent timestamps."
echo " Deletes ALL contents of this folder."
echo "════════════════════════════════════════════════════════════"
echo
echo "Current contents:"
"$ADB" shell ls -la "$RA_SAVES" 2>/dev/null || echo "(folder not found)"
echo
if confirm "Delete ALL contents of $RA_SAVES from the device?"; then
    "$ADB" shell "find '$RA_SAVES' -mindepth 1 -maxdepth 1 -exec rm -rf {} +"
    echo "Done. $RA_SAVES is now empty."
else
    echo "Skipped."
fi
echo

# ── Step 2: Beetle PSX — stale 3-file subset already in DuckStation ────────────
echo "════════════════════════════════════════════════════════════"
echo " STEP 2 — $BEETLE_PSX/"
echo " Stale RetroArch Beetle PSX memory-card copies (3 files)."
echo " Crash Bash .mcr/.srm files are present in DuckStation memcards"
echo " with identical timestamps — pure duplicates, no unique saves."
echo " NOTE: this is a MEMORY CARD folder, not save states."
echo "════════════════════════════════════════════════════════════"
echo
echo "Current contents:"
"$ADB" shell ls -la "$BEETLE_PSX" 2>/dev/null || echo "(folder not found)"
echo
if confirm "Delete $BEETLE_PSX/ from the device?"; then
    "$ADB" shell "rm -rf '$BEETLE_PSX'"
    echo "Deleted."
else
    echo "Skipped."
fi
echo

# ── Step 3: ra-states — delete ONLY steam_autocloud.vdf; keep .state files ─────
echo "════════════════════════════════════════════════════════════"
echo " STEP 3 — $RA_STATES"
echo " Contains real save states (e.g. Kirby .state) — KEEP those."
echo " Only the steam_autocloud.vdf Steam marker is removed."
echo "════════════════════════════════════════════════════════════"
echo
echo "Current contents:"
"$ADB" shell ls -la "$RA_STATES" 2>/dev/null || echo "(folder not found)"
echo
VDF_COUNT=$("$ADB" shell "find '$RA_STATES' -name 'steam_autocloud.vdf' 2>/dev/null | wc -l" | tr -d '[:space:]')
echo "steam_autocloud.vdf files found: $VDF_COUNT"
if [ "$VDF_COUNT" -eq 0 ]; then
    echo "Nothing to delete."
else
    echo
    if confirm "Delete $VDF_COUNT steam_autocloud.vdf file(s) from $RA_STATES?"; then
        "$ADB" shell "find '$RA_STATES' -name 'steam_autocloud.vdf' -delete"
        echo "Done. Remaining contents:"
        "$ADB" shell ls -la "$RA_STATES"
    else
        echo "Skipped."
    fi
fi
echo

# ── Step 4: steam_autocloud.vdf scattered through RetroArch/saves ──────────────
echo "════════════════════════════════════════════════════════════"
echo " STEP 4 — steam_autocloud.vdf markers under $RA_ROOT"
echo " Steam Cloud markers spread across per-core save subfolders."
echo " Only .vdf files are removed; all save files (.srm/.mcr/.sav etc.) are kept."
echo "════════════════════════════════════════════════════════════"
echo
echo "Locations found:"
"$ADB" shell "find '$RA_ROOT' -name 'steam_autocloud.vdf' 2>/dev/null" || true
echo
VDF_RA_COUNT=$("$ADB" shell "find '$RA_ROOT' -name 'steam_autocloud.vdf' 2>/dev/null | wc -l" | tr -d '[:space:]')
if [ "$VDF_RA_COUNT" -eq 0 ]; then
    echo "Nothing to delete."
else
    if confirm "Delete $VDF_RA_COUNT steam_autocloud.vdf marker(s) from RetroArch/saves?"; then
        "$ADB" shell "find '$RA_ROOT' -name 'steam_autocloud.vdf' -delete"
        echo "Deleted."
    else
        echo "Skipped."
    fi
fi
echo

echo "════════════════════════════════════════════════════════════"
echo " Cleanup complete."
echo " Preserved:"
echo "   DuckStation memcards (authoritative PS1 memory cards)"
echo "   All *.state save states in $RA_STATES/"
echo "   All .srm/.mcr/.sav/.mcd in RetroArch/saves/ (except Beetle PSX/ duplicates)"
echo "   All other per-emulator saves (AetherSX2, EX+, melonDS, etc.)"
echo "════════════════════════════════════════════════════════════"
