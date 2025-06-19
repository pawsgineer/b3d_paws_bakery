# pylint: disable=missing-module-docstring
from paws_bakery import enums


def test_enums() -> None:
    assert enums.Colorspace.DEFAULT == enums.Colorspace.SRGB
    assert enums.Colorspace.SRGB == "sRGB"
    assert str(enums.Colorspace.SRGB) == "sRGB"
    assert enums.Colorspace.SRGB.name == "SRGB"
    assert enums.Colorspace.SRGB.value == "sRGB"

    assert enums.Colorspace.NON_COLOR == "Non-Color"
    assert str(enums.Colorspace.NON_COLOR) == "Non-Color"
    assert enums.Colorspace.NON_COLOR.name == "NON_COLOR"
    assert enums.Colorspace.NON_COLOR.value == "Non-Color"
