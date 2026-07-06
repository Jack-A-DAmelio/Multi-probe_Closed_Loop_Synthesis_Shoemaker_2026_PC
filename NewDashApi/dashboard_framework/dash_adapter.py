from dash import html
import requests

from dashboard_framework.action_engine import ActionEngine


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