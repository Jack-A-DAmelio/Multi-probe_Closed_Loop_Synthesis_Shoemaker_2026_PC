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

# NOTE:
# PI_URL = hardware-side server (Raspberry Pi or instrument controller)
# PC_URL = local/remote PC server handling data ingestion + storage

PI_URL = "http://10.193.222.216:8001"
PC_URL = "http://130.126.252.137:8000"

# List of probes that define the measurement channels in this system.
# These must match both:
# - Pi-side sensor configuration
# - PC-side parsing logic
PROBES = ["temperature", "pressure", "pH"]

# Dash application instance
# This object manages the entire web UI + callback system.
app = Dash(__name__)


# =========================================================
# UI HELPERS (LOCAL LAYOUT ONLY)
# =========================================================

def make_panel(title, children):
    """
    Builds a reusable UI panel container.

    This is purely a visual helper and does NOT affect backend logic.

    Parameters:
        title (str): Panel title displayed at top of UI box
        children (list): List of Dash components inside the panel

    Returns:
        dash.html.Div: Styled container element
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
    Creates probe selection checklist UI.

    This defines which sensors will be enabled during an experiment.
    It does NOT immediately send data anywhere; it is only UI state.

    Returns:
        dash.dcc.Checklist: selectable probe list component
    """

    return dcc.Checklist(
        id="probe-select",
        options=[{"label": p, "value": p} for p in PROBES],
        value=[]
    )


# =========================================================
# LAYOUT
# =========================================================

# The layout defines the static structure of the dashboard.
# Dash re-renders ONLY components whose callbacks update them.

app.layout = html.Div([

    # Main title shown in browser
    html.H1("PC CONTROL HUD"),

    # -----------------------------------------------------
    # CLIENT-SIDE STATE STORAGE
    # -----------------------------------------------------
    # dcc.Store holds browser-session state (not server state).
    # This avoids unnecessary API calls for simple flags.

    dcc.Store(id="run-state", data=False),
    # Tracks whether streaming is currently active

    dcc.Store(id="module-spec-store"),
    # Temporary storage for module specification loaded from Pi

    # -------------------------
    # EXPERIMENT CONFIG PANEL
    # -------------------------
    make_panel("Experiment Setup", [

        # User-defined experiment label
        dcc.Input(id="exp-name", placeholder="Experiment Name", type="text"),
        html.Br(), html.Br(),

        # Sampling configuration (how often Pi collects data)
        html.Label("Sample Rate (Hz)"),
        dcc.Input(id="sample-rate-hz", placeholder="Sample Rate (Hz)", type="number"),
        html.Br(), html.Br(),

        # Flush interval controls how often Pi sends data batches to PC
        html.Label("Flush Interval (sec)"),
        dcc.Input(id="flush-interval-sec", placeholder="Flush Interval (sec)", type="number"),
        html.Br(), html.Br(),

        # Probe selection UI (temperature, pressure, pH, etc.)
        probe_selector(),
        html.Br(),

        # Sends configuration to BOTH Pi and PC backend
        html.Button("Send Config", id="config-btn")
    ]),

    # -------------------------
    # CONTROL PANEL (STREAM STATE)
    # -------------------------
    make_panel("Control", [

        # Starts streaming data from Pi → PC server
        html.Button(
            "START",
            id="start-btn",
            style={"backgroundColor": "green", "color": "white"}
        ),

        # Stops streaming data
        html.Button(
            "STOP",
            id="stop-btn",
            style={"backgroundColor": "red", "color": "white"}
        ),

        # Displays status updates from callbacks (API responses, errors, etc.)
        html.Div(id="status-text")
    ]),

    # -------------------------
    # LIVE DATA PANEL
    # -------------------------
    make_panel("Live Data", [

        # Timer triggers periodic UI refresh (polling PC backend)
        dcc.Interval(
            id="update-timer",
            interval=1000,  # 1 second refresh rate
            n_intervals=0
        ),

        # Dynamic container where probe plots/panels are rendered
        html.Div(id="live-panels")
    ]),


    # -------------------------
    # HARDWARE MODULE MANAGEMENT
    # -------------------------
    # NOTE:
    # This panel is used for dynamically defining hardware modules
    # (e.g., LED modules, sensors, GPIO-linked components)

    make_panel("Hardware Modules", [

        html.Button(
            "New Module",
            id="new-module-btn"
        ),

        html.Br(),
        html.Br(),

        # Populated dynamically after querying Pi for available modules
        dcc.Dropdown(
            id="module-dropdown",
            placeholder="Select Module"
        ),

        html.Br(),

        # Dynamic form generated based on module pin requirements
        html.Div(id="module-spec-form"),

        html.Br(),

        # Sends module configuration to Pi for instantiation
        html.Button(
            "Create Module",
            id="create-module-btn"
        ),

        # Displays success/failure response from Pi backend
        html.Div(id="module-build-status")
    ])
])

# =========================================================
# CALLBACKS (DASH EVENT SYSTEM)
# =========================================================
#
# IMPORTANT CONCEPT:
# Dash is NOT procedural.
# You do not call these functions manually.
#
# Instead:
# - Inputs = triggers (button clicks, timer ticks, dropdown changes)
# - Outputs = UI updates
# - State = read-only values used inside callback logic
#
# Each callback is executed automatically when Inputs change.


@app.callback(
    Output("module-dropdown", "options"),
    Input("new-module-btn", "n_clicks"),
    prevent_initial_call=True
)
def load_modules(_):
    """
    Queries Pi backend for available hardware modules.

    Trigger:
        User clicks "New Module"

    Returns:
        list[dict]: dropdown options formatted for Dash
    """

    result = pi_api.get_modules(PI_URL)

    modules = result.get("modules", [])

    # Convert backend list into Dash dropdown format
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
    """
    Fetches module specification from Pi backend.

    This spec defines required pins and configuration schema.

    Returns:
        dict: module specification JSON
    """

    if not module_name:
        # Prevent callback from running with invalid selection
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
    """
    Dynamically generates input form fields for module configuration.

    This allows arbitrary hardware modules to define required pins
    without hardcoding UI elements.

    Returns:
        list[dash components]
    """

    if not spec:
        return []

    pins = spec.get("pins_required", {})

    controls = []

    for pin_name, description in pins.items():

        # Each required pin becomes a numeric input field
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

    # Collect all dynamically generated inputs
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
    """
    Builds a hardware module on the Pi using user-defined pin mapping.

    Flow:
        1. Read selected module type
        2. Collect all pin inputs from UI
        3. Construct pin_map dictionary
        4. Send to Pi backend for instantiation

    Returns:
        str: backend response status
    """

    if not module_name:
        raise dash.exceptions.PreventUpdate

    pin_map = {}

    # Pair each UI input with its corresponding pin name
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
def configure(n, name, probes, flush_interval_sec, sample_rate_hz):
    """
    Sends experiment configuration to both Pi and PC systems.

    This ensures:
        - Pi knows what to measure and how often
        - PC knows how to label and store data
        - Output files are correctly named per experiment

    Returns:
        str: combined status from Pi + PC APIs
    """

    if not n:
        raise dash.exceptions.PreventUpdate

    # -------------------------
    # Pi configuration (hardware control layer)
    # -------------------------
    result_pi = pi_api.configure_experiment(
        PI_URL,
        experiment_id=name,
        enabled_probes=probes,
        flush_interval_sec=flush_interval_sec,
        sample_rate_hz=sample_rate_hz
    )

    # -------------------------
    # PC experiment metadata (tracking layer)
    # -------------------------
    result_pc_exp = pc_api.set_experiment(PC_URL, name)

    # -------------------------
    # PC file output configuration (logging layer)
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
    """
    Starts streaming from Pi to PC.

    Updates:
        - run-state (browser-side flag)
        - status message
    """

    result = pi_api.start_streaming(PI_URL)
    return True, f"Started: {result}"


@app.callback(
    Output("run-state", "data", allow_duplicate=True),
    Output("status-text", "children", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop(_):
    """
    Stops streaming from Pi.

    Ensures run-state is reset so UI stops polling data.
    """

    result = pi_api.stop_streaming(PI_URL)
    return False, f"Stopped: {result}"


@app.callback(
    Output("live-panels", "children"),
    Input("update-timer", "n_intervals"),
    Input("run-state", "data")
)
def update(n, running):
    """
    Periodically fetches latest data from PC server and updates plots.

    Triggered by:
        - timer (every 1 second)
        - run-state changes (start/stop)

    Flow:
        1. Check if experiment is running
        2. Query PC backend for latest buffer
        3. Validate data format
        4. Transform data for plotting
        5. Render probe panels
    """

    if not running:
        return []

    try:
        # Fetch most recent streamed data batch
        data = pc_api.latest(PC_URL)

        # Defensive check: ensure backend returned expected structure
        if not isinstance(data, list):
            return [html.Div("Bad data format")]

    except Exception as e:
        # Catch network / backend errors safely without crashing UI
        return [html.Div(f"API error: {str(e)}")]

    if len(data) == 0:
        return [html.Div("No data yet")]

    # -------------------------
    # Data transformation layer
    # -------------------------
    # Convert raw packets into structures suitable for plotting:
    # - history per probe
    # - latest values per probe
    history = extract_history(data, PROBES)
    latest_values = extract_latest_values(data, PROBES)

    # -------------------------
    # UI rendering layer
    # -------------------------
    # Each probe gets its own visualization panel
    return [
        make_probe_panel(p, history[p], latest_values[p])
        for p in PROBES
    ]


# =========================================================
# ENTRY POINT
# =========================================================
#
# This starts the Dash development server.
# In production, this would typically be replaced by gunicorn/uwsgi.

if __name__ == "__main__":
    app.run(debug=True)