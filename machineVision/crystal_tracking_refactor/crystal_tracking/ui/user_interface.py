"""
Cross-platform startup dialogs for user-facing run settings.

These dialogs are intentionally separate from the analysis code. They only ask
for settings that a user may want to change at run time:
- output folder
- two k-means color channels

The dialog backend is selected by config["startup_dialog_backend"]:
- "auto": macOS uses native AppleScript dialogs; Windows/Linux use Tkinter.
- "tk": force Tkinter dialogs on any operating system.
- "applescript": force AppleScript dialogs. Only works on macOS.
- "terminal": ask in the terminal instead of opening popups.
- "none": skip startup prompts and use config_parameters.json values.

This makes the same project folder usable on both macOS and Windows. The
tracking code does not depend on the startup dialog backend.
"""

from __future__ import annotations

import os

# Silence the macOS system-Tk warning before any optional tkinter import.
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from crystal_tracking.segmentation.color_kmeans import CHANNEL_DISPLAY_NAMES


VALID_STARTUP_DIALOG_BACKENDS = {"auto", "tk", "applescript", "terminal", "none"}


def normalize_startup_dialog_backend(config: Dict[str, Any]) -> str:
    """Return a validated startup dialog backend name."""

    backend = str(config.get("startup_dialog_backend", "auto")).lower().strip()

    if backend not in VALID_STARTUP_DIALOG_BACKENDS:
        print(
            f"Unknown startup_dialog_backend '{backend}'. "
            "Using 'auto' instead."
        )
        return "auto"

    return backend


# =========================================================
# macOS AppleScript dialogs
# =========================================================


def run_applescript(script: str) -> Optional[str]:
    """
    Run a short AppleScript command and return its printed result.

    AppleScript is used on macOS because it opens native chooser dialogs without
    importing tkinter. This avoids the deprecated-Tk warning from Apple's system
    Python. A blank result means the user canceled the dialog.
    """

    if platform.system() != "Darwin":
        return None

    try:
        completed_process = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as error:
        print(f"Could not run AppleScript dialog. Reason: {error}")
        return None

    if completed_process.returncode != 0:
        error_text = completed_process.stderr.strip()
        if error_text:
            print(f"AppleScript dialog was not completed. Reason: {error_text}")
        return None

    return completed_process.stdout.strip()


def applescript_list(items: List[str]) -> str:
    """Convert a Python string list into an AppleScript list literal."""

    quoted_items = []

    for item in items:
        safe_item = str(item).replace('"', '\\"')
        quoted_items.append(f'"{safe_item}"')

    return "{" + ", ".join(quoted_items) + "}"


def choose_output_folder_with_applescript(config: Dict[str, Any]) -> Optional[str]:
    """Ask for an output folder using the native macOS folder chooser."""

    if platform.system() != "Darwin":
        print("AppleScript dialogs are only available on macOS.")
        return None

    configured_folder = Path(str(config["output_folder"])).expanduser()

    if configured_folder.exists():
        default_folder = str(configured_folder)
    else:
        default_folder = str(Path.home())

    safe_default_folder = default_folder.replace('"', '\\"')

    script = f'''
try
    set defaultFolder to POSIX file "{safe_default_folder}"
    set selectedFolder to choose folder with prompt "Choose output folder for crystal tracking results" default location defaultFolder
    return POSIX path of selectedFolder
on error number -128
    return ""
end try
'''

    selected_folder = run_applescript(script)

    if selected_folder:
        return os.path.abspath(selected_folder)

    return None


def choose_one_channel_with_applescript(
    prompt: str,
    default_channel: str,
    channel_options: List[str],
) -> Optional[str]:
    """Ask for one channel using a native macOS list chooser."""

    if platform.system() != "Darwin":
        print("AppleScript dialogs are only available on macOS.")
        return None

    if default_channel not in channel_options:
        default_channel = channel_options[0]

    option_text = applescript_list(channel_options)
    safe_prompt = prompt.replace('"', '\\"')
    safe_default = default_channel.replace('"', '\\"')

    script = f'''
try
    set channelOptions to {option_text}
    set selectedChannel to choose from list channelOptions with title "K-means channel selection" with prompt "{safe_prompt}" default items {{"{safe_default}"}} without multiple selections allowed
    if selectedChannel is false then
        return ""
    end if
    return item 1 of selectedChannel
on error number -128
    return ""
end try
'''

    selected_channel = run_applescript(script)

    if selected_channel:
        return selected_channel.strip()

    return None


def choose_kmeans_channels_with_applescript(config: Dict[str, Any]) -> Optional[List[str]]:
    """Ask for two k-means channels using native macOS list dialogs."""

    valid_channels = list(CHANNEL_DISPLAY_NAMES.keys())
    current_channels = list(config.get("kmeans_channel_names", ["red", "green"]))

    first_default = current_channels[0] if len(current_channels) >= 1 else "red"
    second_default = current_channels[1] if len(current_channels) >= 2 else "green"

    first_channel = choose_one_channel_with_applescript(
        prompt=(
            "Choose the first color channel for k-means clustering. "
            "Examples: red, green, blue, yellow, cyan, magenta, brightness."
        ),
        default_channel=first_default,
        channel_options=valid_channels,
    )

    if first_channel is None:
        return None

    second_options = [channel for channel in valid_channels if channel != first_channel]

    if second_default == first_channel or second_default not in second_options:
        second_default = second_options[0]

    second_channel = choose_one_channel_with_applescript(
        prompt=(
            "Choose the second color channel for k-means clustering. "
            "Choose a different channel from the first one."
        ),
        default_channel=second_default,
        channel_options=second_options,
    )

    if second_channel is None:
        return None

    return [first_channel, second_channel]


# =========================================================
# Tkinter dialogs for Windows, Linux, and optional macOS fallback
# =========================================================


def create_hidden_tk_root():
    """Create a hidden top-level Tk root window, or return None if Tk is unavailable."""

    try:
        import tkinter as tk
    except Exception as error:
        print(f"Could not import tkinter. Reason: {error}")
        return None

    try:
        root = tk.Tk()
        root.withdraw()

        try:
            root.attributes("-topmost", True)
        except Exception:
            pass

        try:
            root.update_idletasks()
            root.lift()
            root.focus_force()
        except Exception:
            pass

        return root
    except Exception as error:
        print(f"Could not create tkinter window. Reason: {error}")
        return None


def choose_output_folder_with_tk(config: Dict[str, Any]) -> Optional[str]:
    """
    Ask for an output folder using tkinter.

    This is the default popup backend on Windows. It also works on most Python
    installations on macOS and Linux, but macOS defaults to AppleScript in auto
    mode to avoid the deprecated system-Tk warning.
    """

    try:
        from tkinter import filedialog
    except Exception as error:
        print(f"Could not import tkinter filedialog. Reason: {error}")
        return None

    configured_folder = Path(str(config["output_folder"])).expanduser()

    if configured_folder.exists():
        initial_folder = str(configured_folder)
    else:
        initial_folder = str(Path.home())

    root = create_hidden_tk_root()

    if root is None:
        return None

    try:
        selected_folder = filedialog.askdirectory(
            parent=root,
            title="Choose output folder for crystal tracking results",
            initialdir=initial_folder,
            mustexist=False,
        )
    finally:
        root.destroy()

    if selected_folder:
        return os.path.abspath(selected_folder)

    return None


def choose_kmeans_channels_with_tk(config: Dict[str, Any]) -> Optional[List[str]]:
    """Ask for the two k-means color channels using a Tkinter window."""

    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except Exception as error:
        print(f"Could not import tkinter channel dialog tools. Reason: {error}")
        return None

    valid_channels: List[str] = list(CHANNEL_DISPLAY_NAMES.keys())
    current_channels = list(config.get("kmeans_channel_names", ["red", "green"]))

    first_default = current_channels[0] if len(current_channels) >= 1 else "red"
    second_default = current_channels[1] if len(current_channels) >= 2 else "green"

    if first_default not in valid_channels:
        first_default = "red"

    if second_default not in valid_channels:
        second_default = "green"

    result = {"accepted": False, "channels": current_channels}

    try:
        root = tk.Tk()
    except Exception as error:
        print(f"Could not create Tk channel dialog. Reason: {error}")
        return None

    root.title("K-means color-channel selection")
    root.resizable(False, False)

    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    padding_options = {"padx": 12, "pady": 6, "sticky": "w"}

    title_label = ttk.Label(
        root,
        text="Choose the two color channels for k-means clustering.",
    )
    title_label.grid(row=0, column=0, columnspan=2, **padding_options)

    help_label = ttk.Label(
        root,
        text=(
            "Examples: red + green for the original behavior, red + blue for a "
            "different channel pair, or red + yellow where yellow = average(red, green)."
        ),
        wraplength=420,
    )
    help_label.grid(row=1, column=0, columnspan=2, **padding_options)

    first_label = ttk.Label(root, text="First k-means channel:")
    first_label.grid(row=2, column=0, **padding_options)

    first_channel = ttk.Combobox(root, values=valid_channels, state="readonly", width=18)
    first_channel.set(first_default)
    first_channel.grid(row=2, column=1, padx=12, pady=6, sticky="e")

    second_label = ttk.Label(root, text="Second k-means channel:")
    second_label.grid(row=3, column=0, **padding_options)

    second_channel = ttk.Combobox(root, values=valid_channels, state="readonly", width=18)
    second_channel.set(second_default)
    second_channel.grid(row=3, column=1, padx=12, pady=6, sticky="e")

    def accept_selection() -> None:
        selected_channels = [
            first_channel.get().strip().lower(),
            second_channel.get().strip().lower(),
        ]

        if selected_channels[0] == selected_channels[1]:
            messagebox.showwarning(
                "Duplicate channels",
                "Choose two different channels for k-means clustering.",
                parent=root,
            )
            return

        result["accepted"] = True
        result["channels"] = selected_channels
        root.destroy()

    def cancel_selection() -> None:
        root.destroy()

    button_frame = ttk.Frame(root)
    button_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=12, sticky="e")

    use_button = ttk.Button(button_frame, text="Use These Channels", command=accept_selection)
    use_button.grid(row=0, column=0, padx=6)

    cancel_button = ttk.Button(button_frame, text="Keep JSON Setting", command=cancel_selection)
    cancel_button.grid(row=0, column=1, padx=6)

    root.update_idletasks()

    try:
        width = root.winfo_width()
        height = root.winfo_height()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_position = int((screen_width - width) / 2)
        y_position = int((screen_height - height) / 2)
        root.geometry(f"+{x_position}+{y_position}")
    except Exception:
        pass

    try:
        root.lift()
        root.focus_force()
    except Exception:
        pass

    root.mainloop()

    if result["accepted"]:
        return result["channels"]

    return None


# =========================================================
# Terminal fallback
# =========================================================


def ask_terminal_output_folder(config: Dict[str, Any]) -> Optional[str]:
    """Ask for the output folder in the terminal."""

    configured_folder = str(config["output_folder"])

    print("")
    print("Output folder selection")
    print(f"Current output folder: {configured_folder}")
    selected_folder = input("Press Enter to keep it, or paste a new output folder path: ").strip()

    if selected_folder:
        return os.path.abspath(os.path.expanduser(selected_folder))

    return None


def ask_terminal_kmeans_channels(config: Dict[str, Any]) -> Optional[List[str]]:
    """Ask for two k-means color channels in the terminal."""

    valid_channels = list(CHANNEL_DISPLAY_NAMES.keys())
    current_channels = list(config.get("kmeans_channel_names", ["red", "green"]))

    print("")
    print("K-means channel selection")
    print(f"Available channels: {', '.join(valid_channels)}")
    print(f"Current channels: {current_channels}")
    raw_text = input("Press Enter to keep them, or type two channels separated by a comma: ").strip()

    if not raw_text:
        return None

    selected_channels = [channel.strip().lower() for channel in raw_text.split(",")]

    if len(selected_channels) != 2:
        print("Invalid entry. Using configured k-means channels.")
        return None

    if selected_channels[0] == selected_channels[1]:
        print("The two k-means channels must be different. Using configured channels.")
        return None

    for channel in selected_channels:
        if channel not in CHANNEL_DISPLAY_NAMES:
            print(f"Unknown channel '{channel}'. Using configured channels.")
            return None

    return selected_channels


# =========================================================
# Backend routing
# =========================================================


def choose_output_folder(config: Dict[str, Any]) -> Dict[str, Any]:
    """Choose the output folder using the configured cross-platform backend."""

    backend = normalize_startup_dialog_backend(config)
    system_name = platform.system()
    selected_folder: Optional[str] = None

    if backend == "none":
        print(f"Startup output-folder prompt skipped. Using: {config['output_folder']}")
        return config

    if backend == "terminal":
        selected_folder = ask_terminal_output_folder(config)

    elif backend == "applescript":
        selected_folder = choose_output_folder_with_applescript(config)

    elif backend == "tk":
        selected_folder = choose_output_folder_with_tk(config)

    elif backend == "auto":
        if system_name == "Darwin":
            selected_folder = choose_output_folder_with_applescript(config)
            if selected_folder is None:
                selected_folder = choose_output_folder_with_tk(config)
        else:
            selected_folder = choose_output_folder_with_tk(config)

    if selected_folder:
        config["output_folder"] = selected_folder
        print(f"Output folder selected: {config['output_folder']}")
    else:
        print(f"Output folder kept from config: {config['output_folder']}")

    return config


def choose_kmeans_channels(config: Dict[str, Any]) -> Dict[str, Any]:
    """Choose the two k-means channels using the configured cross-platform backend."""

    backend = normalize_startup_dialog_backend(config)
    system_name = platform.system()
    selected_channels: Optional[List[str]] = None

    if backend == "none":
        print(f"Startup k-means channel prompt skipped. Using: {config['kmeans_channel_names']}")
        return config

    if backend == "terminal":
        selected_channels = ask_terminal_kmeans_channels(config)

    elif backend == "applescript":
        selected_channels = choose_kmeans_channels_with_applescript(config)

    elif backend == "tk":
        selected_channels = choose_kmeans_channels_with_tk(config)

    elif backend == "auto":
        if system_name == "Darwin":
            selected_channels = choose_kmeans_channels_with_applescript(config)
            if selected_channels is None:
                selected_channels = choose_kmeans_channels_with_tk(config)
        else:
            selected_channels = choose_kmeans_channels_with_tk(config)

    if selected_channels:
        config["kmeans_channel_names"] = selected_channels
        print(f"K-means channels selected: {config['kmeans_channel_names']}")
    else:
        print(f"K-means channels kept from config: {config['kmeans_channel_names']}")

    return config


def apply_startup_dialogs(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply optional startup dialogs based on config flags."""

    backend = normalize_startup_dialog_backend(config)

    if backend == "none":
        print("Startup dialogs disabled by startup_dialog_backend = 'none'.")
        return config

    if config.get("ask_for_output_folder_on_start", False):
        config = choose_output_folder(config)

    if config.get("ask_for_kmeans_channels_on_start", False):
        config = choose_kmeans_channels(config)

    return config
