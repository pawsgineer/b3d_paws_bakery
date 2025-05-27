"""Various operator helpers."""

import colorsys

import bpy
from bpy import types as b_t


def generate_color_set(number_of_colors: int) -> list[tuple[float, float, float]]:
    """Returns a list of visually distinct RGB colors."""
    hsv_colors = [
        (x / number_of_colors, 0.9, 1.0 - 0.25 * (x % 4))
        for x in range(number_of_colors)
    ]
    return list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_colors))


def get_selected_materials() -> dict[str, b_t.Material]:
    """Returns all unique materials used by the selected objects."""
    materials: dict[str, b_t.Material] = {}

    for obj in bpy.context.selected_objects:
        for slot in obj.material_slots:
            if slot.material is not None:
                materials[slot.material.name] = slot.material

    return materials
