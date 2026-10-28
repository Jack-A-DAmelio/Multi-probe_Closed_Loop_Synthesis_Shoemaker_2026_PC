# NewDashApi: Modular Dash Dashboard Framework

NewDashApi is the PC-side Dash interface for the multi-probe closed-loop
synthesis project. It provides reusable panes and widgets for displaying
instrument readings, entering experiment and hardware settings, and sending
actions to the PC server.

## Core concepts

### Pane

A pane groups related widgets under a namespace. A pane defines its widgets in
`build()`; the dashboard adapter uses the pane name and widget labels to render
the interface and communicate with the server.

### Widget

Widgets describe dashboard fields without implementing their rendering.
Available widget types include:

- `Display` and `ImageDisplay` for read-only live values and images
- `TextInput`, `NumberInput`, `Dropdown`, and `Checkbox` for user input
- `Button` for submitting pane inputs to a server endpoint

### DashAdapter

`DashAdapter` creates and renders pane widgets, polls configured display sources,
and registers callbacks for input and action widgets.

## Add a pane

Create a `Pane` subclass in `NewDashApi/panes`. The launcher discovers pane
classes from that directory.

```python
from dashboard_framework.pane import Pane
from dashboard_framework.widgets import Button, Display, TextInput


class HeaterPane(Pane):
    NAME = "heater"

    def build(self):
        self.temperature = Display(
            label="Temperature",
            source="/api/heater/temperature",
        )
        self.mode = TextInput(
            label="Mode",
            default="auto",
        )
        self.apply = Button(
            label="Apply settings",
            endpoint="/api/heater/apply",
        )
```

Display sources and button endpoints are relative to the API URL configured in
the dashboard. The server must provide matching routes.

## Run the dashboard

From the `NewDashApi` directory, run:

```powershell
python launch_dashboard.py
```

Select the desired panes, configure the PC server API URL, and choose
**Update Dashboard** to render them.

## Steps to add a pane

1. Create a Python file in `NewDashApi/panes`.
2. Define a class that inherits from `Pane` and give it a unique `NAME`.
3. Implement `build()` and add the needed widgets. Give each widget a clear
   label; use `source` for live displays and `endpoint` for action buttons.
4. If the pane reads from or sends data to the PC server, add or confirm the
   matching API route and payload in `server/endpoints`.
5. Restart the dashboard so it discovers the new pane class.
6. Select the pane in the dashboard builder, set the API URL and column count,
   then choose **Update Dashboard**.
7. Verify that inputs, live values, and button actions work with the server.
