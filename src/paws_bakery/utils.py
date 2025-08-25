"""Various addon utils."""

import bpy
from bpy import types as b_t

from ._helpers import ASSETS_DIR, log

UTIL_MATS_PATH = ASSETS_DIR.joinpath("materials.blend")

UTIL_NODES_GROUP_AORM = "pawsbkr_utils_aorm"
UTIL_NODES_GROUP_COLOR = "pawsbkr_utils_color"

UTIL_NODE_GROUPS = [
    UTIL_NODES_GROUP_AORM,
    UTIL_NODES_GROUP_COLOR,
]


class AddonException(Exception):
    """Addon specific exception."""


class Registry:
    """Registry of Blender classes."""

    CLASSES: list[type[bpy.types.bpy_struct]] = []
    KEYMAPS: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []

    @staticmethod
    def add(target_class: type[bpy.types.bpy_struct]) -> type[bpy.types.bpy_struct]:
        """Add class to registry."""
        Registry.CLASSES.append(target_class)
        return target_class

    @staticmethod
    def register() -> None:
        """Register classes in Blender."""
        for class_ in Registry.CLASSES:
            # log(f"Registering: {class_.__name__}.")
            try:
                bpy.utils.register_class(class_)
            except BaseException:
                log(f"Can't register: {class_}.")
                Registry.unregister()
                raise

    @staticmethod
    def unregister() -> None:
        """Unregister classes from Blender."""
        for class_ in reversed(Registry.CLASSES):
            # log(f"Unregistering: {class_.__name__}")
            try:
                bpy.utils.unregister_class(class_)
            # pylint: disable-next=broad-exception-caught
            except BaseException:  # noqa: B036
                log(f"Can't unregister: {class_}.")


class TimerManager:
    """Manager of Blender timers."""

    __timer = None
    __ref_count = 0

    @classmethod
    def __remove_timer(cls) -> None:
        if cls.__timer is None:
            return
        # log(f"{cls.__name__}: Removing timer")
        bpy.context.window_manager.event_timer_remove(cls.__timer)
        cls.__timer = None

    @classmethod
    def acquire(cls) -> bpy.types.Timer:
        """Create the timer if it doesn't exist."""
        cls.__ref_count += 1

        if cls.__timer is None:
            # log(f"{cls.__name__}: Creating timer")
            wm = bpy.context.window_manager
            cls.__timer = wm.event_timer_add(1.0, window=bpy.context.window)

        return cls.__timer

    @classmethod
    def release(cls) -> None:
        """Remove the timer if there are no more users."""
        if cls.__ref_count > 0:
            cls.__ref_count -= 1

        if cls.__ref_count == 0:
            cls.__remove_timer()


def load_material_from_lib(name: str, *, ignore_existing: bool = False) -> b_t.Material:
    """Load material from add-on asset library."""
    mat = bpy.data.materials.get(name)

    if mat:
        if ignore_existing:
            return mat

        raise AddonException(
            f"Material with the name {name!r} already exists. "
            "Remove or rename it if you want to reimport material"
        )

    with bpy.data.libraries.load(
        str(UTIL_MATS_PATH),
        link=False,
        assets_only=True,
    ) as (data_src, data_dst):
        if name not in data_src.materials:
            raise AddonException(f"No material with name {name!r} found in library")
        data_dst.materials = [name]

    mat = bpy.data.materials.get(name)
    mat.asset_clear()  # type: disable=no-untyped-call
    mat.use_fake_user = False

    return mat


def load_node_groups_from_lib() -> None:
    """Load node groups from add-on asset library."""
    if all(ng_name in bpy.data.node_groups for ng_name in UTIL_NODE_GROUPS):
        return

    log("Some Node Groups are missing. Loading...")

    with bpy.data.libraries.load(str(UTIL_MATS_PATH)) as (data_src, data_dst):
        for ng_name in UTIL_NODE_GROUPS:
            if ng_name not in data_src.node_groups:
                raise AddonException(f"No Node Group with name {ng_name!r} found")
            data_dst.node_groups.append(ng_name)

    for ng_name in UTIL_NODE_GROUPS:
        ng = bpy.data.node_groups.get(ng_name)
        ng.use_fake_user = False
