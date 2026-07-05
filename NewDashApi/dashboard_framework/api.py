"""
Dashboard API communication helpers.

Author: You | Date: 2026-07-04 | Framework Version: v0.1

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

def submit(endpoint: str, payload: dict, timeout: float = 5.0) -> bool:
    """
    Submit a JSON payload to a backend API endpoint.

    Parameters
    ----------
    endpoint : str
        API endpoint that will receive the payload.

    payload : dict
        Dictionary to send as JSON.

    timeout : float, optional
        Maximum time to wait for a server response in seconds.

    Returns
    -------
    bool
        True if the request succeeded, otherwise False.
    """

    try:

        response = requests.post(
            endpoint,
            json=payload,
            timeout=timeout
        )

        response.raise_for_status()

        print(
            f"Successfully submitted to '{endpoint}' "
            f"(HTTP {response.status_code})"
        )

        return True

    except requests.exceptions.RequestException as error:

        print(
            f"Failed to submit payload to '{endpoint}'"
        )

        print(error)

        return False