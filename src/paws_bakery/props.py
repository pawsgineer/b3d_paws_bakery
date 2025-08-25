# flake8: noqa: F821
"""Addon Blender properties."""

from collections.abc import Mapping, Sequence
from typing import cast
from uuid import uuid4

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .props_enums import BakeMode, BakeState, BakeTextureType
from .utils import Registry

SIMPLE_BAKE_SETTINGS_ID = "pawsbkr_simple"


def _get_name(self: b_t.ID) -> str:
    return cast(str, self["name"])


def _set_force_uuid_name(self: b_t.ID, _value: str) -> None:
    prev_name = self.get("name")
    if not prev_name:
        self["name"] = str(uuid4())


@Registry.add
class BakeSettings(b_t.PropertyGroup):
    """Bake settings."""

    # NOTE: BakeSettings has the same id as Texture for matching
    # name: b_p.StringProperty(get=_get_name, set=_set_force_uuid_name)

    type: BakeTextureType.get_blender_enum_property()  # type: ignore[valid-type]

    name_template: b_p.StringProperty(  # type: ignore[valid-type]
        name="Name Template",
        description="Template of texture filename",
        default="{set_name}_{size}_{type_short}",
    )

    # TODO: use int vector?
    size: b_p.EnumProperty(  # type: ignore[valid-type]
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
        default="512",
    )
    sampling: b_p.EnumProperty(  # type: ignore[valid-type]
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
    samples: b_p.IntProperty(  # type: ignore[valid-type]
        name="Samples",
        description="Number of samples. Global value if 0",
        default=24,
        min=0,
    )
    use_denoising: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Denoise",
        description="Use denoising",
        default=False,
    )
    margin: b_p.IntProperty(  # type: ignore[valid-type]
        name="Margin",
        description="Margin",
        default=4,
    )
    margin_type: b_p.EnumProperty(  # type: ignore[valid-type]
        name="MarginType",
        description="Margin Type",
        items=(
            ("EXTEND", "EXTEND", ""),
            ("ADJACENT_FACES", "ADJACENT_FACES", ""),
        ),
        default="EXTEND",
    )

    # MATID
    matid_use_object_color: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Use Object Color",
        description="Use object color instead of material color for matid map",
        default=False,
    )

    # NORMAL
    match_active_by_suffix: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Match Active by Suffix",
        description="Mark mesh with '_low' suffix as active",
        default=True,
    )
    use_selected_to_active: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Selected To Active",
        description="Selected to active",
        default=False,
    )
    use_cage: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Cage",
        description="Cage",
        default=False,
    )
    cage_extrusion: b_p.FloatProperty(  # type: ignore[valid-type]
        name="Cage Extrusion",
        description="Cage Extrusion",
        default=0.0,
        soft_max=100,
        soft_min=0,
    )
    max_ray_distance: b_p.FloatProperty(  # type: ignore[valid-type]
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
class MaterialCreationSettings(b_t.PropertyGroup):
    """Addon material creation settings."""

    name_prefix: b_p.StringProperty(  # type: ignore[valid-type]
        name="Name Prefix",
        description="Prefix to add to the new material",
        default="",
        maxlen=64,
    )
    name_suffix: b_p.StringProperty(  # type: ignore[valid-type]
        name="Name Suffix",
        description="Suffix to add to the new material",
        default="_baked",
        maxlen=64,
    )
    mark_as_asset: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Mark as Asset",
        description="Mark created material as asset for Asset Library",
        default=False,
    )
    use_fake_user: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Use Fake User",
        description="Apply fake user to created material to prevent it's purge",
        default=False,
    )


@Registry.add
class UtilsSettings(b_t.PropertyGroup):
    """Addon bake settings."""

    unlink_baked_image: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Unlink Baked Image",
        description="Unlink the baked image from the current .blend file",
        default=False,
    )
    show_image_in_editor: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Show Baked Image In Editor",
        description="Load the image to the active editor view",
        default=True,
    )

    material_creation: b_p.PointerProperty(  # type: ignore[valid-type]
        type=MaterialCreationSettings,
    )

    debug_pause: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Debug pause", default=False
    )
    debug_pause_continue: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Continue",
        default=False,
    )


@Registry.add
class MeshProps(b_t.PropertyGroup):
    """Mesh properties."""

    is_enabled: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Bake enabled", default=True
    )
    state: BakeState.get_blender_enum_property()  # type: ignore[valid-type]

    def get_ref(self) -> b_t.Object | None:
        """Get a reference to the mesh."""
        return bpy.data.objects.get(self.name)

    def is_exist(self) -> bool:
        """Check if the mesh exists in the Blender data."""
        return self.get_ref() is not None


@Registry.add
class TextureProps(b_t.PropertyGroup):
    """Texture properties."""

    name: b_p.StringProperty(  # type: ignore[valid-type]
        get=_get_name, set=_set_force_uuid_name
    )

    is_enabled: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Bake enabled", default=True
    )
    state: BakeState.get_blender_enum_property()  # type: ignore[valid-type]
    last_bake_time: b_p.StringProperty(  # type: ignore[valid-type]
        name="Last Bake Time",
        description="Time spent on the last bake",
        default="-",
    )

    @property
    def prop_id(self) -> str:
        """Unique identifier for this item, used for lookups.

        NOTE: Avoid using `name` directly - it's error prone.
        """
        return cast(str, self.name)


@Registry.add
class TextureSetProps(b_t.PropertyGroup):
    """Texture set properties."""

    name: b_p.StringProperty(  # type: ignore[valid-type]
        get=_get_name, set=_set_force_uuid_name
    )

    create_materials: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Create Materials",
        description="Create materials from baked textures after baking",
        default=False,
    )

    create_materials_reuse_existing: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Reuse Existing",
        description=(
            "Add baked textures to the material already assigned to the object instead"
            " of creating a new material"
        ),
        default=False,
    )

    create_materials_template: b_p.PointerProperty(  # type: ignore[valid-type]
        name="Template",
        type=b_t.Material,
        description=(
            "Material template to use as base for created materials."
            "\nLeave empty to use default one"
        ),
    )

    create_materials_assign_to_objects: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Assign to Objects",
        description="Assign created materials to baked objects",
        default=True,
    )

    # TODO: add check for conflicts with texture types in name(rough, normal, etc)
    display_name: b_p.StringProperty(  # type: ignore[valid-type]
        name="Name", default="new_texture_set"
    )
    is_enabled: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Bake Enabled", default=True
    )

    meshes: b_p.CollectionProperty(type=MeshProps)  # type: ignore[valid-type]
    meshes_active_index: b_p.IntProperty()  # type: ignore[valid-type]

    textures: b_p.CollectionProperty(type=TextureProps)  # type: ignore[valid-type]
    textures_active_index: b_p.IntProperty()  # type: ignore[valid-type]

    mode: BakeMode.get_blender_enum_property()  # type: ignore[valid-type]

    @property
    def prop_id(self) -> str:
        """Unique identifier for this item, used for lookups.

        NOTE: Avoid using `name` directly - it's error prone.
        """
        return cast(str, self.name)

    @property
    def active_mesh(self) -> MeshProps | None:
        """Get active mesh."""
        try:
            return cast(MeshProps, self.meshes[self.meshes_active_index])
        except IndexError:
            return None

    @property
    def active_texture(self) -> TextureProps | None:
        """Get active texture."""
        try:
            return cast(TextureProps, self.textures[self.textures_active_index])
        except IndexError:
            return None

    def get_enabled_meshes(self) -> list[MeshProps]:
        """Get enabled meshes."""
        return [x for x in self.meshes if x.is_enabled]

    def get_disabled_meshes(self) -> list[MeshProps]:
        """Get disabled meshes."""
        return [x for x in self.meshes if not x.is_enabled]

    def get_enabled_textures(self) -> list[TextureProps]:
        """Get enabled textures."""
        return [x for x in self.textures if x.is_enabled]

    def get_disabled_textures(self) -> list[TextureProps]:
        """Get disabled textures."""
        return [x for x in self.textures if not x.is_enabled]


@Registry.add
class SceneProps(b_t.PropertyGroup):
    """Addon scene properties."""

    utils_settings: b_p.PointerProperty(type=UtilsSettings)  # type: ignore[valid-type]

    bake_settings_simple: b_p.PointerProperty(  # type: ignore[valid-type]
        type=BakeSettings, description="Settings for simple mode"
    )
    bake_settings_store: b_p.CollectionProperty(  # type: ignore[valid-type]
        type=BakeSettings, description="Settings for texture sets"
    )

    texture_sets: b_p.CollectionProperty(  # type: ignore[valid-type]
        type=TextureSetProps
    )
    texture_sets_active_index: b_p.IntProperty()  # type: ignore[valid-type]

    @property
    def active_texture_set(self) -> TextureSetProps | None:
        """Get active texture."""
        try:
            return cast(
                TextureSetProps, self.texture_sets[self.texture_sets_active_index]
            )
        except IndexError:
            return None


@Registry.add
class WMProps(b_t.PropertyGroup):
    """Addon Window Manager properties."""

    __slots__ = ()

    _settings_scene: b_t.Scene | None = None

    @property
    def settings_scene(self) -> b_t.Scene | None:
        """Reference to the active scene where the settings are stored."""
        return type(self)._settings_scene

    @settings_scene.setter
    def settings_scene(self, scene: b_t.Scene | None) -> None:
        type(self)._settings_scene = scene


def get_bake_settings(ctx: b_t.Context, settings_id: str) -> BakeSettings:
    """Return bake settings."""
    if settings_id == SIMPLE_BAKE_SETTINGS_ID:
        return cast(BakeSettings, get_props(ctx).bake_settings_simple)

    return cast(BakeSettings, get_props(ctx).bake_settings_store.get(settings_id))


def get_props(ctx: b_t.Context) -> SceneProps:
    """Return addon specific Scene properties for current context."""
    props_wm = get_props_wm(ctx)
    return get_props_scene(
        props_wm.settings_scene if props_wm.settings_scene else ctx.scene
    )


def get_props_scene(scene: b_t.Scene) -> SceneProps:
    """Return addon specific Scene properties."""
    return cast(SceneProps, scene.pawsbkr)  # type: ignore[attr-defined]


def get_props_wm(ctx: b_t.Context) -> WMProps:
    """Return addon specific WindowManager properties."""
    return cast(WMProps, ctx.window_manager.pawsbkr)  # type: ignore[attr-defined]
