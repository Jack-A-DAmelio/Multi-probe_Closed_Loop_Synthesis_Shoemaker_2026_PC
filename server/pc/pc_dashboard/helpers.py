"""
Dashboard helper utilities

Author: Undergraduate Research Project
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

    Parameters:
        data (list[dict]): raw output from PC server /latest endpoint
        probes (list[str]): list of probe names to extract

    Returns:
        dict[str, list]: mapping of probe -> time series values
    """

    history = {p: [] for p in probes}  # initialize empty series per probe

    for packet in data:
        sample = packet.get("sample", {})  # safe extraction of measurement block

        for p in probes:
            if p in sample:
                history[p].append(sample[p])  # append value in temporal order

    return history


def extract_latest_values(data, probes):
    """
    Extracts most recent known value for each probe.

    NOTE:
    Iterates through full dataset to ensure robustness even if
    packets are missing probes or arrive out of order.

    Parameters:
        data (list[dict]): raw PC server output
        probes (list[str]): probe names

    Returns:
        dict[str, float | None]: latest observed value per probe
    """

    latest_values = {p: None for p in probes}

    for packet in data:
        sample = packet.get("sample", {})

        for p in probes:
            if p in sample:
                latest_values[p] = sample[p]  # overwrite until last occurrence

    return latest_values


# =========================================================
# PLOTTING HELPERS
# =========================================================

def make_probe_figure(values):
    """
    Creates a fixed-size Plotly line plot for a single probe.

    Parameters:
        values (list[float]): time series values for a probe

    Returns:
        plotly.graph_objs.Figure: formatted figure for Dash rendering
    """

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=values,
            mode="lines"  # simple time-series visualization
        )
    )

    # Fixed layout ensures consistent UI grid alignment across probes
    fig.update_layout(
        height=300,
        width=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig


def make_probe_panel(probe, values, latest_value):
    """
    Builds a Dash UI panel for a single probe.

    Parameters:
        probe (str): probe name (e.g., temperature)
        values (list[float]): time series data
        latest_value (float | None): most recent measurement

    Returns:
        dash.html.Div: formatted UI component
    """

    return html.Div(
        children=[
            html.H3(probe),
            html.Div(f"Latest: {latest_value}"),

            dcc.Graph(
                figure=make_probe_figure(values),
                style={
                    "height": "320px",  # fixed size for consistent layout
                    "width": "320px"
                }
            )
        ],
        style={
            "display": "inline-flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "border": "1px solid #ddd",
            "padding": "10px",
            "margin": "5px",
            "width": "340px",
            "height": "420px"
        }
    )