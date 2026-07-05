"""
Pane system (v1)

Author: You | Date: 2026-07-04

Purpose:
--------
Defines a logical grouping of widgets that maps to a
namespaced JSON payload.

A Pane is a *data structure definition*, not a UI object.
"""

from typing import Dict, Any, List
from dashboard_framework.widgets import Widget


# =========================================================
# BASE PANE CLASS
# =========================================================

class Pane:
    """
    Base class for all panes.

    A Pane:
    - groups widgets
    - defines a namespace
    - produces structured JSON output
    """

    # MUST be overridden
    NAME: str = "unnamed"

    def __init__(self):
        self.widgets: List[Widget] = []
        # Verify that the pane has supplied all required metadata.
        self._validate_metadata()

    # ---------------------------------------------------------
    # WIDGET REGISTRATION
    # ---------------------------------------------------------

    def __setattr__(self, name, value):
        """
        Automatically register widgets assigned as attributes.
        """

        object.__setattr__(self, name, value)

        if isinstance(value, Widget):
            if value not in self.widgets:
                self.widgets.append(value)

    # ---------------------------------------------------------
    # BUILD INTERFACE (USER DEFINED)
    # ---------------------------------------------------------

    def build(self):
        """
        Define widgets here.

        Example:
            self.temperature = NumberInput("temperature")
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build()"
        )

    # ---------------------------------------------------------
    # PAYLOAD GENERATION
    # ---------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pane into namespaced JSON payload.

        Returns
        -------
        dict
            { pane_name: { widget_label: value } }
        """

        data = {}

        for w in self.widgets:
            data[w.label] = w.default

        return {self.NAME: data}
    # ---------------------------------------------------------
    # METADATA VALIDATION
    # ---------------------------------------------------------

    def _validate_metadata(self):
        """
        Verify that required pane metadata has been defined.

        Raises
        ------
        ValueError
            If a required class attribute has not been supplied by
            the pane implementation.
        """

        required_fields = {
            "NAME": self.NAME,
            "TITLE": self.TITLE,
            "API_ENDPOINT": self.API_ENDPOINT
        }

        for field_name, value in required_fields.items():

            if value is None:

                raise ValueError(
                    f"{self.__class__.__name__} must define {field_name}."
                )