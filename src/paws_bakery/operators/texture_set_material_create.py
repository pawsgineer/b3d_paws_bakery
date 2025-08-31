"""Create Materials for Texture Set."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import chain
from typing import cast

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log, log_err
from ..enums import BlenderOperatorReturnType, BlenderWMReportType
from ..props import MeshProps, TextureSetProps, get_bake_settings, get_props
from ..props_enums import BakeMode
from ..utils import AddonException, AssetLibraryManager, Registry
from .bake_common import (
    ensure_mesh_ref,
    generate_image_name_and_path,
    match_low_to_high,
)
from .texture_import import UTIL_MATS_IMPORT_SAMPLE_NAME, assign_images_to_material


@Registry.add
class TextureSetMaterialCreate(b_t.Operator):
    """Create materials from Texture Set textures."""

    bl_idname = "pawsbkr.texture_set_material_create"
    bl_label = "Create Materials from Baked Textures"

    texture_set_id: b_p.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    _texture_set: TextureSetProps

    def execute(self, context: b_t.Context) -> set[str]:  # noqa: D102
        if not self.texture_set_id:
            raise AddonException("texture_set_id is required")

        self._texture_set = get_props(context).texture_sets[self.texture_set_id]

        try:
            create_materials(context=context, texture_set=self._texture_set)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            msg = f"Failed to create materials: {ex}"
            log_err(msg, with_tb=True)
            self.report({BlenderWMReportType.ERROR}, msg)
            return {BlenderOperatorReturnType.CANCELLED}

        return {BlenderOperatorReturnType.FINISHED}


@dataclass(kw_only=True)
class _MaterialUpdateInfo:
    name: str
    meshes: list[b_t.Object]
    images: list[b_t.Image]


def create_materials(*, context: b_t.Context, texture_set: TextureSetProps) -> None:
    """Create material with baked textures."""
    template_material = texture_set.create_materials_template
    if not template_material:
        template_material = AssetLibraryManager.material_load(
            UTIL_MATS_IMPORT_SAMPLE_NAME
        )

    mat_info_list = _collect_material_update_info(
        context=context, texture_set=texture_set
    )

    bpy.ops.ed.undo_push(message="Create Materials")
    for mat_info in mat_info_list:
        if texture_set.create_materials_reuse_existing:
            for mat in set(
                chain.from_iterable(
                    _get_object_materials(mesh) for mesh in mat_info.meshes
                )
            ):
                assign_images_to_material(mat, mat_info.images, True)
            continue

        mat = _setup_material(
            context=context,
            name=mat_info.name,
            images=mat_info.images,
            template_material=template_material,
            recreate=True,
        )

    if not texture_set.create_materials_assign_to_objects:
        return

    bpy.ops.ed.undo_push(message="Assign Materials")
    for mat_info in mat_info_list:
        for mesh in mat_info.meshes:
            for slot in mesh.material_slots:
                slot.material = bpy.data.materials.get(mat_info.name)


def _collect_material_update_info(
    *, context: b_t.Context, texture_set: TextureSetProps
) -> list[_MaterialUpdateInfo]:
    meshes_to_update = _get_meshes_to_update(context=context, texture_set=texture_set)
    mat_info_list: list[_MaterialUpdateInfo] = []
    if BakeMode[texture_set.mode] is BakeMode.PER_OBJECT:
        for mesh in meshes_to_update:
            mat_info_list.append(
                _MaterialUpdateInfo(
                    name=_generate_material_name(
                        context=context,
                        texture_set_name=texture_set.display_name,
                        object_prefix=mesh.name,
                    ),
                    meshes=[mesh],
                    images=_load_images(
                        context=context,
                        texture_set=texture_set,
                        object_prefix=mesh.name,
                    ),
                )
            )
    else:
        mat_info_list.append(
            _MaterialUpdateInfo(
                name=_generate_material_name(
                    context=context, texture_set_name=texture_set.display_name
                ),
                meshes=meshes_to_update,
                images=_load_images(context=context, texture_set=texture_set),
            )
        )

    return mat_info_list


def _get_meshes_to_update(
    *, context: b_t.Context, texture_set: TextureSetProps
) -> list[b_t.Object]:
    meshes_enabled: list[MeshProps] = texture_set.get_enabled_meshes()
    bake_settings = get_bake_settings(context, texture_set.textures[0].prop_id)
    if bake_settings.use_selected_to_active and bake_settings.match_active_by_suffix:
        matching_names = match_low_to_high([m.name for m in meshes_enabled])
        meshes_to_update = [
            ensure_mesh_ref(texture_set.meshes[low_high_map.low])
            for low_high_map in matching_names
        ]
    else:
        meshes_to_update = [ensure_mesh_ref(m) for m in meshes_enabled]

    return meshes_to_update


def _generate_material_name(
    *, context: b_t.Context, texture_set_name: str, object_prefix: str = ""
) -> str:
    """Return generated material name."""
    utils_settings = get_props(context).utils_settings
    prefix = utils_settings.material_creation.name_prefix
    suffix = utils_settings.material_creation.name_suffix
    if object_prefix:
        texture_set_name = "_".join([object_prefix, texture_set_name])

    return f"{prefix}{texture_set_name}{suffix}"


def _load_images(
    *,
    context: b_t.Context,
    texture_set: TextureSetProps,
    object_prefix: str = "",
) -> list[b_t.Image]:
    images: list[b_t.Image] = []
    images_missing: list[str] = []

    for texture_props in texture_set.get_enabled_textures():
        img_name, _ = generate_image_name_and_path(
            context=context,
            settings_id=texture_props.prop_id,
            texture_set_name=texture_set.display_name,
            object_prefix=object_prefix,
        )

        image = bpy.data.images.get(img_name)
        if image:
            images.append(image)
        else:
            images_missing.append(img_name)

    if not images or images_missing:
        raise AddonException(
            "No baked images found. Bake textures first. Images missing: "
            f"{images_missing}"
        )

    return images


def _get_object_materials(bobj: b_t.Object) -> set[b_t.Material]:
    mats: set[b_t.Material] = set()
    for slot in bobj.material_slots:
        if not slot.material:
            continue
        mats.add(slot.material)

    return mats


def _setup_material(
    *,
    context: b_t.Context,
    name: str,
    images: Sequence[b_t.Image],
    template_material: b_t.Material,
    recreate: bool,
) -> b_t.Material:
    """Assign images to material.

    Creates new material if not exists.
    """
    mat: b_t.Material | None = bpy.data.materials.get(name)

    if recreate and mat:
        bpy.data.materials.remove(mat)
        mat = None

    if not mat:
        log(f"Material {name!r} doesn't exist, creating from {template_material!r}")
        mat = cast(b_t.Material, template_material.copy())
        mat.name = name

    opts = get_props(context).utils_settings.material_creation
    if opts.mark_as_asset:
        mat.asset_mark()  # type: ignore[no-untyped-call]
    if opts.use_fake_user:
        mat.use_fake_user = True

    assign_images_to_material(mat, images, True)

    return mat
