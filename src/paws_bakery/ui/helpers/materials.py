"""UI Panel - Materials."""

from bpy import types as b_t

from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class Materials(SidePanelMixin):
    """List of materials assigned to selected objects."""

    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_helpers_materials"
    bl_label = "Materials"
    bl_order = 3
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: b_t.Context) -> None:  # noqa: D102
        layout = self.layout

        if not context.selected_objects:
            layout.alert = True
            layout.label(text="No objects selected", icon="ERROR")
            return

        flow = layout.grid_flow(
            row_major=True,
            columns=0,
            even_columns=True,
            even_rows=True,
            align=True,
        )
        col = flow.column(align=True)

        materials: set[b_t.Material] = set()

        for obj in context.selected_objects:
            row = col.row()
            row.label(text=obj.name, icon="OBJECT_DATA")

            if not obj.material_slots:
                row.alert = True
                row.label(text="No materials assigned", icon="ERROR")
                continue

            for slot in obj.material_slots:
                if slot.material is None:
                    row.alert = True
                    row.label(text="No material assigned to slot", icon="ERROR")
                    continue

                materials.add(slot.material)
                row.prop(slot, "material", icon="MATERIAL", text="")
