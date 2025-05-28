"""UI Panel - Texture Import."""

from pathlib import Path

import bpy
from bpy import types as b_t

from ... import operators as ops
from ...preferences import get_preferences
from ...props_enums import TextureTypeAlias
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class TextureImportSpecialsMenu(b_t.Menu):
    """Texture Import specials menu."""

    bl_idname = "PAWSBKR_MT_texture_import_specials"
    bl_label = "Texture Import Specials"

    def draw(self, _context: b_t.Context) -> None:
        """draw() override."""
        layout = self.layout

        subl = layout.column(align=True)
        subl.operator(ops.TextureImportLoadSampleMaterial.bl_idname, icon="IMPORT")


@register_and_duplicate_to_node_editor
class TextureImport(SidePanelMixin):
    """UI Panel - Texture Import."""

    # TODO: Add doc about material setup
    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_helpers_texture_import"
    bl_label = "Texture Import"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        layout = self.layout

        if not context.selected_objects:
            layout.alert = True
            layout.label(text="No objects selected", icon="ERROR")
            return

        materials: set[b_t.Material] = set()

        for obj in context.selected_objects:
            for slot in obj.material_slots:
                if slot.material is not None:
                    materials.add(slot.material)

        if not materials:
            layout.alert = True
            layout.label(text="No materials assigned to objects", icon="ERROR")
            return

        col = layout.column(align=True)
        row = col.row()
        row.scale_y = 1.5
        props = row.operator(
            ops.TextureImport.bl_idname,
            text="Batch Import Textures",
        )

        row.menu(TextureImportSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")

        flow = layout.grid_flow(
            row_major=True,
            columns=2,
            even_columns=False,
            even_rows=False,
            align=True,
        )

        for mat in materials:
            tex_nodes = {
                x: mat.node_tree.nodes.get(x.node_name) for x in TextureTypeAlias
            }

            col = flow.column(align=True)
            row = col.row()
            row.scale_y = 1.5
            row.prop(mat, "name", icon="MATERIAL", text="")

            col = flow.column(align=True)
            row = col.row()
            row.scale_y = 1.5
            props = row.operator(
                ops.TextureImport.bl_idname,
            )
            props.target_material_name = mat.name

            if (
                tex_nodes[TextureTypeAlias.ALBEDO] is not None
                and tex_nodes[TextureTypeAlias.ALBEDO].image is not None
                and tex_nodes[TextureTypeAlias.ALBEDO].image.filepath
            ):
                props.filepath = bpy.path.relpath(
                    str(
                        Path(
                            bpy.path.abspath(
                                tex_nodes[TextureTypeAlias.ALBEDO].image.filepath
                            )
                        ).parent
                    )
                )
            else:
                props.filepath = f"{get_preferences().output_directory}/"

            for node_type, node in tex_nodes.items():
                col = flow.column(align=True)
                row = col.row()
                row.label(text=node_type.name, icon="NODE_TEXTURE")

                col = flow.column(align=True)
                row = col.row()
                if node is None:
                    row.alert = True
                    row.label(
                        text=f"No node with name {node_type.node_name!r}",
                        icon="ERROR",
                    )
                    continue

                if node.image is None:
                    row.label(text="No image set", icon="ERROR")
                    continue

                if node.image.filepath:
                    row.label(text=bpy.path.basename(node.image.filepath))
                else:
                    row.label(text="No image path found", icon="ERROR")
