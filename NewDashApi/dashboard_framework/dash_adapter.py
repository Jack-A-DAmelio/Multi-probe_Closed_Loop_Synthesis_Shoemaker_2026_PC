"""
Dash adapter.

Author: You | Date: 2026-07-04 | Framework Version: v0.1

Purpose:
--------
Render dashboard panes as Dash components and submit pane data
to backend API endpoints.

Responsibilities
----------------
- Build the Dash layout from Pane definitions.
- Collect user input.
- Submit pane data through dashboard_framework.api.

The adapter intentionally contains no experiment logic.
"""

import dash
from dash import html, dcc, Input, Output, State

from dashboard_framework.api import submit


# =========================================================
# DASH ADAPTER
# =========================================================

class DashAdapter:
    """
    Render panes using Dash and submit pane data to backend APIs.
    """

    def __init__(self, panes):
        """
        Parameters
        ----------
        panes : list
            List of instantiated Pane objects.
        """

        self.panes = panes
        self.app = dash.Dash(__name__)

        # Build all pane widgets before creating the layout.
        for pane in self.panes:
            pane.build()

        self.app.layout = self._build_layout()

        self._register_callbacks()

    # ---------------------------------------------------------
    # BUILD LAYOUT
    # ---------------------------------------------------------

    def _build_layout(self):
        """
        Convert pane definitions into a Dash layout.

        Returns
        -------
        dash.html.Div
        """

        dashboard = []

        for pane in self.panes:

            controls = []

            # -------------------------------------------------
            # Pane title
            # -------------------------------------------------

            controls.append(
                html.H3(
                    pane.NAME.replace("_", " ").title()
                )
            )

            # -------------------------------------------------
            # Widgets
            # -------------------------------------------------

            for widget in pane.widgets:

                component_id = f"{pane.NAME}:{widget.label}"

                if widget.widget_type == "number":

                    component = dcc.Input(
                        id=component_id,
                        type="number",
                        value=widget.default
                    )

                elif widget.widget_type == "dropdown":

                    component = dcc.Dropdown(
                        id=component_id,
                        options=[
                            {
                                "label": option,
                                "value": option
                            }
                            for option in widget.options
                        ],
                        value=widget.default
                    )

                else:

                    component = dcc.Input(
                        id=component_id,
                        type="text",
                        value=widget.default
                    )

                controls.append(

                    html.Div(

                        [

                            html.Label(widget.label),

                            component

                        ],

                        style={
                            "marginBottom": "10px"
                        }

                    )

                )

            # -------------------------------------------------
            # Confirm button
            # -------------------------------------------------

            confirm_id = f"{pane.NAME}:confirm"

            controls.append(

                html.Button(

                    "Confirm",

                    id=confirm_id,

                    n_clicks=0

                )

            )

            dashboard.append(

                html.Div(

                    controls,

                    style={

                        "border": "1px solid #cccccc",

                        "padding": "15px",

                        "margin": "15px",

                        "borderRadius": "5px"

                    }

                )

            )

        # Hidden output required by Dash callbacks.
        dashboard.append(

            html.Div(

                id="dummy-output",

                style={"display": "none"}

            )

        )

        return html.Div(dashboard)

    # ---------------------------------------------------------
    # CALLBACKS
    # ---------------------------------------------------------

    def _register_callbacks(self):
        """
        Register one callback for each pane.
        """

        for pane in self.panes:

            confirm_id = f"{pane.NAME}:confirm"

            widget_ids = [

                f"{pane.NAME}:{widget.label}"

                for widget in pane.widgets

            ]

            @self.app.callback(

                Output("dummy-output", "children"),

                Input(confirm_id, "n_clicks"),

                [State(component_id, "value") for component_id in widget_ids],

                prevent_initial_call=True

            )
            def submit_callback(

                _,

                *values,

                pane=pane

            ):

                payload = {

                    pane.NAME: {}

                }

                for widget, value in zip(

                    pane.widgets,

                    values

                ):

                    payload[pane.NAME][widget.label] = value

                submit(

                    pane.API_ENDPOINT,

                    payload

                )

                return ""

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    def run(
        self,
        debug=True
    ):
        """
        Launch the Dash application.

        Parameters
        ----------
        debug : bool
            Enable Dash debug mode.
        """

        self.app.run(
            debug=debug
        )