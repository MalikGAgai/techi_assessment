"""Validate the supplied monthly traffic CSV without changing it."""
import argparse
from pathlib import Path

import pandas as pd

CATEGORIES = ["AI", "Markets", "Crypto", "Breakthroughs", "Policy", "Guides"]
COUNTS = CATEGORIES + ["newsletter_signups"]
DEFAULT_INPUT = Path(__file__).resolve().parent / "traffic_table.csv"


def load_traffic(path=DEFAULT_INPUT):
    """Return validated rows sorted by month; raise ValueError on bad data."""
    data = pd.read_csv(path, dtype=str)
    expected = ["month"] + COUNTS
    if set(data.columns) != set(expected):
        raise ValueError(f"Expected exactly these columns: {', '.join(expected)}")
    if data.empty:
        raise ValueError("The traffic file has no rows.")
    if not data["month"].str.fullmatch(r"\d{4}-\d{2}").fillna(False).all():
        raise ValueError("Months must use YYYY-MM format.")
    dates = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError("Months must be valid and unique.")
    expected_months = pd.period_range(dates.min(), dates.max(), freq="M")
    if len(expected_months) != len(data):
        raise ValueError("Missing month(s) within the observed date range.")
    for column in COUNTS:
        values = pd.to_numeric(data[column], errors="coerce")
        valid = values.notna() & values.ge(0) & values.lt(float("inf"))
        if not valid.all():
            raise ValueError(f"{column} must contain finite, nonnegative counts.")
        if not values.mod(1).eq(0).all():
            raise ValueError(f"{column} must contain integer counts.")
        data[column] = values
    return data[expected].sort_values("month").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    try:
        data = load_traffic(args.input)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f"Validation failed: {error}\n")
    print(f"Valid: {len(data)} months, {data.month.iloc[0]} to {data.month.iloc[-1]}.")


if __name__ == "__main__":
    main()
