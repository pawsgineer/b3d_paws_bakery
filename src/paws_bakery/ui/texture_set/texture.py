"""UI Panel - Texture Set Textures."""

from typing import Any, cast

import bpy
from bpy import types as b_t

from ...enums import BlenderJobType
from ...operators import (
    TextureSetBake,
    TextureSetTextureAdd,
    TextureSetTextureCleanupMaterial,
    TextureSetTextureRemove,
    TextureSetTextureSetupMaterial,
)
from ...props import get_bake_settings, get_props
from .._draw_bake_settings import draw_bake_settings
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class TextureSpecialsMenu(b_t.Menu):
    """Texture specials menu."""

    bl_idname = "PAWSBKR_MT_texture_set_textures_specials"
    bl_label = "Texture Specials"

    def draw(self, context: b_t.Context | None) -> None:
        """draw() override."""
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        texture = texture_set.active_texture

        layout = self.layout

        subl = layout.column(align=True)

        # Original setup materials
        props = subl.operator(
            TextureSetTextureSetupMaterial.bl_idname,
            icon="MATERIAL",
            text="Setup Materials",
        )
        props.texture_set_id = texture_set.prop_id
        props.texture_id = texture.prop_id

        subl.separator()

        # Enhanced material creation with description
        subl.label(text="Auto BSDF Creation:", icon="NODE_MATERIAL")

        props = subl.operator(
            "pawsbkr.texture_set_material_create",
            icon="MATERIAL_DATA",
            text="Create Principled BSDF Materials",
        )
        props.texture_set_id = texture_set.prop_id

        # Add sub-text
        sub_row = subl.row()
        sub_row.scale_y = 0.7
        sub_row.enabled = False
        sub_row.label(text="(from baked textures)")

        subl.separator()

        subl.alert = True
        props = subl.operator(
            TextureSetTextureCleanupMaterial.bl_idname,
            icon="NODE_MATERIAL",
            text="Cleanup Materials",
        )


@register_and_duplicate_to_node_editor
class TextureUIList(b_t.UIList):
    """UI List - Texture Set textures."""

    bl_idname = "PAWSBKR_UL_texture_set_textures"

    def draw_item(
        self,
        context: b_t.Context | None,
        layout: b_t.UILayout,
        _data: Any | None,
        item: Any | None,
        _icon: int | None,
        _active_data: Any,
        _active_property: str | None,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        """draw() override."""
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        bake_settings = get_bake_settings(context, item.prop_id)

        row = layout.split(factor=0.05)
        row.label(
            text="",
            icon=row.enum_item_name(item, "state", item.state),
        )
        row = row.split(factor=0.05)
        row.prop(item, "is_enabled", text="")

        row = row.split(factor=0.6)
        row.label(text=f"{bake_settings.get_name(texture_set.display_name)}")
        row = row.split(factor=0.6)
        row.label(text=f"{bake_settings.type}")
        row.label(text=f"{item.last_bake_time}")


@register_and_duplicate_to_node_editor
class Texture(SidePanelMixin):
    """UI Panel - TextureSet - Textures."""

    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_main_texture_set_textures"
    bl_label = "Textures"

    @classmethod
    def poll(cls, context: b_t.Context) -> bool:
        """poll() override."""
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        return texture_set is not None

    def draw_header(self, context: b_t.Context) -> None:
        """draw_header() override."""
        pawsbkr = get_props(context)
        if len(pawsbkr.active_texture_set.textures) < 1:
            self.layout.alert = True
            self.layout.label(text="", icon="ERROR")

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        texture = texture_set.active_texture

        lyt = self.layout

        is_bake_running = bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE)
        lyt.enabled = not is_bake_running

        if not texture_set.textures:
            col = lyt.column()
            col.alert = True
            col.label(text="No Textures added to Texture Set", icon="ERROR")

        if texture is not None:
            draw_bake_settings(
                lyt,
                get_bake_settings(context, texture.prop_id),
                texture_set.display_name,
            )

        row = lyt.row()
        row.template_list(
            TextureUIList.bl_idname,
            "pawsbkr_texture_set_textures",
            texture_set,
            "textures",
            texture_set,
            "textures_active_index",
        )
        col = row.column(align=True)
        col.operator(TextureSetTextureAdd.bl_idname, icon="ADD", text="")
        col.operator(TextureSetTextureRemove.bl_idname, icon="REMOVE", text="")
        col.separator()

        if texture is None:
            return

        props = col.operator(TextureSetBake.bl_idname, icon="RENDER_STILL", text="")
        props.texture_set_id = texture_set.prop_id
        props.texture_id = texture.prop_id

        col.separator()

        col.menu(TextureSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")

         # Check if any textures have been baked
        has_baked_textures = False
        if texture_set.textures:
            has_baked_textures = any(
                texture.last_bake_time
                for texture in texture_set.textures
                if texture.is_enabled
            )

        if has_baked_textures:
            lyt.separator()

            # Create collapsible panel for material creation
            header, panel = cast(
                tuple[b_t.UILayout, b_t.UILayout | None],
                lyt.panel("material_creation", default_closed=False),
            )
            header.label(text="Auto BSDF Material Creation", icon="NODE_MATERIAL")
            
            if panel:
                # Description text
                desc_col = panel.column(align=True)
                desc_col.scale_y = 0.8
                desc_col.label(
                    text="Creates Principled BSDF materials from baked textures",
                    icon="INFO",
                )
                desc_col.label(
                    text="Automatically connects diffuse, normal, roughness, etc."
                )

                panel.separator(factor=0.5)

                # Main creation button
                row = panel.row(align=True)
                row.scale_y = 1.2
                props = row.operator(
                    "pawsbkr.texture_set_material_create",
                    text="Create BSDF Materials",
                    icon="NODE_MATERIAL",
                )
                props.texture_set_id = texture_set.prop_id

                # Show available texture types
                status_col = panel.column(align=True)
                status_col.scale_y = 0.8

                # Get texture types that have been baked
                baked_types = []
                for texture_props in texture_set.textures:
                    if texture_props.is_enabled and texture_props.last_bake_time:
                        bake_settings = get_bake_settings(context, texture_props.prop_id)
                        baked_types.append(bake_settings.type)

                if baked_types:
                    status_col.label(
                        text=f"Available types: {', '.join(baked_types[:3])}",
                        icon="CHECKMARK",
                    )
                    if len(baked_types) > 3:
                        status_col.label(text=f"... and {len(baked_types) - 3} more")
                else:
                    status_col.label(text="No baked textures found", icon="ERROR")

                panel.separator(factor=0.5)