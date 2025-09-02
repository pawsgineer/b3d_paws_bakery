# pylint: disable=missing-module-docstring
import importlib
import inspect

from bpy import types as blt

PACKAGES_TO_CHECK = ["paws_bakery"]


# TODO: test nested submodules
def test_unique_bl_idname() -> None:  # noqa: C901
    """Check that all bl_idname properties are uniq."""
    for package_name in PACKAGES_TO_CHECK:
        module = importlib.import_module(package_name)

        classes_to_check: set[type] = set()

        classes = inspect.getmembers(module, inspect.isclass)
        for _, cls in classes:
            if issubclass(cls, blt.bpy_struct):
                classes_to_check.add(cls)

        submodules = inspect.getmembers(module, inspect.ismodule)
        for _, smodule in submodules:
            if smodule.__package__.split(".")[0] == package_name:
                print(f"Checking module: {smodule}")
                classes = inspect.getmembers(smodule, inspect.isclass)
                for _, cls in classes:
                    if issubclass(cls, blt.bpy_struct):
                        classes_to_check.add(cls)
            else:
                print(f"Skipping module: {smodule}, package: {smodule.__package__}")

        classes_with_bl_idname: dict[str, set[type]] = {}

        for cls in classes_to_check:
            print(f"Class checked: {cls}")
            bl_idname = getattr(cls, "bl_idname", None)
            if bl_idname is not None:
                if cls.bl_idname in classes_with_bl_idname:
                    classes_with_bl_idname[cls.bl_idname].add(cls)
                else:
                    classes_with_bl_idname[cls.bl_idname] = {cls}

        for bl_idname, classes in classes_with_bl_idname.items():
            if len(classes) > 1:
                print(f"bl_idname: {bl_idname} found in more than 1 class: {classes}")

            assert len(classes) <= 1
