from dataclasses import dataclass, field  # Import dataclass helpers.
from typing import Any, List, Optional  # Import type hints.


@dataclass
class Widget:
    """
    Base class for all widgets.

    Contains only properties common to every widget.
    """

    label: str  # Human-readable name shown in the dashboard.

    widget_type: str = "widget"  # Identifier used by DashAdapter for rendering.

    default: Any = None  # Initial value if a widget requires one.

    _is_widget: bool = True  # Marker used to identify widget objects.


#
# Display widgets
#


@dataclass
class Display(Widget):
    """
    Read-only value display.

    Can optionally refresh from a server source.
    """

    source: Optional[str] = None  # API endpoint used to retrieve live values.

    params: Optional[dict] = None  # Optional request parameters for the source.

    widget_type: str = "display"  # Renderer type for DashAdapter.


#
# User input widgets
#


@dataclass
class TextInput(Widget):
    """
    User editable text field.
    """

    default: str = ""  # Starting text value.

    widget_type: str = "text"  # Renderer type for DashAdapter.


@dataclass
class NumberInput(Widget):
    """
    User editable numeric field.
    """

    default: float = 0.0  # Starting numeric value.

    widget_type: str = "number"  # Renderer type for DashAdapter.


@dataclass
class Dropdown(Widget):
    """
    User selectable list.
    """

    options: Optional[List[str]] = None
    default: Optional[str] = None  # Initial selected value.

    widget_type: str = "dropdown"  # Renderer type for DashAdapter.


@dataclass
class Checkbox(Widget):
    """
    User boolean input.
    """

    default: bool = False  # Initial checked state.

    widget_type: str = "checkbox"  # Renderer type for DashAdapter.


#
# Action widgets
#


@dataclass
class Button(Widget):
    """
    User action trigger.

    Sends pane input values to a server.
    """

    endpoint: str = ""  # Server endpoint called by the button.

    widget_type: str = "button"  # Renderer type for DashAdapter.