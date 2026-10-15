from pathlib import Path

import pandas as pd

from combine_evidence import build_evidence, run
from validate_data import load_traffic

ROOT = Path(__file__).resolve().parents[1]


def test_findings_have_exact_observed_numerators_and_denominators():
    articles = pd.read_csv(ROOT / 'outputs/techi_articles.csv', dtype=str, keep_default_na=False)
    findings, notes, facts = build_evidence(articles, load_traffic())
    assert list(findings.numerator) == [5, 18]
    assert list(findings.denominator) == [20, 20]
    assert list(findings.percentage) == [25, 90]
    assert set(findings.source_type) == {'real_article_sample'}
    assert facts['ai_byline_labels'] == 8
    assert facts['ai_rows_after_traffic_end'] == 20
    assert facts['crypto_rows_from_november_2025'] == 0
    assert set(notes.status) == {'untestable', 'contradicted_on_visible_dates'}


def test_generation_keeps_both_source_files_unchanged(tmp_path):
    source_articles = ROOT / 'outputs/techi_articles.csv'
    source_traffic = ROOT / 'traffic_table.csv'
    before = source_articles.read_bytes(), source_traffic.read_bytes()
    run(output_dir=tmp_path)
    assert (source_articles.read_bytes(), source_traffic.read_bytes()) == before
    assert (tmp_path / 'report.md').exists()
    assert len(pd.read_csv(tmp_path / 'quantified_article_findings.csv')) == 2
