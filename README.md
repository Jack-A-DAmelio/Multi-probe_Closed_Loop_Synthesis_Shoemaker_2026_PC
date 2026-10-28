# Multi-probe Closed-Loop Synthesis: PC

This repository contains the PC-side software for a multi-probe system used to
record measurements during solution reactions. The project is
designed to collect chemical and process descriptors such as temperature,
volume, pH, and images of the solution. Sensor acquisition is coordinated with
a Raspberry Pi over a network.

This repository covers the PC application. Raspberry Pi software is maintained
separately:

- PC: [Multi-probe Closed-Loop Synthesis (PC)](https://github.com/Jack-A-DAmelio/Multi-probe_Closed_Loop_Synthesis_Shoemaker_2026_PC)
- Raspberry Pi: [Multi-probe Closed-Loop Synthesis (Pi)](https://github.com/Jack-A-DAmelio/Multi-probe_Closed_Loop_Synthesis_Shoemaker_2026_Pi)

## System overview

The PC application has two main components:

1. **Dash dashboard (`dashapi/`)** — provides GUI for experiment settings,
   experiment control, thermocouple setup, scale setup, and camera setup.
2. **FastAPI server (`server/`)** — receives dashboard actions, maintains
   experiment and hardware configuration, communicates with the Pi, and serves
   current readings to the dashboard.

During an experiment, the PC requests measurements from the Pi, updates the
dashboard's latest readings, and writes timestamped measurements to a CSV file.
If a USB camera is configured, images are saved alongside the CSV data.

## Repository layout

```text
NewDashApi/
  dashboard_framework/  Reusable pane, widget, API, and Dash adapter code
  panes/                Dashboard panes for setup and experiment control
  launch_dashboard.py   Dashboard entry point
  dashboard_readme.md  Dashboard framework guide
server/
  endpoints/            FastAPI control and data-retrieval routes
  camera_class.py       USB camera capture and image saving
  pc_server_v2.py       FastAPI server entry point
  pc_state.py           Shared state, Pi communication, and experiment loop
```

## Getting started

### Prerequisites

- Python with the packages used by the application installed, including Dash,
  FastAPI, Uvicorn, Requests, OpenCV, and NumPy.
- The Raspberry Pi service running and reachable from the PC for hardware
  configuration and measurement.
- A USB camera connected to the PC if image capture is required.

There is currently no dependency manifest in this repository. Create or activate
an environment with the required packages before launching the applications.

### Configure and launch

1. Configure the PC's network access to the Pi. The Pi address is currently set
   in `server/pc_state.py`; update it there if your network uses a different
   address.
2. Open a terminal in `server/` and start the API:

   ```powershell
   python pc_server_v2.py
   ```

   The server listens on port `8000`.
3. In a separate terminal, open `NewDashApi/` and start the dashboard:

   ```powershell
   python launch_dashboard.py
   ```

4. In the dashboard builder, set the API URL (normally
   `http://localhost:8000`), select the panes, and choose **Update Dashboard**.
5. Enter experiment settings and configure the required hardware panes. Send
   the module configuration to the PC and Pi, then use the experiment controls
   to test a measurement and start or stop collection.

For details on creating dashboard panes, see
[NewDashApi/dashboard_readme.md](./NewDashApi/dashboard_readme.md).

## Data output

Set the experiment's data folder in the dashboard before starting collection.
The PC creates a timestamped `experiment_*.csv` file in that folder. Each
measurement row includes a timestamp, the reported measurement values, and a
camera-image path when a camera is active. Captured images are stored in the
folder's `camera/` subdirectory.

## Current dashboard panes

- **Experiment setup:** experiment name, data folder, sample name, and sample
  interval.
- **Thermocouple setup:** thermocouple configuration and current temperature.
- **Scale setup:** scale configuration and current reading.
- **Camera setup:** camera port selection and camera view.
- **Experiment control:** current status and configuration, test measurement,
  start/stop, and Pi configuration actions.

The overall project aims to record temperature, volume, pH, and solution images.
The active hardware and measurements depend on the corresponding pane
configuration and Raspberry Pi implementation.

## Documentation and follow-up

- [Dashboard framework guide](./NewDashApi/dashboard_readme.md)
- Raspberry Pi setup and software: see the linked Pi repository above.


