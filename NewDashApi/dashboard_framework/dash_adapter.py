from dash import html, dcc, Input, Output, State  # Dash UI components and callback tools.
import requests  # Used for polling display widget sources.

from app import app  # Your Dash application instance.
from dashboard_framework.api import submit  # Used for sending button actions.


class DashAdapter:

    def __init__(self, pane_classes, columns=2, api_url=None):

        # Store pane classes that should be created.
        self.pane_classes = pane_classes

        # Number of dashboard columns.
        self.columns = columns

        # Base API address for this dashboard instance.
        self.api_url = api_url or ""

        # Create pane instances.
        self.panes = [p() for p in pane_classes]

        # Build each pane's widgets.
        for p in self.panes:
            p.build()

        # Cache stores display values and initial widget values.
        self._cache = {}

        # Initialize widget values.
        self._init_cache()

        # Register callbacks for input widgets.
        self._register_inputs()

        # Register callbacks for buttons.
        self._register_buttons()


    def _init_cache(self):

        # Loop through every pane.
        for p in self.panes:

            # Loop through every widget.
            for w in p.widgets:

                # Store initial widget value.
                self._cache[(p.NAME, w.label)] = w.default


    def _build_url(self, path):

        """
        Combine API base address with widget endpoint.
        """

        # Remove trailing slash from base.
        base = self.api_url.rstrip("/")

        # Remove leading slash from endpoint.
        endpoint = path.lstrip("/")

        # Combine into full URL.
        return f"{base}/{endpoint}"


    def _refresh(self):

        # Update display widgets from their sources.
        for p in self.panes:

            # Check every widget.
            for w in p.widgets:

                # Only widgets with sources refresh.
                if getattr(w, "source", None):

                    try:

                        # Build complete API URL.
                        url = self._build_url(
                            w.source
                        )

                        # Default request parameters.
                        params = {
                            "pane": p.NAME,
                            "widget": w.label
                        }

                        # Add optional parameters.
                        if getattr(w, "params", None):
                            params.update(w.params)

                        # Request latest value.
                        response = requests.get(
                            url,
                            params=params,
                            timeout=2
                        )

                        # Store successful response.
                        if response.status_code == 200:

                            self._cache[
                                (p.NAME, w.label)
                            ] = response.json()


                    except Exception:

                        # Ignore failed refreshes.
                        pass



    def _widget_id(self, pane, widget):

        # Create unique Dash ID.
        return f"{pane.NAME}:{widget.label}"



    def _render_widget(self, pane, widget):

        # Generate widget ID.
        widget_id = self._widget_id(
            pane,
            widget
        )

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
                    id=f"{self._widget_id(pane, widget)}:value",
                    style={
                        "backgroundColor": "#f2f2f2",
                        "padding": "6px",
                        "borderRadius": "4px"
                    }
                )

            ])


        #
        # Image display widget.
        #
        elif widget.widget_type == "image":

            return html.Div([

                html.Div(
                    widget.label
                ),

                html.Img(
                    src=self._build_url(widget.source),
                    style={
                        "width": "100%",
                        "maxHeight": "300px",
                        "objectFit": "contain",
                        "backgroundColor": "#f2f2f2",
                        "borderRadius": "4px"
                    }
                )

            ])


        #
        # Text input widget.
        #
        elif widget.widget_type == "text":

            return html.Div([

                html.Div(
                    widget.label
                ),

                dcc.Input(
                    id=widget_id,
                    value=value,
                    type="text"
                )

            ])


        #
        # Number input widget.
        #
        elif widget.widget_type == "number":

            return html.Div([

                html.Div(
                    widget.label
                ),

                dcc.Input(
                    id=widget_id,
                    value=value,
                    type="number"
                )

            ])


        #
        # Dropdown widget.
        #
        elif widget.widget_type == "dropdown":

            return html.Div([

                html.Div(
                    widget.label
                ),

                dcc.Dropdown(
                    id=widget_id,
                    options=[
                        {
                            "label": option,
                            "value": option
                        }
                        for option in (widget.options or [])
                    ],
                    value=value
                )

            ])


        #
        # Checkbox widget.
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
        # Button widget.
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


        # Build panes.
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


            # Render widgets.
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



    def _register_inputs(self):

        """
        Store user input values into layout-store.
        """

        for pane in self.panes:

            for widget in pane.widgets:

                # Only register user input widgets.
                if widget.widget_type not in [
                    "text",
                    "number",
                    "dropdown",
                    "checkbox"
                ]:
                    continue


                widget_id = self._widget_id(
                    pane,
                    widget
                )


                @app.callback(

                    Output(
                        "layout-store",
                        "data",
                        allow_duplicate=True
                    ),

                    Input(
                        widget_id,
                        "value"
                    ),

                    State(
                        "layout-store",
                        "data"
                    ),

                    prevent_initial_call=True

                )
                def update_input(
                    value,
                    layout,
                    pane=pane,
                    widget=widget
                ):

                    if not layout:
                        layout = {}


                    if pane.NAME not in layout:
                        layout[pane.NAME] = {}


                    if widget.widget_type == "checkbox":

                        layout[pane.NAME][widget.label] = bool(value)

                    else:

                        layout[pane.NAME][widget.label] = value


                    return layout



    def _register_buttons(self):

        """
        Register callbacks for buttons.
        """

        for pane in self.panes:

            for widget in pane.widgets:


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


                    if not layout:
                        return "No layout"


                    payload = layout.get(
                        pane.NAME,
                        {}
                    )


                    api_url = layout["api"]


                    ok = submit(

                        api_url,

                        widget.endpoint,

                        payload

                    )


                    return "OK" if ok else "FAILED"