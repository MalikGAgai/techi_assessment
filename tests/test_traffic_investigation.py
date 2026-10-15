from pathlib import Path

import pandas as pd
import pytest

from investigate_traffic import calculate, article_timeline, run
from validate_data import load_traffic

ROOT = Path(__file__).resolve().parents[1]


def test_known_totals_and_growth():
    tables, metrics = calculate(load_traffic())
    monthly = tables['monthly_calculations'].set_index('month')
    assert monthly.loc['2025-09', 'reported_sessions'] == 57500
    assert monthly.loc['2026-01', 'reported_sessions'] == 64000
    assert monthly.loc['2026-02', 'reported_sessions'] == 94685
    assert monthly.loc['2026-08', 'reported_sessions'] == 102805
    assert monthly.loc['2026-02', 'reported_mom_pct'] == pytest.approx(47.9453125)
    assert metrics['reported_endpoint_pct'] == pytest.approx((102805 / 57500 - 1) * 100)


def test_tracking_factor_has_a_traceable_forecast():
    tables, metrics = calculate(load_traffic())
    calibration = tables['tracking_calibration'].set_index('section')
    assert calibration.loc['AI', 'median_pre_change_increment'] == 700
    assert calibration.loc['Markets', 'forecast_february_sessions'] == 13700
    assert calibration.loc['Markets', 'measurement_factor_estimate'] == pytest.approx(19865 / 13700)
    assert metrics['central_factor'] == pytest.approx(1.45)
    assert metrics['adjusted_august'] == pytest.approx(70900)
    assert metrics['adjusted_endpoint_pct'] == pytest.approx((70900 / 57500 - 1) * 100)


def test_crypto_excess_uses_only_excess_not_whole_month():
    tables, metrics = calculate(load_traffic())
    assert metrics['crypto_baseline'] == 10550
    assert metrics['crypto_excess'] == 14250
    assert metrics['crypto_excess_pct_of_november_total'] == pytest.approx(19)
    monthly = tables['monthly_calculations'].set_index('month')
    assert monthly.loc['2025-11', 'adjusted_without_crypto_excess'] == 60750
    assert monthly.loc['2026-08', 'adjusted_without_crypto_excess'] == pytest.approx(70900)


def test_sensitivity_and_newsletter_are_separate():
    tables, metrics = calculate(load_traffic())
    assert metrics['signup_endpoint_pct'] == pytest.approx((1140 / 820 - 1) * 100)
    assert set(tables['measurement_sensitivity'].assumed_organic_growth_pct.dropna()) == set(range(6))
    no_adjustment = tables['measurement_sensitivity'].query("scenario == 'no_adjustment'").iloc[0]
    assert no_adjustment.adjusted_endpoint_pct == pytest.approx(metrics['reported_endpoint_pct'])
    joint = tables['joint_period_sensitivity']
    assert set(joint.removed_fraction_of_estimated_excess) == {0, 0.5, 1}
    assert all(tables['monthly_calculations'].newsletter_signups == load_traffic().newsletter_signups)


def test_original_data_is_not_changed():
    data = load_traffic()
    before = data.copy(deep=True)
    calculate(data)
    pd.testing.assert_frame_equal(data, before)


def test_article_timeline_does_not_guess_relative_dates():
    articles = pd.read_csv(ROOT / 'outputs' / 'techi_articles.csv', dtype=str, keep_default_na=False)
    before = articles.copy(deep=True)
    dates = article_timeline(articles).set_index('section')
    assert dates.loc['Guides', 'latest_absolute_shown_date'] == '2026-09-22'
    assert dates.loc['Guides', 'earliest_absolute_shown_date'] == '2026-03-12'
    assert dates.loc['Markets', 'relative_date_rows'] == 13
    assert dates.loc['Markets', 'absolute_date_rows'] == 7
    pd.testing.assert_frame_equal(articles, before)


def test_monthly_and_section_adjustments_reconcile():
    tables, _ = calculate(load_traffic())
    monthly = tables['monthly_calculations'].set_index('month')
    section_totals = tables['section_monthly_calculations'].groupby('month').adjusted_without_crypto_excess.sum()
    for month in monthly.index:
        assert monthly.loc[month, 'adjusted_without_crypto_excess'] == pytest.approx(section_totals[month])
    january_february = monthly.loc['2026-02', 'recording_scale_difference']
    assert january_february == pytest.approx(29385)


def test_report_generation_preserves_both_inputs(tmp_path):
    traffic = tmp_path / 'traffic.csv'
    articles = tmp_path / 'articles.csv'
    traffic.write_bytes((ROOT / 'traffic_table.csv').read_bytes())
    articles.write_bytes((ROOT / 'outputs' / 'techi_articles.csv').read_bytes())
    before = traffic.read_bytes(), articles.read_bytes()
    output = tmp_path / 'results'
    run(traffic, output, articles)
    assert (traffic.read_bytes(), articles.read_bytes()) == before
    first_tables = {p.name: p.read_bytes() for p in output.glob('*.csv')}
    run(traffic, output, articles)
    assert first_tables == {p.name: p.read_bytes() for p in output.glob('*.csv')}
    assert 'year-on-year' in (output / 'report.md').read_text(encoding='utf-8')
    assert (traffic.read_bytes(), articles.read_bytes()) == before
