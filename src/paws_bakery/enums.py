"""A collection of different Enums."""

import enum
from enum import auto
from typing import Any


class CaseSensitiveStrEnum(enum.StrEnum):
    """Case-sensitive StrEnum implementation."""

    @staticmethod
    def _generate_next_value_(
        name: str, _start: int, _count: int, _last_values: list[Any]
    ) -> Any:
        return name


class BlenderOperatorReturnType(CaseSensitiveStrEnum):
    """Blender operator return types.

    List may not be complete and contain only used types.
    """

    RUNNING_MODAL = auto()
    CANCELLED = auto()
    FINISHED = auto()
    PASS_THROUGH = auto()
    INTERFACE = auto()


class BlenderEventType(CaseSensitiveStrEnum):
    """Blender WindowManager event types.

    List may not be complete and contain only used types.
    """

    ESC = auto()
    TIMER = auto()


class BlenderJobType(CaseSensitiveStrEnum):
    """Blender Job types.

    bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE)

    List may not be complete and contain only used types.
    """

    OBJECT_BAKE = auto()


class CyclesBakeType(CaseSensitiveStrEnum):
    """Blender cycles bake type names used in addon.

    List may not be complete and contain only used types.
    """

    EMIT = auto()
    DIFFUSE = auto()
    ROUGHNESS = auto()
    NORMAL = auto()
    


class Colorspace(CaseSensitiveStrEnum):
    """Blender colorspace names.

    List may not be complete and contain only used types.
    """

    SRGB = DEFAULT = "sRGB"
    NON_COLOR = "Non-Color"
