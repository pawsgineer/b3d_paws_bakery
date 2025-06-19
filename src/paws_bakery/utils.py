"""Various addon utils."""

import bpy

from ._helpers import log


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
