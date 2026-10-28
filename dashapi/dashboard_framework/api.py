"""
Dashboard API communication helpers.

Author: You | Date: 2026-07-05 | Framework Version: v0.2

Purpose:
--------
Provides a simple interface for sending dashboard data to backend
services.

This module intentionally contains no experiment logic. It only
handles HTTP communication and basic error reporting.
"""

import requests


# =========================================================
# API SUBMISSION
# =========================================================

def submit(
    api_url: str,
    endpoint: str,
    payload: dict,
    timeout: float = 5.0
) -> bool:
    """
    Submit a JSON payload to a backend API endpoint.

    Parameters
    ----------
    api_url : str
        Base API URL.

    endpoint : str
        Pane API endpoint.

    payload : dict
        Dictionary to send as JSON.

    timeout : float, optional
        Maximum time to wait for a server response.

    Returns
    -------
    bool
        True if the request succeeded.
    """

    # Build the full URL.
    url = api_url.rstrip("/") + "/" + endpoint.lstrip("/")

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=timeout
        )

        response.raise_for_status()

        print(
            f"Successfully submitted to '{url}' "
            f"(HTTP {response.status_code})"
        )

        return True

    except requests.exceptions.RequestException as error:

        print(
            f"Failed to submit payload to '{url}'"
        )

        print(error)

        return False