"""Texture set texture controls."""

from uuid import uuid4

import bpy
from bpy import props as b_p
from bpy import types as b_t

from ..enums import BlenderOperatorReturnType
from ..utils import AddonException, Registry
from ._utils import generate_color_set


@Registry.add
class TextureSetTextureAdd(b_t.Operator):
    """Add new Texture to Texture Set."""

    bl_idname = "pawsbkr.texture_set_texture_add"
    bl_label = "Add Texture"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.active_texture_set
        textures = texture_set.textures
        settings_store = pawsbkr.bake_settings_store

        texture = textures.add()
        texture.name = ""
        settings = settings_store.add()
        settings.name = texture.prop_id

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetTextureRemove(b_t.Operator):
    """Remove selected Texture from Texture Set."""

    bl_idname = "pawsbkr.texture_set_texture_remove"
    bl_label = "Remove Texture"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        pawsbkr = context.scene.pawsbkr
        settings_store = pawsbkr.bake_settings_store
        texture_set = pawsbkr.active_texture_set
        texture = texture_set.active_texture

        settings_store.remove(settings_store.find(texture.prop_id))
        texture_set.textures.remove(texture_set.textures_active_index)

        return {BlenderOperatorReturnType.FINISHED}


def _get_materials(context: b_t.Context, texture_set_id: str) -> set[b_t.Material]:
    pawsbkr = context.scene.pawsbkr
    texture_set = pawsbkr.texture_sets[texture_set_id]
    meshes = texture_set.meshes

    materials: set[b_t.Material] = set()

    for mesh in meshes:
        for slot in bpy.data.objects[mesh.name].material_slots:
            if slot.material is not None:
                materials.add(slot.material)

    return materials


@Registry.add
class TextureSetTextureSetupMaterial(b_t.Operator):
    """Setup material for texture baking."""

    bl_idname = "pawsbkr.texture_set_texture_setup_material"
    bl_label = "Setup Material"
    bl_options = {"REGISTER", "UNDO"}

    texture_set_id: b_p.StringProperty(name="Target texture set name", default="")
    texture_id: b_p.StringProperty(name="Target texture name", default="")

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if not self.texture_set_id:
            raise NotImplementedError("Baking without texture_set_id not implemented")
        if not self.texture_id:
            raise NotImplementedError("Baking without texture_id not implemented")

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.texture_set_id]
        textures = texture_set.textures
        texture = textures[self.texture_id]

        materials = _get_materials(context, self.texture_set_id)

        if not materials:
            raise AddonException("No materials found for specified objects")

        colors = generate_color_set(len(materials))
        for mat in materials:
            self.report({"INFO"}, f"Initializing material {mat.name!r}")
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)
            bpy.ops.pawsbkr.material_setup(
                target_material_name=mat.name,
                mat_id_color=colors[list(materials).index(mat)],
                texture_type=texture.get_bake_settings().type,
                settings_id=self.texture_id,
            )

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetTextureCleanupMaterial(b_t.Operator):
    """Cleanup material after texture baking."""

    bl_idname = "pawsbkr.texture_set_texture_cleanup_material"
    bl_label = "Cleanup Material"
    bl_options = {"REGISTER", "UNDO"}

    texture_set_id: b_p.StringProperty(name="Target texture set name", default="")

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if not self.texture_set_id:
            raise NotImplementedError("Baking without texture_set_id not implemented")

        materials = _get_materials(context, self.texture_set_id)

        if not materials:
            raise AddonException("No materials found for specified meshes")

        for mat in materials:
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)

        return {BlenderOperatorReturnType.FINISHED}
