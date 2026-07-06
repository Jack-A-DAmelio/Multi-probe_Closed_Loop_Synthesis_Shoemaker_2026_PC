from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Widget:
    label: str
    default: Any = None
    widget_type: str = "text"

    # NEW: live endpoint
    source: Optional[str] = None

    # NEW: request parameters
    params: Optional[dict] = None

    _is_widget: bool = True


@dataclass
class NumberInput(Widget):
    widget_type: str = "number"
    default: float = 0.0


@dataclass
class TextInput(Widget):
    widget_type: str = "text"
    default: str = ""


@dataclass
class Dropdown(Widget):
    options: List[str] = None
    widget_type: str = "dropdown"
    default: Optional[str] = None