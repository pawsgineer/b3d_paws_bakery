"""Various addon utils."""

import bpy
from bpy import types as b_t

from ._helpers import ASSETS_DIR, log

UTIL_MATS_PATH = ASSETS_DIR.joinpath("materials.blend")

UTIL_NODES_GROUP_AORM = "pawsbkr_utils_aorm"
UTIL_NODES_GROUP_COLOR = "pawsbkr_utils_color"

UTIL_NODE_GROUPS = frozenset(
    {
        UTIL_NODES_GROUP_AORM,
        UTIL_NODES_GROUP_COLOR,
    }
)


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
                bpy.utils.register_class(class_)  # type: ignore[no-untyped-call]
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
                bpy.utils.unregister_class(class_)  # type: ignore[no-untyped-call]
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


class AssetLibraryManager:
    """Manager of Blender timers."""

    # TODO: handle opening another file?
    _is_nodes_imported = False

    @staticmethod
    def material_load(
        name: str,
        *,
        link: bool = False,
        use_existing: bool = False,
        replace_existing: bool = True,
    ) -> b_t.Material:
        """Load material from add-on asset library.

        :param str name: Material name
        :param bool use_existing: Skip import if material already exists,
            defaults to False
        :param bool replace_existing: Re-import the material and replace references from
            the old one, defaults to True
        :raises AddonException: If material not found in the library
        :return b_t.Material: Imported material
        """
        mat = bpy.data.materials.get(name)

        if mat:
            if use_existing:
                return mat

            mat.use_fake_user = False
            if mat.users < 1:
                bpy.data.materials.remove(mat)

        mat_old = bpy.data.materials.get(name)
        if mat_old:
            mat_old.name += "_old"

        with bpy.data.libraries.load(
            str(UTIL_MATS_PATH), link=link, assets_only=True
        ) as (
            data_src,
            data_dst,
        ):
            if name not in data_src.materials:
                raise AddonException(f"No material with name {name!r} found in library")
            data_dst.materials = [name]

        mat = bpy.data.materials.get(name)
        mat.asset_clear()  # type: ignore[no-untyped-call]
        mat.use_fake_user = False

        if mat_old and replace_existing:
            mat_old.user_remap(mat)
            bpy.data.materials.remove(mat_old)

        return mat

    @classmethod
    def node_groups_load(cls) -> None:
        """Load node groups from add-on asset library."""
        missing_names: set[str]

        if not cls._is_nodes_imported:
            log("Importing Node Groups for the first time.")
            for ng_name in UTIL_NODE_GROUPS:
                node = bpy.data.node_groups.get(ng_name)
                if not node:
                    continue
                bpy.data.node_groups.remove(node)
            missing_names = UTIL_NODE_GROUPS
        else:
            missing_names = {
                ng_name
                for ng_name in UTIL_NODE_GROUPS
                if ng_name not in bpy.data.node_groups
            }
        if not missing_names:
            return

        log("Some Node Groups are missing. Loading...", missing_names)

        with bpy.data.libraries.load(str(UTIL_MATS_PATH)) as (data_src, data_dst):
            for ng_name in missing_names:
                if ng_name not in data_src.node_groups:
                    raise AddonException(f"No Node Group with name {ng_name!r} found")
                data_dst.node_groups.append(ng_name)

        for ng_name in UTIL_NODE_GROUPS:
            ng = bpy.data.node_groups.get(ng_name)
            ng.use_fake_user = False

        cls._is_nodes_imported = True
