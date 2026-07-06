from dash import html
from dashboard_framework.action_engine import ActionEngine


class DashAdapter:

    def __init__(self, pane_classes, columns=2):
        self.pane_classes = pane_classes
        self.columns = columns

        self.panes = [p() for p in pane_classes]
        for p in self.panes:
            p.build()

        # ACTION ENGINE (NEW)
        self.actions = ActionEngine(self.panes)

    def layout(self):

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

            # existing widgets
            for w in p.widgets:
                controls.append(
                    html.Div([
                        html.Div(w.label),
                        html.Div(str(w.default))
                    ])
                )

            # NEW: actions injected here
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