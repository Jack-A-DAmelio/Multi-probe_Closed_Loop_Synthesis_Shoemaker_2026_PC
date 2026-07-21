"""
Basic file input/output helpers.

Keeping these helpers separate makes the analysis modules easier to read and
keeps file-system behavior in one place.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from skimage import io


def create_output_folder(output_folder: str | Path) -> None:
    """Create an output folder if it does not already exist."""

    Path(output_folder).mkdir(parents=True, exist_ok=True)


def save_image(image: Any, file_path: str | Path) -> None:
    """Save an image to disk."""

    io.imsave(str(file_path), image, check_contrast=False)


def save_json(data: Any, file_path: str | Path) -> None:
    """Save JSON-compatible data to disk."""

    with Path(file_path).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def save_table(data_table: pd.DataFrame, output_file_path: str | Path) -> None:
    """Save a pandas DataFrame as a CSV file."""

    data_table.to_csv(output_file_path, index=False)


def load_image(image_file_path: str | Path):
    """Load an image frame from disk."""

    image_path = Path(image_file_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Could not find image file: {image_path}")

    return io.imread(str(image_path))
