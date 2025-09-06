"""UI Panel - Settings."""

from typing import cast

from bpy import types as blt

from ..props import get_props
from ._utils import LayoutPanel, SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class Settings(SidePanelMixin):
    """UI Panel - Settings."""

    bl_idname = "PAWSBKR_PT_settings"
    bl_label = "🍰PAWS: Bakery Settings"
    bl_order = 0
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: blt.Context) -> None:  # noqa: D102
        pawsbkr = get_props(context)
        layout = self.layout

        subl = layout.column(align=True)
        subl.prop(pawsbkr.utils_settings, "unlink_baked_image")
        subl.prop(pawsbkr.utils_settings, "show_image_in_editor")

        self._draw_material_creation(context)

    def _draw_material_creation(self, context: blt.Context) -> None:
        header, panel = cast(
            LayoutPanel, self.layout.panel("mat_creation", default_closed=False)
        )
        header.label(text="Material Creation")
        if not panel:
            return

        pawsbkr = get_props(context)

        col = panel.column(align=True)
        col.prop(pawsbkr.utils_settings.material_creation, "name_prefix")
        col.prop(pawsbkr.utils_settings.material_creation, "name_suffix")

        name_example = "".join(
            [
                pawsbkr.utils_settings.material_creation.name_prefix,
                "texture_set_name",
                pawsbkr.utils_settings.material_creation.name_suffix,
            ]
        )

        row = col.row(align=True)
        row = row.split(factor=0.25, align=True)
        row.label(text="Name Preview:")
        row.label(text=name_example)

        col.prop(pawsbkr.utils_settings.material_creation, "mark_as_asset")
        col.prop(pawsbkr.utils_settings.material_creation, "use_fake_user")
