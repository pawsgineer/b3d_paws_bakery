"""Various operator helpers."""

import colorsys
from itertools import chain
from typing import cast

import bpy
from bpy import types as b_t

from ..enums import BlenderImageType, BlenderSpaceType
from ..props import get_props


def generate_color_set(number_of_colors: int) -> list[tuple[float, float, float]]:
    """Return a list of visually distinct RGB colors."""
    hsv_colors = [
        (x / number_of_colors, 0.9, 1.0 - 0.25 * (x % 4))
        for x in range(number_of_colors)
    ]
    return [colorsys.hsv_to_rgb(*color) for color in hsv_colors]


def get_selected_materials(ctx: b_t.Context = None) -> dict[str, b_t.Material]:
    """Return all unique materials used by the selected objects."""
    materials: dict[str, b_t.Material] = {}
    if ctx is None:
        ctx = bpy.context

    for obj in ctx.selected_objects:
        for slot in obj.material_slots:
            if slot.material is not None:
                materials[slot.material.name] = slot.material

    return materials


def show_image_in_editor(context: b_t.Context, image: b_t.Image) -> None:
    """Show Image in Image Editor area."""
    if not get_props(context).utils_settings.show_image_in_editor:
        return

    for window in chain([context.window], context.window_manager.windows):
        for area in window.screen.areas:
            if area.type != BlenderSpaceType.IMAGE_EDITOR:
                continue

            img_space = cast(b_t.SpaceImageEditor, area.spaces.active)
            if img_space.use_image_pin or (
                img_space.image
                and img_space.image.type
                in {
                    BlenderImageType.RENDER_RESULT,
                    BlenderImageType.COMPOSITING,
                }
            ):
                continue
            img_space.image = image
            img_space.use_image_pin = False
            break
