# flake8: noqa: F821
"""Addon Blender properties."""

from collections.abc import Callable, Mapping
from typing import Any, TypeVar, cast
from uuid import uuid4

import bpy
from bpy import props as blp
from bpy import types as blt

from .common import sort_mesh_names
from .props_enums import BakeMode, BakeState, BakeTextureType
from .utils import Registry, naturalize_key

SIMPLE_BAKE_SETTINGS_ID = "pawsbkr_simple"


def _get_name(self: blt.ID) -> str:
    """Return custom property `name`. To be used as getter."""
    return cast(str, self["name"])


def _set_force_uuid_name(self: blt.ID, _value: str) -> None:
    """Set property `name` to UUID if empty."""
    prev_name = self.get("name")
    if not prev_name:
        self["name"] = str(uuid4())


class _UUIDNamePropertyGroup(blt.PropertyGroup):
    name: blp.StringProperty(  # type: ignore[valid-type]
        get=_get_name, set=_set_force_uuid_name
    )

    @property
    def prop_id(self) -> str:
        """Unique identifier for this item, used for lookups.

        NOTE: Avoid using `name` directly - it's error prone.
        """
        return cast(str, self.name)


@Registry.add
class BakeSettings(blt.PropertyGroup):
    """Bake settings."""

    # NOTE: BakeSettings has the same id as Texture for matching
    # name: blp.StringProperty(get=_get_name, set=_set_force_uuid_name)

    type: BakeTextureType.get_blender_enum_property()  # type: ignore[valid-type]

    name_template: blp.StringProperty(  # type: ignore[valid-type]
        name="Name Template",
        description="Template of texture filename",
        default="{set_name}_{size}_{type_short}",
    )

    # TODO: use int vector?
    size: blp.EnumProperty(  # type: ignore[valid-type]
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
    sampling: blp.EnumProperty(  # type: ignore[valid-type]
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
    samples: blp.IntProperty(  # type: ignore[valid-type]
        name="Samples",
        description="Number of samples. Global value if 0",
        default=24,
        min=0,
    )
    use_denoising: blp.BoolProperty(  # type: ignore[valid-type]
        name="Denoise",
        description="Use denoising",
        default=False,
    )
    margin: blp.IntProperty(  # type: ignore[valid-type]
        name="Margin",
        description="Margin",
        default=4,
    )
    margin_type: blp.EnumProperty(  # type: ignore[valid-type]
        name="MarginType",
        description="Margin Type",
        items=(
            ("EXTEND", "EXTEND", ""),
            ("ADJACENT_FACES", "ADJACENT_FACES", ""),
        ),
        default="EXTEND",
    )

    # MATID
    matid_use_object_color: blp.BoolProperty(  # type: ignore[valid-type]
        name="Use Object Color",
        description="Use object color instead of material color for matid map",
        default=False,
    )

    # NORMAL
    match_active_by_suffix: blp.BoolProperty(  # type: ignore[valid-type]
        name="Match Active by Suffix",
        description="Mark mesh with '_low' suffix as active",
        default=True,
    )
    use_selected_to_active: blp.BoolProperty(  # type: ignore[valid-type]
        name="Selected To Active",
        description="Selected to active",
        default=False,
    )
    use_cage: blp.BoolProperty(  # type: ignore[valid-type]
        name="Cage",
        description="Cage",
        default=False,
    )
    cage_extrusion: blp.FloatProperty(  # type: ignore[valid-type]
        name="Cage Extrusion",
        description="Cage Extrusion",
        default=0.0,
        soft_max=100,
        soft_min=0,
    )
    max_ray_distance: blp.FloatProperty(  # type: ignore[valid-type]
        name="Ray Distance",
        description="Ray Distance",
        default=0.0,
        soft_max=100,
        soft_min=0,
    )

    @property
    def bake_high_to_low(self) -> bool:
        """Whether baking should run from high to low matched by name."""
        return cast(bool, self.use_selected_to_active and self.match_active_by_suffix)

    def get_name(self, set_name: str = "") -> str:
        """Return compiled name."""
        placeholders: Mapping[str, str] = {
            "set_name": set_name,
            "size": self.size,
            "type_short": BakeTextureType[self.type].short_name,
            "type_full": BakeTextureType[self.type].name.lower(),
        }

        template_computed: str = self.name_template.format_map(placeholders)

        return template_computed


@Registry.add
class MaterialCreationSettings(blt.PropertyGroup):
    """Addon material creation settings."""

    name_prefix: blp.StringProperty(  # type: ignore[valid-type]
        name="Name Prefix",
        description="Prefix to add to the new material",
        default="",
        maxlen=64,
    )
    name_suffix: blp.StringProperty(  # type: ignore[valid-type]
        name="Name Suffix",
        description="Suffix to add to the new material",
        default="_baked",
        maxlen=64,
    )
    mark_as_asset: blp.BoolProperty(  # type: ignore[valid-type]
        name="Mark as Asset",
        description="Mark created material as asset for Asset Library",
        default=False,
    )
    use_fake_user: blp.BoolProperty(  # type: ignore[valid-type]
        name="Use Fake User",
        description="Apply fake user to created material to prevent it's purge",
        default=False,
    )


@Registry.add
class UtilsSettings(blt.PropertyGroup):
    """Addon bake settings."""

    unlink_baked_image: blp.BoolProperty(  # type: ignore[valid-type]
        name="Unlink Baked Image",
        description="Unlink the baked image from the current .blend file",
        default=False,
    )
    show_image_in_editor: blp.BoolProperty(  # type: ignore[valid-type]
        name="Show Baked Image In Editor",
        description="Load the image to the active editor view",
        default=True,
    )

    material_creation: blp.PointerProperty(  # type: ignore[valid-type]
        type=MaterialCreationSettings,
    )

    debug_pause: blp.BoolProperty(  # type: ignore[valid-type]
        name="Debug pause", default=False
    )
    debug_pause_continue: blp.BoolProperty(  # type: ignore[valid-type]
        name="Continue",
        default=False,
    )


@Registry.add
class MeshProps(blt.PropertyGroup):
    """Mesh properties."""

    is_enabled: blp.BoolProperty(  # type: ignore[valid-type]
        name="Bake enabled", default=True
    )
    state: BakeState.get_blender_enum_property()  # type: ignore[valid-type]

    def get_ref(self) -> blt.Object | None:
        """Get a reference to the mesh."""
        return bpy.data.objects.get(self.name)

    def ensure_mesh_ref(self) -> blt.Object:
        """Ensure Object exists.

        :raises ValueError: When object doesn't exist.
        :return: Blender Object
        """
        mesh_ref: blt.Object | None = self.get_ref()
        if mesh_ref is None:
            raise ValueError(f"Can not find Object with name {self.name!r}")
        return mesh_ref

    def is_exist(self) -> bool:
        """Check if the mesh exists in the Blender data."""
        return self.get_ref() is not None


@Registry.add
class TextureProps(_UUIDNamePropertyGroup):
    """Texture properties."""

    is_enabled: blp.BoolProperty(  # type: ignore[valid-type]
        name="Bake enabled", default=True
    )
    state: BakeState.get_blender_enum_property()  # type: ignore[valid-type]
    last_bake_time: blp.StringProperty(  # type: ignore[valid-type]
        name="Last Bake Time",
        description="Time spent on the last bake",
        default="-",
    )


@Registry.add
class TextureSetProps(_UUIDNamePropertyGroup):
    """Texture set properties."""

    create_materials: blp.BoolProperty(  # type: ignore[valid-type]
        name="Create Materials",
        description="Create materials from baked textures after baking",
        default=False,
    )

    create_materials_reuse_existing: blp.BoolProperty(  # type: ignore[valid-type]
        name="Reuse Existing",
        description=(
            "Add baked textures to the material already assigned to the object instead"
            " of creating a new material"
        ),
        default=False,
    )

    create_materials_template: blp.PointerProperty(  # type: ignore[valid-type]
        name="Template",
        type=blt.Material,
        description=(
            "Material template to use as base for created materials."
            "\nLeave empty to use default one"
        ),
    )

    create_materials_assign_to_objects: blp.BoolProperty(  # type: ignore[valid-type]
        name="Assign to Objects",
        description="Assign created materials to baked objects",
        default=True,
    )

    # TODO: add check for conflicts with texture types in name(rough, normal, etc)
    display_name: blp.StringProperty(  # type: ignore[valid-type]
        name="Name", default="new_texture_set"
    )
    is_enabled: blp.BoolProperty(  # type: ignore[valid-type]
        name="Bake Enabled", default=True
    )

    meshes: blp.CollectionProperty(type=MeshProps)  # type: ignore[valid-type]
    meshes_active_index: blp.IntProperty()  # type: ignore[valid-type]

    textures: blp.CollectionProperty(type=TextureProps)  # type: ignore[valid-type]
    textures_active_index: blp.IntProperty()  # type: ignore[valid-type]

    mode: BakeMode.get_blender_enum_property()  # type: ignore[valid-type]

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

    def sort_meshes(self) -> None:
        """Sort meshes."""
        meshes_sorted = [
            self.meshes[name]
            for name in sort_mesh_names([mesh_props.name for mesh_props in self.meshes])
        ]

        new_active_idx = sort_collection_property(
            self.meshes,
            active_name=self.active_mesh.name if self.active_mesh else "",
            sorted_collection=cast(list[blt.ID], meshes_sorted),
        )
        self.meshes_active_index = new_active_idx

    def sort_textures(self) -> None:
        """Sort textures."""

        def key(x: TextureProps) -> list[str | int]:
            return naturalize_key(
                get_bake_settings(bpy.context, x.name).get_name(self.display_name)
            )

        new_active_idx = sort_collection_property(
            self.textures,
            active_name=self.active_texture.name if self.active_texture else "",
            key=key,  # type: ignore[type-var]
        )
        self.textures_active_index = new_active_idx


@Registry.add
class SceneProps(blt.PropertyGroup):
    """Addon scene properties."""

    utils_settings: blp.PointerProperty(type=UtilsSettings)  # type: ignore[valid-type]

    bake_settings_simple: blp.PointerProperty(  # type: ignore[valid-type]
        type=BakeSettings, description="Settings for simple mode"
    )
    bake_settings_store: blp.CollectionProperty(  # type: ignore[valid-type]
        type=BakeSettings, description="Settings for texture sets"
    )

    texture_sets: blp.CollectionProperty(  # type: ignore[valid-type]
        type=TextureSetProps
    )
    texture_sets_active_index: blp.IntProperty()  # type: ignore[valid-type]

    @property
    def active_texture_set(self) -> TextureSetProps | None:
        """Get active texture."""
        try:
            return cast(
                TextureSetProps, self.texture_sets[self.texture_sets_active_index]
            )
        except IndexError:
            return None

    def sort_texture_sets(self) -> None:
        """Sort texture sets."""
        active_ts = self.active_texture_set
        new_active_idx = sort_collection_property(
            self.texture_sets,
            active_name=active_ts.name if active_ts else "",
            key=lambda tset: naturalize_key(
                tset.display_name  # type: ignore[attr-defined]
            ),
        )
        self.texture_sets_active_index = new_active_idx


@Registry.add
class WMProps(blt.PropertyGroup):
    """Addon Window Manager properties."""

    __slots__ = ()

    _settings_scene: blt.Scene | None = None

    @property
    def settings_scene(self) -> blt.Scene | None:
        """Reference to the active scene where the settings are stored."""
        return type(self)._settings_scene

    @settings_scene.setter
    def settings_scene(self, scene: blt.Scene | None) -> None:
        type(self)._settings_scene = scene


def get_bake_settings(ctx: blt.Context, settings_id: str) -> BakeSettings:
    """Return bake settings."""
    if settings_id == SIMPLE_BAKE_SETTINGS_ID:
        return cast(BakeSettings, get_props(ctx).bake_settings_simple)

    return cast(BakeSettings, get_props(ctx).bake_settings_store.get(settings_id))


def get_props(ctx: blt.Context) -> SceneProps:
    """Return addon specific Scene properties for current context."""
    props_wm = get_props_wm(ctx)
    return get_props_scene(
        props_wm.settings_scene if props_wm.settings_scene else ctx.scene
    )


def get_props_scene(scene: blt.Scene) -> SceneProps:
    """Return addon specific Scene properties."""
    return cast(SceneProps, scene.pawsbkr)  # type: ignore[attr-defined]


def get_props_wm(ctx: blt.Context) -> WMProps:
    """Return addon specific WindowManager properties."""
    return cast(WMProps, ctx.window_manager.pawsbkr)  # type: ignore[attr-defined]


_PCollT = TypeVar("_PCollT", bound=blt.bpy_prop_collection)  # type: ignore[type-arg]
_PCollItemT = TypeVar("_PCollItemT", bound=blt.ID)


def sort_collection_property(
    collection: _PCollT,
    *,
    key: Callable[[_PCollItemT], Any] | None = None,
    sorted_collection: list[_PCollItemT] | None = None,
    active_name: str = "",
    reverse: bool = False,
) -> int:
    """Sort items of a collection property in-place.

    :param collection: Collection
    :param key: Key function to get sorting key from items, defaults to naturalized
    `item.name`
    :param sorted_collection: Pre-sorted list to use instead of key, if set the method
    only moves items inside the collection
    :param active_name: Name of the current active item, defaults to ""
    :param reverse: Sort in descending order
    :return: New index of the active item
    """
    if key and sorted_collection:
        raise ValueError("Provide either key or sorted_collection, not both")

    if sorted_collection is not None:
        coll_sorted = sorted_collection
    else:
        coll_sorted = cast(list[_PCollItemT], collection[:])
        coll_sorted.sort(
            key=key if key else lambda x: naturalize_key(x.name),
            reverse=reverse,
        )

    for idx, name in enumerate([x.name for x in coll_sorted]):
        current_idx = collection.find(name)
        if current_idx == idx:
            continue
        collection.move(current_idx, idx)  # type: ignore[attr-defined]

    return collection.find(active_name) if active_name else 0
