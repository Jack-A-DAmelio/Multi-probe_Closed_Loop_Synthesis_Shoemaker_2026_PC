from dash import html


class DashAdapter:

    def __init__(self, pane_classes, columns=2):
        self.pane_classes = pane_classes
        self.columns = columns

    def layout(self):

        panes = [p() for p in self.pane_classes]

        for p in panes:
            p.build()

        children = []

        for p in panes:

            controls = [html.H3(p.NAME)]

            for w in p.widgets:
                controls.append(html.Div([
                    html.Label(w.label),
                    str(w.default)
                ]))

            children.append(
                html.Div(
                    controls,
                    style={
                        "border": "1px solid #ccc",
                        "padding": "10px",
                        "margin": "5px"
                    }
                )
            )

        return html.Div(
            children,
            style={
                "display": "grid",
                "gridTemplateColumns": f"repeat({self.columns}, 1fr)",
                "gap": "10px"
            }
        )