"""
modules/data_handler.py - Data Persistence and CSV Processing Module

Responsibilities:
    - Parse uploaded CSV files and extract a validated numeric column
    - Append single encrypted values to the storage CSV
    - Overwrite the storage CSV with a full dataset
    - Load stored encrypted values back into memory for computation
"""

import os
import io
from typing import List, Optional, Tuple

import pandas as pd


class DataHandler:
    """Manages reading and writing of encrypted values in data.csv."""

    COLUMN_NAME = "encrypted_value"  # Header used in the storage CSV

    def __init__(self, data_path: str):
        """
        Args:
            data_path: Path to the CSV file used for persistent storage.
        """
        self.data_path = data_path
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        # Bootstrap empty CSV if it doesn't exist
        if not os.path.exists(data_path):
            self._init_csv()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_csv(
        self, file_obj, column: str
    ) -> Tuple[Optional[List[float]], Optional[str]]:
        """
        Parse an uploaded CSV file and extract a numeric column.

        Args:
            file_obj: A file-like object (from Flask request.files).
            column:   The column name the user wants to process.

        Returns:
            (values, None)        on success
            (None, error_message) on failure
        """
        try:
            content = file_obj.read()
            df = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            return None, f"Could not parse CSV: {exc}"

        if df.empty:
            return None, "The uploaded CSV file is empty."

        if column not in df.columns:
            available = ", ".join(df.columns.tolist())
            return None, f"Column '{column}' not found. Available columns: {available}"

        series = df[column]

        # Attempt numeric conversion
        numeric_series = pd.to_numeric(series, errors="coerce")
        if numeric_series.isna().all():
            return None, f"Column '{column}' contains no numeric values."

        # Drop rows that couldn't be converted (NaN)
        valid = numeric_series.dropna().tolist()
        if not valid:
            return None, f"Column '{column}' has no valid numeric rows after cleaning."

        return valid, None

    def append_value(self, encrypted_value: float) -> None:
        """
        Append a single encrypted value to the storage CSV.

        Args:
            encrypted_value: The encrypted numeric value to persist.
        """
        existing = self.load_values()
        existing.append(encrypted_value)
        self.write_values(existing)

    def write_values(self, encrypted_values: List[float]) -> None:
        """
        Overwrite the storage CSV with a fresh list of encrypted values.

        Args:
            encrypted_values: Complete list of encrypted values to persist.
        """
        df = pd.DataFrame({self.COLUMN_NAME: encrypted_values})
        df.to_csv(self.data_path, index=False)

    def load_values(self) -> List[float]:
        """
        Load all encrypted values from the storage CSV.

        Returns:
            List of floats (may be empty if no data has been stored yet).
        """
        try:
            df = pd.read_csv(self.data_path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return []

        if self.COLUMN_NAME not in df.columns:
            return []

        return df[self.COLUMN_NAME].dropna().tolist()

    def clear(self) -> None:
        """Reset the storage CSV to an empty state."""
        self._init_csv()

    # ------------------------------------------------------------------
    # Multi-Column API  (NEW — does not touch any existing method)
    # ------------------------------------------------------------------

    def parse_csv_all_numeric(
        self, file_obj
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Parse an uploaded CSV and extract ALL numeric columns automatically.

        Uses pandas select_dtypes so no column name needs to be supplied
        by the caller.

        Args:
            file_obj: A file-like object (from Flask request.files).

        Returns:
            ({"col_name": [float, ...]}, None)  on success
            (None, error_message)               on failure
        """
        try:
            content = file_obj.read()
            df = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            return None, f"Could not parse CSV: {exc}"

        if df.empty:
            return None, "The uploaded CSV file is empty."

        # Auto-detect all numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not numeric_cols:
            return None, "CSV contains no numeric columns."

        # Build a dict: column_name → list of valid float values
        result: dict = {}
        for col in numeric_cols:
            clean = pd.to_numeric(df[col], errors="coerce").dropna().tolist()
            if clean:
                result[col] = clean

        if not result:
            return None, "No numeric values found after cleaning."

        return result, None

    def write_column_data(self, encrypted_columns: dict) -> None:
        """
        Persist a multi-column encrypted dataset.

        Stores as a wide CSV where each column header is the original
        column name and each cell is an encrypted float.  Columns may
        have different lengths; shorter columns are NaN-padded.

        Args:
            encrypted_columns: {"col_name": [encrypted_float, ...], ...}
        """
        df = pd.DataFrame(
            {col: pd.Series(vals) for col, vals in encrypted_columns.items()}
        )
        df.to_csv(self.data_path, index=False)

    def load_column_data(self) -> dict:
        """
        Load a multi-column encrypted dataset written by write_column_data().

        Returns:
            {"col_name": [float, ...], ...}  (empty dict if no data yet)
        """
        try:
            df = pd.read_csv(self.data_path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return {}

        # Skip the legacy single-column format (produced by write_values)
        if list(df.columns) == [self.COLUMN_NAME]:
            return {}

        result: dict = {}
        for col in df.columns:
            clean = df[col].dropna().tolist()
            if clean:
                result[col] = clean
        return result

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _init_csv(self) -> None:
        """Create an empty storage CSV with the correct header."""
        df = pd.DataFrame(columns=[self.COLUMN_NAME])
        df.to_csv(self.data_path, index=False)
