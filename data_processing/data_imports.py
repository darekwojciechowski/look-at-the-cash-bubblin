"""CSV import utilities for PKO BP / IPKO bank exports."""

import gzip
from pathlib import Path

import pandas as pd
from loguru import logger


def _warn_and_skip_bad_line(bad_line: list[str]) -> list[str] | None:
    """Log a warning for each malformed CSV row and instruct pandas to skip it."""
    logger.warning(f"[SKIP_BAD_LINE] Malformed row skipped: {bad_line}")
    return None


_MAX_GZIP_RATIO: float = 50.0  # max allowed ratio of uncompressed/compressed bytes
_GZIP_PROBE_SIZE: int = 65536  # 64 KB probe window


def _check_gzip_bomb(file_path: Path) -> None:
    """Raise ValueError if the gzip file appears to be a decompression bomb.

    Reads the first 64 KB of uncompressed data and compares it to the
    compressed file size.  A ratio above 50x indicates a likely bomb.
    """
    compressed_size = file_path.stat().st_size
    if compressed_size == 0:
        return
    with gzip.open(file_path, "rb") as gz:
        probe = gz.read(_GZIP_PROBE_SIZE)
    ratio = len(probe) / compressed_size
    if ratio > _MAX_GZIP_RATIO:
        raise ValueError(
            f"Gzip decompression bomb detected: {ratio:.0f}x expansion ratio exceeds "
            f"limit of {_MAX_GZIP_RATIO:.0f}x (file: {file_path})"
        )


def ipko_import(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a raw IPKO CSV DataFrame into the standard pipeline format.

    Renames the nine unnamed columns, extracts month and year from the
    transaction date, lowercases the text columns used downstream for
    categorization, and concatenates them into a single ``data`` column
    separated by ``//``. Source columns required for stable ``txn_id``
    computation (``booking_date``, ``value_date``, ``currency``, ``txn_type``,
    ``description``) are retained as separate columns alongside the merged
    ``data`` column.

    Args:
        df: Raw DataFrame loaded from an IPKO CSV export (nine columns,
            no header).

    Returns:
        DataFrame with columns: ``booking_date``, ``value_date``, ``txn_type``,
        ``amount``, ``currency``, ``description``, ``data``, ``month``,
        ``year``, ``day``.
    """
    # Rename columns for consistency
    df = df.rename(
        columns={
            df.columns[0]: "booking_date",
            df.columns[1]: "value_date",
            df.columns[2]: "txn_type",
            df.columns[3]: "amount",
            df.columns[4]: "currency",
            df.columns[5]: "description",
            df.columns[6]: "unnamed_6",
            df.columns[7]: "data",
            df.columns[8]: "unnamed_8",
        },
    )

    # Convert dates to datetime
    df["booking_date"] = pd.to_datetime(df["booking_date"])
    df["value_date"] = pd.to_datetime(df["value_date"], errors="coerce")

    # Extract day, month and year from booking_date
    df["month"] = df["booking_date"].dt.month
    df["year"] = df["booking_date"].dt.year
    df["day"] = df["booking_date"].dt.day

    # Convert specified columns to lowercase safely
    columns_to_lower = [
        "data",
        "txn_type",
        "description",
        "unnamed_6",
        "unnamed_8",
    ]
    for col in columns_to_lower:
        df[col] = df[col].astype(str).str.lower()

    # Combine multiple columns into a single 'data' column
    df["data"] = df[
        [
            "txn_type",
            "description",
            "unnamed_6",
            "unnamed_8",
            "data",
        ]
    ].apply(lambda row: "//".join(s for s in map(str, row) if s != "nan"), axis=1)

    # Drop helper columns; retain source columns needed for txn_id
    df = df.drop(columns=["unnamed_6", "unnamed_8"])

    return df


def read_transaction_csv(file_path: str | Path, encoding: str) -> pd.DataFrame:
    """Load a transaction CSV file, trying multiple encodings in priority order.

    Deprioritizes latin-1 variants to avoid silent mojibake on Polish text.
    Falls back through ``utf-8``, ``utf-8-sig``, ``cp1250``, ``iso-8859-2``,
    then ``cp1252`` / ``iso-8859-1`` as a last resort.

    Args:
        file_path: Path to the CSV file.
        encoding: Preferred encoding to try first. Latin-1 variants are
            automatically moved to the end of the fallback chain.

    Returns:
        Decoded DataFrame.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
        ValueError: If the file cannot be decoded with any tried encoding, or
            if a symlink target escapes the parent directory, or if the file
            is a gzip decompression bomb.
    """
    # Guard against symlinks escaping the parent directory
    path = Path(file_path)
    if path.is_symlink():
        resolved = path.resolve()
        base = path.parent.resolve()
        if not resolved.is_relative_to(base):
            raise ValueError(f"Symlink target {resolved!r} escapes base directory {base!r}")

    # Guard against gzip decompression bombs before handing off to pandas
    if path.suffix.lower() in {".gz", ".gzip"}:
        _check_gzip_bomb(path)

    # Prefer encodings that are commonly used for Polish text first.
    preferred_pl_encodings = ["utf-8", "utf-8-sig", "cp1250", "iso-8859-2"]
    # keep latin1 last as it rarely fails but can mojibake
    secondary_encodings = ["cp1252", "iso-8859-1"]

    # If caller passes latin-1/iso-8859-1, deprioritize it to avoid silent mojibake.
    enc_lower = (encoding or "").replace("_", "-").lower()
    is_latin1 = enc_lower in {"iso-8859-1", "latin1", "latin-1", "iso_8859_1"}

    if encoding and not is_latin1:
        # Respect caller-provided encoding by trying it first
        encodings_to_try = [encoding] + [e for e in preferred_pl_encodings + secondary_encodings if e != encoding]
    else:
        # Use a safe default order for Polish data
        encodings_to_try = preferred_pl_encodings + secondary_encodings

    try:
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(
                    file_path,
                    on_bad_lines=_warn_and_skip_bad_line,
                    engine="python",
                    encoding=enc,
                )
                logger.info(f"[SUCCESS] Loaded CSV file: {file_path} with encoding: {enc}")
                return df
            except UnicodeError:
                logger.debug(f"[ENCODING] Failed with encoding: {enc}")
                continue
            except FileNotFoundError as e:
                # Explicit log message expected by tests and users
                logger.error(f"[ERROR] Failed to read CSV file: {file_path}. Error: {str(e)}")
                raise
            except Exception as e:
                # If it's clearly encoding-related, try next; otherwise, log and re-raise
                if "codec" in str(e).lower() or "encoding" in str(e).lower():
                    logger.warning(f"[WARNING] Encoding error with {enc}: {e}")
                    continue
                else:
                    logger.error(f"[ERROR] Failed to read CSV file: {file_path}. Error: {str(e)}")
                    raise
    finally:
        # For visibility, log the attempted encodings if we end up failing completely
        logger.debug(f"Tried encodings in order: {encodings_to_try}")

    # If all encodings fail, raise an error
    raise ValueError(f"Could not read {file_path} with any of the tried encodings: {encodings_to_try}")
