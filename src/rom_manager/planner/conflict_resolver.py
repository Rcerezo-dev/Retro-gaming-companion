from __future__ import annotations

from collections import defaultdict

from rom_manager.planner.operation_planner import RenameOperation


def resolve(
    ops: list[RenameOperation],
    *,
    keep_both: bool = False,
) -> list[RenameOperation]:
    """Detect plan-level collisions: two pending ops targeting the same path.

    When two (or more) operations share the same *target_path*, both are
    marked ``status='conflict'`` by default so they are excluded from apply.

    With *keep_both=True* each colliding op gets a unique numeric suffix
    (``_1``, ``_2``, …) appended to the target stem so all renames can
    proceed without overwriting each other.

    Operations that do not collide are returned unchanged.
    """
    # Build target_path → [indices] map over the received ops
    target_to_indices: dict[str, list[int]] = defaultdict(list)
    for i, op in enumerate(ops):
        target_to_indices[str(op.target_path)].append(i)

    result: list[RenameOperation] = []
    for i, op in enumerate(ops):
        key = str(op.target_path)
        indices = target_to_indices[key]

        if len(indices) <= 1:
            result.append(op)
            continue

        if keep_both:
            rank = indices.index(i) + 1
            new_name = f"{op.target_path.stem}_{rank}{op.target_path.suffix}"
            op.target_path = op.target_path.parent / new_name
            op.status = "pending"
        else:
            op.status = "conflict"

        result.append(op)

    return result
