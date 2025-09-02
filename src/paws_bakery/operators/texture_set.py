"""Texture set controls."""

from bpy import types as b_t

from ..enums import BlenderOperatorReturnType
from ..props import get_props
from ..utils import Registry


@Registry.add
class TextureSetAdd(b_t.Operator):
    """Add a new Texture Set."""

    bl_idname = "pawsbkr.texture_set_add"
    bl_label = "Add Texture Set"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: b_t.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_sets = pawsbkr.texture_sets
        t_set = texture_sets.add()
        t_set.name = ""

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetRemove(b_t.Operator):
    """Remove selected Texture Set."""

    bl_idname = "pawsbkr.texture_set_remove"
    bl_label = "Remove Texture Set"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: b_t.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_sets = pawsbkr.texture_sets
        texture_sets.remove(pawsbkr.texture_sets_active_index)

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureSetSort(b_t.Operator):
    """Sort Texture Sets."""

    bl_idname = "pawsbkr.texture_set_sort"
    bl_label = "Sort Texture Sets"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context: b_t.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        pawsbkr.sort_texture_sets()

        return {BlenderOperatorReturnType.FINISHED}
