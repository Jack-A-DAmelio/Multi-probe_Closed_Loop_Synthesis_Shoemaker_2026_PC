"""
PC CONTROL DASHBOARD

Author: Jack A. D'Amelio
Date: 2026-06-18
Internal Pi-Hardware Version: v0.1

View this dashboard in a web browser at: http://127.0.0.1:8050
"""

from dash import Dash, html, dcc, Input, Output, State, ALL
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

PI_URL = "http://10.193.222.216:8001"
PC_URL = "http://130.126.252.137:8000"

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
    dcc.Store(id="module-spec-store"),

    # -------------------------
    # EXPERIMENT CONFIG
    # -------------------------
    make_panel("Experiment Setup", [
        dcc.Input(id="exp-name", placeholder="Experiment Name", type="text"),
        html.Br(), html.Br(),
        html.Label("Sample Rate (Hz)"),
        dcc.Input(id="sample-rate-hz", placeholder="Sample Rate (Hz)", type="number"),
        html.Br(), html.Br(),
        html.Label("Flush Interval (sec)"),
        dcc.Input(id="flush-interval-sec", placeholder="Flush Interval (sec)", type="number"),
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
    ]),


make_panel("Hardware Modules", [

    html.Button(
        "New Module",
        id="new-module-btn"
    ),

    html.Br(),
    html.Br(),

    dcc.Dropdown(
        id="module-dropdown",
        placeholder="Select Module"
    ),

    html.Br(),

    html.Div(id="module-spec-form"),

    html.Br(),

    html.Button(
        "Create Module",
        id="create-module-btn"
    ),

    html.Div(id="module-build-status")
])
])

# =========================================================
# CALLBACKS
# =========================================================
#
# Dash applications are event-driven.
#
# Unlike a normal Python program, we do notT call these
# functions ourselves.
#
# Dash monitors UI components (buttons, timers, text boxes,
# dropdowns, etc.) and automatically executes callback
# functions whenever an Input changes.
#
# Callback Anatomy:
#
#   Output:
#       Which UI component gets updated.
#
#   Input:
#       What event triggers the callback.
#
#   State:
#       Additional values to read without triggering.
#
# Example:
#
#   Input("start-btn", "n_clicks")
#
# means:
#   "Run this callback whenever the START button is clicked."
#
# Example:
#
#   Output("status-text", "children")
#
# means:
#   "Place the callback's return value into the text shown
#    inside the status-text component."
#
#below each call back is the function that is executed when the callback is triggered. The function's parameters correspond to the Inputs and State defined in the callback decorator. The function's return value(s) are assigned to the Output(s) defined in the decorator.
# =========================================================

@app.callback(
    Output("module-dropdown", "options"),
    Input("new-module-btn", "n_clicks"),
    prevent_initial_call=True
)
def load_modules(_):

    result = pi_api.get_modules(PI_URL)

    modules = result.get("modules", [])

    return [
        {
            "label": name,
            "value": name
        }
        for name in modules
    ]

@app.callback(
    Output("module-spec-store", "data"),
    Input("module-dropdown", "value"),
    prevent_initial_call=True
)
def get_spec(module_name):

    if not module_name:
        raise dash.exceptions.PreventUpdate

    return pi_api.get_module_spec(
        PI_URL,
        module_name
    )

@app.callback(
    Output("module-spec-form", "children"),
    Input("module-spec-store", "data")
)
def generate_module_form(spec):

    if not spec:
        return []

    pins = spec.get("pins_required", {})

    controls = []

    for pin_name, description in pins.items():

        controls.append(

            html.Div([

                html.Label(
                    f"{pin_name}: {description}"
                ),

                dcc.Input(
                    id={
                        "type": "pin-input",
                        "pin": pin_name
                    },
                    type="number",
                    placeholder="Pin Number"
                )

            ])

        )

    return controls


@app.callback(
    Output("module-build-status", "children"),
    Input("create-module-btn", "n_clicks"),
    State("module-dropdown", "value"),
    State(
        {"type": "pin-input", "pin": ALL},
        "value"
    ),
    State(
        {"type": "pin-input", "pin": ALL},
        "id"
    ),
    prevent_initial_call=True
)
def create_module(
    _,
    module_name,
    pin_values,
    pin_ids
):

    if not module_name:
        raise dash.exceptions.PreventUpdate

    pin_map = {}

    for pin_id, value in zip(pin_ids, pin_values):

        pin_map[
            pin_id["pin"]
        ] = value

    result = pi_api.build_module(
        PI_URL,
        module_name,
        pin_map
    )

    return str(result)

@app.callback(
    Output("status-text", "children"),
    Input("config-btn", "n_clicks"),
    State("exp-name", "value"),
    State("probe-select", "value"),
    State("flush-interval-sec", "value"),
    State("sample-rate-hz", "value"),
    prevent_initial_call=True
)
def configure(n, name, probes,flush_interval_sec, sample_rate_hz):

    if not n:
        raise dash.exceptions.PreventUpdate

    # -------------------------
    # Pi configuration (hardware control)
    # -------------------------
    result_pi = pi_api.configure_experiment(
        PI_URL,
        experiment_id=name,
        enabled_probes=probes,
        flush_interval_sec=flush_interval_sec,
        sample_rate_hz=sample_rate_hz
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