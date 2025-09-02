"""Randomize objects color."""

from collections.abc import Sequence

import bpy
from bpy import props as blp
from bpy import types as blt

from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderOperatorType as BOT
from ..utils import Registry
from ._utils import generate_color_set


@Registry.add
class RandomizeColor(blt.Operator):
    """Randomize objects color."""

    bl_idname = "pawsbkr.randomize_color"
    bl_label = "Randomize Color"
    bl_options = {BOT.REGISTER, BOT.UNDO}

    target_object: blp.StringProperty(  # type: ignore[valid-type]
        name="Target Object",
        description="Object to randomize color. If empty, applies to all selected",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        if self.target_object:
            targets: Sequence[bpy.types.Object] = [bpy.data.objects[self.target_object]]
        else:
            targets = context.selected_objects

        colors = generate_color_set(len(targets))

        for i, obj in enumerate(targets):
            new_color = colors[i]
            obj.color = new_color + (1.0,)

        return {BORT.FINISHED}
