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
from ...operators.texture_set_texture import TextureSetTextureSort
from ...props import TextureProps, get_bake_settings, get_props
from .._draw_bake_settings import draw_bake_settings
from .._utils import SidePanelMixin, register_and_duplicate_to_node_editor
from .main import Main


@register_and_duplicate_to_node_editor
class TextureSpecialsMenu(b_t.Menu):
    """Texture specials menu."""

    bl_idname = "PAWSBKR_MT_texture_set_textures_specials"
    bl_label = "Texture Specials"

    def draw(self, context: b_t.Context | None) -> None:  # noqa: D102
        assert context
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        assert texture_set
        texture = texture_set.active_texture
        assert texture

        layout = self.layout

        subl = layout.column(align=True)

        props = cast(
            TextureSetTextureSetupMaterial,
            subl.operator(
                TextureSetTextureSetupMaterial.bl_idname,
                icon="MATERIAL",
                text="Setup Materials",
            ),
        )
        props.texture_set_id = texture_set.prop_id
        props.texture_id = texture.prop_id

        cm_props = cast(
            TextureSetTextureCleanupMaterial,
            subl.operator(
                TextureSetTextureCleanupMaterial.bl_idname,
                icon="NODE_MATERIAL",
                text="Cleanup Materials",
            ),
        )
        cm_props.texture_set_id = texture_set.prop_id

        subl.separator()

        subl.operator(
            TextureSetTextureSort.bl_idname, icon="NODE_MATERIAL", text="Sort Textures"
        )


@register_and_duplicate_to_node_editor
class TextureUIList(b_t.UIList):
    """UI List - Texture Set textures."""

    bl_idname = "PAWSBKR_UL_texture_set_textures"

    def draw_item(  # noqa: D102
        self,
        context: b_t.Context | None,
        layout: b_t.UILayout,
        _data: Any | None,
        item: TextureProps | None,
        _icon: int | None,
        _active_data: Any,
        _active_property: str | None,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        assert context
        assert item
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        assert texture_set
        bake_settings = get_bake_settings(context, item.prop_id)

        row = layout.row(align=True)
        row.prop(item, "is_enabled", text="")

        row = row.split(factor=0.4, align=True)
        row.label(
            text=f"{bake_settings.get_name(texture_set.display_name)}",
            icon=row.enum_item_name(item, "state", item.state),
        )
        row.label(text=bake_settings.type)
        row = row.row(align=True)
        row.alignment = "RIGHT"
        row.label(text=item.last_bake_time)

        props = cast(
            TextureSetBake,
            row.operator(TextureSetBake.bl_idname, icon="RENDER_STILL", text=""),
        )
        props.texture_set_id = texture_set.prop_id
        props.texture_id = item.prop_id


@register_and_duplicate_to_node_editor
class Texture(SidePanelMixin):
    """UI Panel - TextureSet - Textures."""

    bl_parent_id = Main.bl_idname
    bl_idname = "PAWSBKR_PT_main_texture_set_textures"
    bl_label = "Textures"

    @classmethod
    def poll(cls, context: b_t.Context) -> bool:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        return texture_set is not None

    def draw_header(self, context: b_t.Context) -> None:  # noqa: D102
        pawsbkr = get_props(context)
        assert pawsbkr.active_texture_set
        if len(pawsbkr.active_texture_set.textures) < 1:
            self.layout.alert = True
            self.layout.label(text="", icon="ERROR")

    def draw(self, context: b_t.Context) -> None:  # noqa: D102
        pawsbkr = get_props(context)
        texture_set = pawsbkr.active_texture_set
        assert texture_set
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

        if texture is None:
            return

        col.separator()
        col.menu(TextureSpecialsMenu.bl_idname, icon="DOWNARROW_HLT", text="")
