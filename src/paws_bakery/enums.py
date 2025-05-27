from enum import Enum, auto


class StrEnum(str, Enum):
    """StrEnum implementation."""

    def __str__(self) -> str:
        return str(self.value)

    # pylint: disable-next=no-self-argument
    def _generate_next_value_(  # type: ignore[no-untyped-def]
        name, _start, _count, _last_values  # noqa: B902
    ):
        return name


class NameStrEnum(StrEnum):
    """NameStrEnum implementation."""

    def __str__(self) -> str:
        return str(self.name)


class BlenderOperatorReturnType(StrEnum):
    """Blender operator return types.

    List may not be complete and contain only used types.
    """

    RUNNING_MODAL = auto()
    CANCELLED = auto()
    FINISHED = auto()
    PASS_THROUGH = auto()
    INTERFACE = auto()


class CyclesBakeType(StrEnum):
    """Blender cycles bake type names used in addon.

    List may not be complete and contain only used types.
    """

    EMIT = auto()
    DIFFUSE = auto()
    ROUGHNESS = auto()
    NORMAL = auto()


class Colorspace(StrEnum):
    """Blender colorspace names.

    List may not be complete and contain only used types.
    """

    SRGB = DEFAULT = "sRGB"
    NON_COLOR = "Non-Color"
