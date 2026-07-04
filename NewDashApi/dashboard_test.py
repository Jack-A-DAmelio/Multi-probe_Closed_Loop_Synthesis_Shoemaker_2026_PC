from dashboard_framework.discovery import discover_panes

panes = discover_panes("panes")

for pane in panes:

    print(
        pane.TITLE,
        len(pane.widgets)
    )