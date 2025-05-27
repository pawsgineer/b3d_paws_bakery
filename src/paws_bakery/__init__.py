"""PAWS Bakery Addon."""

import bpy
from bpy.props import PointerProperty

from . import operators, props, ui
from .preferences import AddonPreferences
from .props import SceneProps
from .utils import Registry

# Importing modules with Registry definitions
__all__ = [
    "AddonPreferences",
    "operators",
    "props",
    "ui",
]


def register() -> None:
    "Register addon."
    Registry.register()

    bpy.types.Scene.pawsbkr = PointerProperty(type=SceneProps)


def unregister() -> None:
    "Unregister addon."
    Registry.unregister()

    del bpy.types.Scene.pawsbkr
