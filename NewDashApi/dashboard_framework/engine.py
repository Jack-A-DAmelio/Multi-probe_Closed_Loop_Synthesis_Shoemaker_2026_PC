"""
Dashboard engine (non-Dash core runtime).

Author: You | Date: 2026-07-04 | Framework Version: v0.1

Purpose:
--------
Core execution layer for the dashboard framework.

The engine is responsible for:
- loading panes
- building panes
- collecting widget values
- executing pane-level submit actions

This version is intentionally backend-agnostic (no Dash dependency).
"""

from typing import List, Dict, Any

from dashboard_framework.discovery import discover_panes


# =========================================================
# ENGINE CLASS
# =========================================================

class DashboardEngine:
    """
    Core runtime engine for executing dashboard logic.
    """

    def __init__(self, pane_directory: str, state=None):

        self.pane_directory = pane_directory
        self.state = state

        # Loaded pane objects
        self.panes: List = []

    # ---------------------------------------------------------
    # LOAD + INITIALIZE
    # ---------------------------------------------------------

    def load(self):
        """
        Discover and initialize all panes.
        """

        self.panes = discover_panes(
            self.pane_directory,
            state=self.state
        )

        # Build all panes
        for pane in self.panes:

            try:
                pane.build()

                print(f"[ENGINE] Built pane: {pane.TITLE}")

            except Exception as e:

                print(f"[ENGINE] Failed to build pane: {pane.TITLE}")
                print(e)

    # ---------------------------------------------------------
    # CORE ACTION: COLLECT VALUES
    # ---------------------------------------------------------

    def _collect_values(self, pane) -> Dict[str, Any]:
        """
        Extract all widget values from a pane.

        Returns
        -------
        dict
        """

        values = {}

        for widget in pane.widgets:

            # Use attribute name if available, fallback to label
            name = getattr(widget, "label", None)

            if name is None:
                continue

            values[name] = widget.value

        return values

    # ---------------------------------------------------------
    # CORE ACTION: SUBMIT PANE
    # ---------------------------------------------------------

    def submit_pane(self, pane):
        """
        Simulate pressing the "Confirm" button for a pane.
        """

        try:

            values = self._collect_values(pane)

            print(f"\n[ENGINE] Submitting pane: {pane.TITLE}")
            print(f"[ENGINE] Values: {values}")

            pane.on_submit(values)

        except Exception as e:

            print(f"[ENGINE] Error during submit: {pane.TITLE}")
            print(e)

    # ---------------------------------------------------------
    # TEST LOOP (NO DASH YET)
    # ---------------------------------------------------------

    def run_cli_test(self):
        """
        Simple CLI simulation of the dashboard.
        """

        print("\n[ENGINE] Dashboard loaded\n")

        for i, pane in enumerate(self.panes):

            print(f"{i}: {pane.TITLE}")

        print("\nType pane number to submit, or 'q' to quit.\n")

        while True:

            cmd = input("> ")

            if cmd == "q":
                break

            try:
                idx = int(cmd)
                pane = self.panes[idx]

                self.submit_pane(pane)

            except Exception as e:
                print("Invalid input:", e)