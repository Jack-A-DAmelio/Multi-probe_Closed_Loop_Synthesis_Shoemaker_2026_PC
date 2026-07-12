from dash import html, dcc, Input, Output, State

from dashboard_framework.dash_adapter import DashAdapter
from dashboard_framework.pane import Pane
from app import app

import os
import importlib


def discover_panes(folder="panes"):
    pane_classes = []

    for file in os.listdir(folder):
        if not file.endswith(".py"):
            continue

        module = importlib.import_module(f"{folder}.{file[:-3]}")

        for name in dir(module):
            obj = getattr(module, name)

            if (
                isinstance(obj, type)
                and issubclass(obj, Pane)
                and obj is not Pane
            ):
                pane_classes.append(obj)

    return pane_classes


class LayoutEditor:

    def __init__(self, pane_classes):
        self.available_panes = pane_classes
        self._register()

    def layout(self):

        return html.Div([

            html.H3("Builder"),

            dcc.Input(
                id="api-url",
                value="http://localhost:8000"
            ),

            dcc.RadioItems(
                id="columns",
                options=[1, 2, 3],
                value=2
            ),

            dcc.Checklist(
                id="pane-selector",
                options=[
                    {
                        "label": p.__name__,
                        "value": p.__name__
                    }
                    for p in self.available_panes
                ],
                value=[]
            ),

            html.Button(
                "Update Dashboard",
                id="build"
            )

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
                "panes": [
                    p.__name__
                    for p in chosen
                ]
            }



def main():

    panes = discover_panes("panes")

    builder = LayoutEditor(panes)

    adapter = DashAdapter(
        panes,
        columns=2
    )
    adapter.start_polling()

    app.layout = html.Div([

        dcc.Store(
            id="layout-store"
            
        ),
        
        dcc.Store(id="input-store"),

        dcc.Interval(
            id="refresh-timer",
            interval=1000,
            n_intervals=0
        ),

        builder.layout(),

        html.Hr(),

        html.Div(
            id="dashboard-area"
        )

    ])


    #
    # Build dashboard only when requested.
    #
    @app.callback(
        Output(
            "dashboard-area",
            "children"
        ),
        Input(
            "layout-store",
            "data"
        ),
        prevent_initial_call=True
    )
    def render_dashboard(data):
        print("### RENDER DASHBOARD FIRED ###")
        if not data:
            return "No dashboard yet"

        adapter.columns = data["columns"]
        adapter.api_url = data["api"]
        print("Selected panes:", data["panes"])
        adapter.set_active_panes(data["panes"])
        print("Active panes:", [p.__class__.__name__ for p in adapter.active_panes])

        print("BUILD DASHBOARD")
        print("LAYOUT DATA:", data)

        return adapter.layout()



    


    app.run(
        debug=True
    )


if __name__ == "__main__":
    main()


    