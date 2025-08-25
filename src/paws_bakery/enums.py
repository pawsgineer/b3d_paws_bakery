"""A collection of different Enums."""

import enum
from enum import auto
from typing import Any


class CaseSensitiveStrEnum(enum.StrEnum):
    """Case-sensitive StrEnum implementation."""

    @staticmethod
    def _generate_next_value_(
        name: str, _start: int, _count: int, _last_values: list[Any]
    ) -> Any:
        return name


class BlenderWMReportType(CaseSensitiveStrEnum):
    """Blender WM report types.

    List may not be complete and contain only used types.
    """

    DEBUG = auto()
    INFO = auto()
    OPERATOR = auto()
    PROPERTY = auto()
    WARNING = auto()
    ERROR = auto()
    ERROR_INVALID_INPUT = auto()
    ERROR_INVALID_CONTEXT = auto()
    ERROR_OUT_OF_MEMORY = auto()


class BlenderOperatorType(CaseSensitiveStrEnum):
    """Blender operator types.

    List may not be complete and contain only used types.
    """

    REGISTER = auto()
    """
    Register.
    Display in the info window and support the redo toolbar panel.
    """
    UNDO = auto()
    """
    Undo.
    Push an undo event when the operator returns `FINISHED` (needed for operator redo,
    mandatory if the operator modifies Blender data).
    """
    UNDO_GROUPED = auto()
    """
    Grouped Undo.
    Push a single undo event for repeated instances of this operator.
    """
    BLOCKING = auto()
    """
    Blocking.
    Block anything else from using the cursor.
    """
    MACRO = auto()
    """
    Macro.
    Use to check if an operator is a macro.
    """
    GRAB_CURSOR = auto()
    """
    Grab Pointer.
    Use so the operator grabs the mouse focus, enables wrapping when continuous grab is
    enabled.
    """
    GRAB_CURSOR_X = auto()
    """
    Grab Pointer X.
    Grab, only warping the X axis.
    """
    GRAB_CURSOR_Y = auto()
    """
    Grab Pointer Y.
    Grab, only warping the Y axis.
    """
    DEPENDS_ON_CURSOR = auto()
    """
    Depends on Cursor.
    The initial cursor location is used, when running from a menus or buttons the user
    is prompted to place the cursor before beginning the operation.
    """
    PRESET = auto()
    """
    Preset.
    Display a preset button with the operators settings.
    """
    INTERNAL = auto()
    """
    Internal.
    Removes the operator from search results.
    """
    MODAL_PRIORITY = auto()
    """
    Modal Priority.
    Handle events before other modal operators without this option. Use with caution, do
    not modify data that other modal operators assume is unchanged during their
    operation.
    """


class BlenderOperatorReturnType(CaseSensitiveStrEnum):
    """Blender operator return types.

    List may not be complete and contain only used types.
    """

    RUNNING_MODAL = auto()
    CANCELLED = auto()
    FINISHED = auto()
    PASS_THROUGH = auto()
    INTERFACE = auto()


class BlenderEventType(CaseSensitiveStrEnum):
    """Blender WindowManager event types.

    List may not be complete and contain only used types.
    """

    ESC = auto()
    TIMER = auto()


class BlenderJobType(CaseSensitiveStrEnum):
    """Blender Job types.

    bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE)

    List may not be complete and contain only used types.
    """

    OBJECT_BAKE = auto()


class BlenderImageType(CaseSensitiveStrEnum):
    """Blender Image types.

    List may not be complete and contain only used types.
    """

    IMAGE = auto()
    MULTILAYER = auto()
    UV_TEST = auto()
    RENDER_RESULT = auto()
    COMPOSITING = auto()


class BlenderSpaceType(CaseSensitiveStrEnum):
    """Blender Space types.

    List may not be complete and contain only used types.
    """

    VIEW_3D = auto()
    IMAGE_EDITOR = auto()
    NODE_EDITOR = auto()
    SEQUENCE_EDITOR = auto()
    CLIP_EDITOR = auto()

    DOPESHEET_EDITOR = auto()
    GRAPH_EDITOR = auto()
    NLA_EDITOR = auto()

    TEXT_EDITOR = auto()
    CONSOLE = auto()
    INFO = auto()
    TOPBAR = auto()
    STATUSBAR = auto()

    OUTLINER = auto()
    PROPERTIES = auto()
    FILE_BROWSER = auto()
    SPREADSHEET = auto()
    PREFERENCES = auto()


class CyclesBakeType(CaseSensitiveStrEnum):
    """Blender cycles bake type names used in addon.

    List may not be complete and contain only used types.
    """

    COMBINED = auto()
    AO = auto()
    SHADOW = auto()
    POSITION = auto()
    NORMAL = auto()
    UV = auto()
    ROUGHNESS = auto()
    EMIT = auto()
    ENVIRONMENT = auto()
    DIFFUSE = auto()
    GLOSSY = auto()
    TRANSMISSION = auto()


class Colorspace(CaseSensitiveStrEnum):
    """Blender colorspace names.

    List may not be complete and contain only used types.
    """

    SRGB = DEFAULT = "sRGB"
    NON_COLOR = "Non-Color"
