"""
Dashboard Layout.

Stores the current dashboard configuration.
"""


class DashboardLayout:
    """
    Dashboard configuration.
    """

    def __init__(
        self,
        columns=2,
        pane_classes=None,
        api_url="http://localhost:5000/api"
    ):

        self.columns = columns
        self.api_url = api_url
        self.pane_classes = pane_classes or []