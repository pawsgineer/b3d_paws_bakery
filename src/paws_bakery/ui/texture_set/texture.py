"""UI Panel - Texture Set Textures."""

from typing import Any

from bpy import types as b_t

from ...operators import (
    TextureSetTextureAdd,
    TextureSetTextureBake,
    TextureSetTextureCleanupMaterial,
    TextureSetTextureRemove,
    TextureSetTextureSetupMaterial,
)
from .._draw_bake_settings import draw_bake_settings
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class TextureSpecialsMenu(b_t.Menu):
    """Texture specials menu."""

    bl_idname = "PAWSBKR_MT_texture_set_textures_specials"
    bl_label = "Texture Specials"

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.active_texture_set
        texture = texture_set.active_texture

        layout = self.layout

        subl = layout.column(align=True)

        props = subl.operator(
            TextureSetTextureSetupMaterial.bl_idname,
            icon="MATERIAL",
            text="Setup Materials",
        )
        props.texture_set_name = texture_set.name
        props.texture_name = texture.name

        subl.alert = True
        props = subl.operator(
            TextureSetTextureCleanupMaterial.bl_idname,
            icon="NODE_MATERIAL",
            text="Cleanup Materials",
        )
        props.texture_set_name = texture_set.name


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
        _active_property: str,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        """draw() override."""
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.active_texture_set
        bake_settings = item.get_bake_settings()

        row = layout.split(factor=0.05)
        row.label(
            text="",
            icon=row.enum_item_name(item, "state", item.state),
        )
        row = row.split(factor=0.05)
        row.prop(item, "is_enabled", text="")

        row = row.split(factor=0.6)
        row.label(text=f"{bake_settings.get_name(texture_set.name)}")
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
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.active_texture_set
        return texture_set is not None

    def draw_header(self, context):
        """draw_header() override."""
        pawsbkr = context.scene.pawsbkr
        if len(pawsbkr.active_texture_set.textures) < 1:
            self.layout.alert = True
            self.layout.label(text="", icon="ERROR")

    def draw(self, context: b_t.Context) -> None:
        """draw() override."""
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.active_texture_set
        texture = texture_set.active_texture

        layout = self.layout

        flow = layout.grid_flow(
            row_major=False,
            columns=0,
            even_columns=True,
            even_rows=False,
            align=True,
        )

        if texture is not None:
            col = flow.column()
            row = col.row()
            draw_bake_settings(col, texture.get_bake_settings(), texture_set.name)

        col = flow.column()

        if len(texture_set.textures) < 1:
            col.alert = True
            col.label(text="No Textures added to Texture Set", icon="ERROR")

        row = col.row()
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

        props = col.operator(
            TextureSetTextureBake.bl_idname, icon="RENDER_STILL", text=""
        )
        props.texture_set_name = texture_set.name
        props.texture_name = texture.name

        col.separator()

        col.menu(TextureSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")
