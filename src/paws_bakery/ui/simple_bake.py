"""UI Panel - Simple Bake."""

from typing import cast

import bpy
from bpy import types as blt

from ..enums import BlenderJobType
from ..operators import BakeSelected, MaterialCleanupSelected, MaterialSetupSelected
from ..props import SIMPLE_BAKE_SETTINGS_ID, get_bake_settings
from ..utils import Registry
from ._draw_bake_settings import draw_bake_settings
from ._utils import SidePanelMixin, register_and_duplicate_to_node_editor


@Registry.add
class SimpleBakeSpecialsMenu(blt.Menu):
    """Simple bake specials menu."""

    bl_idname = "PAWSBKR_MT_simple_bake_specials"
    bl_label = "Simple Bake Specials"

    def draw(self, _context: blt.Context | None) -> None:  # noqa: D102
        layout = self.layout

        subl = layout.column(align=True)

        props = cast(
            MaterialSetupSelected,
            subl.operator(
                MaterialSetupSelected.bl_idname,
                text="Setup Materials",
                icon="MATERIAL",
            ),
        )
        props.settings_id = SIMPLE_BAKE_SETTINGS_ID

        subl.operator(
            MaterialCleanupSelected.bl_idname,
            text="Cleanup Materials",
            icon="NODE_MATERIAL",
        )


@register_and_duplicate_to_node_editor
class SimpleBake(SidePanelMixin):
    """UI Panel - Simple Bake."""

    bl_idname = "PAWSBKR_PT_simple_mode"
    bl_label = "Simple Mode"
    bl_order = 1
    bl_options = {"HEADER_LAYOUT_EXPAND"}

    def draw(self, context: blt.Context) -> None:  # noqa: D102
        lyt = self.layout

        if not context.selected_objects:
            lyt.alert = True
            lyt.label(text="No objects selected", icon="ERROR")
            return

        # TODO: won't work in shader editor
        if (
            isinstance(context.space_data, blt.SpaceView3D)
            and context.space_data.local_view
        ):
            col = lyt.column()
            col.alert = True
            col.label(text="Local View is active!", icon="VIS_SEL_01")
            col.label(text="The result may not be what you expect.")

        is_bake_running = bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE)
        lyt.enabled = not is_bake_running

        row = lyt.row()
        row.alert = is_bake_running
        row.scale_y = 2
        row.enabled = not is_bake_running
        row.operator(
            BakeSelected.bl_idname,
            text="BAKING IN PROGRESS" if is_bake_running else "BAKE SELECTED",
            icon="RENDER_STILL",
        )

        row.menu(SimpleBakeSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")

        draw_bake_settings(
            lyt,
            get_bake_settings(context, SIMPLE_BAKE_SETTINGS_ID),
            SIMPLE_BAKE_SETTINGS_ID,
        )
