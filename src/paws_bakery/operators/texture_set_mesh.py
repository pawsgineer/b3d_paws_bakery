"""Texture set mesh controls."""

from bpy import types as blt

from ..enums import BlenderOperatorReturnType
from ..props import get_props
from ..utils import Registry


@Registry.add
class TextureSetMeshAdd(blt.Operator):
    """Add Object to Texture Set."""

    bl_idname = "pawsbkr.texture_set_mesh_add"
    bl_label = "Add Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        assert texture_set

        for obj in context.selected_objects:
            if obj.type != "MESH":
                self.report({"WARNING"}, f"PAWSBKR: Object {obj.name!r} is not a mesh")
                continue

            if obj.name not in texture_set.meshes:
                mesh_props = texture_set.meshes.add()
                mesh_props.name = obj.name
                texture_set.sort_meshes()
            else:
                self.report({"INFO"}, f"PAWSBKR: Object {obj.name!r} already in set")

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetMeshRemove(blt.Operator):
    """Remove Object from Texture Set."""

    bl_idname = "pawsbkr.texture_set_mesh_remove"
    bl_label = "Remove Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set

        assert texture_set
        texture_set.meshes.remove(texture_set.meshes_active_index)

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetMeshClear(blt.Operator):
    """Remove all Objects from Texture Set."""

    bl_idname = "pawsbkr.texture_set_mesh_clear"
    bl_label = "Remove All Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set

        assert texture_set
        texture_set.meshes.clear()

        return {BlenderOperatorReturnType.FINISHED}
