"""Preferences defaults."""

from dataclasses import dataclass
from enum import Enum


@dataclass(kw_only=True)
class _TextureImportRuleDescription:
    node_prefix: str
    aliases: list[str]
    is_non_color: bool = False


class DefaultTextureImportRule(Enum):
    """Default values for Texture Import Rules."""

    ALBEDO = _TextureImportRuleDescription(
        aliases=["albedo", "color", "base", "basecolor", "diffuse"],
        node_prefix="texture_albedo",
    )
    METALNESS = _TextureImportRuleDescription(
        aliases=["metalness", "metallic", "metal"],
        node_prefix="texture_metalness",
        is_non_color=True,
    )
    ROUGHNESS = _TextureImportRuleDescription(
        aliases=["roughness", "rough"],
        node_prefix="texture_roughness",
        is_non_color=True,
    )
    NORMAL = _TextureImportRuleDescription(
        aliases=["normalgl", "normal", "nor"],
        node_prefix="texture_normal",
        is_non_color=True,
    )
    DISPLACEMENT = _TextureImportRuleDescription(
        aliases=["displacement", "height"],
        node_prefix="texture_displacement",
        is_non_color=True,
    )
    AMBIENT_OCCLUSION = _TextureImportRuleDescription(
        aliases=["ambientocclusion", "oclussion", "ao"],
        node_prefix="texture_ao",
        is_non_color=True,
    )
    AORM = _TextureImportRuleDescription(
        aliases=["aorm", "orm"],
        node_prefix="texture_aorm",
        is_non_color=True,
    )
    OPACITY = _TextureImportRuleDescription(
        aliases=["opacity", "alpha"],
        node_prefix="texture_opacity",
        is_non_color=True,
    )
    EMISSION = _TextureImportRuleDescription(
        aliases=["emission", "emissive", "emit"],
        node_prefix="texture_emission",
    )
    SCATTERING = _TextureImportRuleDescription(
        aliases=["scattering"],
        node_prefix="texture_scattering",
        is_non_color=True,
    )
    MATERIAL_ID = _TextureImportRuleDescription(
        aliases=["matid"],
        node_prefix="texture_matid",
    )
    OBJECT_ID = _TextureImportRuleDescription(
        aliases=["objid", "id"],
        node_prefix="texture_objid",
    )
    POSITION = _TextureImportRuleDescription(
        aliases=["position", "pos"],
        node_prefix="texture_position",
        is_non_color=True,
    )
    TRANSMISSION = _TextureImportRuleDescription(
        aliases=["transmission"],
        node_prefix="texture_transmission",
        is_non_color=True,
    )

    @property
    def aliases(self) -> list[str]:
        """List of aliases."""
        return self.value.aliases

    @property
    def node_prefix(self) -> str:
        """Node name prefix."""
        return self.value.node_prefix

    @property
    def is_non_color(self) -> bool:
        """Is non-color space."""
        return self.value.is_non_color

    @classmethod
    def get_all_node_prefixes(cls) -> set[str]:
        """Return set of all node prefixes for Texture Import Rules."""
        return {rule.node_prefix for rule in cls}
