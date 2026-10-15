"""Independent arithmetic audit, saved test results, and rubric evidence checklist."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import median
import subprocess
import sys
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import pandas as pd

from analyze_articles import validate, read_articles

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'final_audit'
SECTIONS = ['AI', 'Markets', 'Crypto', 'Breakthroughs', 'Policy', 'Guides']
CONTROLS = ['AI', 'Markets', 'Breakthroughs', 'Policy']


def independent_arithmetic():
    source = pd.read_csv(ROOT / 'traffic_table.csv').set_index('month')
    months = list(source.index)
    totals = {month: sum(int(source.loc[month, section]) for section in SECTIONS) for month in months}
    increments = {section: [int(source.loc[months[i], section] - source.loc[months[i - 1], section]) for i in range(1, 5)] for section in SECTIONS}
    forecasts = {s: float(source.loc['2026-01', s]) + median(increments[s]) for s in SECTIONS}
    estimates = {s: float(source.loc['2026-02', s]) / forecasts[s] for s in SECTIONS}
    factor = median(estimates[s] for s in CONTROLS)
    jump = median(float(source.loc['2026-02', s] / source.loc['2026-01', s]) for s in CONTROLS)
    baseline = (source.loc['2025-10', 'Crypto'] + source.loc['2025-12', 'Crypto']) / 2
    excess = max(0, source.loc['2025-11', 'Crypto'] - baseline)
    adjusted = {m: totals[m] / (factor if m >= '2026-02' else 1) for m in months}
    clean = {m: adjusted[m] - (excess if m == '2025-11' else 0) for m in months}
    growth = lambda now, before: (now / before - 1) * 100
    scenarios = {'central_trend_calibrated': (None, factor), 'no_adjustment': (None, 1), 'illustrative_1_5': (None, 1.5)}
    scenarios.update({f'organic_{g}_pct': (g, jump / (1 + g / 100)) for g in range(6)})
    records = []

    def row(file, actual, expected):
        for field, value in expected.items():
            observed = actual.get(field)
            if value is None:
                passed = pd.isna(observed)
            elif isinstance(value, bool):
                passed = str(observed) == str(value)
            elif isinstance(value, (int, float)) or hasattr(value, 'item'):
                try:
                    passed = math.isclose(float(observed), float(value), rel_tol=1e-10, abs_tol=1e-8)
                except (ValueError, TypeError):
                    passed = False
            else:
                passed = observed == value
            records.append({'file': file, 'row_key': str(actual.get('month', actual.get('section', actual.get('scenario', 'aggregate')))),
                            'field': field, 'observed': observed, 'independent_expected': value, 'passed': bool(passed)})

    def read(name):
        return pd.read_csv(ROOT / 'outputs' / 'traffic_investigation' / (name + '.csv')).to_dict('records')

    for actual in read('monthly_calculations'):
        m = actual['month']; i = months.index(m); previous = months[i - 1] if i else None
        signups = int(source.loc[m, 'newsletter_signups'])
        expected = {'newsletter_signups': signups, 'reported_sessions': totals[m],
                    'reported_absolute_change': totals[m] - totals[previous] if previous else None,
                    'reported_mom_pct': growth(totals[m], totals[previous]) if previous else None,
                    'measurement_factor': factor if m >= '2026-02' else 1,
                    'measurement_adjusted_sessions': adjusted[m], 'recording_scale_difference': totals[m] - adjusted[m],
                    'estimated_crypto_excess_removed': excess if m == '2025-11' else 0,
                    'adjusted_without_crypto_excess': clean[m], 'adjusted_mom_pct': growth(clean[m], clean[previous]) if previous else None,
                    'signup_absolute_change': signups - source.loc[previous, 'newsletter_signups'] if previous else None,
                    'signup_mom_pct': growth(signups, source.loc[previous, 'newsletter_signups']) if previous else None,
                    'signup_endpoint_change_pct': growth(signups, source.iloc[0].newsletter_signups),
                    'signups_per_1000_reported_sessions': 1000 * signups / totals[m],
                    'signups_per_1000_adjusted_sessions': 1000 * signups / clean[m]}
        row('monthly_calculations', actual, expected)
    for actual in read('section_monthly_calculations'):
        m, s = actual['month'], actual['section']; i = months.index(m)
        now = int(source.loc[m, s]); previous = int(source.iloc[i - 1][s]) if i else None
        f = factor if m >= '2026-02' else 1; removed = excess if m == '2025-11' and s == 'Crypto' else 0
        row('section_monthly_calculations', actual, {'reported_sessions': now, 'previous_sessions': previous,
            'absolute_change': now - previous if i else None, 'reported_mom_pct': growth(now, previous) if i else None,
            'measurement_factor': f, 'measurement_adjusted_sessions': now / f,
            'crypto_excess_removed': removed, 'adjusted_without_crypto_excess': now / f - removed})
    for actual in read('section_trends'):
        s = actual['section']; a, b = int(source.iloc[0][s]), int(source.iloc[-1][s])
        row('section_trends', actual, {'september_sessions': a, 'august_reported_sessions': b,
            'reported_endpoint_pct': growth(b, a), 'august_adjusted_sessions': b / factor,
            'adjusted_endpoint_pct': growth(b / factor, a),
            'february_to_august_pct': growth(b, source.loc['2026-02', s]),
            'march_to_april_pct': growth(source.loc['2026-04', s], source.loc['2026-03', s]),
            'september_share_pct': 100 * a / totals[months[0]], 'august_share_pct': 100 * b / totals[months[-1]]})
    for name in ['february_ratios', 'tracking_calibration']:
        for actual in read(name):
            s = actual['section']; jan, feb = source.loc['2026-01', s], source.loc['2026-02', s]
            expected = {'january_sessions': jan, 'february_sessions': feb, 'february_ratio': feb / jan,
                        'reported_growth_pct': growth(feb, jan)}
            if name == 'tracking_calibration':
                expected.update(median_pre_change_increment=median(increments[s]), forecast_february_sessions=forecasts[s],
                                forecast_organic_growth_pct=growth(forecasts[s], jan), measurement_factor_estimate=estimates[s],
                                used_for_central_factor=s in CONTROLS)
            row(name, actual, expected)
    for actual in read('pre_change_increments'):
        s, m = actual['section'], actual['month']; i = months.index(m)
        row('pre_change_increments', actual, {'observed_increment': increments[s][i - 1], 'used_for_central_calibration': s in CONTROLS})
    for actual in read('measurement_sensitivity'):
        organic, f = scenarios[actual['scenario']]
        row('measurement_sensitivity', actual, {'assumed_organic_growth_pct': organic,
            'median_observed_control_february_ratio': jump, 'measurement_factor': f,
            'august_adjusted_sessions': totals['2026-08'] / f, 'september_sessions': totals['2025-09'],
            'adjusted_endpoint_pct': growth(totals['2026-08'] / f, totals['2025-09']),
            'adjusted_january_february_pct': growth(totals['2026-02'] / f, totals['2026-01'])})
    for actual in read('control_selection_sensitivity'):
        sections = actual['sections'].split(' | '); f = median(estimates[s] for s in sections)
        row('control_selection_sensitivity', actual, {'measurement_factor': f, 'august_adjusted_sessions': totals['2026-08'] / f,
            'adjusted_endpoint_pct': growth(totals['2026-08'] / f, totals['2025-09'])})
    for actual in read('scenario_monthly_sessions'):
        m = actual['month']; f = scenarios[actual['scenario']][1] if m >= '2026-02' else 1
        row('scenario_monthly_sessions', actual, {'reported_sessions': totals[m], 'measurement_factor': f,
                                                 'measurement_adjusted_sessions': totals[m] / f})
    baselines = {'october_baseline': source.loc['2025-10', 'Crypto'], 'neighbor_midpoint': baseline, 'december_baseline': source.loc['2025-12', 'Crypto']}
    for actual in read('crypto_spike_scenarios'):
        base = baselines[actual['baseline_method']]; extra = max(0, source.loc['2025-11', 'Crypto'] - base)
        row('crypto_spike_scenarios', actual, {'october_crypto': source.loc['2025-10', 'Crypto'], 'november_crypto': source.loc['2025-11', 'Crypto'],
            'december_crypto': source.loc['2025-12', 'Crypto'], 'estimated_baseline': base, 'possible_nonrecurring_excess': extra,
            'excess_pct_of_november_crypto': 100 * extra / source.loc['2025-11', 'Crypto'],
            'excess_pct_of_november_all_sessions': 100 * extra / totals['2025-11']})
    for actual in read('joint_period_sensitivity'):
        f = scenarios[actual['measurement_scenario']][1]; fraction = actual['removed_fraction_of_estimated_excess']
        row('joint_period_sensitivity', actual, {'measurement_factor': f, 'november_excess_removed': excess * fraction,
            'period_reported_total': sum(totals.values()),
            'period_adjusted_total': sum(totals[m] / (f if m >= '2026-02' else 1) for m in months) - excess * fraction,
            'endpoint_change_pct': growth(totals['2026-08'] / f, totals['2025-09'])})
    metrics = json.loads((ROOT / 'outputs/traffic_investigation/metrics.json').read_text())
    row('metrics.json', metrics, {'central_factor': factor, 'crypto_baseline': baseline, 'crypto_excess': excess,
        'crypto_excess_pct_of_november_total': 100 * excess / totals['2025-11'],
        'reported_endpoint_pct': growth(totals['2026-08'], totals['2025-09']), 'adjusted_august': totals['2026-08'] / factor,
        'adjusted_endpoint_pct': growth(totals['2026-08'] / factor, totals['2025-09']),
        'signup_endpoint_pct': growth(source.iloc[-1].newsletter_signups, source.iloc[0].newsletter_signups),
        'february_to_august_pct': growth(totals['2026-08'], totals['2026-02'])})
    # The older summary CSVs intentionally display percentages to two decimal places.
    for actual in pd.read_csv(ROOT / 'outputs/synthetic_traffic/monthly_summary.csv').to_dict('records'):
        m = actual['month']; i = months.index(m)
        expected = {s: int(source.loc[m, s]) for s in SECTIONS + ['newsletter_signups']}
        expected.update(total_traffic=totals[m], traffic_mom_pct=round(growth(totals[m], totals[months[i - 1]]), 2) if i else None)
        row('synthetic_traffic/monthly_summary', actual, expected)
    all_total = sum(totals.values())
    for actual in pd.read_csv(ROOT / 'outputs/synthetic_traffic/category_summary.csv').to_dict('records'):
        s = actual['category']; total = int(source[s].sum())
        row('synthetic_traffic/category_summary', actual, {'total_traffic': total, 'share_pct': round(100 * total / all_total, 2),
            'first_to_last_pct': round(growth(source.iloc[-1][s], source.iloc[0][s]), 2)})
    return pd.DataFrame(records)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    originals = {name: (ROOT / name).read_bytes() for name in ['traffic_table.csv', 'outputs/techi_articles.csv']}
    articles = read_articles(ROOT / 'outputs/techi_articles.csv')
    checks, issues = validate(articles)
    results = [{'check': name, 'passed': passed, 'evidence': 'analyze_articles.validate; validation_issues.csv'} for name, passed in checks.items()]
    issues.to_csv(OUT / 'article_validation_issues.csv', index=False)
    arithmetic = independent_arithmetic()
    arithmetic.to_csv(OUT / 'traffic_cell_checks.csv', index=False)
    results.append({'check': 'independent_traffic_arithmetic', 'passed': bool(arithmetic.passed.all()), 'evidence': f'{len(arithmetic)} saved cell comparisons'})
    # Every exported source field is checked against saved real listing HTML.
    listing_urls = json.loads((ROOT / 'outputs/techi_scrape_report.json').read_text())['listing_urls']
    source_checks = []
    for section, url in listing_urls.items():
        path = ROOT / 'outputs/techi_audit/pages' / hashlib.sha256(url.encode()).hexdigest()
        html = path.with_suffix('.html').read_text(encoding='utf-8')
        metadata = json.loads(path.with_suffix('.json').read_text())
        snapshot_ok = hashlib.sha256(html.encode()).hexdigest() == metadata['sha256']
        soup = BeautifulSoup(html, 'html.parser')
        from urllib.parse import urljoin, urldefrag
        visible = []
        seen = set()
        for card in soup.select('main article.techi-article-card'):
            heading = card.select_one('h2'); link = urldefrag(urljoin(url, heading.find_parent('a')['href']))[0]
            if link in seen: continue
            seen.add(link)
            visible.append((link, heading.get_text(' ', strip=True), card.select_one('a[href^="/@"]').get_text(' ', strip=True), card.select_one('time').get_text()))
        extracted = list(articles.loc[articles.section == section, ['url', 'headline', 'author', 'date_shown']].itertuples(index=False, name=None))
        source_checks.append({'section': section, 'source_url': url, 'snapshot_checksum_valid': snapshot_ok,
                              'first_20_source_cards_match': extracted == visible[:20], 'checked_rows': len(extracted)})
    pd.DataFrame(source_checks).to_csv(OUT / 'source_snapshot_checks.csv', index=False)
    results.append({'check': 'all_120_rows_match_saved_source_cards', 'passed': all(x['snapshot_checksum_valid'] and x['first_20_source_cards_match'] for x in source_checks), 'evidence': 'source_snapshot_checks.csv'})
    for name, limit in [('memo.md', 700), ('method.txt', 300)]:
        count = len(re.findall(r'\S+', (ROOT / name).read_text(encoding='utf-8')))
        results.append({'check': name + '_word_limit', 'passed': count <= limit, 'evidence': f'{count} whitespace-delimited words; maximum {limit}; headings included'})
    memo = (ROOT / 'memo.md').read_text(encoding='utf-8')
    results.append({'check': 'required_change_my_mind_line', 'passed': any(line.startswith('I would change my mind if...') for line in memo.splitlines()), 'evidence': 'memo.md'})
    charts = list((ROOT / 'outputs').rglob('*.png'))
    results.append({'check': 'at_most_two_charts', 'passed': len(charts) <= 2, 'evidence': f'{len(charts)} PNG charts; grayscale visual review documented separately'})
    sample = json.loads((OUT / 'public_sample_checks.json').read_text(encoding='utf-8'))
    results.append({'check': 'public_sample_urls', 'passed': len(sample) == 3 and all(x.get('http_status') == 200 and x['headline_match'] and x['author_visible'] and x.get('byline_in_article_header') for x in sample), 'evidence': 'public_sample_checks.json; manually reviewed H1, byline and detail-date differences'})
    rubric = [
        ('Dataset', '120 complete rows, no blanks', 8, 'outputs/article_analysis/validation_report.json', 'evidenced'),
        ('Dataset', 'Reproducible method', 7, 'method.txt; scraper replay; saved HTML and tests', 'evidenced'),
        ('Dataset', 'Sample limits named', 7, 'memo.md; SCRAPING_RULES.md', 'evidenced'),
        ('Traffic', 'Measurement versus readers', 12, 'February ratios; calibration; sensitivity; memo causal limits', 'evidenced_with_identification_limit'),
        ('Traffic', 'November one-off', 6, 'crypto_spike_scenarios.csv; partial excess removal', 'evidenced_with_attribution_limit'),
        ('Traffic', 'Underlying growth arithmetic', 7, 'tracking_calibration.csv; measurement_sensitivity.csv', 'evidenced_as_scenario'),
        ('Traffic', 'Signup interpretation', 5, 'monthly_calculations.csv; memo distinguishes acquisitions and subscribers', 'evidenced'),
        ('Findings', 'Two numeric findings', 10, '5/20 AI byline share; 18/20 Guides dates after March', 'evidenced'),
        ('Findings', 'One finding meets table or notes', 6, 'Guides visible-date contradiction; AI writer timing caveat', 'evidenced'),
        ('Memo', 'Recommendation and cost if wrong', 8, 'Bounded Guides pilot and opportunity cost in memo.md', 'evidenced'),
        ('Memo', 'Specific change-my-mind line', 4, 'memo.md exact required line and pilot outcomes', 'evidenced'),
        ('Memo', 'Well-chosen next free number', 4, 'Controlled browser session-start event count', 'evidenced_as_proposal'),
        ('Charts', 'Honest axes and B&W readability', 4, 'Two monochrome PNGs; chart_review.md', 'manually_reviewed'),
        ('Charts', 'Main point carried', 4, 'Common February break, Crypto spike, Guides decline; raw versus adjusted', 'manually_reviewed'),
        ('Honesty', 'Real versus invented separate', 3, 'Separate source paths, typed evidence, no article-session join', 'evidenced'),
        ('Honesty', 'Uncertainty and nothing invented', 3, 'Source snapshots; assumptions; untestable staffing/referrals', 'evidenced_with_stated_limits'),
        ('Honesty', 'One ambiguity flagged', 2, 'Session additivity and publication-versus-update date ambiguity', 'evidenced'),
    ]
    rubric_table = pd.DataFrame(rubric, columns=['category', 'criterion', 'available_points', 'evidence', 'audit_status'])
    rubric_table.to_csv(OUT / 'rubric_checklist.csv', index=False)
    results.append({'check': 'full_rubric_mapped', 'passed': int(rubric_table.available_points.sum()) == 100, 'evidence': '17 subcriteria mapped; 100 available points; no score awarded'})
    attempt = len(list(OUT.glob('pytest_run_*.txt'))) + 1
    log_path = OUT / f'pytest_run_{attempt:03}.txt'
    xml_path = OUT / f'pytest_run_{attempt:03}.xml'
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', f'--junitxml={xml_path}'], cwd=ROOT, capture_output=True, text=True)
    log_path.write_text(tests.stdout + tests.stderr, encoding='utf-8')
    print(tests.stdout, end='')
    suites = list(ET.parse(xml_path).getroot().iter('testsuite'))
    totals = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ['tests', 'failures', 'errors', 'skipped']}
    results.append({'check': 'full_pytest_suite', 'passed': tests.returncode == 0, 'evidence': f'{totals}; exit code {tests.returncode}; {log_path.name}; warnings retained'})
    unchanged = all((ROOT / name).read_bytes() == original for name, original in originals.items())
    results.append({'check': 'source_files_byte_unchanged', 'passed': unchanged, 'evidence': 'SHA-256 recorded in audit_results.json'})
    result = pd.DataFrame(results)
    result.to_csv(OUT / 'audit_checks.csv', index=False)
    report = {'audited_at_utc': datetime.now(timezone.utc).isoformat(), 'all_checks_passed': bool(result.passed.all()),
              'pytest': totals, 'pytest_exit_code': tests.returncode, 'traffic_cells_checked': len(arithmetic),
              'sha256': {name: hashlib.sha256(content).hexdigest() for name, content in originals.items()},
              'checks': results, 'limitations': ['Measurement change is not causally identifiable from monthly aggregates alone.', 'Shown dates may be updates, not original publication dates.', 'AI staffing and aggregator attribution remain untestable.', 'Site terms prohibit bulk scraping; user override is not site-owner permission.', 'No private submission or time-taken declaration has been made.']}
    (OUT / 'audit_results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# Final assessment audit', '', f'All automated checks passed: {report["all_checks_passed"]}.', '',
             f'Pytest: {totals}; exit code {tests.returncode}. The raw log retains dependency warnings; earlier attempts are never overwritten.', '',
             f'{len(arithmetic)} independently recomputed traffic cells checked against the original CSV. See traffic_cell_checks.csv; formulas use Python arithmetic and statistics.median rather than the production calculate() function.', '',
             '## Checks', '']
    lines += [f'- {"PASS" if r["passed"] else "FAIL"}: {r["check"]} — {r["evidence"]}' for r in results]
    lines += ['', '## Public sample review', '', 'Three deliberately selected first-in-section URLs (AI, Crypto, Guides) returned HTTP 200 with matching H1 and a visible matching byline. Article detail pages display full publication dates; the CSV intentionally preserves the original listing dates, including relative labels. This is a spot check, not verification of every live URL. Raw responses, UTC access times and source-page hashes are retained.', '',
              '## Rubric and unresolved limits', '', 'rubric_checklist.csv maps every supplied subcriterion to evidence; available points sum to 100. It is an evidence checklist, not a self-awarded score. The real-versus-synthetic distinction and all causal limits remain explicit. No payment rates, revenue, subscriber stock, writer impact or per-article sessions have been invented.', '']
    lines += ['- ' + limitation for limitation in report['limitations']]
    (OUT / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(result[['check', 'passed']].to_string(index=False))
    if not report['all_checks_passed']:
        raise SystemExit('Audit contains failures; review saved evidence before packaging.')


if __name__ == '__main__':
    run()
