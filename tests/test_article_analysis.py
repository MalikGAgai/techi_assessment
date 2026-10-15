from pathlib import Path

import pandas as pd
import pytest

from analyze_articles import validate, summarize, read_articles, run

SOURCE = Path(__file__).resolve().parents[1] / 'outputs' / 'techi_articles.csv'


def test_original_values_are_valid_and_overlaps_are_not_duplicates():
    data = read_articles(SOURCE)
    checks, issues = validate(data)
    assert all(checks.values())
    assert issues.empty
    assert data.url.nunique() == 109
    assert not data.duplicated(['section', 'url']).any()


@pytest.mark.parametrize('field,value,check', [
    ('headline_word_count', '999', 'headline_word_counts'),
    ('format', 'question', 'format_rules'),
    ('names_a_company', 'False', 'company_rules'),
    ('contains_a_number', 'False', 'number_rules'),
    ('author', '  ', 'no_blank_cells'),
    ('url', 'https://www.techi.com.evil.invalid/story/', 'valid_urls'),
    ('url', 'https://name:password@www.techi.com/story/', 'valid_urls'),
])
def test_bad_values_are_reported_without_repair(field, value, check):
    data = read_articles(SOURCE)
    data.loc[0, field] = value
    original = data.copy(deep=True)
    checks, issues = validate(data)
    assert not checks[check]
    assert not issues.empty
    pd.testing.assert_frame_equal(data, original)


def test_wrong_columns_and_short_input_report_failure():
    data = read_articles(SOURCE).drop(columns='author').iloc[:-1]
    checks, issues = validate(data)
    assert not checks['nine_columns_in_exact_order']
    assert not checks['exactly_120_rows']
    assert not issues.empty


def test_within_section_duplicates_are_errors():
    data = read_articles(SOURCE)
    data.loc[1, 'url'] = data.loc[0, 'url']
    checks, _ = validate(data)
    assert not checks['no_within_section_url_duplicates']


def test_summary_denominators_and_exact_date_strings():
    data = read_articles(SOURCE)
    before = data.copy(deep=True)
    tables = summarize(data)
    assert tables['section_summary']['n'].sum() == 120
    assert tables['format_distribution']['count'].sum() == 120
    assert tables['author_by_section']['count'].sum() == 120
    assert tables['shown_date_counts']['count'].sum() == 120
    assert set(tables['shown_date_counts']['date_shown']) == set(data.date_shown)
    assert tables['author_overall']['distinct_articles'].sum() == 109
    pd.testing.assert_frame_equal(data, before)


def test_report_run_preserves_source_and_is_reproducible(tmp_path):
    source = tmp_path / 'original.csv'
    original = SOURCE.read_bytes()
    source.write_bytes(original)
    output = tmp_path / 'analysis'
    assert run(source, output)
    first = {path.name: path.read_bytes() for path in output.iterdir()}
    assert source.read_bytes() == original
    assert run(source, output)
    assert first == {path.name: path.read_bytes() for path in output.iterdir()}
    assert source.read_bytes() == original


def test_output_collision_cannot_overwrite_input(tmp_path):
    source = tmp_path / 'section_summary.csv'
    source.write_bytes(SOURCE.read_bytes())
    original = source.read_bytes()
    with pytest.raises(ValueError, match='overwrite the input'):
        run(source, tmp_path)
    assert source.read_bytes() == original
