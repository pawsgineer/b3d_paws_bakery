"""Addon Blender property enums."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from bpy import props as b_p

from .enums import Colorspace, CyclesBakeType

AnyTextureTypeAlias = TypeVar("AnyTextureTypeAlias", bound="TextureTypeAlias")


@dataclass(kw_only=True)
class _TextureTypeDescription:
    node_name: str
    aliases: list[str]


class TextureTypeAlias(Enum):
    "Aliases for texture names."

    ALBEDO = _TextureTypeDescription(
        aliases=["albedo", "color", "base"],
        node_name="texture_albedo",
    )
    METALNESS = _TextureTypeDescription(
        aliases=["metalness", "metallic", "metal"],
        node_name="texture_metalness",
    )
    ROUGHNESS = _TextureTypeDescription(
        aliases=["roughness", "rough"],
        node_name="texture_roughness",
    )
    NORMAL = _TextureTypeDescription(
        aliases=["normalgl", "normal", "nor"],
        node_name="texture_normal",
    )
    DISPLACEMENT = _TextureTypeDescription(
        aliases=["displacement", "height"],
        node_name="texture_displacement",
    )
    AMBIENT_OCCLUSION = _TextureTypeDescription(
        aliases=["ambientocclusion", "ao"],
        node_name="texture_ao",
    )
    AORM = _TextureTypeDescription(
        aliases=["aorm"],
        node_name="texture_aorm",
    )
    OPACITY = _TextureTypeDescription(
        aliases=["opacity"],
        node_name="texture_opacity",
    )
    EMISSION = _TextureTypeDescription(
        aliases=["emission", "emit"],
        node_name="texture_emission",
    )
    SCATTERING = _TextureTypeDescription(
        aliases=["scattering"],
        node_name="texture_scattering",
    )

    @property
    def node_name(self) -> str:
        "Return node name."

        return self.value.node_name

    def check_aliases(self, filename: str) -> bool:
        "Check if filename contains one of aliases."
        gen = (
            re.search(f"_{alias}" + r"[._\-\s]", filename.lower())
            for alias in self.value.aliases
        )

        return any(gen)

    @staticmethod
    def check_type(filename: str) -> AnyTextureTypeAlias | None:
        "Returns texture type or None."
        for texture_type in TextureTypeAlias:
            if texture_type.check_aliases(filename):
                return texture_type

        return None


@dataclass(kw_only=True)
class EnumItemInfo:
    "Common Blender enum item info."

    ui_name: str
    description: str


# NOTE: We're not using inheretance from dataclass because linting doesn't work
class BlenderPropertyEnum(Enum):
    "Aliases for texture names."

    __bl_prop__: type[b_p.EnumProperty] | None = None
    __bl_prop_name__: str
    __bl_prop_description__: str = ""

    value: EnumItemInfo
    DEFAULT: EnumItemInfo

    def __init__(self, _value: EnumItemInfo) -> None:
        assert self.__bl_prop_name__
        assert self.__bl_prop_description__ is not None

    @classmethod
    def get_blender_enum_property(cls) -> type[b_p.EnumProperty]:
        "Generates EnumProperty to use in blender props definition."
        if cls.__bl_prop__ is None:
            items = tuple((i.name, i.value.ui_name, i.value.description) for i in cls)
            cls.__bl_prop__ = b_p.EnumProperty(
                name=cls.__bl_prop_name__,
                description=cls.__bl_prop_description__,
                items=items,
                default=cls.DEFAULT.name if cls.DEFAULT is not None else None,
            )

        return cls.__bl_prop__


@dataclass(kw_only=True)
class BakeTextureTypeInfo(EnumItemInfo):
    "Texture type additional info."

    short_name: str
    cycles_type: str = CyclesBakeType.EMIT
    colorspace: Colorspace = Colorspace.DEFAULT
    is_float: bool = False


class BakeTextureType(BlenderPropertyEnum):
    "Aliases for texture names."

    __bl_prop_name__ = "Type"
    __bl_prop_description__ = "Texture Type"

    value: BakeTextureTypeInfo

    EMIT = BakeTextureTypeInfo(
        ui_name="Emit",
        description="Bake current material output in emit mode",
        short_name="emit",
    )
    EMIT_COLOR = DEFAULT = BakeTextureTypeInfo(
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
        description="Bake uv grid map",
        short_name="grid_uv",
    )

    def __init__(self, info: BakeTextureTypeInfo) -> None:
        self.short_name = info.short_name
        self.cycles_type = info.cycles_type
        self.colorspace = info.colorspace
        self.is_float = info.is_float
        super().__init__(info)


class BakeMode(BlenderPropertyEnum):
    "Aliases for texture names."

    __bl_prop_name__ = "Bake mode"

    value: EnumItemInfo

    SINGLE = DEFAULT = EnumItemInfo(
        ui_name="Single Texture",
        description="Bake all materials from all objects into a single texture",
    )
    # PER_OBJECT = EnumItemInfo(
    #     ui_name="Per Object",
    #     description=(
    #         "Bake the materials of each object into a single texture. "
    #         # TODO: Implement matching
    #         "Tries to match objects by names if 'Match active by suffix' enabled"
    #     ),
    # )
    # PER_MATERIAL = EnumItemInfo(
    #     ui_name="Per Material",
    #     description=(
    #         "Bake each material into separate textures"
    #         # TODO: Implement matching
    #         "Tries to match objects by names if 'Match active by suffix' enabled"
    #     ),
    # )


class BakeState(BlenderPropertyEnum):
    "Aliases for texture names."

    __bl_prop_name__ = "Render State"
    __bl_prop_description__ = "Render State"

    value: EnumItemInfo

    CANCELLED = DEFAULT = EnumItemInfo(
        ui_name="STRIP_COLOR_01",
        description="Bake cancelled or was not started yet",
    )
    QUEUED = EnumItemInfo(
        ui_name="STRIP_COLOR_02",
        description="Bake queued",
    )
    RUNNING = EnumItemInfo(
        ui_name="STRIP_COLOR_03",
        description="Bake running",
    )
    FINISHED = EnumItemInfo(
        ui_name="STRIP_COLOR_04",
        description="Bake finished",
    )
