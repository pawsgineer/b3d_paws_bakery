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

    bpy.app.timers.register(prefs.init_texture_import_rules, first_interval=1.0)

    bpy.types.Scene.pawsbkr = PointerProperty(type=SceneProps)
    bpy.types.WindowManager.pawsbkr = PointerProperty(type=WMProps)


def unregister() -> None:
    """Unregister addon."""
    Registry.unregister()

    del bpy.types.Scene.pawsbkr
    del bpy.types.WindowManager.pawsbkr
