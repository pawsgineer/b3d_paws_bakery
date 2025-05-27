# flake8: noqa: F821
"""Addon Blender properties."""

from typing import Mapping
from uuid import uuid4

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .props_enums import BakeMode, BakeState, BakeTextureType
from .utils import Registry

SIMPLE_BAKE_SETTINGS_ID = "pawsbkr_simple"


def _get_name(self) -> str:
    return self["name"]


def _set_force_uuid_name(self, _value) -> None:
    prev_name = self.get("name")
    if not prev_name:
        self["name"] = str(uuid4())


@Registry.add
class BakeSettings(b_t.PropertyGroup):
    """Bake settings."""

    name: b_p.StringProperty(get=_get_name, set=_set_force_uuid_name)

    @property
    def prop_id(self) -> str:
        """Unique identifier for this item, used for lookups.

        NOTE: Avoid using `name` directly - it's error prone.
        """
        return self.name

    type: BakeTextureType.get_blender_enum_property()

    name_template: b_p.StringProperty(
        name="Name Template",
        description="Template of texture filename",
        default="{set_name}_{size}_{type_short}",
    )

    # TODO: use int vector?
    size: b_p.EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("64", "64", ""),
            ("128", "128", ""),
            ("256", "256", ""),
            ("512", "512", ""),
            ("1024", "1024", ""),
            ("2048", "2048", ""),
            ("4096", "4096", ""),
            ("8192", "8192", ""),
        ),
        default="2048",
    )
    sampling: b_p.EnumProperty(
        name="AA",
        description="Anti Aliasing",
        items=(
            ("1", "None", ""),
            ("2", "2x", ""),
            ("4", "4x", ""),
            ("8", "8x", ""),
        ),
        default="1",
    )
    samples: b_p.IntProperty(
        name="Samples",
        description="Number of samples. Global value if 0",
        default=48,
        min=0,
    )
    use_denoising: b_p.BoolProperty(
        name="Denoise",
        description="Use denoising",
        default=False,
    )
    margin: b_p.IntProperty(
        name="Margin",
        description="Margin",
        default=24,
    )
    margin_type: b_p.EnumProperty(
        name="MarginType",
        description="Margin Type",
        items=(
            ("EXTEND", "EXTEND", ""),
            ("ADJACENT_FACES", "ADJACENT_FACES", ""),
        ),
        default="EXTEND",
    )

    # MATID
    matid_use_object_color: b_p.BoolProperty(
        name="Use object color",
        description="Use object color instead of material color for matid map",
        default=False,
    )

    # NORMAL
    match_active_by_suffix: b_p.BoolProperty(
        name="Match active by suffix",
        description="Mark mesh with '_low' suffix as active",
        default=True,
    )
    use_selected_to_active: b_p.BoolProperty(
        name="Selected to active",
        description="Selected to active",
        default=False,
    )
    use_cage: b_p.BoolProperty(
        name="Cage",
        description="Cage",
        default=False,
    )
    cage_extrusion: b_p.FloatProperty(
        name="Cage Extrusion",
        description="Cage Extrusion",
        default=0.0,
        soft_max=100,
        soft_min=0,
    )
    max_ray_distance: b_p.FloatProperty(
        name="Ray Distance",
        description="Ray Distance",
        default=0.0,
        soft_max=100,
        soft_min=0,
    )

    def get_name(self, set_name: str = "") -> str:
        """Returns compiled name."""
        placeholders: Mapping[str, str] = {
            "set_name": set_name,
            "size": self.size,
            "type_short": BakeTextureType[self.type].short_name,
            "type_full": BakeTextureType[self.type].name.lower(),
        }

        template_computed: str = self.name_template.format_map(placeholders)

        return template_computed


@Registry.add
class UtilsSettings(b_t.PropertyGroup):
    """Addon bake settings."""

    unlink_baked_image: b_p.BoolProperty(
        name="Unlink baked image",
        description="Unlink the baked image from the current .blend file",
        default=False,
    )
    show_image_in_editor: b_p.BoolProperty(
        name="Show baked image in editor",
        description="Load the image to the active editor view",
        default=True,
    )

    debug_pause: b_p.BoolProperty(name="Debug pause", default=False)
    debug_pause_continue: b_p.BoolProperty(name="Continue", default=False)


@Registry.add
class MeshProps(b_t.PropertyGroup):
    """Mesh properties."""

    is_enabled: b_p.BoolProperty(name="Bake enabled", default=True)
    state: BakeState.get_blender_enum_property()

    def get_ref(self) -> b_t.Object | None:
        """Get a reference to the mesh."""
        return bpy.data.objects.get(self.name)

    def is_exist(self) -> bool:
        """Check if the mesh exists in the Blender data."""
        return self.get_ref() is not None


@Registry.add
class TextureProps(b_t.PropertyGroup):
    """Texture properties."""

    is_enabled: b_p.BoolProperty(name="Bake enabled", default=True)
    state: BakeState.get_blender_enum_property()
    last_bake_time: b_p.StringProperty(
        name="Last Bake Time",
        description="Time spent on the last bake",
        default="-",
    )

    def get_bake_settings(self) -> BakeSettings:
        """Returns reference to texture bake settings."""
        return bpy.context.scene.pawsbkr.get_bake_settings(self.name)


@Registry.add
class TextureSetProps(b_t.PropertyGroup):
    """Texture set properties."""

    name: b_p.StringProperty(get=_get_name, set=_set_force_uuid_name)

    # TODO: add check for conflicts with texture types in name(rough, normal, etc)
    display_name: b_p.StringProperty(name="Texture Name", default="new_texture_set")
    is_enabled: b_p.BoolProperty(name="Bake Enabled", default=True)

    meshes: b_p.CollectionProperty(type=MeshProps)
    meshes_active_index: b_p.IntProperty()

    textures: b_p.CollectionProperty(type=TextureProps)
    textures_active_index: b_p.IntProperty()

    mode: BakeMode.get_blender_enum_property()

    @property
    def prop_id(self) -> str:
        """Unique identifier for this item, used for lookups.

        NOTE: Avoid using `name` directly - it's error prone.
        """
        return self.name

    @property
    def active_mesh(self) -> MeshProps | None:
        """Get active mesh."""
        try:
            return self.meshes[self.meshes_active_index]
        except IndexError:
            return None

    @property
    def active_texture(self) -> TextureProps | None:
        """Get active texture."""
        try:
            return self.textures[self.textures_active_index]
        except IndexError:
            return None


@Registry.add
class SceneProps(b_t.PropertyGroup):
    """Addon scene properties."""

    utils_settings: b_p.PointerProperty(type=UtilsSettings)

    bake_settings_simple: b_p.PointerProperty(
        type=BakeSettings, description="Settings for simple mode"
    )
    bake_settings_store: b_p.CollectionProperty(
        type=BakeSettings, description="Settings for texture sets"
    )

    texture_sets: b_p.CollectionProperty(type=TextureSetProps)
    texture_sets_active_index: b_p.IntProperty()

    @property
    def active_texture_set(self) -> TextureSetProps | None:
        """Get active texture."""
        try:
            return self.texture_sets[self.texture_sets_active_index]
        except IndexError:
            return None

    def get_bake_settings(self, settings_id: str) -> BakeSettings:
        """Get bake settings."""
        if settings_id == SIMPLE_BAKE_SETTINGS_ID:
            return self.bake_settings_simple

        return bpy.context.scene.pawsbkr.bake_settings_store.get(settings_id)
