from dash import html, dcc, Input, Output, State
from dashboard_framework.app import app


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

            html.Button("Add Dashboard", id="build"),

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