# Modular k-means crystal tracking

This is a refactored version of the original single-file crystal tracking script. The main behavior is the same, but the code is split by purpose so comments and methods are closer together.


## How to run

Run only the top-level launcher.

macOS/Linux:

```bash
python3 "/path/to/crystal_tracking_refactor/run_tracking.py"
```

Windows PowerShell:

```powershell
py "C:\path\to\crystal_tracking_refactor\run_tracking.py"
```

or:

```powershell
python "C:\path\to\crystal_tracking_refactor\run_tracking.py"
```

Do not run files inside `crystal_tracking/` directly, such as
`crystal_tracking/components.py`. Those files are package modules and use
relative imports, so they are meant to be imported by `run_tracking.py`.

`run_tracking.py` finds `config_parameters.json` using its own file location,
not the current terminal folder. This avoids the common error:

```text
FileNotFoundError: Could not find config file: config_parameters.json
```


## Files

- `run_tracking.py`: entry point. Run this file.
- `config_parameters.json`: user-editable parameter file.
- `crystal_tracking/config.py`: default settings and JSON config loading.
- `crystal_tracking/user_interface.py`: cross-platform startup dialogs for output folder and k-means channels.
- `crystal_tracking/input_sources.py`: single image, image list, image folder, and MP4 input handling.
- `crystal_tracking/roi_manager.py`: ROI selection, manual ROIs, and multiple-ROI masks.
- `crystal_tracking/color_kmeans.py`: channel extraction, k-means fitting, cluster assignment, and crystal/non-crystal pixel filtering.
- `crystal_tracking/components.py`: connected-component detection and Region object creation.
- `crystal_tracking/tracker.py`: frame-to-frame crystal index preservation.
- `crystal_tracking/outputs.py`: overlays, plots, CSV tables, and JSON exports.
- `crystal_tracking/main.py`: ties the full workflow together.

## Install packages

macOS/Linux:

```bash
python3 -m pip install numpy pandas matplotlib scipy scikit-image opencv-python
```

Windows PowerShell:

```powershell
py -m pip install numpy pandas matplotlib scipy scikit-image opencv-python
```

Tkinter is used for Windows popups. It is included with most normal Python installers from python.org. If Tkinter is unavailable, turn off startup dialogs or use terminal mode in `config_parameters.json`.


## Cross-platform startup popups

The same code folder is intended to work on macOS and Windows.

In `config_parameters.json`:

```json
"startup_dialog_backend": "auto",
"ask_for_output_folder_on_start": true,
"ask_for_kmeans_channels_on_start": true
```

Backend options:

- `"auto"`: macOS uses AppleScript dialogs first, then Tkinter as fallback. Windows uses Tkinter.
- `"tk"`: force Tkinter dialogs on macOS, Windows, or Linux.
- `"applescript"`: force AppleScript dialogs. This is macOS only.
- `"terminal"`: ask for the output folder and channels in the terminal.
- `"none"`: skip startup prompts and use the JSON settings directly.

On macOS, `auto` avoids the deprecated system-Tk warning by using AppleScript before Tkinter. On Windows, `auto` uses normal Tkinter folder and channel dialogs.

If you want the cleanest repeatable run on either operating system, set:

```json
"startup_dialog_backend": "none",
"ask_for_output_folder_on_start": false,
"ask_for_kmeans_channels_on_start": false
```

Then manually edit:

```json
"output_folder": "/Users/darrenco/Downloads/Crystal_Tracking_Output",
"kmeans_channel_names": ["red", "green"]
```

On Windows, paths can be written with escaped backslashes:

```json
"output_folder": "C:\\Users\\Darren\\Downloads\\Crystal_Tracking_Output"
```

or with forward slashes:

```json
"output_folder": "C:/Users/Darren/Downloads/Crystal_Tracking_Output"
```


## Changing color channels

The old behavior was red-green k-means:

```json
"kmeans_channel_names": ["red", "green"]
```

For red-blue:

```json
"kmeans_channel_names": ["red", "blue"]
```

For red-yellow:

```json
"kmeans_channel_names": ["red", "yellow"]
```

`yellow` is computed as the average of red and green. Other available channels are `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, and `brightness`.


## Multiple ROIs

For interactive ROI selection, set:

```json
"roi_input_mode": "interactive"
```

The ROI preview window has three buttons:

- `Add Another ROI`: saves the current ROI and lets you draw another one.
- `Accept ROI(s)`: saves the current ROI, if one is drawn, and continues the analysis.
- `Clear Current`: removes only the currently proposed ROI. Already accepted ROIs stay on the preview.

You do not need to know the number of ROIs before the run. Draw one ROI, click `Add Another ROI` if you need another, and click `Accept ROI(s)` when finished.

For manual ROIs, set:

```json
"roi_input_mode": "manual",
"manual_rois": [
    {"roi_index": 1, "center_x": 200.0, "center_y": 200.0, "radius": 100.0},
    {"roi_index": 2, "center_x": 500.0, "center_y": 250.0, "radius": 80.0}
]
```

The workflow creates a combined ROI mask and an ROI label mask. Output tables include `roi_index`.


## Crystal vs non-crystal color analysis

This only controls `color_analysis_summary.csv`; it does not change tracking unless you also change which k-means clusters count as crystal pixels.

```json
"color_analysis_pixel_filter": "all_roi"
```

Options:

- `all_roi`: summarize all ROI pixels.
- `crystal_only`: summarize only pixels assigned to the crystal cluster(s).
- `non_crystal_only`: summarize only ROI pixels not assigned to the crystal cluster(s).


## Common errors

### `ImportError: attempted relative import with no known parent package`

This happens when an internal file is run directly, for example:

```bash
python crystal_tracking/components.py
```

Run `run_tracking.py` instead.

### `DEPRECATION WARNING: The system version of Tk is deprecated...`

On macOS, use:

```json
"startup_dialog_backend": "auto"
```

or:

```json
"startup_dialog_backend": "applescript"
```

The launcher also sets `TK_SILENCE_DEPRECATION=1` before importing the tracking package.

### Dialogs cause problems or get hidden behind other windows

Use terminal mode:

```json
"startup_dialog_backend": "terminal"
```

or disable startup dialogs:

```json
"startup_dialog_backend": "none"
```
