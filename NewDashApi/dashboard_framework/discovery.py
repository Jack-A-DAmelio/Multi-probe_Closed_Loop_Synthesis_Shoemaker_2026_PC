import os
import importlib
from dashboard_framework.pane import Pane


def discover_panes(folder="panes"):
    """
    Automatically load all Pane subclasses from a folder.
    """

    panes = []

    for file in os.listdir(folder):

        if not file.endswith(".py"):
            continue

        module_name = file[:-3]
        module_path = f"{folder}.{module_name}"

        module = importlib.import_module(module_path)

        for attr_name in dir(module):

            obj = getattr(module, attr_name)

            if (
                isinstance(obj, type)
                and issubclass(obj, Pane)
                and obj is not Pane
            ):
                panes.append(obj())

    return panes