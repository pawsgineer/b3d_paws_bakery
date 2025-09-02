"""Texture set controls."""

from bpy import types as blt

from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderOperatorType as BOT
from ..props import get_props
from ..utils import Registry


@Registry.add
class TextureSetAdd(blt.Operator):
    """Add a new Texture Set."""

    bl_idname = "pawsbkr.texture_set_add"
    bl_label = "Add Texture Set"
    bl_options = {BOT.REGISTER, BOT.UNDO}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_sets = pawsbkr.texture_sets
        t_set = texture_sets.add()
        t_set.name = ""

        return {BORT.FINISHED}


@Registry.add
class TextureSetRemove(blt.Operator):
    """Remove selected Texture Set."""

    bl_idname = "pawsbkr.texture_set_remove"
    bl_label = "Remove Texture Set"
    bl_options = {BOT.REGISTER, BOT.UNDO}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        texture_sets = pawsbkr.texture_sets
        texture_sets.remove(pawsbkr.texture_sets_active_index)

        return {BORT.FINISHED}


@Registry.add
class TextureSetSort(blt.Operator):
    """Sort Texture Sets."""

    bl_idname = "pawsbkr.texture_set_sort"
    bl_label = "Sort Texture Sets"
    bl_options = {BOT.UNDO, BOT.INTERNAL}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        pawsbkr = get_props(context)
        pawsbkr.sort_texture_sets()

        return {BORT.FINISHED}
