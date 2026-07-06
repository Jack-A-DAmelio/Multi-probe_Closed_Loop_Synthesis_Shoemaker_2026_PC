from dash import html, Input, Output, State
from dashboard_framework.app import app
from dashboard_framework.api import submit


class ActionEngine:
    """
    Turns pane.action declarations into Dash UI + callbacks.
    """

    def __init__(self, panes):
        self.panes = panes
        self._register_actions()

    def render_actions(self, pane):

        if not hasattr(pane, "actions"):
            return []

        ui = []

        for action_name, action in pane.actions.items():

            button_id = f"{pane.NAME}:{action_name}"
            status_id = f"{pane.NAME}:{action_name}:status"

            ui.append(
                html.Button(
                    action.get("label", action_name),
                    id=button_id
                )
            )

            ui.append(
                html.Div(id=status_id)
            )

        return ui

    def _register_actions(self):

        for pane in self.panes:

            if not hasattr(pane, "actions"):
                continue

            for action_name, action in pane.actions.items():

                button_id = f"{pane.NAME}:{action_name}"
                status_id = f"{pane.NAME}:{action_name}:status"

                @app.callback(
                    Output(status_id, "children"),
                    Input(button_id, "n_clicks"),
                    State("layout-store", "data"),
                    prevent_initial_call=True
                )
                def run_action(n, layout, action=action):

                    if not layout:
                        return "No layout"

                    api_url = layout["api"]

                    payload_fn = action["payload"]
                    endpoint = action["endpoint"]

                    payload = payload_fn()

                    ok = submit(
                        api_url,
                        endpoint,
                        payload
                    )

                    return "OK" if ok else "FAILED"