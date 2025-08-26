"""Create Materials for Texture Set."""

from collections.abc import Sequence
from typing import cast

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log, log_err
from ..enums import BlenderOperatorReturnType, BlenderWMReportType
from ..props import MeshProps, TextureSetProps, get_bake_settings, get_props
from ..utils import AddonException, Registry, load_material_from_lib
from .bake_common import (
    ensure_mesh_ref,
    generate_image_name_and_path,
    match_low_to_high,
)
from .texture_import import UTIL_MATS_IMPORT_SAMPLE_NAME, assign_images_to_material


def generate_material_name(*, context: b_t.Context, texture_set_name: str) -> str:
    """Return generated material name."""
    utils_settings = get_props(context).utils_settings
    prefix = utils_settings.material_creation.name_prefix
    suffix = utils_settings.material_creation.name_suffix

    return f"{prefix}{texture_set_name}{suffix}"


@Registry.add
class TextureSetMaterialCreate(b_t.Operator):
    """Create materials from Texture Set textures."""

    bl_idname = "pawsbkr.texture_set_material_create"
    bl_label = "Create Materials from Baked Textures"
    bl_options = {"REGISTER", "UNDO"}

    texture_set_id: b_p.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    _texture_set: TextureSetProps

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
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


def _setup_material(
    *,
    context: b_t.Context,
    images: Sequence[b_t.Image],
    template_material: b_t.Material,
    texture_set: TextureSetProps,
    recreate: bool,
) -> b_t.Material:
    """Assign images to material.

    Creates new material if not exists.
    """
    mat_name = generate_material_name(
        context=context, texture_set_name=texture_set.display_name
    )
    mat = bpy.data.materials.get(mat_name)

    if recreate and mat:
        bpy.data.materials.remove(mat)
        mat = None

    if not mat:
        log(
            f"Material {mat_name!r} doesn't exist, creating from "
            f"{template_material!r}"
        )
        mat = cast(b_t.Material, template_material.copy())
        mat.name = mat_name

    opts = get_props(context).utils_settings.material_creation
    if opts.mark_as_asset:
        mat.asset_mark()  # type: ignore[no-untyped-call]
    if opts.use_fake_user:
        mat.use_fake_user = True

    assign_images_to_material(mat, images, True)

    return mat


def create_materials(*, context: b_t.Context, texture_set: TextureSetProps) -> None:
    """Create material with baked textures."""
    template_material = texture_set.create_materials_template
    if not template_material:
        template_material = load_material_from_lib(
            UTIL_MATS_IMPORT_SAMPLE_NAME, ignore_existing=True
        )

    images: dict[str, b_t.Image] = {}
    images_missing = []

    for texture_props in texture_set.get_enabled_textures():
        bake_settings = get_bake_settings(context, texture_props.prop_id)

        img_name, _ = generate_image_name_and_path(
            context=context,
            settings_id=texture_props.prop_id,
            texture_set_name=texture_set.display_name,
        )

        image = bpy.data.images.get(img_name)
        if image:
            images[bake_settings.type] = image
        else:
            images_missing.append(img_name)

    if not images or images_missing:
        raise AddonException(
            "No baked images found. Bake textures first. Images missing: "
            f"{images_missing}"
        )

    meshes_enabled: Sequence[MeshProps] = texture_set.get_enabled_meshes()
    bake_settings = get_bake_settings(context, texture_set.textures[0].prop_id)
    if bake_settings.use_selected_to_active and bake_settings.match_active_by_suffix:
        matching_names = match_low_to_high([m.name for m in meshes_enabled])
        meshes_to_update = [
            ensure_mesh_ref(texture_set.meshes[low_high_map.low])
            for low_high_map in matching_names
        ]
    else:
        meshes_to_update = [ensure_mesh_ref(m) for m in meshes_enabled]

    if texture_set.create_materials_reuse_existing:
        materials_to_update: set[b_t.Material] = set()
        for mesh_ref in meshes_to_update:
            for slot in mesh_ref.material_slots:
                if not slot.material:
                    continue
                materials_to_update.add(slot.material)

        for mat in materials_to_update:
            assign_images_to_material(mat, list(images.values()), True)

        return

    mat = _setup_material(
        context=context,
        images=list(images.values()),
        texture_set=texture_set,
        template_material=template_material,
        recreate=True,
    )

    if not texture_set.create_materials_assign_to_objects:
        return

    for mesh_ref in meshes_to_update:
        for slot in mesh_ref.material_slots:
            # if not slot.material:
            #     continue
            slot.material = mat
