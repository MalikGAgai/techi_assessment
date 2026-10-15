"""Small test cases are fixtures only, never assessment or scraped data."""
from pathlib import Path

import pandas as pd
import pytest
import requests

from validate_data import CATEGORIES, load_traffic
from analyze_traffic import summarize_traffic, save_outputs


SOURCE = Path(__file__).resolve().parents[1] / "traffic_table.csv"


def test_original_data():
    data = load_traffic(SOURCE)
    assert len(data) == 12
    assert data.iloc[0]["month"] == "2025-09"
    assert data.iloc[-1]["month"] == "2026-08"


@pytest.mark.parametrize("problem", ["missing_column", "negative", "fraction", "blank",
                                     "duplicate", "invalid_month", "gap", "infinity", "empty"])
def test_invalid_data_is_rejected(tmp_path, problem):
    data = pd.read_csv(SOURCE, dtype=str)
    if problem == "missing_column":
        data = data.drop(columns="AI")
    elif problem == "negative":
        data.loc[0, "AI"] = "-1"
    elif problem == "fraction":
        data.loc[0, "AI"] = "1.5"
    elif problem == "blank":
        data.loc[0, "AI"] = ""
    elif problem == "duplicate":
        data.loc[1, "month"] = data.loc[0, "month"]
    elif problem == "invalid_month":
        data.loc[0, "month"] = "2025-13"
    elif problem == "gap":
        data = data.drop(index=1)
    elif problem == "infinity":
        data.loc[0, "AI"] = "inf"
    else:
        data = data.iloc[:0]
    path = tmp_path / "invalid.csv"
    data.to_csv(path, index=False)
    with pytest.raises(ValueError):
        load_traffic(path)


def test_summary_uses_only_traffic_categories():
    data = load_traffic(SOURCE)
    monthly, categories = summarize_traffic(data)
    assert monthly.iloc[0]["total_traffic"] == 57500
    assert pd.isna(monthly.iloc[0]["traffic_mom_pct"])
    assert monthly.iloc[1]["traffic_mom_pct"] == pytest.approx((59000 / 57500 - 1) * 100)
    assert categories["total_traffic"].sum() == data[CATEGORIES].sum().sum()
    assert monthly["newsletter_signups"].sum() == data["newsletter_signups"].sum()


def test_zero_previous_total_has_no_percentage():
    data = load_traffic(SOURCE)
    data.loc[0, CATEGORIES] = 0
    monthly, _ = summarize_traffic(data)
    assert pd.isna(monthly.iloc[1]["traffic_mom_pct"])


def test_unsorted_input_is_sorted_without_rewriting(tmp_path):
    path = tmp_path / "unsorted.csv"
    pd.read_csv(SOURCE).iloc[::-1].to_csv(path, index=False)
    before = path.read_bytes()
    data = load_traffic(path)
    assert data.month.iloc[0] == "2025-09"
    assert path.read_bytes() == before


def test_output_files_and_input_preservation(tmp_path):
    original = SOURCE.read_bytes()
    monthly, categories = summarize_traffic(load_traffic(SOURCE))
    save_outputs(monthly, categories, tmp_path)
    assert set(path.name for path in tmp_path.iterdir()) == {
        "monthly_summary.csv", "category_summary.csv", "traffic_by_month.png",
        "summary.txt",
    }
    saved = pd.read_csv(tmp_path / "monthly_summary.csv")
    assert saved.total_traffic.sum() == monthly.total_traffic.sum()
    for name in ["traffic_by_month.png"]:
        assert (tmp_path / name).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert SOURCE.read_bytes() == original

