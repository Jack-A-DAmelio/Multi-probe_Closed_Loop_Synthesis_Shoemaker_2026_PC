from dash import html, dcc, Input, Output

from dashboard_framework.layout_editor import LayoutEditor
from dashboard_framework.dash_adapter import DashAdapter
from dashboard_framework.app import app

import os
import importlib

from dashboard_framework.pane import Pane


def discover_panes(folder="panes"):
    """
    Automatically discover all Pane subclasses.

    Returns
    -------
    list[type]
        List of Pane classes.
    """

    pane_classes = []

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

                pane_classes.append(obj)

    return pane_classes


def main():

    panes = discover_panes("panes")

    builder = LayoutEditor(panes)

    @app.callback(
        Output("dashboard-area", "children"),
        Input("layout-store", "data")
    )
    def render_dashboard(data):

        if not data:
            return "No dashboard yet"

        selected = [
            p for p in panes
            if p.__name__ in data["panes"]
        ]

        return DashAdapter(selected, columns=data["columns"]).layout()

    app.layout = html.Div([

        dcc.Store(id="layout-store"),

        builder.layout(),

        html.Hr(),

        html.Div(id="dashboard-area")

    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()