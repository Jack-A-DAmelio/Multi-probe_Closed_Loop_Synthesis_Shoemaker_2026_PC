# Modular Dashboard Framework

A lightweight, extensible dashboard system for scientific and control applications.

---

# 🧠 Core Concepts

This system is built around 3 abstractions:

## 1. Pane
A Pane is a logical grouping of widgets.

- Defines a namespace
- Contains no UI logic
- Produces structured data

## 2. Widget
A Widget is a declarative field definition.

Widgets describe:
- label
- default value
- type (number, text, dropdown, etc.)
- optional live data source

Widgets do NOT handle rendering or state.

## 3. DashAdapter
The DashAdapter:
- instantiates panes
- renders widgets
- fetches live data from APIs
- injects action buttons

---

# 📦 Creating a New Pane

## Step 1: Define the Pane

```python
from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput, TextInput


class HeaterPane(Pane):

    NAME = "heater"

    def build(self):

        self.temperature = NumberInput(
            label="temperature",
            default=25,
            source="http://localhost:5000/api/heater/temp"
        )

        self.mode = TextInput(
            label="mode",
            default="auto"
        )