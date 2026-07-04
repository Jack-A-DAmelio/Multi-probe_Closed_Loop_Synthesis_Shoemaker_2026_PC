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
- batch submission of all widget values

A Pane does NOT know anything about:
- Dash
- HTML
- component IDs
- callback registration

Those responsibilities belong to the dashboard engine.
"""

from typing import List, Dict, Any


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
    on_submit(values)
        Called when the user presses the pane "Confirm" button.

    refresh()
        Called periodically by the dashboard engine.
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
        self.widgets: List = []

    # ---------------------------------------------------------
    # AUTOMATIC WIDGET REGISTRATION
    # ---------------------------------------------------------

    def __setattr__(self, name, value):
        """
        Automatically register widgets assigned to the pane.
        """

        # Always set attribute first
        object.__setattr__(self, name, value)

        # Register widget if it is a Widget instance (flag-based for now)
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
        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build()."
        )

    # ---------------------------------------------------------
    # NEW: BATCH SUBMISSION MODEL
    # ---------------------------------------------------------

    def on_submit(self, values: Dict[str, Any]):
        """
        Called when the user presses the pane-level Confirm button.

        Parameters
        ----------
        values : dict
            Dictionary of all widget values in the pane.

        Returns
        -------
        None

        Notes
        -----
        This replaces all per-widget callback behavior.
        Override this in each pane to run experiments or actions.
        """
        pass

    # ---------------------------------------------------------
    # OPTIONAL METHODS
    # ---------------------------------------------------------

    def refresh(self):
        """
        Periodic update function.

        Override this method if the pane should periodically
        update displayed values.
        """
        pass