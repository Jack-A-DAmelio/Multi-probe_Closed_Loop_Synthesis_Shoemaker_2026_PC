from dash import html, dcc, Input, Output
from dashboard_framework.discovery import discover_panes
from dashboard_framework.layout_editor import LayoutEditor
from dashboard_framework.dash_adapter import DashAdapter
from dashboard_framework.app import app


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