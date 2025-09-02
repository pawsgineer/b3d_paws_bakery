"""Common bake utils."""

from collections.abc import Sequence
from dataclasses import dataclass

from .utils import naturalize_key

SUFFIX_HIGH = "_high"
SUFFIX_LOW = "_low"


@dataclass
class LowHighObjectNames:
    """Container for map of low to high Object names."""

    low: str
    high: list[str]


def is_name_low(name: str) -> bool:
    """Whether mesh name is considered low."""
    return SUFFIX_LOW in name.casefold()


def is_name_high(name: str) -> bool:
    """Whether mesh name is considered high."""
    return SUFFIX_HIGH in name.casefold()


def match_low_to_high(names: Sequence[str]) -> list[LowHighObjectNames]:
    """Match low Object names to high."""
    names_norm = {n.casefold(): n for n in names}
    names_norm_low = [n for n in names_norm if is_name_low(n)]
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


def sort_mesh_names(names: Sequence[str]) -> list[str]:
    """Sort mesh names considering low to high suffixes."""
    low_to_high_names = match_low_to_high(names)
    low_to_high_names.sort(key=lambda x: naturalize_key(x.low))
    sorted_names = []
    for lh in low_to_high_names:
        sorted_names.append(lh.low)
        lh.high.sort(key=naturalize_key)
        sorted_names.extend(lh.high)
    return sorted_names
