"""Draw bake settings function."""

from typing import cast

from bpy import types as b_t

from ..props import BakeSettings, BakeTextureType
from ._utils import LayoutPanel


def draw_bake_settings(
    layout: b_t.UILayout,
    settings: BakeSettings,
    texture_set_display_name: str = "",
) -> None:
    """Draws a bake settings layout."""
    assert isinstance(settings, BakeSettings)

    row = layout.row()
    row.label(text="SETTINGS", icon="TOOL_SETTINGS")

    row = layout.row()
    row.prop(settings, "name_template")
    row = layout.row()
    row = row.split(factor=0.25, align=True)
    row.label(text="Name Preview:")
    row.label(text=settings.get_name(texture_set_display_name))

    row = layout.row()
    row.prop(settings, "type")

    row = layout.row()
    row.prop(settings, "size")
    row.prop(settings, "sampling")
    row = layout.row()
    row.prop(settings, "samples")
    row.prop(settings, "use_denoising")

    row = layout.row()
    row.prop(settings, "margin")
    row.prop(settings, "margin_type")

    if BakeTextureType[settings.type] == BakeTextureType.MATERIAL_ID:
        row = layout.row()
        row.prop(settings, "matid_use_object_color")

    header, panel = cast(
        LayoutPanel,
        layout.panel("use_selected_to_active", default_closed=True),
    )
    header.prop(settings, "use_selected_to_active", text="")
    header.label(text="Selected To Active")
    if panel:
        panel.active = settings.use_selected_to_active
        panel.prop(settings, "match_active_by_suffix")

        row = panel.row()
        row.prop(settings, "use_cage")
        row = panel.row()
        row.prop(settings, "cage_extrusion")
        row.prop(settings, "max_ray_distance")
