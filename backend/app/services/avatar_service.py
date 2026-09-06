"""
AvatarService — maps a gloss sequence to the animation IDs the frontend's
Three.js avatar should play (see avatar/mappings/, Phase 15).

STATUS: interface only. The mapping table itself is simple data (not an ML
dependency) but is scheduled for Phase 15 so it's built together with the
actual avatar assets it needs to reference.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class NotConfiguredError(RuntimeError):
    pass


class AvatarService(ABC):
    @abstractmethod
    def gloss_sequence_to_animations(self, gloss_sequence: list[str]) -> list[str]:
        """Map each gloss to a known animation ID (e.g. 'WATER' -> 'water_animation').
        Unmapped glosses should be reported, not silently dropped."""
        raise NotImplementedError


class NotConfiguredAvatarService(AvatarService):
    def gloss_sequence_to_animations(self, gloss_sequence: list[str]) -> list[str]:
        raise NotConfiguredError(
            "Avatar gloss->animation mapping is not implemented yet "
            "(scheduled: Phase 15). See PROJECT_STATUS.md."
        )
