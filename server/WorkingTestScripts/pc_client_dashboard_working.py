from dash import Dash, html, dcc, Input, Output, State
import dash
import dash.exceptions
import plotly.graph_objs as go

import api  # your refactored API layer

# =========================================================
# CONFIG
# =========================================================

PI_URL = "http://127.0.0.1:8001"
PROBES = ["temperature", "pressure", "pH"]

app = Dash(__name__)

# =========================================================
# HELPERS
# =========================================================

def make_panel(title, children):
    return html.Div(
        children=[
            html.H3(title),
            html.Div(children)
        ],
        style={
            "border": "2px solid #ccc",
            "padding": "15px",
            "margin": "10px",
            "width": "30%",
            "display": "inline-block",
            "verticalAlign": "top"
        }
    )


def probe_selector():
    return dcc.Checklist(
        id="probe-select",
        options=[{"label": p, "value": p} for p in PROBES],
        value=[]
    )


# =========================================================
# LAYOUT
# =========================================================

app.layout = html.Div([

    html.H1("PC CONTROL HUD"),

    dcc.Store(id="run-state", data=False),

    # -----------------------------------------------------
    # PANEL 1 - CONFIG
    # -----------------------------------------------------
    make_panel("Experiment Setup", [

        dcc.Input(
            id="exp-name",
            placeholder="Experiment Name",
            type="text"
        ),

        html.Br(), html.Br(),

        dcc.Input(
            id="sample-rate",
            placeholder="Sample Rate (Hz)",
            type="number"
        ),

        html.Br(), html.Br(),

        probe_selector(),

        html.Br(),

        html.Button("Send Config", id="config-btn")
    ]),

    # -----------------------------------------------------
    # PANEL 2 - CONTROL
    # -----------------------------------------------------
    make_panel("Control", [

        html.Button(
            "START",
            id="start-btn",
            style={"backgroundColor": "green", "color": "white"}
        ),

        html.Button(
            "STOP",
            id="stop-btn",
            style={"backgroundColor": "red", "color": "white"}
        ),

        html.Div(id="status-text")
    ]),

    # -----------------------------------------------------
    # PANEL 3 - LIVE DATA
    # -----------------------------------------------------
    make_panel("Live Data", [

        dcc.Interval(
            id="update-timer",
            interval=1000,
            n_intervals=0
        ),

        html.Div(id="live-panels")
    ])
])


# =========================================================
# CALLBACK 1 - CONFIG
# =========================================================

@app.callback(
    Output("status-text", "children"),
    Input("config-btn", "n_clicks"),
    State("exp-name", "value"),
    State("sample-rate", "value"),
    State("probe-select", "value"),
    prevent_initial_call=True
)
def configure(n, name, rate, probes):

    if not n:
        raise dash.exceptions.PreventUpdate

    result = api.configure_experiment(
        PI_URL,
        experiment_id=name,
        enabled_probes=probes
    )

    return f"Config: {result}"


# =========================================================
# CALLBACK 2 - START
# =========================================================

@app.callback(
    Output("run-state", "data"),
    Output("status-text", "children", allow_duplicate=True),
    Input("start-btn", "n_clicks"),
    prevent_initial_call=True
)
def start(_):

    result = api.start_streaming(PI_URL)

    return True, f"Started: {result}"


# =========================================================
# CALLBACK 3 - STOP
# =========================================================

@app.callback(
    Output("run-state", "data", allow_duplicate=True),
    Output("status-text", "children", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop(_):

    result = api.stop_streaming(PI_URL)

    return False, f"Stopped: {result}"


# =========================================================
# CALLBACK 4 - LIVE DATA
# =========================================================

@app.callback(
    Output("live-panels", "children"),
    Input("update-timer", "n_intervals"),
    Input("run-state", "data")
)
def update(n, running):

    if not running:
        return []

    try:
        data = api.latest(PI_URL)
    except:
        return []

    if not data:
        return []

    latest = data[-1]
    sample = latest.get("sample", {})

    panels = []

    for p in PROBES:

        value = sample.get(p, None)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=[value] if value is not None else [],
            mode="lines+markers"
        ))

        panels.append(
            html.Div([
                html.H4(p),
                html.Div(f"Value: {value}"),
                dcc.Graph(figure=fig)
            ],
            style={
                "border": "1px solid #ddd",
                "padding": "10px",
                "margin": "5px",
                "width": "30%",
                "display": "inline-block"
            })
        )

    return panels


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)