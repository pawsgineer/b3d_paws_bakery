"""UI Panel - Texture Set."""

from typing import Any, cast

import bpy
from bpy import types as b_t

from ...enums import BlenderJobType
from ...operators import TextureSetAdd, TextureSetRemove
from ...operators.texture_set_bake import TextureSetBake
from ...operators.texture_set_material_create import TextureSetMaterialCreate
from ...preferences import get_preferences
from ...props import TextureSetProps, get_props
from .._utils import LayoutPanel, SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class SetUIList(b_t.UIList):
    """UI List - Texture Set."""

    bl_idname = "PAWSBKR_UL_texture_set"

    def draw_item(
        self,
        context: b_t.Context | None,
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
        assert item
        row = layout.row(align=True)
        row.prop(item, "is_enabled", text="")

        if not item.prop_id:
            row.alert = True
            row.label(text="Internal name not set", icon="ERROR")
            return
        if not item.display_name:
            row.alert = True
            row.label(text="Name not set", icon="ERROR")
            return

        row.label(text=item.display_name)

        if not get_props(context).texture_sets[item.prop_id].textures:
            row.alert = True
            row.label(text="No textures in set", icon="ERROR")
            return

        props = row.operator(TextureSetBake.bl_idname, icon="RENDER_STILL", text="")
        props.texture_set_id = item.prop_id

        if get_props(context).texture_sets[item.prop_id].create_materials:
            props = row.operator(
                TextureSetMaterialCreate.bl_idname, icon="MATERIAL", text=""
            )
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

            col = layout.column(align=True)
            col.prop(active_set, "mode")

            self._draw_material_creation(context, active_set)

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

    def _draw_material_creation(
        self, _context: b_t.Context, active_set: TextureSetProps
    ) -> None:
        header, panel = cast(
            LayoutPanel, self.layout.panel("mat_creation", default_closed=False)
        )
        header.prop(active_set, "create_materials", text="")
        header.label(text="Create Materials")
        if not panel:
            return

        panel.active = active_set.create_materials

        panel.prop(active_set, "create_materials_reuse_existing")
        if not active_set.create_materials_reuse_existing:
            panel.prop(active_set, "create_materials_assign_to_objects")
            panel.prop(active_set, "create_materials_template")
