"""
Dashboard helper utilities

Author: Jack A. D'Amelio
Date: 2026-06-18
Internal Pi-Hardware Version: v0.1

Purpose:
--------
Pure helper functions for:
- parsing PC server streaming data
- generating per-probe time series
- building reusable Plotly + Dash UI components

NOTE:
These functions are intentionally stateless to keep them reusable
across multiple dashboards or analysis scripts.
"""

import plotly.graph_objs as go
from dash import html, dcc


# =========================================================
# DATA PROCESSING HELPERS
# =========================================================

def extract_history(data, probes):
    """
    Converts raw PC packet list into per-probe time series.

    This function restructures streaming data into a format that is
    easier to plot and analyze.

    Expected input format:
        data = [
            {
                "timestamp": ...,
                "sample": {
                    "temperature": ...,
                    "pressure": ...,
                    ...
                }
            },
            ...
        ]

    Parameters:
        data (list[dict]): raw output from PC server /latest endpoint
            Each element represents one streamed packet from the Pi.

        probes (list[str]): list of probe names to extract
            These define which sensor channels we care about.

    Returns:
        dict[str, list]: mapping of probe -> time series values
            Each list preserves temporal ordering as received.
    """

    # Initialize empty time-series containers for each probe
    history = {p: [] for p in probes}

    # Iterate sequentially through streaming packets
    # IMPORTANT: order matters because we assume append order = time order
    for packet in data:

        # Extract sensor payload safely
        # Using .get avoids KeyError if malformed packet arrives
        sample = packet.get("sample", {})

        # Append values per probe if present in this packet
        for p in probes:
            if p in sample:
                history[p].append(sample[p])

    return history


def extract_latest_values(data, probes):
    """
    Extracts most recent known value for each probe.

    Unlike extract_history(), this function does NOT assume complete
    or perfectly ordered data. It scans the full dataset to ensure
    robustness against missing or partial packets.

    Parameters:
        data (list[dict]): raw PC server output
        probes (list[str]): probe names

    Returns:
        dict[str, float | None]:
            Latest observed value per probe, or None if never seen
    """

    # Start with unknown values for all probes
    latest_values = {p: None for p in probes}

    # Walk through full dataset in order
    # Each new occurrence overwrites previous value
    for packet in data:

        sample = packet.get("sample", {})

        for p in probes:
            if p in sample:
                # overwrite ensures last-known value is retained
                latest_values[p] = sample[p]

    return latest_values


# =========================================================
# PLOTTING HELPERS
# =========================================================

def make_probe_figure(values):
    """
    Creates a fixed-size Plotly line plot for a single probe.

    This function is intentionally simple:
    - no axis formatting complexity
    - no styling beyond layout constraints
    - designed for dashboard consistency, not publication plots

    Parameters:
        values (list[float]): time series values for a probe

    Returns:
        plotly.graph_objs.Figure: Plotly figure object for Dash rendering
    """

    fig = go.Figure()

    # Add time-series line plot
    # x-axis is implicit index (0...N)
    fig.add_trace(
        go.Scatter(
            y=values,
            mode="lines"
        )
    )

    # Fixed layout ensures all probe panels align visually
    # This avoids uneven UI layout when embedded in grid
    fig.update_layout(
        height=300,
        width=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig


def make_probe_panel(probe, values, latest_value):
    """
    Builds a Dash UI panel for a single probe.

    This is a high-level UI wrapper that combines:
    - probe label
    - latest value display
    - embedded time-series plot

    Parameters:
        probe (str): probe name (e.g., "temperature")
        values (list[float]): full time series for plotting
        latest_value (float | None): most recent measurement

    Returns:
        dash.html.Div:
            Fully constructed UI block for dashboard rendering
    """

    return html.Div(
        children=[

            # Probe identifier
            html.H3(probe),

            # Lightweight numeric readout (fast debugging / monitoring)
            html.Div(f"Latest: {latest_value}"),

            # Embedded plot for trend visualization
            dcc.Graph(
                figure=make_probe_figure(values),
                style={
                    "height": "320px",
                    "width": "320px"
                }
            )
        ],

        # Container styling ensures consistent grid layout across probes
        style={
            "display": "inline-flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",

            # Visual separation between probes
            "border": "1px solid #ddd",
            "padding": "10px",
            "margin": "5px",

            # Fixed sizing prevents layout shifting when values change
            "width": "340px",
            "height": "420px"
        }
    )