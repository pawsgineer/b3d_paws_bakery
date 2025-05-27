"""UI Panel - Simple Bake."""

from bpy import types as b_t

from ..operators import Bake, MaterialSetupSelected
from ..operators.material_setup import MaterialCleanupSelected
from ..props import SIMPLE_BAKE_SETTINGS_ID
from ._draw_bake_settings import draw_bake_settings
from ._utils import SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class SimpleBakeSpecialsMenu(b_t.Menu):
    """Simple bake specials menu."""

    bl_idname = "PAWSBKR_MT_simple_bake_specials"
    bl_label = "Simple Bake Specials"

    def draw(self, _context: b_t.Context) -> None:
        """draw() override."""
        layout = self.layout

        subl = layout.column(align=True)

        props = subl.operator(
            MaterialSetupSelected.bl_idname,
            text="Setup Materials",
            icon="MATERIAL",
        )
        props.settings_id = SIMPLE_BAKE_SETTINGS_ID

        props = subl.operator(
            MaterialCleanupSelected.bl_idname,
            text="Cleanup Materials",
            icon="NODE_MATERIAL",
        )
        props.settings_id = SIMPLE_BAKE_SETTINGS_ID


@register_and_duplicate_to_node_editor
class SimpleBake(SidePanelMixin):
    """UI Panel - Simple Bake."""

    bl_idname = "PAWSBKR_PT_simple_bake"
    bl_label = "Simple Bake"
    bl_order = 1
    bl_options = {"HEADER_LAYOUT_EXPAND"}

    @classmethod
    def poll(cls, context: b_t.Context) -> bool:
        """poll() override."""
        return context.object is not None

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        layout = self.layout

        if not context.selected_objects:
            layout.alert = True
            layout.label(text="No objects selected", icon="ERROR")
            return

        row = layout.row()
        row.scale_y = 2
        props = row.operator(
            Bake.bl_idname,
            text="BAKE SELECTED",
            icon="RENDER_STILL",
        )
        props.settings_id = SIMPLE_BAKE_SETTINGS_ID
        props.texture_set_name = SIMPLE_BAKE_SETTINGS_ID

        row.menu(SimpleBakeSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")

        draw_bake_settings(
            layout,
            context.scene.pawsbkr.get_bake_settings(SIMPLE_BAKE_SETTINGS_ID),
            SIMPLE_BAKE_SETTINGS_ID,
        )
