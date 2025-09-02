# flake8: noqa: F821
"""Addon Preferences."""

from typing import Any, cast

import bpy
from bpy import props as blp
from bpy import types as blt

from .._helpers import log_warn
from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderOperatorType as BOT
from ..utils import Registry
from .defaults import DefaultTextureImportRule
from .props import TextureImportRuleProps

ROOT_PACKAGE_NAME = __package__.rsplit(".", 1)[0]


@Registry.add
class TextureImportRuleAdd(blt.Operator):
    """Add Texture Import Rule."""

    bl_idname = "pawsbkr.prefs_texture_import_rule_add"
    bl_label = "Add Texture Import Rule"
    bl_options = {BOT.INTERNAL}

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        prop = get_preferences().texture_import_rules.add()
        prop.name = ""

        return {BORT.FINISHED}


@Registry.add
class TextureImportRuleRemove(blt.Operator):
    """Remove Texture Import Rule."""

    bl_idname = "pawsbkr.prefs_texture_import_rule_remove"
    bl_label = "Remove Texture Import Rule"
    bl_options = {BOT.INTERNAL}

    idx: blp.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def execute(self, context: blt.Context) -> set[str]:  # noqa: D102
        get_preferences().texture_import_rules.remove(self.idx)

        return {BORT.FINISHED}


@Registry.add
class TextureImportRuleUIList(blt.UIList):
    """UI List - Texture Import Rules."""

    bl_idname = "PAWSBKR_UL_prefs_texture_import_rules"

    def draw_item(  # noqa: D102
        self,
        context: blt.Context | None,
        layout: blt.UILayout,
        _data: Any | None,
        item: TextureImportRuleProps | None,
        _icon: int | None,
        _active_data: Any,
        _active_property: str | None,
        _index: Any | None = 0,
        _flt_flag: Any | None = 0,
    ) -> None:
        assert item
        prefs = get_preferences()

        non_uniq_aliases: set[str] = set()
        non_uniq_prefixes: set[str] = set()
        uniq_aliases: set[str] = set()
        uniq_prefixes: set[str] = set()
        for imp_rule in prefs.get_enabled_import_rules():
            where = (
                non_uniq_prefixes
                if imp_rule.node_name_prefix in uniq_prefixes
                else uniq_prefixes
            )
            where.add(imp_rule.node_name_prefix)

            for alias in imp_rule.get_parsed_aliases():
                where = non_uniq_aliases if alias in uniq_aliases else uniq_aliases
                where.add(alias)

        imp_rule = item
        row = layout.row()
        if item.is_enabled and (
            imp_rule.node_name_prefix in non_uniq_prefixes
            or any(alias in non_uniq_aliases for alias in imp_rule.get_parsed_aliases())
        ):
            row.alert = True
        row.prop(item, "is_enabled", text="")

        col = row.column()
        if imp_rule.is_builtin:
            col.enabled = False
        if prefs.enable_debug_tools:
            subrow = col.column()
            subrow.enabled = False
            subrow.prop(imp_rule, "name")

        subrow = col.column()
        if len(imp_rule.node_name_prefix) < 1:
            subrow.alert = True
        subrow.prop(imp_rule, "node_name_prefix")

        subrow = col.column()
        if len(imp_rule.aliases) < 1:
            subrow.alert = True
        subrow.prop(imp_rule, "aliases")

        subrow = col.column()
        subrow.prop(imp_rule, "is_non_color")

        if not imp_rule.is_builtin:
            props = cast(
                TextureImportRuleRemove,
                row.operator(TextureImportRuleRemove.bl_idname, icon="TRASH", text=""),
            )
            props.idx = prefs.texture_import_rules.find(imp_rule.name)


@Registry.add
class AddonPreferences(blt.AddonPreferences):
    """UI Panel - Preferences."""

    bl_idname = ROOT_PACKAGE_NAME

    output_directory: blp.StringProperty(  # type: ignore[valid-type]
        name="Output Directory",
        description="Directory to save baked images",
        default="//pawsbkr_textures",
        subtype="DIR_PATH",
        options=set() if bpy.app.version < (4, 5) else {"PATH_SUPPORTS_BLEND_RELATIVE"},
    )

    enable_debug_tools: blp.BoolProperty(  # type: ignore[valid-type]
        name="Enable Debug Tools",
        description=(
            "Enable development utils. Use only if you know what you're doing."
        ),
        default=False,
    )

    tabs: blp.EnumProperty(  # type: ignore[valid-type]
        items=[
            ("GENERAL", "GENERAL", ""),
            ("TEXTUREIMPORT", "Texture Import Rules", ""),
            # ("ABOUT", "ABOUT", ""), # TODO:
        ],
        default="GENERAL",
    )

    texture_import_rules: blp.CollectionProperty(  # type: ignore[valid-type]
        type=TextureImportRuleProps
    )
    texture_import_rules_active_index: blp.IntProperty()  # type: ignore[valid-type]

    def get_enabled_import_rules(self) -> list[TextureImportRuleProps]:
        """Get enabled texture import rules."""
        return [x for x in self.texture_import_rules if x.is_enabled]

    def get_matching_import_rule(self, filename: str) -> TextureImportRuleProps | None:
        """Return texture import rule or None."""
        # TODO: only look at basename to avoid matches in dir struct
        for t_imp_rule in self.get_enabled_import_rules():
            if t_imp_rule.is_matches_name(filename):
                return t_imp_rule

        return None

    def draw(self, _context: blt.Context) -> None:  # noqa: D102
        lyt = self.layout

        column = lyt.column(align=True)
        row = column.row()
        row.prop(self, "tabs", expand=True)

        box = lyt.box()

        if self.tabs == "GENERAL":
            self._draw_general(box)
        elif self.tabs == "TEXTUREIMPORT":
            self._draw_texture_import(box)

    def _draw_general(self, lyt: blt.UILayout) -> None:
        lyt.prop(self, "output_directory")
        lyt.prop(self, "enable_debug_tools")

    def _draw_texture_import(self, lyt: blt.UILayout) -> None:
        row = lyt
        row.template_list(
            TextureImportRuleUIList.bl_idname,
            "pawsbkr_prefs_texture_import_rules",
            self,
            "texture_import_rules",
            self,
            "texture_import_rules_active_index",
            sort_lock=True,
        )
        col = row.column(align=True)
        col.operator(TextureImportRuleAdd.bl_idname, icon="ADD", text="")

    def init_texture_import_rules(self) -> None:
        """Validate existing Texture Import Rules and update default data."""
        node_prefixes = DefaultTextureImportRule.get_all_node_prefixes()
        uniq_names: set[str] = set()
        for idx, item in enumerate(self.texture_import_rules):
            if item.name not in node_prefixes:
                item.is_builtin = False

            if item.name == "" or item.name in uniq_names:
                new_name = f"unknown_{idx}"
                log_warn(
                    f"Wrong rule name found {item.name!r}. Renaming to {new_name!r}"
                )
                item.name = new_name

            uniq_names.add(item.name)

        for idx, imp_rule in enumerate(DefaultTextureImportRule):
            item = self.texture_import_rules.get(imp_rule.node_prefix)
            if not item:
                log_warn(f"Rule not found in prefs: {imp_rule.node_prefix!r}")
                item = self.texture_import_rules.add()
                item.name = imp_rule.node_prefix

            item.is_builtin = True
            item.is_non_color = imp_rule.is_non_color
            item.node_name_prefix = imp_rule.node_prefix
            item.aliases = ",".join(imp_rule.aliases)
            self.texture_import_rules.move(
                self.texture_import_rules.find(imp_rule.node_prefix), idx
            )


def get_preferences() -> AddonPreferences:
    """Return registered addon preferences."""
    return cast(
        AddonPreferences,
        bpy.context.preferences.addons[ROOT_PACKAGE_NAME].preferences,
    )
