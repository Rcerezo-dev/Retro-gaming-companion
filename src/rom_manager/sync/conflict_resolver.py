from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SyncDecision:
    action: str  # 'upload' | 'download' | 'up_to_date' | 'conflict'
    relative: str
    local_mtime: datetime | None
    remote_mtime: datetime | None
    last_sync_at: datetime | None


def decide(
    relative: str,
    local_mtime: datetime | None,
    remote_mtime: datetime | None,
    last_sync_at: datetime | None,
    *,
    tolerance_seconds: int = 2,
) -> SyncDecision:
    """Decide what to do with a save file based on modification times.

    Rules
    -----
    - One side missing → trivial upload or download.
    - Both sides present and a previous sync time is known:
        - Both mtimes > last_sync_at → CONFLICT (both changed since last sync).
    - Newest wins; equal within *tolerance_seconds* → up_to_date.
    """
    if local_mtime is None and remote_mtime is None:
        return SyncDecision("up_to_date", relative, None, None, last_sync_at)

    if local_mtime is None:
        return SyncDecision("download", relative, None, remote_mtime, last_sync_at)

    if remote_mtime is None:
        return SyncDecision("upload", relative, local_mtime, None, last_sync_at)

    diff = (local_mtime - remote_mtime).total_seconds()

    # Detect conflict: both files changed after last successful sync.
    if last_sync_at is not None:
        local_changed = (local_mtime - last_sync_at).total_seconds() > tolerance_seconds
        remote_changed = (remote_mtime - last_sync_at).total_seconds() > tolerance_seconds
        if local_changed and remote_changed:
            return SyncDecision("conflict", relative, local_mtime, remote_mtime, last_sync_at)

    if abs(diff) <= tolerance_seconds:
        return SyncDecision("up_to_date", relative, local_mtime, remote_mtime, last_sync_at)

    action = "upload" if diff > 0 else "download"
    return SyncDecision(action, relative, local_mtime, remote_mtime, last_sync_at)
