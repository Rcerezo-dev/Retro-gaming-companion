"""Canonical image/video extension sets.

REV43-39: image/video classification was duplicated with drifting subsets in
3 places (assets repository, ES-DE export, folder analysis) — a single
source of truth means adding a format once covers all of them.
"""

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tga", ".bmp"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
