"""Common bake utils."""

from dataclasses import dataclass

from bpy import types as blt

from ..preferences import get_preferences
from ..props import get_bake_settings


def generate_image_name_and_path(
    *,
    context: blt.Context,
    settings_id: str,
    texture_set_name: str,
    object_prefix: str = "",
) -> tuple[str, str]:
    """Return generated image name and path."""
    image_name_parts = [texture_set_name]
    if object_prefix:
        image_name_parts.insert(0, object_prefix)

    name = (
        get_bake_settings(context, settings_id).get_name("_".join(image_name_parts))
        + ".png"
    )
    filepath = "/".join(
        [
            get_preferences().output_directory,
            texture_set_name,
            name,
        ]
    )

    return name, filepath


@dataclass(kw_only=True)
class BakeObjects:
    """Container for objects to bake.

    The list of selected objects is expected to contain the active object to
    maintain similarity with the Blender API.
    """

    active: blt.Object
    selected: list[blt.Object]

    def __post_init__(self) -> None:
        """Validate state after initialization."""
        if self.active not in self.selected:
            raise ValueError(f"Active Object {self.active!r} is not in selected")
