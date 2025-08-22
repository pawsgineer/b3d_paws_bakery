"""UI Panel - Preferences."""

from typing import cast

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .utils import Registry


@Registry.add
class AddonPreferences(b_t.AddonPreferences):
    """UI Panel - Preferences."""

    bl_idname = __package__

    output_directory: b_p.StringProperty(  # type: ignore[valid-type]
        name="Output Directory",
        description="Directory to save baked images",
        default="//pawsbkr_textures",
        subtype="DIR_PATH",  # noqa: F821
        options={"PATH_SUPPORTS_BLEND_RELATIVE"},  # noqa: F821
    )

    enable_debug_tools: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Enable Debug Tools",
        description=(
            "Enable development utils. Use only if you know what you're doing."
        ),
        default=False,
    )

    def draw(self, _context: b_t.Context) -> None:
        """draw() override."""
        layout = self.layout
        layout.prop(self, "output_directory")
        layout.prop(self, "enable_debug_tools")


def get_preferences() -> AddonPreferences:
    """Return registered addon preferences."""
    return cast(
        AddonPreferences, bpy.context.preferences.addons[__package__].preferences
    )
