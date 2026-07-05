"""
Widget system (v1)

Author: You | Date: 2026-07-04

Purpose:
--------
Defines pure input field descriptors used by Panes.

Widgets do NOT:
- handle UI rendering
- store runtime state
- handle callbacks

They ONLY describe input structure.
"""

from dataclasses import dataclass
from typing import Any, List, Optional


# =========================================================
# BASE WIDGET
# =========================================================

@dataclass
class Widget:
    """
    Base widget definition.

    Parameters
    ----------
    label : str
        Name of the field (used in UI + payload)

    default : Any
        Default value for the field

    widget_type : str
        Type of input ("number", "text", "dropdown", etc.)
    """

    label: str
    default: Any = None
    widget_type: str = "text"

    # internal flag for framework detection
    _is_widget: bool = True


# =========================================================
# SPECIFIC WIDGET TYPES
# =========================================================

@dataclass
class NumberInput(Widget):
    """
    Numeric input field.
    """

    widget_type: str = "number"
    default: float = 0.0


@dataclass
class TextInput(Widget):
    """
    Text input field.
    """

    widget_type: str = "text"
    default: str = ""


@dataclass
class Dropdown(Widget):
    """
    Dropdown selection field.
    """

    options: List[str] = None
    widget_type: str = "dropdown"
    default: Optional[str] = None