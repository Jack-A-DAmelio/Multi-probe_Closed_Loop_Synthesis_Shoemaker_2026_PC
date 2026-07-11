from dash import html
import requests


from dash import html, Input, Output, State
from app import app
from dashboard_framework.api import submit

class DashAdapter:

    def __init__(self, pane_classes, columns=2):
        self.pane_classes = pane_classes
        self.columns = columns

        self.panes = [p() for p in pane_classes]
        for p in self.panes:
            p.build()

        self.actions = ActionEngine(self.panes)

        # cache prevents flicker
        self._cache = {}
        self._init_cache()

    def _init_cache(self):
        for p in self.panes:
            for w in p.widgets:
                self._cache[(p.NAME, w.label)] = w.default

    def _refresh(self):
        for p in self.panes:
            for w in p.widgets:

                if getattr(w, "source", None):

                    try:
                        params = {
                            "pane": p.NAME,
                            "widget": w.label
                        }

                        if getattr(w, "params", None):
                            params.update(w.params)

                        resp = requests.get(
                            w.source,
                            params=params,
                            timeout=2
                        )

                        if resp.status_code == 200:
                            self._cache[(p.NAME, w.label)] = resp.json()

                    except Exception:
                        pass

    def layout(self):

        self._refresh()

        children = []

        for p in self.panes:

            controls = [
                html.Div(
                    p.NAME,
                    style={
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "marginBottom": "10px"
                    }
                )
            ]

            for w in p.widgets:

                value = self._cache.get((p.NAME, w.label), w.default)

                controls.append(
                    html.Div([
                        html.Div(w.label),
                        html.Div(str(value))
                    ])
                )

            controls += self.actions.render_actions(p)

            children.append(
                html.Div(
                    controls,
                    style={
                        "border": "1px solid #ddd",
                        "padding": "14px",
                        "borderRadius": "10px",
                        "backgroundColor": "#fff"
                    }
                )
            )

        return html.Div(
            children,
            style={
                "display": "grid",
                "gridTemplateColumns": f"repeat({self.columns}, 1fr)",
                "gap": "12px",
                "padding": "10px"
            }
        )




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