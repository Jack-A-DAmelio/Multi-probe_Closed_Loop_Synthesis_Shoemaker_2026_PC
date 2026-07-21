"""
Run script for the modular crystal tracking package.

Edit config_parameters.json for normal use. This file can be run from any
terminal location because it finds config_parameters.json relative to itself.
"""

import os

# macOS may print a Tk deprecation warning when tkinter popups are used.
# This does not affect the analysis, but silencing it keeps terminal output cleaner.
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

from pathlib import Path

from crystal_tracking.main import run_crystal_tracking


if __name__ == "__main__":
    project_folder = Path(__file__).resolve().parent
    config_file_path = project_folder / "config_parameters.json"

    # Make relative input/output paths in config_parameters.json resolve from
    # the project folder instead of from whatever folder the terminal is in.
    os.chdir(project_folder)

    run_crystal_tracking(config_file_path=config_file_path)
