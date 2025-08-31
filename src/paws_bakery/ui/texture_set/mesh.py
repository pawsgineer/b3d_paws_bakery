"""UI Panel - Texture Set Mesh."""

from typing import Any

import bpy
from bpy import types as b_t

from ...enums import BlenderJobType
from ...operators import TextureSetMeshAdd, TextureSetMeshClear, TextureSetMeshRemove
from ...props import MeshProps, get_props
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class MeshSpecialsMenu(b_t.Menu):
    """Mesh specials menu."""

    bl_idname = "PAWSBKR_MT_texture_set_mesh_specials"
    bl_label = "Mesh Specials"

    def draw(self, _context: b_t.Context | None) -> None:  # noqa: D102
        layout = self.layout
        subl = layout.column(align=True)
        subl.operator(TextureSetMeshClear.bl_idname, icon="CANCEL")


@register_and_duplicate_to_node_editor
class MeshUIList(b_t.UIList):
    """UI List - Texture Set meshes."""

    bl_idname = "PAWSBKR_UL_texture_set_meshes"

    def draw_item(  # noqa: D102
        self,
        _context: b_t.Context | None,
        layout: b_t.UILayout,
        _data: Any | None,
        item: MeshProps | None,
        _icon: int | None,
        _active_data: Any,
        _active_property: str | None,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        assert item

        row = layout.split(factor=0.05)
        row.label(
            text="",
            icon=row.enum_item_name(item, "state", item.state),
        )

        row = row.split(factor=0.05)
        row.prop(item, "is_enabled", text="")

        obj = item.get_ref()
        if obj is None:
            row.alert = True
            row.label(text=f"{item.name}(Object with this name doesn't exist)")
            return

        row = row.split(factor=0.65)
        row.label(text=f"{item.name}")

        active_uv_layer = next(
            (
                layer
                for layer in item.get_ref().data.uv_layers
                if layer.active_render is True
            ),
            None,
        )

        # TODO: Implement UV Map selection
        if active_uv_layer is None:
            row.alert = True
            row.label(text="No active UV map")
        else:
            row.label(text=f"{active_uv_layer.name}")


@register_and_duplicate_to_node_editor
class Meshes(SidePanelMixin):
    """UI Panel - Texture Set - Meshes."""

    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_main_texture_set_meshes"
    bl_label = "Objects"

    @classmethod
    def poll(cls, context: b_t.Context) -> bool:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        return texture_set is not None

    def draw_header(self, context: b_t.Context) -> None:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        assert texture_set
        if len(texture_set.meshes) < 1:
            self.layout.alert = True
            self.layout.label(text="", icon="ERROR")

    def draw(self, context: b_t.Context) -> None:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set

        layout = self.layout

        is_bake_running = bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE)
        layout.enabled = not is_bake_running

        assert texture_set
        row = layout.row()
        if len(texture_set.meshes) < 1:
            row.alert = True
            row.label(text="No Objects added to Texture Set", icon="ERROR")
        row = layout.row()
        row.template_list(
            MeshUIList.bl_idname,
            "pawsbkr_texture_set_meshes",
            texture_set,
            "meshes",
            texture_set,
            "meshes_active_index",
            rows=3,
        )

        col = row.column(align=True)
        col.operator(TextureSetMeshAdd.bl_idname, icon="ADD", text="")
        col.operator(TextureSetMeshRemove.bl_idname, icon="REMOVE", text="")

        col.separator()

        col.menu(MeshSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")
