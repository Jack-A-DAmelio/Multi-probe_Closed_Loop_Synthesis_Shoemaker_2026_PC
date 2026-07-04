"""
Dashboard pane discovery.

Author: You | Date: 2026-07-04 | Framework Version: v0.1

Purpose:
--------
Automatically discover dashboard panes contained within a
directory.

A pane is any class that inherits from the Pane base class.

This allows new dashboard functionality to be added by simply
creating a new Python file inside the panes directory.
"""

import importlib.util
import inspect
from pathlib import Path

from .pane import Pane


# =========================================================
# PANE DISCOVERY
# =========================================================

def discover_panes(
    pane_directory,
    state=None
):
    """
    Discover and instantiate dashboard panes.

    Parameters
    ----------
    pane_directory : str or Path
        Directory containing pane modules.

    state : object, optional
        Shared application state passed to every pane.

    Returns
    -------
    list
        List of instantiated Pane objects.
    """

    discovered_panes = []

    pane_directory = Path(pane_directory)

    if not pane_directory.exists():

        print(f"Pane directory does not exist: {pane_directory}")

        return discovered_panes

    # ---------------------------------------------------------
    # SEARCH FOR PYTHON FILES
    # ---------------------------------------------------------

    for python_file in sorted(pane_directory.glob("*.py")):

        # Skip package initialization files.
        if python_file.name == "__init__.py":
            continue

        try:

            # -------------------------------------------------
            # IMPORT MODULE
            # -------------------------------------------------

            spec = importlib.util.spec_from_file_location(
                python_file.stem,
                python_file
            )

            module = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(module)

            # -------------------------------------------------
            # SEARCH FOR PANE CLASSES
            # -------------------------------------------------

            for _, obj in inspect.getmembers(
                module,
                inspect.isclass
            ):

                if not issubclass(obj, Pane):
                    continue

                if obj is Pane:
                    continue

                pane = obj(state=state)

                discovered_panes.append(pane)

                print(
                    f"Loaded pane: {pane.TITLE}"
                )

        except Exception as error:

            print(
                f"Failed to load {python_file.name}"
            )

            print(error)

    # ---------------------------------------------------------
    # SORT BY DISPLAY ORDER
    # ---------------------------------------------------------

    discovered_panes.sort(
        key=lambda pane: pane.ORDER
    )

    return discovered_panes