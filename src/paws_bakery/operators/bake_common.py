from dataclasses import dataclass

from bpy import types as b_t

from ..preferences import get_preferences
from ..props import get_bake_settings

SUFFIX_HIGH = "_high"
SUFFIX_LOW = "_low"
BAKE_COLLECTION_NAME = "pawsbakery"


@dataclass
class LowHighObjectNames:
    """Container for map of low to high Object names."""

    low: str
    high: list[str]


def match_low_to_high(names: list[str]) -> list[LowHighObjectNames]:
    """Match low Object names to high."""
    names_norm = {n.lower(): n for n in names}
    names_norm_low = [n for n in names_norm if SUFFIX_LOW in n]
    matching = []

    for n_norm_low in names_norm_low:
        name_base = n_norm_low.rsplit(SUFFIX_LOW, 1)[0]
        high_base = name_base + SUFFIX_HIGH

        n_norm_high = [n for n in names_norm if high_base in n]
        matching.append(
            LowHighObjectNames(
                names_norm[n_norm_low],
                [names_norm[n] for n in n_norm_high],
            )
        )

    return matching


def generate_image_name_and_path(
    *,
    context: b_t.Context,
    settings_id: str,
    texture_set_name: str,
    texture_set_object_suffix: str = "",
) -> tuple[str, str]:
    """Return generated image name and path."""
    image_name_parts = [texture_set_name]
    if texture_set_object_suffix:
        image_name_parts.append(texture_set_object_suffix)

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

    active: b_t.Object
    selected: list[b_t.Object]

    def __post_init__(self) -> None:
        if self.active not in self.selected:
            raise ValueError(f"Active Object {self.active!r} is not in selected")
