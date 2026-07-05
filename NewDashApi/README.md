Dashboard Framework Development Summary
Version: v0.1
Date: 2026-07-04

Project Goal
============
Build a lightweight Python framework that allows scientists to create
scientific dashboards without needing to learn Dash.

The framework should generate Dash interfaces automatically from simple
Python classes.

Design Philosophy
=================

Scientists should only define:

    1. What inputs exist.
    2. What the pane is called.
    3. Where the data should be sent.

They should never need to write:
- Dash layouts
- Dash callbacks
- HTML
- CSS
- API request code

Everything else is handled by the framework.

------------------------------------------------------------
FINAL ARCHITECTURE
------------------------------------------------------------

Scientist
    │
    ▼
Pane
    │
    ▼
Widgets
    │
    ▼
Dash Adapter
    │
    ▼
API Module
    │
    ▼
Backend Service(s)

No Engine.
No runtime state manager.
No experiment logic inside the framework.

------------------------------------------------------------
WIDGETS
------------------------------------------------------------

Widgets are pure data descriptors.

They describe:

- label
- widget type
- default value

They contain NO:

- callbacks
- Dash code
- API code
- experiment logic

Current widget types:

- NumberInput
- TextInput
- Dropdown

Future widget types may include:

- Checkbox
- Toggle
- Slider
- FilePicker
- StatusDisplay
- Plot
- Image

------------------------------------------------------------
PANES
------------------------------------------------------------

A Pane is simply a collection of widgets.

Each pane defines:

NAME
API_ENDPOINT

Example:

class HeaterPane(Pane):

    NAME = "heater"

    API_ENDPOINT = "/api/heater"

    def build(self):

        self.temperature = NumberInput(...)
        self.mode = Dropdown(...)

The framework automatically registers widgets assigned as attributes.

The Pane has no Dash knowledge.

------------------------------------------------------------
PAYLOAD MODEL
------------------------------------------------------------

Each pane submits only its own data.

Example payload:

{
    "heater":
    {
        "temperature":25,
        "mode":"auto"
    }
}

No global dashboard payload is currently used.

Each pane has its own Confirm button.

------------------------------------------------------------
API MODEL
------------------------------------------------------------

Each pane owns its destination endpoint.

Example:

API_ENDPOINT = "/api/heater"

The Dash adapter simply calls:

submit(
    pane.API_ENDPOINT,
    payload
)

Future enhancement:

Allow API_ENDPOINT to be either:

"/api/heater"

or

"http://192.168.1.25:8000/api/heater"

allowing different panes to submit to different computers.

------------------------------------------------------------
DASH ADAPTER
------------------------------------------------------------

The Dash adapter is intentionally "dumb".

Responsibilities:

- Build Dash UI
- Render widgets
- Collect user input
- Build payload
- Call api.submit()

It performs NO:

- experiment logic
- routing logic
- state management
- scientific validation

------------------------------------------------------------
API MODULE
------------------------------------------------------------

api.py contains the HTTP communication layer.

Current responsibility:

submit(endpoint, payload)

Future responsibilities may include:

- retries
- authentication
- logging
- configurable timeout
- base server URL
- HTTPS certificates

without changing the dashboard code.

------------------------------------------------------------
DISCOVERY
------------------------------------------------------------

discover_panes()

Automatically imports every Pane subclass from the panes directory.

Adding a new dashboard pane only requires adding a new Python file.

No registration list.

No manual imports.

------------------------------------------------------------
CURRENT FILE STRUCTURE
------------------------------------------------------------

dashboard_framework/

    pane.py
    widgets.py
    discovery.py
    dash_adapter.py
    api.py

panes/

    heater.py
    camera.py

dashboard_test.py

------------------------------------------------------------
IMPORTANT DESIGN DECISIONS
------------------------------------------------------------

Removed:

- DashboardEngine
- Runtime state manager
- Widget callbacks
- Per-widget execution logic
- Global Confirm button

Kept:

- Automatic widget registration
- Automatic pane discovery
- Declarative pane definitions
- Per-pane Confirm button
- Automatic Dash generation

------------------------------------------------------------
FRAMEWORK RESPONSIBILITIES
------------------------------------------------------------

Framework:

✓ Build UI
✓ Collect input
✓ Submit payload
✓ Discover panes

Scientist:

✓ Define widgets
✓ Define pane name
✓ Define API endpoint

Backend:

✓ Validate values
✓ Execute experiments
✓ Store data
✓ Return responses

------------------------------------------------------------
NEXT DEVELOPMENT IDEAS
------------------------------------------------------------

Priority:

1. API response handling
2. Input validation framework
3. Additional widget types
4. Improved Dash styling
5. Tabs / collapsible panes
6. Plot widgets
7. Status widgets
8. Presets (save/load configuration)

Lower priority:

- Theme support
- Plugin packaging
- Authentication
- Multi-user dashboards

------------------------------------------------------------
MAJOR ARCHITECTURAL LESSON
------------------------------------------------------------

Early development included an Engine layer and runtime state management.

After several design iterations, we concluded these abstractions were
adding complexity without providing meaningful value.

The final architecture is intentionally simpler:

Pane → Widgets → Dash Adapter → API

The framework is now primarily a UI generation tool rather than an
application framework.

This simplicity aligns with the original project goal:
allow scientists to build dashboards by writing plain Python classes,
without understanding Dash or web development.