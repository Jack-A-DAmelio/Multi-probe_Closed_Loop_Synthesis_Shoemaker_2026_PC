"""
PC CONTROL DASHBOARD

Author: Undergraduate Research Project
Date: 2026-06-18
Internal Pi-Hardware Version: v0.1
"""

from dash import Dash, html, dcc, Input, Output, State
import dash
import dash.exceptions

import pi_api
import pc_api

from helpers import (
    extract_history,
    extract_latest_values,
    make_probe_panel
)

# =========================================================
# CONFIGURATION
# =========================================================

PI_URL = "http://127.0.0.1:8001"
PC_URL = "http://127.0.0.1:8000"

PROBES = ["temperature", "pressure", "pH"]

app = Dash(__name__)


# =========================================================
# UI HELPERS (LOCAL LAYOUT ONLY)
# =========================================================

def make_panel(title, children):
    """
    Builds a reusable UI panel container.

    Parameters:
        title (str)
        children (list): Dash components

    Returns:
        dash.html.Div
    """
    return html.Div(
        children=[html.H3(title), html.Div(children)],
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
    """
    Creates probe selection checklist.

    Returns:
        dash.dcc.Checklist
    """
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

    # stores run-state locally in browser session
    dcc.Store(id="run-state", data=False),

    # -------------------------
    # EXPERIMENT CONFIG
    # -------------------------
    make_panel("Experiment Setup", [
        dcc.Input(id="exp-name", placeholder="Experiment Name", type="text"),
        html.Br(), html.Br(),

        dcc.Input(id="sample-rate", placeholder="Sample Rate (Hz)", type="number"),
        html.Br(), html.Br(),

        probe_selector(),
        html.Br(),

        html.Button("Send Config", id="config-btn")
    ]),

    # -------------------------
    # CONTROL PANEL
    # -------------------------
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

    # -------------------------
    # LIVE DATA PANEL
    # -------------------------
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
# CALLBACKS (ORCHESTRATION ONLY)
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

    # -------------------------
    # Pi configuration (hardware control)
    # -------------------------
    result_pi = pi_api.configure_experiment(
        PI_URL,
        experiment_id=name,
        enabled_probes=probes
    )

    # -------------------------
    # PC experiment metadata
    # -------------------------
    result_pc_exp = pc_api.set_experiment(PC_URL, name)

    # -------------------------
    # PC logging file
    # -------------------------
    result_pc_file = pc_api.set_filename(PC_URL, name)

    return f"PI: {result_pi} | PC: {result_pc_exp} | FILE: {result_pc_file}"


@app.callback(
    Output("run-state", "data"),
    Output("status-text", "children", allow_duplicate=True),
    Input("start-btn", "n_clicks"),
    prevent_initial_call=True
)
def start(_):

    result = pi_api.start_streaming(PI_URL)
    return True, f"Started: {result}"


@app.callback(
    Output("run-state", "data", allow_duplicate=True),
    Output("status-text", "children", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop(_):

    result = pi_api.stop_streaming(PI_URL)
    return False, f"Stopped: {result}"


@app.callback(
    Output("live-panels", "children"),
    Input("update-timer", "n_intervals"),
    Input("run-state", "data")
)
def update(n, running):

    if not running:
        return []

    try:
        data = pc_api.latest(PC_URL)

        if not isinstance(data, list):
            return [html.Div("Bad data format")]

    except Exception as e:
        return [html.Div(f"API error: {str(e)}")]

    if len(data) == 0:
        return [html.Div("No data yet")]

    # -------------------------
    # Data transformation layer
    # -------------------------
    history = extract_history(data, PROBES)
    latest_values = extract_latest_values(data, PROBES)

    # -------------------------
    # UI rendering layer
    # -------------------------
    return [
        make_probe_panel(p, history[p], latest_values[p])
        for p in PROBES
    ]


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)