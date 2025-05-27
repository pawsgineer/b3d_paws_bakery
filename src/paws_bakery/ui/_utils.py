"""Various UI helpers."""

import textwrap
from typing import Callable, TypeVar

from bpy import types as b_t

from ..utils import Registry


def register_and_duplicate_to_node_editor(cls: type) -> type:
    """Register panel and duplicate to Node Editor."""
    target_cls = Registry.add(cls)
    node_panel_add(target_cls)
    return target_cls


def node_panel_add(cls: type) -> type:
    """Add existing panel to Node Editor."""

    def node_panel_rewrite(cls: type):
        """Adapt properties editor panel to display in node editor.
        We have to copy the class rather than inherit due to the way bpy
        registration works.
        """
        node_cls = type("NodeEditor" + cls.__name__, cls.__bases__, dict(cls.__dict__))

        node_cls.bl_space_type = "NODE_EDITOR"

        if hasattr(node_cls, "bl_idname"):
            node_cls.bl_idname = "NODE_" + node_cls.bl_idname
        if hasattr(node_cls, "bl_parent_id"):
            node_cls.bl_parent_id = "NODE_" + node_cls.bl_parent_id

        return node_cls

    Registry.add(node_panel_rewrite(cls))
    return cls


_T = TypeVar("_T", bound=type)


def generate_info_popover_idname(prefix: str) -> Callable[[_T], _T]:
    """Generates `bl_idname` from prefix and class name."""

    def wrapper(cls: _T) -> _T:
        cls.bl_idname = f"PAWSBKR_PT_{prefix}_{cls.__name__.lower()}"
        return cls

    return wrapper


class SidePanelMixin(b_t.Panel):
    """UI Side Panel mixin."""

    bl_category = "🍰PAWSBKR"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class InfoPopover(b_t.Panel):
    """UI Info Popover mixin."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_ui_units_x = 16

    def draw(self, _context):
        """draw() override."""
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 0.80

        for paraghraph in textwrap.dedent(self.bl_description).splitlines():
            if not paraghraph:
                col.label()
                continue

            for line in textwrap.wrap(
                paraghraph,
                width=self.bl_ui_units_x * 4,
                initial_indent=" " * 4,
            ):
                col.label(text=line)
