from dash import html, dcc, Input, Output


from dashboard_framework.dash_adapter import DashAdapter
from app import app

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
from dash import html, dcc, Input, Output, State
from app import app



class LayoutEditor:

    def __init__(self, pane_classes):
        self.available_panes = pane_classes
        self._register()

    def layout(self):

        return html.Div([

            html.H3("Builder"),

            dcc.Input(
                id="api-url",
                value="http://localhost:5000/api"
            ),

            dcc.RadioItems(
                id="columns",
                options=[1, 2, 3],
                value=2
            ),

            dcc.Checklist(
                id="pane-selector",
                options=[
                    {"label": p.__name__, "value": p.__name__}
                    for p in self.available_panes
                ],
                value=[p.__name__ for p in self.available_panes]
            ),

            html.Button("Update Dashboard", id="build"),

        ])

    def _register(self):

        @app.callback(
            Output("layout-store", "data"),
            Input("build", "n_clicks"),
            State("api-url", "value"),
            State("columns", "value"),
            State("pane-selector", "value"),
            prevent_initial_call=True
        )
        def build(_, api, cols, selected):

            chosen = [
                p for p in self.available_panes
                if p.__name__ in selected
            ]

            return {
                "api": api,
                "columns": cols,
                "panes": [p.__name__ for p in chosen]
            }

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