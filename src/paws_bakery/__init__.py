"""PAWS Bakery Addon."""

import bpy
from bpy.props import PointerProperty

from . import operators, props, ui
from .preferences import AddonPreferences, get_preferences
from .props import SceneProps, WMProps
from .utils import Registry

# Importing modules with Registry definitions
__all__ = [
    "AddonPreferences",
    "operators",
    "props",
    "ui",
]


def register() -> None:
    """Register addon."""
    Registry.register()

    prefs = get_preferences()

    # pylint: disable-next=unexpected-keyword-arg
    bpy.app.timers.register(  # type: ignore[call-arg]
        prefs.init_texture_import_rules,  # type: ignore[arg-type]
        first_interval=1.0,
        persistent=True,
    )

    bpy.types.Scene.pawsbkr = PointerProperty(  # type: ignore[attr-defined]
        type=SceneProps
    )
    bpy.types.WindowManager.pawsbkr = PointerProperty(  # type: ignore[attr-defined]
        type=WMProps
    )


def unregister() -> None:
    """Unregister addon."""
    Registry.unregister()

    del bpy.types.Scene.pawsbkr  # type: ignore[attr-defined]
    del bpy.types.WindowManager.pawsbkr  # type: ignore[attr-defined]
