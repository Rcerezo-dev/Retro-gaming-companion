from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)

# Retry settings for transient rclone failures (timeouts, network blips)
_RETRY_DELAYS = (5, 15, 45)  # seconds between attempts 1→2, 2→3, 3→4
_RETRYABLE_PHRASES = (
    "timeout",
    "timed out",
    "connection reset",
    "connection refused",
    "eof",
    "broken pipe",
    "i/o error",
    "network error",
    "no such host",
    "dial tcp",
    "read tcp",
    "write tcp",
)


@dataclass(slots=True)
class RemoteEntry:
    relative: str  # path relative to the remote root
    mtime: datetime  # UTC
    size: int


class RcloneError(RuntimeError):
    pass


class RcloneTransport:
    """Thin wrapper around the rclone CLI binary."""

    def __init__(self, rclone: str = "rclone") -> None:
        self.rclone = rclone

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diagnose_routing(
        self,
        filename: str,
        saves_remote: str | None = None,
        states_remote: str | None = None,
        save_extensions: tuple[str, ...] = (),
        state_extensions: tuple[str, ...] = (),
        fallback_remote: str | None = None,
    ) -> dict:
        """Diagnose which remote a file would route to and why.

        Useful for troubleshooting sync configuration issues.

        Returns a dict with keys:
            - filename: original filename
            - extension: detected file extension
            - routing_decision: which remote was chosen
            - routing_reason: why (e.g., "state extension (.state)")
            - config_summary: dict of remotes and extensions recognized
        """
        file_ext = Path(filename).suffix.lower()
        saves_remote_clean = (saves_remote or "").strip() or None
        states_remote_clean = (states_remote or "").strip() or None
        fallback_remote_clean = (fallback_remote or "").strip() or None

        chosen_remote: str | None = None
        routing_reason = ""

        # Same logic as upload/download
        if state_extensions and file_ext in state_extensions:
            if states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason = f"state extension ({file_ext})"
            else:
                routing_reason = f"matches state ext ({file_ext}) but states_remote not configured"
        elif save_extensions and file_ext in save_extensions:
            if saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason = f"save extension ({file_ext})"
            else:
                routing_reason = f"matches save ext ({file_ext}) but saves_remote not configured"
        else:
            routing_reason = f"unknown extension ({file_ext})"

        # Fallback chain if no match
        if not chosen_remote:
            if fallback_remote_clean:
                chosen_remote = fallback_remote_clean
                routing_reason += " → using fallback_remote"
            elif saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason += " → using saves_remote (default)"
            elif states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason += " → using states_remote (default)"
            else:
                routing_reason += " → NO REMOTE CONFIGURED (ERROR)"

        return {
            "filename": filename,
            "extension": file_ext,
            "routing_decision": chosen_remote or "(ERROR: no remote)",
            "routing_reason": routing_reason,
            "config_summary": {
                "saves_remote": saves_remote_clean,
                "states_remote": states_remote_clean,
                "fallback_remote": fallback_remote_clean,
                "save_extensions_count": len(save_extensions),
                "state_extensions_count": len(state_extensions),
                "extension_overlap": len(set(save_extensions) & set(state_extensions)),
            },
        }

    def list_remote(self, remote_root: str) -> list[RemoteEntry]:
        """Return all files under *remote_root* as RemoteEntry objects."""
        result = self._run(["lsjson", "--recursive", "--no-modtime-truncate", remote_root])
        entries: list[RemoteEntry] = []
        for item in json.loads(result):
            if item.get("IsDir"):
                continue
            entries.append(
                RemoteEntry(
                    relative=item["Path"].replace("\\", "/"),
                    mtime=_parse_rclone_time(item["ModTime"]),
                    size=int(item["Size"]),
                )
            )
        return entries

    def upload(
        self,
        local_path: Path,
        relative: str,
        saves_remote: str | None = None,
        states_remote: str | None = None,
        save_extensions: tuple[str, ...] = (),
        state_extensions: tuple[str, ...] = (),
        fallback_remote: str | None = None,
        verbose_logging: bool = False,
    ) -> None:
        """Copy *local_path* to appropriate remote (saves_remote or states_remote) based on file extension.

        Args:
            local_path: Path to local file to upload.
            relative: Path relative to remote root (e.g., "Sega Genesis/game.srm").
            saves_remote: Remote path for permanent saves (e.g., "dropbox:/saves").
            states_remote: Remote path for savestates (e.g., "dropbox:/states").
            save_extensions: Tuple of save file extensions (e.g., (".sav", ".srm")).
            state_extensions: Tuple of state file extensions (e.g., (".state", ".state0")).
            fallback_remote: Remote to use if extension doesn't match any category.
                            If None, uses saves_remote; if that's also None, raises error.
            verbose_logging: If True, log detailed diagnostics about routing decision.

        Raises:
            ValueError: If file doesn't exist or no suitable remote is available.
            RcloneError: If rclone command fails.
        """
        # Validate local file exists
        local_path = Path(local_path)
        if not local_path.exists():
            raise ValueError(f"Local file does not exist: {local_path}")

        # Log diagnostics if requested
        if verbose_logging:
            diag = self.diagnose_routing(
                local_path.name,
                saves_remote,
                states_remote,
                save_extensions,
                state_extensions,
                fallback_remote,
            )
            log.info(
                "Upload diagnostics: %s → %s (%s) | Config: saves=%s, states=%s, fallback=%s",
                diag["filename"],
                diag["routing_decision"],
                diag["routing_reason"],
                diag["config_summary"]["saves_remote"],
                diag["config_summary"]["states_remote"],
                diag["config_summary"]["fallback_remote"],
            )

        # Normalize and validate remotes (filter empty strings)
        saves_remote_clean = (saves_remote or "").strip() or None
        states_remote_clean = (states_remote or "").strip() or None
        fallback_remote_clean = (fallback_remote or "").strip() or None

        # Determine destination remote based on file extension
        file_ext = Path(local_path).suffix.lower()
        chosen_remote: str | None = None
        routing_reason = ""

        # Priority: check states_remote first (higher priority to avoid ambiguity)
        if state_extensions and file_ext in state_extensions:
            if states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason = f"state extension ({file_ext})"
            else:
                log.warning(
                    "File %s matches state extension (%s) but states_remote not configured; "
                    "will use fallback or saves_remote",
                    local_path.name,
                    file_ext,
                )
        # Then check saves_remote
        elif save_extensions and file_ext in save_extensions:
            if saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason = f"save extension ({file_ext})"
            else:
                log.warning(
                    "File %s matches save extension (%s) but saves_remote not configured; "
                    "will use fallback or states_remote",
                    local_path.name,
                    file_ext,
                )
        else:
            # Unknown extension
            log.warning(
                "File %s has unknown extension (%s); will use fallback or default remote",
                local_path.name,
                file_ext,
            )

        # Fallback chain: explicit fallback → saves_remote → states_remote
        if not chosen_remote:
            if fallback_remote_clean:
                chosen_remote = fallback_remote_clean
                routing_reason = "fallback_remote"
            elif saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason = "default (saves_remote)"
            elif states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason = "default (states_remote)"

        if not chosen_remote:
            raise ValueError(
                f"Cannot upload {local_path.name}: no suitable remote configured. "
                f"Please configure saves_remote, states_remote, or fallback_remote."
            )

        remote_dest = f"{chosen_remote.rstrip('/')}/{relative}"
        log.debug(
            "Uploading %s → %s (routing: %s)",
            local_path.name,
            relative,
            routing_reason,
        )
        self._run(["copyto", str(local_path), remote_dest])

    def download(
        self,
        relative: str,
        local_path: Path,
        saves_remote: str | None = None,
        states_remote: str | None = None,
        save_extensions: tuple[str, ...] = (),
        state_extensions: tuple[str, ...] = (),
        fallback_remote: str | None = None,
        verbose_logging: bool = False,
    ) -> None:
        """Copy appropriate remote file to *local_path* based on file extension.

        Args:
            relative: Path relative to remote root (e.g., "Sega Genesis/game.srm").
            local_path: Path to copy file to.
            saves_remote: Remote path for permanent saves (e.g., "dropbox:/saves").
            states_remote: Remote path for savestates (e.g., "dropbox:/states").
            save_extensions: Tuple of save file extensions (e.g., (".sav", ".srm")).
            state_extensions: Tuple of state file extensions (e.g., (".state", ".state0")).
            fallback_remote: Remote to use if extension doesn't match any category.
                            If None, uses saves_remote; if that's also None, raises error.
            verbose_logging: If True, log detailed diagnostics about routing decision.

        Raises:
            ValueError: If no suitable remote is available for the file.
            RcloneError: If rclone command fails.
        """
        # Log diagnostics if requested
        if verbose_logging:
            diag = self.diagnose_routing(
                Path(relative).name,
                saves_remote,
                states_remote,
                save_extensions,
                state_extensions,
                fallback_remote,
            )
            log.info(
                "Download diagnostics: %s ← %s (%s) | Config: saves=%s, states=%s, fallback=%s",
                diag["filename"],
                diag["routing_decision"],
                diag["routing_reason"],
                diag["config_summary"]["saves_remote"],
                diag["config_summary"]["states_remote"],
                diag["config_summary"]["fallback_remote"],
            )

        # Normalize and validate remotes (filter empty strings)
        saves_remote_clean = (saves_remote or "").strip() or None
        states_remote_clean = (states_remote or "").strip() or None
        fallback_remote_clean = (fallback_remote or "").strip() or None

        # Ensure parent directory exists for local file
        local_path = Path(local_path)
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create parent directory for {local_path}: {e}")

        # Determine source remote based on file extension
        file_ext = Path(relative).suffix.lower()
        chosen_remote: str | None = None
        routing_reason = ""

        # Priority: check states_remote first (higher priority to avoid ambiguity)
        if state_extensions and file_ext in state_extensions:
            if states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason = f"state extension ({file_ext})"
            else:
                log.warning(
                    "File %s matches state extension (%s) but states_remote not configured; "
                    "will use fallback or saves_remote",
                    Path(relative).name,
                    file_ext,
                )
        # Then check saves_remote
        elif save_extensions and file_ext in save_extensions:
            if saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason = f"save extension ({file_ext})"
            else:
                log.warning(
                    "File %s matches save extension (%s) but saves_remote not configured; "
                    "will use fallback or states_remote",
                    Path(relative).name,
                    file_ext,
                )
        else:
            # Unknown extension
            log.warning(
                "File %s has unknown extension (%s); will use fallback or default remote",
                Path(relative).name,
                file_ext,
            )

        # Fallback chain: explicit fallback → saves_remote → states_remote
        if not chosen_remote:
            if fallback_remote_clean:
                chosen_remote = fallback_remote_clean
                routing_reason = "fallback_remote"
            elif saves_remote_clean:
                chosen_remote = saves_remote_clean
                routing_reason = "default (saves_remote)"
            elif states_remote_clean:
                chosen_remote = states_remote_clean
                routing_reason = "default (states_remote)"

        if not chosen_remote:
            raise ValueError(
                f"Cannot download {Path(relative).name}: no suitable remote configured. "
                f"Please configure saves_remote, states_remote, or fallback_remote."
            )

        remote_src = f"{chosen_remote.rstrip('/')}/{relative}"
        log.debug(
            "Downloading %s → %s (routing: %s)",
            relative,
            local_path.name,
            routing_reason,
        )
        self._run(["copyto", remote_src, str(local_path)])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: list[str]) -> str:
        """Run rclone with exponential-backoff retries on transient errors."""
        cmd = [self.rclone, *args]
        last_exc: RcloneError | None = None

        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
            except FileNotFoundError:
                raise RcloneError(
                    f"rclone binary not found: '{self.rclone}'. "
                    "Install rclone and ensure it is in PATH, or pass --rclone <path>."
                )

            if proc.returncode == 0:
                return proc.stdout

            stderr = proc.stderr.strip()
            err = RcloneError(f"rclone exited with code {proc.returncode}:\n{stderr}")

            # Only retry on transient network/timeout errors
            if delay is not None and any(p in stderr.lower() for p in _RETRYABLE_PHRASES):
                log.warning(
                    "rclone transient error (attempt %d/%d), retrying in %ds: %s",
                    attempt,
                    len(_RETRY_DELAYS) + 1,
                    delay,
                    stderr[:120],
                )
                last_exc = err
                time.sleep(delay)
                continue

            raise err  # permanent error — don't retry

        raise last_exc  # type: ignore[misc]  — all retries exhausted


def _parse_rclone_time(raw: str) -> datetime:
    """Parse the RFC-3339 / ISO-8601 timestamp returned by rclone lsjson.

    rclone uses nanosecond precision, e.g. '2024-01-15T10:30:00.123456789+00:00'.
    We truncate to microseconds for stdlib compatibility.
    """
    # Truncate sub-microsecond digits: keep at most 6 decimal places.
    if "." in raw:
        base, frac_and_tz = raw.split(".", 1)
        # Split fractional seconds from timezone offset
        for sep in ("+", "-", "Z"):
            if sep in frac_and_tz:
                idx = frac_and_tz.index(sep)
                frac = frac_and_tz[:idx][:6]
                tz = frac_and_tz[idx:]
                raw = f"{base}.{frac}{tz}"
                break
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt.astimezone(UTC).replace(tzinfo=UTC)
