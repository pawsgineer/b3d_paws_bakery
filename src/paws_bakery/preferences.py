"""UI Panel - Preferences."""

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .utils import Registry


@Registry.add
class AddonPreferences(b_t.AddonPreferences):
    """UI Panel - Preferences."""

    bl_idname = __package__

    enable_debug_tools: b_p.BoolProperty(
        name="Enable Debug Tools",
        description=(
            "Enable development utils. Use only if you know what you're doing."
        ),
        default=False,
    )

    def draw(self, _context: b_t.Context):
        """draw() override."""
        layout = self.layout
        layout.prop(self, "enable_debug_tools")


def get_preferences() -> AddonPreferences:
    """Returns registered addon preferences."""
    return bpy.context.preferences.addons[__package__].preferences
