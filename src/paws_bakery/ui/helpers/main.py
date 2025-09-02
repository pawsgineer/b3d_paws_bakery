"""Helpers UI Panel."""

from bpy import types as blt

from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor


@register_and_duplicate_to_node_editor
class Main(SidePanelMixin):
    """UI Panel - Helpers."""

    bl_idname = "PAWSBKR_PT_helpers"
    bl_label = "Helpers"
    bl_order = 10
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, _context: blt.Context) -> None:  # noqa: D102
        pass
