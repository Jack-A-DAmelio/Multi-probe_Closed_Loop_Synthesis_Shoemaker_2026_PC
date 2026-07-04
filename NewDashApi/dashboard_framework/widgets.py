"""
Dashboard widget definitions.

Author: You | Date: 2026-07-04 | Framework Version: v0.1

Purpose:
--------
Defines the widget classes used to build dashboard panes.

Widgets are lightweight Python objects that describe what should
appear in the dashboard.

Widgets do NOT know anything about Dash or HTML. Their only
responsibility is storing state and validating user input.

Rendering is handled by the dashboard engine.
"""

from typing import Any, Callable, List


# =========================================================
# BASE WIDGET CLASS
# =========================================================

class Widget:
    """
    Base class for all dashboard widgets.

    Parameters
    ----------
    label : str
        Text shown beside the widget.

    default : Any
        Initial widget value.

    callback : Callable, optional
        Function called when the widget is activated.

    Returns
    -------
    None
    """

    def __init__(
        self,
        label: str = "",
        default: Any = None,
        callback: Callable = None
    ):

        # ---------------------------------------------------------
        # DISPLAY INFORMATION
        # ---------------------------------------------------------

        self.label = label

        self.enabled = True
        self.visible = True

        # Assigned later by the dashboard engine
        self.widget_id = None

        # ---------------------------------------------------------
        # CALLBACK
        # ---------------------------------------------------------

        self.callback = callback

        # ---------------------------------------------------------
        # VALIDATION STATE
        # ---------------------------------------------------------

        self.valid = True
        self.error_message = ""

        # ---------------------------------------------------------
        # VALUE STORAGE
        # ---------------------------------------------------------

        self._value = None
        self.value = default

    # ---------------------------------------------------------
    # VALUE PROPERTY
    # ---------------------------------------------------------

    @property
    def value(self):
        """
        Current widget value.
        """

        return self._value

    @value.setter
    def value(self, new_value):
        """
        Update the widget value after validation.
        """

        is_valid, message = self.validate(new_value)

        self.valid = is_valid
        self.error_message = message

        if is_valid:
            self._value = new_value

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def validate(self, value):
        """
        Validate a new value.

        Parameters
        ----------
        value : object

        Returns
        -------
        tuple(bool, str)
            (is_valid, error_message)
        """

        return True, ""


# =========================================================
# LABEL
# =========================================================

class Label(Widget):
    """
    Read-only text label.
    """

    pass


# =========================================================
# STATUS
# =========================================================

class Status(Widget):
    """
    Status message widget.
    """

    pass


# =========================================================
# BUTTON
# =========================================================

class Button(Widget):
    """
    Push button widget.
    """

    def __init__(
        self,
        label: str,
        callback: Callable = None
    ):

        super().__init__(
            label=label,
            callback=callback
        )


# =========================================================
# TEXT INPUT
# =========================================================

class TextInput(Widget):
    """
    Single-line text input.
    """

    def __init__(
        self,
        label: str,
        default: str = "",
        maximum_length: int = None,
        placeholder: str = ""
    ):

        super().__init__(
            label=label,
            default=default
        )

        self.maximum_length = maximum_length
        self.placeholder = placeholder

    def validate(self, value):

        if not isinstance(value, str):
            return False, "Value must be text."

        if self.maximum_length is not None:

            if len(value) > self.maximum_length:
                return (
                    False,
                    f"Maximum length is {self.maximum_length} characters."
                )

        return True, ""


# =========================================================
# NUMBER INPUT
# =========================================================

class NumberInput(Widget):
    """
    Numeric input widget.
    """

    def __init__(
        self,
        label: str,
        default: float = 0,
        minimum: float = None,
        maximum: float = None,
        units: str = ""
    ):

        super().__init__(
            label=label,
            default=default
        )

        self.minimum = minimum
        self.maximum = maximum
        self.units = units

    def validate(self, value):

        if not isinstance(value, (int, float)):
            return False, "Value must be numeric."

        if self.minimum is not None:

            if value < self.minimum:
                return (
                    False,
                    f"Value must be greater than or equal to {self.minimum}."
                )

        if self.maximum is not None:

            if value > self.maximum:
                return (
                    False,
                    f"Value must be less than or equal to {self.maximum}."
                )

        return True, ""


# =========================================================
# DROPDOWN
# =========================================================

class Dropdown(Widget):
    """
    Dropdown selection widget.
    """

    def __init__(
        self,
        label: str,
        options: List[str],
        default: str = None
    ):

        self.options = options

        super().__init__(
            label=label,
            default=default
        )

    def validate(self, value):

        if value not in self.options:

            return (
                False,
                "Selection is not in the available options."
            )

        return True, ""


# =========================================================
# CHECKBOX
# =========================================================

class Checkbox(Widget):
    """
    Boolean checkbox widget.
    """

    def validate(self, value):

        if not isinstance(value, bool):

            return (
                False,
                "Checkbox value must be True or False."
            )

        return True, ""


# =========================================================
# GRAPH
# =========================================================

class Graph(Widget):
    """
    Graph display widget.
    """

    pass


# =========================================================
# IMAGE
# =========================================================

class Image(Widget):
    """
    Image display widget.
    """

    pass


# =========================================================
# TABLE
# =========================================================

class Table(Widget):
    """
    Table display widget.
    """

    pass