from dataclasses import dataclass  # Import dataclass decorator for simple data containers.
from typing import Any, List, Optional  # Import type hints for flexible widget definitions.


@dataclass
class Widget:
    """
    Base class for all widgets.

    Contains only properties common to every widget.
    Widgets do not know about servers, APIs, or Dash rendering.
    """

    label: str  # Human-readable name shown in the dashboard.

    widget_type: str = "widget"  # Identifier used by DashAdapter to select the renderer.

    default: Any = None  # Initial value used when no value has been received.

    _is_widget: bool = True  # Marker used to identify widget objects.


#
# Display widgets
#


@dataclass
class Display(Widget):
    """
    Read-only value display.

    Retrieves live information from a server source.
    """

    source: Optional[str] = None  
    # Relative API path used to retrieve the value.
    # DashAdapter combines this with the configured API address.
    # Example:
    # api = "http://localhost:8000"
    # source = "/api/temperature"
    # becomes:
    # http://localhost:8000/api/temperature

    params: Optional[dict] = None  
    # Optional request parameters sent with the API request.

    widget_type: str = "display"  
    # Renderer type used by DashAdapter.


@dataclass
class ImageDisplay(Widget):
    """
    Read-only image display.

    Retrieves an image from a server source.
    """

    source: Optional[str] = None  
    # Relative API path or image URL.
    # DashAdapter combines relative paths with the configured API address.

    params: Optional[dict] = None  
    # Optional request parameters for the image source.

    widget_type: str = "image"  
    # Tells DashAdapter to render an image component.


#
# User input widgets
#


@dataclass
class TextInput(Widget):
    """
    User editable text field.
    """

    default: str = ""  
    # Starting text value.

    widget_type: str = "text"  
    # Renderer type used by DashAdapter.


@dataclass
class NumberInput(Widget):
    """
    User editable numeric field.
    """

    default: float = 0.0  
    # Starting numeric value.

    widget_type: str = "number"  
    # Renderer type used by DashAdapter.


@dataclass
class Dropdown(Widget):
    """
    User selectable list.
    """

    options: Optional[List[str]] = None  
    # Available choices presented to the user.

    default: Optional[str] = None  
    # Initially selected choice.

    widget_type: str = "dropdown"  
    # Renderer type used by DashAdapter.


@dataclass
class Checkbox(Widget):
    """
    User boolean input.
    """

    default: bool = False  
    # Initial checked state.

    widget_type: str = "checkbox"  
    # Renderer type used by DashAdapter.


#
# Action widgets
#


@dataclass
class Button(Widget):
    """
    User action trigger.

    Sends pane input values to a server when pressed.
    """

    endpoint: str = ""  
    # Relative API path called when the button is pressed.
    # DashAdapter combines this with the configured API address.
    # Example:
    # api = "http://localhost:8000"
    # endpoint = "/heater/apply"
    # becomes:
    # http://localhost:8000/heater/apply

    widget_type: str = "button"  
    # Renderer type used by DashAdapter.