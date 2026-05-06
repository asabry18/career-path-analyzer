"""Shared DSS types — pure Python."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobRequirements:
    """
    Per-job similarity inputs: mandatory skills (AND) and framework OR slots.

    ``framework_slots`` is an ordered tuple: each frozenset is one OR group
    (same ``slot_index`` in the catalog). Caller must aggregate DB rows accordingly.
    """

    job_id: int
    mandatory_skill_ids: frozenset[int]
    framework_slots: tuple[frozenset[int], ...]
