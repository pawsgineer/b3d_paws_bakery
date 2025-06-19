"""UI Panel - Texture Set."""

from typing import Any

import bpy
from bpy import types as b_t

from ...enums import BlenderJobType
from ...operators import TextureSetAdd, TextureSetRemove
from ...operators.texture_set_bake import TextureSetBake
from ...preferences import get_preferences
from ...props import TextureSetProps, get_props
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class SetUIList(b_t.UIList):
    """UI List - Texture Set."""

    bl_idname = "PAWSBKR_UL_texture_set"

    def draw_item(
        self,
        _context: b_t.Context | None,
        layout: b_t.UILayout,
        _data: Any | None,
        item: TextureSetProps | None,
        _icon: int | None,
        _active_data: Any,
        _active_property: str | None,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        """draw() override."""
        layout.separator(factor=0.1)

        split = layout.row()
        split.prop(item, "is_enabled", text="")

        # split = split.split()

        if not item.prop_id:
            split.alert = True
            split.label(text="Internal name not set", icon="ERROR")
            return
        if not item.display_name:
            split.alert = True
            split.label(text="Name not set", icon="ERROR")
            return

        split.label(text=item.display_name)

        props = split.operator(TextureSetBake.bl_idname, icon="RENDER_STILL", text="")
        props.texture_set_id = item.prop_id


@register_and_duplicate_to_node_editor
class Main(SidePanelMixin):
    """UI Panel - Texture Set."""

    bl_idname = "PAWSBKR_PT_texture_set"
    bl_label = "Texture Set Bake"
    bl_order = 2

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        pawsbkr = get_props(context)
        active_set = pawsbkr.active_texture_set

        layout = self.layout

        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.alert = True
            row.scale_y = 2
            row.label(text="BAKING IN PROGRESS")

            layout.enabled = False
            layout.active = False

        if active_set is not None:
            row = layout.row(align=True)
            if not active_set.display_name:
                row.alert = True
            row.prop(active_set, "display_name")
            if get_preferences().enable_debug_tools:
                row = layout.row(align=True)
                row.label(text="bl name:")
                row.label(text=active_set.prop_id)

            row = layout.row()
            row.prop(active_set, "mode")

        row = layout.row()
        row.template_list(
            SetUIList.bl_idname,
            "pawsbkr_texture_sets",
            pawsbkr,
            "texture_sets",
            pawsbkr,
            "texture_sets_active_index",
            rows=2,
        )

        col = row.column(align=True)
        col.operator(TextureSetAdd.bl_idname, icon="ADD", text="")
        col.operator(TextureSetRemove.bl_idname, icon="REMOVE", text="")
