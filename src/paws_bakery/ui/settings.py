"""UI Panel - Settings."""

from bpy import types as b_t

from ..props import get_props
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
        pawsbkr = get_props(context)
        layout = self.layout

        subl = layout.column(align=True)
        subl.prop(pawsbkr.utils_settings, "unlink_baked_image")
        subl.prop(pawsbkr.utils_settings, "show_image_in_editor")

        # Material Creation Settings
        box = layout.box()
        box.label(text="Auto Material Creation", icon="MATERIAL")
        
        box.prop(pawsbkr.utils_settings, "material_name_prefix")
        box.prop(pawsbkr.utils_settings, "material_output_suffix")
        box.prop(pawsbkr.utils_settings, "keep_original_materials")
        
        preview_row = box.row(align=True)
        preview_row.scale_y = 0.7
        preview_row.enabled = False
        example_name = (
            f"{pawsbkr.utils_settings.material_name_prefix}MaterialName{pawsbkr.utils_settings.material_output_suffix}"
        )
        preview_row.label(text=f"Preview: {example_name}", icon="INFO")
