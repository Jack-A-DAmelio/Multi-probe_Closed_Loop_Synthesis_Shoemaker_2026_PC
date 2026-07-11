from dash import html, dcc, Input, Output, State  # Dash UI components and callback tools.
import requests  # Used for polling display widget sources.

from app import app  # Your Dash application instance.
from dashboard_framework.api import submit  # Used for sending button actions.


class DashAdapter:

    def __init__(self, pane_classes, columns=2):
        # Store pane classes that should be created.
        self.pane_classes = pane_classes

        # Number of dashboard columns.
        self.columns = columns

        # Create pane instances.
        self.panes = [p() for p in pane_classes]

        # Build each pane's widgets.
        for p in self.panes:
            p.build()

        # Cache stores display values and initial widget values.
        self._cache = {}

        # Initialize widget values.
        self._init_cache()

        # Register callbacks for buttons.
        self._register_buttons()


    def _init_cache(self):
        # Loop through every pane.
        for p in self.panes:

            # Loop through every widget in the pane.
            for w in p.widgets:

                # Store initial widget value.
                self._cache[(p.NAME, w.label)] = w.default


    def _refresh(self):
        # Update display widgets from their sources.
        for p in self.panes:

            # Check every widget.
            for w in p.widgets:

                # Only widgets with a source should refresh.
                if getattr(w, "source", None):

                    try:
                        # Default query parameters.
                        params = {
                            "pane": p.NAME,
                            "widget": w.label
                        }

                        # Add user supplied parameters.
                        if getattr(w, "params", None):
                            params.update(w.params)

                        # Request latest value.
                        resp = requests.get(
                            w.source,
                            params=params,
                            timeout=2
                        )

                        # Save successful response.
                        if resp.status_code == 200:
                            self._cache[(p.NAME, w.label)] = resp.json()

                    except Exception:
                        # Ignore failed refreshes.
                        pass


    def _widget_id(self, pane, widget):
        # Create a unique Dash ID for widgets.
        return f"{pane.NAME}:{widget.label}"


    def _render_widget(self, pane, widget):
        # Generate unique ID.
        widget_id = self._widget_id(pane, widget)

        # Retrieve current value.
        value = self._cache.get(
            (pane.NAME, widget.label),
            widget.default
        )

        #
        # Read-only display widget.
        #
        if widget.widget_type == "display":

            return html.Div([
                html.Div(
                    widget.label
                ),

                html.Div(
                    str(value),
                    style={
                        "backgroundColor": "#f2f2f2",  # Light grey background for live values.
                        "padding": "6px",              # Adds spacing around the displayed value.
                        "borderRadius": "4px"           # Slightly rounds the display box corners.
                    }
                )
            ])


        #
        # User text entry.
        #
        elif widget.widget_type == "text":

            return html.Div([
                html.Div(widget.label),

                dcc.Input(
                    id=widget_id,
                    value=value,
                    type="text"
                )
            ])


        #
        # User numeric entry.
        #
        elif widget.widget_type == "number":

            return html.Div([
                html.Div(widget.label),

                dcc.Input(
                    id=widget_id,
                    value=value,
                    type="number"
                )
            ])


        #
        # Dropdown selection.
        #
        elif widget.widget_type == "dropdown":

            return html.Div([
                html.Div(widget.label),

                dcc.Dropdown(
                    id=widget_id,
                    options=[
                        {
                            "label": option,
                            "value": option
                        }
                        for option in widget.options
                    ],
                    value=value
                )
            ])


        #
        # Checkbox input.
        #
        elif widget.widget_type == "checkbox":

            return html.Div([
                dcc.Checklist(
                    id=widget_id,
                    options=[
                        {
                            "label": widget.label,
                            "value": True
                        }
                    ],
                    value=[True] if value else []
                )
            ])


        #
        # Button action.
        #
        elif widget.widget_type == "button":

            return html.Div([

                html.Button(
                    widget.label,
                    id=widget_id
                ),

                html.Div(
                    id=f"{widget_id}:status"
                )
            ])


        #
        # Unknown widget fallback.
        #
        else:

            return html.Div([
                html.Div(widget.label),
                html.Div(str(value))
            ])


    def layout(self):

        # Refresh live displays.
        self._refresh()

        # Store pane cards.
        children = []

        # Build every pane.
        for p in self.panes:

            controls = [

                html.Div(
                    p.NAME,
                    style={
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "marginBottom": "10px"
                    }
                )
            ]

            # Render every widget.
            for w in p.widgets:

                controls.append(
                    self._render_widget(
                        p,
                        w
                    )
                )

            children.append(

                html.Div(
                    controls,

                    style={
                        "border": "1px solid #ddd",
                        "padding": "14px",
                        "borderRadius": "10px",
                        "backgroundColor": "#fff"
                    }
                )
            )


        return html.Div(
            children,

            style={
                "display": "grid",
                "gridTemplateColumns": f"repeat({self.columns}, 1fr)",
                "gap": "12px",
                "padding": "10px"
            }
        )


    def _register_buttons(self):

        # Register callback for every button widget.
        for pane in self.panes:

            for widget in pane.widgets:

                # Only buttons create callbacks.
                if widget.widget_type != "button":
                    continue


                button_id = self._widget_id(
                    pane,
                    widget
                )

                status_id = f"{button_id}:status"


                @app.callback(
                    Output(
                        status_id,
                        "children"
                    ),

                    Input(
                        button_id,
                        "n_clicks"
                    ),

                    State(
                        "layout-store",
                        "data"
                    ),

                    prevent_initial_call=True
                )
                def run_button(
                    n,
                    layout,
                    widget=widget,
                    pane=pane
                ):

                    # Ensure layout exists.
                    if not layout:
                        return "No layout"


                    # Get API base URL.
                    api_url = layout["api"]


                    # Get pane input values.
                    payload = layout.get(
                        pane.NAME,
                        {}
                    )


                    # Send request.
                    ok = submit(
                        api_url,
                        widget.endpoint,
                        payload
                    )


                    return "OK" if ok else "FAILED"