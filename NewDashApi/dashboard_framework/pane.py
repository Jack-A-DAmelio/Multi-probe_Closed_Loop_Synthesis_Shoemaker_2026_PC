from typing import List
from dashboard_framework.widgets import Widget


class Pane:
    """
    Minimal Pane abstraction.

    A Pane is:
    - a container for widgets
    - a namespace (NAME)
    - an optional action definition container
    """

    NAME: str = "unnamed"

    def __init__(self):
        self.widgets: List[Widget] = []


    # ---------------------------------------------------------
    # WIDGET REGISTRATION
    # ---------------------------------------------------------

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

        if isinstance(value, Widget):
            if value not in self.widgets:
                self.widgets.append(value)

    # ---------------------------------------------------------
    # USER DEFINED BUILD
    # ---------------------------------------------------------

    def build(self):
        """
        Define widgets and actions here.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build()"
        )