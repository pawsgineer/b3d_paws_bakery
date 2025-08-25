# flake8: noqa: F821
"""Preferences Properties."""

import re
from collections.abc import Callable
from typing import cast
from uuid import uuid4

from bpy import props as b_p
from bpy import types as b_t

from ..utils import Registry


def _set_force_non_empty_name(self: b_t.ID, value: str) -> None:
    self["name"] = value if value != "" else str(uuid4())


def _string_getter_factory(name: str) -> Callable[[b_t.StringProperty], str]:
    def cb(self: b_t.StringProperty) -> str:
        try:
            value = self[name]
        except KeyError:
            # value = ""
            value = self.bl_rna.properties[name].default  # type: ignore[attr-defined]
        return cast(str, value)

    return cb


def _string_setter_factory(
    name: str, pattern: re.Pattern[str]
) -> Callable[[b_t.StringProperty, str], None]:
    def cb(self: b_t.StringProperty, value: str) -> None:
        if re.search(pattern, value):
            return
        self[name] = value.lower()

    return cb


@Registry.add
class TextureImportRuleProps(b_t.PropertyGroup):
    """Node and texture name matching for texture import."""

    name: b_p.StringProperty(  # type: ignore[valid-type]
        get=_string_getter_factory("name"),
        set=_set_force_non_empty_name,
    )

    is_enabled: b_p.BoolProperty(default=True)  # type: ignore[valid-type]
    is_builtin: b_p.BoolProperty(default=False)  # type: ignore[valid-type]

    is_non_color: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Non-Color",
        description="Use non-color space for image",
        default=False,
    )

    node_name_prefix: b_p.StringProperty(  # type: ignore[valid-type]
        name="Node Name Prefix",
        description=(
            "The texture node name prefix used to determine where to assign the image"
        ),
        default="pawsbkr_custom_001",
        get=_string_getter_factory("node_name_prefix"),
        set=_string_setter_factory("node_name_prefix", r"[^\w\s_]+"),
        options={"TEXTEDIT_UPDATE"},
    )
    aliases: b_p.StringProperty(  # type: ignore[valid-type]
        name="Aliases",
        description=(
            "A comma separated list of aliases to search for in filenames "
            "(e.g. `albedo, color, basecolor`)"
        ),
        default="alias_one, alias_two",
        get=_string_getter_factory("aliases"),
        set=_string_setter_factory("aliases", r"[^\w,\s_]+"),
        options={"TEXTEDIT_UPDATE"},
    )

    def get_parsed_aliases(self) -> list[str]:
        """Get a list of aliases."""
        return re.findall(r"(\w+)[, ]?", self.aliases)

    def is_matches_name(self, name: str) -> bool:
        """Check if name matches one of aliases."""
        gen = (
            re.search(f"_{alias}" + r"[._\-\s]", name.lower())
            for alias in self.get_parsed_aliases()
        )

        return any(gen)
