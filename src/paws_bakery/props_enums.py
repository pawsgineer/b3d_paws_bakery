# pylint: disable=invalid-enum-extension
"""Addon Blender property enums."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from bpy import props as b_p

from . import icons
from .enums import Colorspace, CyclesBakeType


@dataclass(kw_only=True, frozen=True)
class EnumItemInfo:
    """Common Blender enum item info."""

    ui_name: str
    description: str


class BlenderPropertyEnum(Enum):
    """Blender Property Enum."""

    __bl_prop_cache__: Any | None = None

    __bl_prop_name__: str
    __bl_prop_description__: str = ""

    value: EnumItemInfo
    DEFAULT: EnumItemInfo

    def __init_subclass__(cls) -> None:
        assert cls.__bl_prop_name__
        assert cls.__bl_prop_description__

    @classmethod
    def get_blender_enum_property(cls) -> Any:
        """Return EnumProperty to use in blender props definition."""
        if cls.__bl_prop_cache__ is not None:
            return cls.__bl_prop_cache__

        items = tuple((i.name, i.value.ui_name, i.value.description) for i in cls)
        cls.__bl_prop_cache__ = b_p.EnumProperty(
            name=cls.__bl_prop_name__,
            description=cls.__bl_prop_description__,
            items=items,
            default=cls.DEFAULT.name if cls.DEFAULT is not None else None,
        )

        return cls.__bl_prop_cache__


@dataclass(kw_only=True, frozen=True)
class BakeTextureTypeInfo(EnumItemInfo):
    """Texture type additional info."""

    short_name: str
    cycles_type: str = CyclesBakeType.EMIT
    colorspace: Colorspace = Colorspace.DEFAULT
    is_float: bool = False


class BakeTextureType(BlenderPropertyEnum):
    """Bake texture types."""

    __bl_prop_name__ = "Type"
    __bl_prop_description__ = "Texture Type"

    value: BakeTextureTypeInfo

    EMIT = BakeTextureTypeInfo(
        ui_name="Emit",
        description="Bake current material output in emit mode",
        short_name="emit",
    )
    EMIT_COLOR = BakeTextureTypeInfo(
        ui_name="Color(Emit)",
        description="Bake color value as emit output",
        short_name="color",
    )
    EMIT_ROUGHNESS = BakeTextureTypeInfo(
        ui_name="Roughness(Emit)",
        description="Bake roughness value as emit output",
        short_name="roughness",
        colorspace=Colorspace.NON_COLOR,
    )
    EMIT_METALNESS = BakeTextureTypeInfo(
        ui_name="Metalness(Emit)",
        description="Bake metalness value as emit output",
        short_name="metalness",
        colorspace=Colorspace.NON_COLOR,
    )
    EMIT_OPACITY = BakeTextureTypeInfo(
        ui_name="Opacity(Emit)",
        description="Bake opacity value as emit output",
        short_name="opacity",
        colorspace=Colorspace.NON_COLOR,
    )
    DIFFUSE = BakeTextureTypeInfo(
        ui_name="Diffuse",
        description="Bake current material output in diffuse mode",
        short_name="diffuse",
        cycles_type=CyclesBakeType.DIFFUSE,
    )
    ROUGHNESS = BakeTextureTypeInfo(
        ui_name="Roughness",
        description="Bake current material output in roughness mode",
        short_name="roughness",
        cycles_type=CyclesBakeType.ROUGHNESS,
        colorspace=Colorspace.NON_COLOR,
    )
    NORMAL = BakeTextureTypeInfo(
        ui_name="Normal",
        description="Bake current material output in normal mode",
        short_name="normalgl",
        cycles_type=CyclesBakeType.NORMAL,
        colorspace=Colorspace.NON_COLOR,
        is_float=True,
    )
    MATERIAL_ID = BakeTextureTypeInfo(
        ui_name="Material ID",
        description="Bake Material ID map",
        short_name="matid",
    )
    AO = BakeTextureTypeInfo(
        ui_name="AO",
        description="Bake AO map",
        short_name="ao",
        colorspace=Colorspace.NON_COLOR,
    )
    AORM = BakeTextureTypeInfo(
        ui_name="AORM",
        description="Bake packed AORM map",
        short_name="aorm",
        colorspace=Colorspace.NON_COLOR,
    )
    UTILS_GRID_COLOR = BakeTextureTypeInfo(
        ui_name="Utils: Grid Color",
        description="Bake color grid map",
        short_name="grid_color",
    )
    UTILS_GRID_UV = BakeTextureTypeInfo(
        ui_name="Utils: Grid UV",
        description="Bake UV grid map",
        short_name="grid_uv",
    )
    COMBINED = BakeTextureTypeInfo(
        ui_name="Combined",
        description="Bake current material output in Combined mode",
        short_name="combined",
        cycles_type=CyclesBakeType.COMBINED,
    )
    SHADOW = BakeTextureTypeInfo(
        ui_name="Shadow",
        description="Bake current material output in Shadow mode",
        short_name="shadow",
        cycles_type=CyclesBakeType.SHADOW,
        colorspace=Colorspace.NON_COLOR,
    )
    POSITION = BakeTextureTypeInfo(
        ui_name="Position",
        description="Bake current material output in Position mode",
        short_name="position",
        cycles_type=CyclesBakeType.POSITION,
        colorspace=Colorspace.NON_COLOR,
        is_float=True,
    )
    UV = BakeTextureTypeInfo(
        ui_name="UV",
        description="Bake current material output in UV mode",
        short_name="uv",
        cycles_type=CyclesBakeType.UV,
        colorspace=Colorspace.NON_COLOR,
    )
    ENVIRONMENT = BakeTextureTypeInfo(
        ui_name="Environment",
        description="Bake current material output in Environment mode",
        short_name="env",
        cycles_type=CyclesBakeType.ENVIRONMENT,
    )
    GLOSSY = BakeTextureTypeInfo(
        ui_name="Glossy",
        description="Bake current material output in Glossy mode",
        short_name="glossy",
        cycles_type=CyclesBakeType.GLOSSY,
    )
    TRANSMISSION = BakeTextureTypeInfo(
        ui_name="Transmission",
        description="Bake current material output Transmission mode",
        short_name="transmission",
        cycles_type=CyclesBakeType.TRANSMISSION,
    )

    def __init__(self, info: BakeTextureTypeInfo) -> None:
        self.short_name = info.short_name
        self.cycles_type = info.cycles_type
        self.colorspace = info.colorspace
        self.is_float = info.is_float

    DEFAULT = EMIT_COLOR


class BakeMode(BlenderPropertyEnum):
    """Bake modes."""

    __bl_prop_name__ = "Bake mode"
    __bl_prop_description__ = "Bake mode"

    value: EnumItemInfo

    SINGLE = EnumItemInfo(
        ui_name="Single Texture",
        description="Bake all materials from all objects into a single texture",
    )

    DEFAULT = SINGLE

    # PER_OBJECT = EnumItemInfo(
    #     ui_name="Per Object",
    #     description=(
    #         "Bake the materials of each object into a single texture. "
    #     ),
    # )
    # PER_MATERIAL = EnumItemInfo(
    #     ui_name="Per Material",
    #     description=(
    #         "Bake each material into separate textures"
    #     ),
    # )


class BakeState(BlenderPropertyEnum):
    """Bake states."""

    __bl_prop_name__ = "Render State"
    __bl_prop_description__ = "Render State"

    value: EnumItemInfo

    CANCELLED = EnumItemInfo(
        ui_name=icons.STRIP_COLOR_01,
        description="Bake cancelled or was not started yet",
    )
    QUEUED = EnumItemInfo(
        ui_name=icons.STRIP_COLOR_02,
        description="Bake queued",
    )
    RUNNING = EnumItemInfo(
        ui_name=icons.STRIP_COLOR_03,
        description="Bake running",
    )
    FINISHED = EnumItemInfo(
        ui_name=icons.STRIP_COLOR_04,
        description="Bake finished",
    )

    DEFAULT = CANCELLED
