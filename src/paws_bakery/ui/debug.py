"""Main UI Panel - Debug."""

import datetime
from pprint import pformat

from bpy import types as b_t

from ..operators.bake_manager import BakeManager
from ..operators.debug import DebugResetState
from ..preferences import get_preferences
from ..props import SceneProps, get_props
from ._utils import (
    InfoPopover,
    SidePanelMixin,
    generate_info_popover_idname,
    register_and_duplicate_to_node_editor,
)


@register_and_duplicate_to_node_editor
@generate_info_popover_idname("debug")
class _StateInfoPopover(InfoPopover):
    bl_label = "Internal State"
    bl_description = "The internal state of addon systems."


@register_and_duplicate_to_node_editor
@generate_info_popover_idname("debug")
class _SettingsStorageInfoPopover(InfoPopover):
    bl_label = "Settings Storage"
    bl_description = "The state of settings storage in the current file."


@register_and_duplicate_to_node_editor
class Debug(SidePanelMixin):
    """UI Panel - Debug."""

    bl_idname = "PAWSBKR_PT_debug"
    bl_label = "Debug"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 9999

    @classmethod
    def poll(cls, _context: b_t.Context) -> bool:
        """Panel poll override."""
        return get_preferences().enable_debug_tools

    def draw(self, context: b_t.Context) -> None:
        """Panel draw override."""
        pawsbkr = get_props(context)

        layout = self.layout

        row = layout.row(align=True)
        row.alert = True
        row.label(text="Development utils. Use only if you know what you're doing.")

        row = layout.row(align=True)
        row.alignment = "LEFT"
        row.alert = True
        row.prop(pawsbkr.utils_settings, "debug_pause")
        row.prop(pawsbkr.utils_settings, "debug_pause_continue")

        header, panel = layout.panel("state", default_closed=True)
        header.label(text="State")
        header.emboss = "NONE"
        header.popover(_StateInfoPopover.bl_idname, icon="INFO", text="")
        if panel:
            self._draw_state(context)

        header, panel = layout.panel("settings_storage", default_closed=True)
        header.label(text="Settings Storage")
        header.emboss = "NONE"
        header.popover(_SettingsStorageInfoPopover.bl_idname, icon="INFO", text="")
        if panel:
            self._draw_settings_storage(panel, get_props(context))

        header, panel = layout.panel("texture_sets_storage", default_closed=True)
        header.label(text="Texture Sets Storage")
        header.emboss = "NONE"
        # header.popover(_SettingsStorageInfoPopover.bl_idname, icon="INFO", text="")
        if panel:
            self._draw_texture_sets_storage(panel, get_props(context))

    def _draw_settings_storage(self, layout: b_t.UILayout, props: SceneProps) -> None:
        col = layout.column(align=True)
        for settings in props.bake_settings_store:
            subl = col.row()
            subl.label(text=settings.name)
            subl.label(text=settings.type)
            subl.label(text=settings.name_template)

    def _draw_texture_sets_storage(
        self, layout: b_t.UILayout, props: SceneProps
    ) -> None:
        col = layout.column(align=True)
        for texture_set in props.texture_sets:
            subl = col.column()
            # subl.label(text=texture_set.name)
            subl.label(text=texture_set.prop_id)
            subl.label(text=texture_set.display_name)
            subl.label(text=f"{pformat(texture_set.meshes.items())}")
            subl.label(text=f"{pformat(texture_set.textures.items())}")

    def _draw_state(self, _context: b_t.Context) -> None:
        layout = self.layout

        col = layout.column(align=True)

        row = col.row(align=True)
        # row.scale_y = 0.8
        row.alignment = "EXPAND"
        row.label(text=f"UI Updated: {datetime.datetime.now().second:02}")

        row.alert = True
        row.alignment = "RIGHT"
        row.operator(
            DebugResetState.bl_idname,
            text="",
            icon="CANCEL",
        )

        row = col.row(align=True)
        row.alignment = "LEFT"
        row.alert = BakeManager.is_running()
        row.label(text="R")
        row.label(text="BakeManager")
