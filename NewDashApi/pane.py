"""
Base dashboard pane object.

Author: You | Date: 2026-07-04 | Framework Version: v0.1

Purpose:
--------
Defines the base class used for every dashboard pane.

A Pane is responsible for describing:
- its title
- its display order
- the widgets it contains
- optional periodic refresh behavior

A Pane does NOT know anything about:
- Dash
- HTML
- component IDs
- callback registration

Those responsibilities belong to the dashboard engine.
"""

from typing import List


# =========================================================
# BASE PANE CLASS
# =========================================================

class Pane:
    """
    Base class for all dashboard panes.

    Every pane in the dashboard should inherit from this class.

    Required methods
    ----------------
    build()
        Create and configure widgets for the pane.

    Optional methods
    ----------------
    refresh()
        Called periodically by the dashboard engine.

    Notes
    -----
    Widgets should always be assigned as instance attributes.

    Example
    -------
    self.temperature = NumberInput("Temperature")
    self.start = Button("Start")
    self.status = Status()

    Widgets assigned this way are automatically registered with the pane.
    """

    # Display title shown above the pane
    TITLE = "Untitled"

    # Lower numbers appear earlier in the dashboard
    ORDER = 100

    def __init__(self, state=None):
        """
        Create a new dashboard pane.

        Parameters
        ----------
        state : object, optional
            Shared application state object.
        """

        # Shared application state
        self.state = state

        # Internal widget storage.
        # This list is populated automatically whenever a widget is
        # assigned to the pane.
        self.widgets: List = []

    # ---------------------------------------------------------
    # AUTOMATIC WIDGET REGISTRATION
    # ---------------------------------------------------------

    def __setattr__(self, name, value):
        """
        Automatically register widgets assigned to the pane.

        Parameters
        ----------
        name : str
            Attribute name.

        value : object
            Value being assigned.

        Returns
        -------
        None
        """

        # Store the attribute normally.
        object.__setattr__(self, name, value)

        # Widgets identify themselves using the _is_widget flag.
        # This avoids importing widgets.py and creating circular imports.
        if getattr(value, "_is_widget", False):

            widgets = self.__dict__.get("widgets")

            if widgets is not None and value not in widgets:
                widgets.append(value)

    # ---------------------------------------------------------
    # REQUIRED METHODS
    # ---------------------------------------------------------

    def build(self):
        """
        Create widgets for this pane.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        This method must be implemented by subclasses.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build()."
        )

    # ---------------------------------------------------------
    # OPTIONAL METHODS
    # ---------------------------------------------------------

    def refresh(self):
        """
        Periodic update function.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        Override this method if the pane should periodically
        update displayed values.
        """

        pass