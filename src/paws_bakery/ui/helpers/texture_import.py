"""UI Panel - Texture Import."""

from pathlib import Path
from typing import cast

import bpy
from bpy import types as b_t

from ... import operators as ops
from ...operators.texture_import import get_prefix_to_nodes_map
from ...preferences import get_preferences
from .._utils import LayoutPanel, SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class TextureImportSpecialsMenu(b_t.Menu):
    """Texture Import specials menu."""

    bl_idname = "PAWSBKR_MT_texture_import_specials"
    bl_label = "Texture Import Specials"

    def draw(self, _context: b_t.Context | None) -> None:
        """UIList draw override."""
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

    def draw(self, context: b_t.Context) -> None:  # noqa: C901
        """Panel draw override."""
        lyt = self.layout

        if not context.selected_objects:
            lyt.alert = True
            lyt.label(text="No objects selected", icon="ERROR")
            return

        materials: set[b_t.Material] = set()

        for obj in context.selected_objects:
            for slot in obj.material_slots:
                if slot.material is not None:
                    materials.add(slot.material)

        if not materials:
            lyt.alert = True
            lyt.label(text="No materials assigned to objects", icon="ERROR")
            return

        row = lyt.row()
        op_props = row.operator(
            ops.TextureImport.bl_idname, text="Batch Import Textures"
        )

        row.menu(TextureImportSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")

        for mat in materials:
            pref_to_nodes = get_prefix_to_nodes_map(mat)

            current_image_filepath = ""
            for node in pref_to_nodes.nodes:
                if node.image is None or not node.image.filepath:
                    continue
                current_image_filepath = node.image.filepath
                break

            nodes_found = sum(bool(v) for v in pref_to_nodes.by_prefix.values())
            nodes_used = sum(bool(node.image) for node in pref_to_nodes.nodes)

            header, panel = cast(
                LayoutPanel,
                lyt.panel("_".join([self.bl_idname, mat.name]), default_closed=True),
            )
            header.prop(mat, "name", icon="MATERIAL", text="")
            op_props = header.operator(
                ops.TextureImport.bl_idname,
                text=f"Import Textures ({nodes_found}/{nodes_used})",
            )
            op_props.target_material_name = mat.name
            if not panel:
                continue

            if current_image_filepath:
                op_props.filepath = str(
                    Path(bpy.path.abspath(current_image_filepath)).parent
                )
            else:
                op_props.filepath = bpy.path.abspath(
                    get_preferences().output_directory + "/"
                )

            for node_prefix, node_set in pref_to_nodes.by_prefix.items():
                if not node_set:
                    row = panel.row()
                    row.alert = True
                    row.label(
                        text=f"No nodes with name prefix {node_prefix!r}",
                        icon="ERROR",
                    )
                    continue

                for node in node_set:
                    row = panel.row()
                    row.label(text=node.name, icon="NODE_TEXTURE")

                    if node.image is None:
                        row.label(text="No image set", icon="ERROR")
                        continue

                    if node.image.filepath:
                        row.label(text=bpy.path.basename(node.image.filepath))
                    else:
                        row.label(text="Image without path", icon="ERROR")
