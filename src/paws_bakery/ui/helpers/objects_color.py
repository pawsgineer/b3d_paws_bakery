"""UI Panel - Objects Color."""

from bpy import types as b_t

from ...operators import RandomizeColor
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class ObjectsColor(SidePanelMixin):
    "UI Panel - Objects Color."

    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_helpers_objects_color"
    bl_label = "Objects Color"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: b_t.Context) -> None:
        "Panel draw() override."
        layout = self.layout

        if not context.selected_objects:
            layout.alert = True
            layout.label(text="No objects selected", icon="ERROR")
            return

        flow = layout.grid_flow(
            row_major=False,
            columns=0,
            even_columns=True,
            even_rows=False,
            align=True,
        )

        row = flow.row(align=True)
        props = row.operator(
            RandomizeColor.bl_idname,
            text="Randomize selected",
            icon="FILE_REFRESH",
        )
        props.target_object = ""

        for obj in context.selected_objects:
            row = flow.row()

            row.prop(obj, "color", text=obj.name)
            row.scale_x = 1.5
