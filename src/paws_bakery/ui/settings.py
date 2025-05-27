"""UI Panel - Settings."""

from bpy import types as b_t

from ._utils import SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class Settings(SidePanelMixin):
    """UI Panel - Settings."""

    bl_idname = "PAWSBKR_PT_settings"
    bl_label = "🍰PAWS Bakery Settings"
    bl_order = 0
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        pawsbkr = context.scene.pawsbkr
        layout = self.layout

        subl = layout.column(align=True)
        subl.prop(pawsbkr.utils_settings, "unlink_baked_image")
        subl.prop(pawsbkr.utils_settings, "show_image_in_editor")
