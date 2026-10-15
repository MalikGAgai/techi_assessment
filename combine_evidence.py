"""Compare real article observations and synthetic traffic without assigning article-level sessions."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from analyze_articles import date_details, read_articles, validate
from investigate_traffic import article_timeline, calculate
from validate_data import DEFAULT_INPUT, load_traffic

ROOT = Path(__file__).resolve().parent
ARTICLES = ROOT / 'outputs' / 'techi_articles.csv'
OUTPUT = ROOT / 'outputs' / 'combined_evidence'


def build_evidence(articles, traffic):
    timeline = article_timeline(articles).set_index('section')
    ai = articles.loc[articles.section == 'AI']
    counts = ai.author.value_counts()
    leader_count = int(counts.max())
    leaders = ' | '.join(sorted(counts.index[counts.eq(leader_count)]))
    guides_n = int(timeline.loc['Guides', 'sample_n'])
    during = int(timeline.loc['Guides', 'absolute_dates_during_traffic_period'])
    after_march = sum(kind == 'absolute' and date >= '2026-04-01' for kind, date in articles.loc[articles.section == 'Guides', 'date_shown'].map(date_details))
    findings = pd.DataFrame([
        {'finding_id': 1, 'source_type': 'real_article_sample', 'section': 'AI',
         'observation': f'Largest visible AI byline count: {leaders}',
         'numerator': leader_count, 'denominator': len(ai), 'percentage': 100 * leader_count / len(ai),
         'formula': f'{leader_count} / {len(ai)} * 100',
         'selection_rule': 'Filter section=AI; group exact author labels; take largest count; retain tied leaders',
         'note_connection': 'AI writer note: tests the sampled byline distribution, not historical employment or impact'},
        {'finding_id': 2, 'source_type': 'real_article_sample', 'section': 'Guides',
         'observation': 'Guides rows with an explicit shown date after March 2026',
         'numerator': after_march, 'denominator': guides_n, 'percentage': 100 * after_march / guides_n,
         'formula': f'{after_march} / {guides_n} * 100',
         'selection_rule': 'Filter section=Guides; count explicit absolute shown dates on or after 2026-04-01',
         'note_connection': 'Challenges the almost-nothing-since-March note on visible dates; does not measure a historical publishing rate'},
    ])
    notes = pd.DataFrame([
        {'note': 'AI writer', 'status': 'untestable',
         'scope': 'A second AI writer joined September 2025: historical staffing and causal traffic impact cannot be tested from this October sample',
         'verified_evidence': f'{len(ai)} AI rows have {ai.author.nunique()} distinct byline labels; largest count is {leader_count}',
         'missing_evidence': 'Named writer and tenure evidence; contemporaneous historical bylines; article-level traffic; tracking-consistent comparison'},
        {'note': 'A November Crypto article received temporary aggregator exposure', 'status': 'untestable',
         'scope': 'Article identity, referral source and causal attribution; the section-level spike is separately observable in the synthetic file',
         'verified_evidence': 'Synthetic Crypto sessions: October 10100, November 24800, December 11000; no November 2025 article in this recent Crypto sample',
         'missing_evidence': 'November 2025 article URL; contemporaneous referral/landing-page logs; source-tagged sessions; subsequent retention'},
        {'note': 'Guides has published almost nothing since March 2026', 'status': 'contradicted_on_visible_dates',
         'scope': 'Visible dates challenge blanket inactivity; original publication dates, reduced historical rate and causation remain untestable',
         'verified_evidence': 'Synthetic Guides sessions fall in March–April; sampled Guides shown dates extend farther back than sampled AI dates',
         'missing_evidence': 'Complete historical publication and revision calendar; category changes; URL-level landings; search and referral data'},
    ])
    tables, metrics = calculate(traffic)
    guides_trend = tables['section_trends'].set_index('section').loc['Guides']
    crypto = articles.loc[articles.section == 'Crypto']
    crypto_dates = crypto.date_shown.map(date_details)
    facts = {'ai_leading_byline': leaders, 'ai_byline_labels': int(ai.author.nunique()),
             'ai_rows_after_traffic_end': int(timeline.loc['AI', 'absolute_dates_after_traffic_period']),
             'guides_after_march': after_march, 'guides_during_traffic': during,
             'guides_after_traffic_end': int(timeline.loc['Guides', 'absolute_dates_after_traffic_period']),
             'guides_earliest_date': timeline.loc['Guides', 'earliest_absolute_shown_date'],
             'guides_latest_date': timeline.loc['Guides', 'latest_absolute_shown_date'],
             'ai_earliest_date': timeline.loc['AI', 'earliest_absolute_shown_date'],
             'ai_latest_date': timeline.loc['AI', 'latest_absolute_shown_date'],
             'crypto_rows_from_november_2025': sum(kind == 'absolute' and date.startswith('2025-11') for kind, date in crypto_dates),
             'crypto_earliest_absolute_date': timeline.loc['Crypto', 'earliest_absolute_shown_date'],
             'crypto_relative_date_rows': int(timeline.loc['Crypto', 'relative_date_rows']),
             'guides_march_sessions': int(traffic.set_index('month').loc['2026-03', 'Guides']),
             'guides_april_sessions': int(traffic.set_index('month').loc['2026-04', 'Guides']),
             'guides_march_april_pct': float(guides_trend.march_to_april_pct),
             'crypto_baseline_estimate': metrics['crypto_baseline'], 'crypto_excess_estimate': metrics['crypto_excess'],
             'central_measurement_factor': metrics['central_factor'],
             'central_comparable_session_endpoint_pct': metrics['adjusted_endpoint_pct'],
             'article_rows': len(articles), 'distinct_article_urls': articles.url.nunique()}
    return findings, notes, facts


def run(articles_path=ARTICLES, traffic_path=DEFAULT_INPUT, output_dir=OUTPUT):
    articles_path, traffic_path, output = Path(articles_path), Path(traffic_path), Path(output_dir)
    originals = {path: path.read_bytes() for path in [articles_path, traffic_path]}
    artifacts = ['report.md', 'quantified_article_findings.csv', 'assessment_notes.csv', 'article_timeline.csv', 'provenance.json']
    if any(source.resolve() == (output / name).resolve() for source in originals for name in artifacts):
        raise ValueError('Output would overwrite a source')
    articles = read_articles(articles_path)
    checks, _ = validate(articles)
    if not all(checks.values()):
        raise ValueError('Article validation failed; source values will not be repaired')
    findings, notes, facts = build_evidence(articles, load_traffic(traffic_path))
    output.mkdir(parents=True, exist_ok=True)
    findings.to_csv(output / 'quantified_article_findings.csv', index=False)
    notes.to_csv(output / 'assessment_notes.csv', index=False)
    article_timeline(articles).to_csv(output / 'article_timeline.csv', index=False)
    first, second = findings.iloc[0], findings.iloc[1]
    report = f'''# Combined assessment: real articles and synthetic traffic

## Evidence boundaries

**Real public article sample:** {facts['article_rows']} article-section rows collected in October 2026, with 20 per section and {facts['distinct_article_urls']} distinct URLs. Headlines, bylines and shown dates describe the saved public listings at access time. They are not independent verification of the events reported in the stories.

**Synthetic assessment traffic:** monthly section sessions and newsletter signups from September 2025 through August 2026. Calculations verify the numbers in the supplied invented dataset, not actual TECHi analytics. Context about staffing, tracking and referrals is an assessment note, not independently measured evidence.

The sources are compared side by side. They have no supplied article-to-session key; no sessions or signups are assigned to individual sampled articles, writers or formats.

## Two quantified findings from the article rows

1. **AI byline concentration:** {facts['ai_leading_byline']} has the largest visible byline count: **{int(first.numerator)}/{int(first.denominator)} × 100 = {first.percentage:.2f}%**. There are {facts['ai_byline_labels']} distinct AI byline labels. Calculation: filter AI rows, group exact extracted author labels, count rows and select the largest group. This is a contribution share within the recent sample, not a traffic share or a measure of writer productivity. It connects to the AI writer note, but cannot establish who was employed historically, when they joined, or whether they caused a traffic change. All {facts['ai_rows_after_traffic_end']}/20 AI rows have explicit shown dates after August 2026, so they do not overlap the traffic period.

2. **Guides date mix:** **{int(second.numerator)}/{int(second.denominator)} × 100 = {second.percentage:.2f}%** of sampled Guides rows have explicit shown dates within September 1, 2025–August 31, 2026. Of these, {facts['guides_after_march'] - facts['guides_after_traffic_end']}/20 are dated April?August and {facts['guides_after_traffic_end']}/20 are dated after the traffic period. Guides' visible dates span {facts['guides_earliest_date']} to {facts['guides_latest_date']}, versus AI's {facts['ai_earliest_date']} to {facts['ai_latest_date']}. Calculation: filter Guides rows, parse only explicit absolute shown dates and count those on or after April 1, 2026. This challenges the assessment's 'almost nothing since Mar 2026' note on visible dates. It does not quantify a change in historical publishing frequency or establish the cause of the synthetic traffic decline.

These percentages use all 20 rows in the relevant section, not 120 pooled rows or the 109-URL denominator. Both findings have exact source-row selection rules in quantified_article_findings.csv.

## Assessment notes: verified, contradicted or untestable?

**Verified** means directly observable within the stated dataset and scope. **Contradicted** means directly inconsistent with that evidence, not merely unsupported. **Untestable** means the required identity, period, measurement or causal evidence is absent. Consistency is not verification; lack of evidence is not contradiction.

| Assessment note | Verdict on the note | What the available data establish |
| --- | --- | --- |
| A second AI writer joined September 2025 | Untestable historical staffing and impact | The recent AI sample has eight bylines and a largest byline share of 5/20. It cannot establish hiring, a departure or causal traffic impact. |
| November Crypto article gained temporary aggregator exposure | Untestable attribution; consistent with the synthetic pattern | Crypto sessions rise from 10,100 to 24,800 then fall to 11,000. The spike exists in the invented table, but it does not identify an article or an aggregator. |
| Guides has published almost nothing since March 2026 | Contradicted as a blanket inactivity claim on visible dates; historical rate and causation remain untestable | Guides sessions fall from {facts['guides_march_sessions']:,} in March to {facts['guides_april_sessions']:,} in April: ({facts['guides_april_sessions']:,}/{facts['guides_march_sessions']:,} − 1) × 100 = {facts['guides_march_april_pct']:.2f}%. The October Guides sample reaches farther back than AI's. Eighteen of 20 Guides shown dates are after March, including 15 in April?August. This challenges inactivity but does not establish a complete monthly count or reduced rate. |

**Verified:** the byline/date observations are verified in the real sample; the spike and decline are verified only as patterns in the synthetic file. **Contradicted on visible dates:** the Guides inactivity note is challenged by 18 post-March rows, with publication-versus-update ambiguity retained. **Untestable:** the AI hiring event, Crypto article attribution, historical publishing-rate change and all proposed traffic causes. Multiple recent AI bylines do not disprove hiring a second writer in September 2025.

The Crypto sample has {facts['crypto_rows_from_november_2025']}/20 rows with an explicit November 2025 shown date; its earliest absolute shown date is {facts['crypto_earliest_absolute_date']}, and {facts['crypto_relative_date_rows']} row has a recent relative label at October access time. Thus it cannot identify or inspect the alleged November article. This is an evidence-coverage gap, not a contradiction of the note.

## How the traffic calculations inform the evaluation

The Crypto midpoint counterfactual is (10,100 + 11,000)/2 = {facts['crypto_baseline_estimate']:,.0f}. The possible November excess is 24,800 − {facts['crypto_baseline_estimate']:,.0f} = {facts['crypto_excess_estimate']:,.0f}. This is an estimate under a smooth-neighboring-baseline assumption, not measured aggregator sessions or a per-article count. It cannot be attached to any of the October-sampled articles. See outputs/traffic_investigation/crypto_spike_scenarios.csv for alternative baselines.

The synthetic February jump occurs across sections. The trend-calibrated common measurement factor is {facts['central_measurement_factor']:.2f}, yielding {facts['central_comparable_session_endpoint_pct']:.2f}% September–August comparable-session growth under that model. It does not identify an AI writer effect or extra unique readers. A constant post-February multiplier cancels in Guides' March–April ratio, so that decline remains within the same assumed recording regime. A section-specific tracking problem, referral change or search loss remains possible. Sensitivity assumptions and every traffic calculation are saved separately in outputs/traffic_investigation/.

## Timing and sample limitations

- Traffic ends August 31, 2026; article collection occurs in October 2026. September/October rows cannot measure or explain March/April output or November 2025 traffic.
- These are the newest 20 visible articles per section, not random samples or complete historical publication calendars. Equal sample sizes span unequal periods. Do not divide 20 by those spans to infer historical publication rates or a change in rates.
- Even the 17 Guides rows with dates in the traffic period are a selected subset, not evidence of complete monthly output. The absence of a date or writer from the recent 20 does not prove that no article existed or that someone stopped writing.
- Shown dates are preserved as displayed and are not independently verified original publication dates. Updates, migrations, taxonomy changes, removed pages and listing rules could affect what is visible. Relative date labels are not guessed into exact dates.
- Cross-listed articles remain once per section. Overall pooled row statistics would count some URLs more than once; section findings use the section's own 20 distinct URLs. A byline is a visible label, not proof of an employment contract, workload, or writing process.
- Headline word counts, formats and company/number flags follow deterministic documented rules. Their presence cannot establish readership, quality, engagement, or causation. The company dictionary is incomplete and format labels are headline patterns, not verified editorial genres.
- Monthly aggregate sessions contain no unique-reader identifiers, article-level landings, referral attribution, staff timeline or editorial history. The traffic values are synthetic and cannot corroborate real-world historical events. Newsletter signups are monthly acquisitions, not the active subscriber stock.
- A before/after association is not a causal test. Tracking adjustments and the Crypto baseline are assumption-dependent scenarios, not recovered ground truth. The file also lacks prior-year comparison months, so it cannot verify a 30% YoY claim.

## What would resolve the notes

Obtain a dated staffing/byline history identifying the second AI writer; the November 2025 Crypto URL with contemporaneous referral and landing-page records; and a complete Guides publication/revision calendar covering the relevant months. Compare these with tracking-consistent URL-level analytics, accounting for category changes and other traffic sources. Treat visible-date contradictions separately from the untestable historical-rate and causal claims. The advertising and subscriber-pricing notes are commercial premises supplied by the assessment, not independently verified rates or revenue measurements.

Reproduce with `python combine_evidence.py`. This script validates the article CSV, recalculates traffic context from the original CSV and never fetches the site or rewrites either source. Source hashes are recorded in provenance.json.
'''
    (output / 'report.md').write_text(report, encoding='utf-8')
    if any(path.read_bytes() != before for path, before in originals.items()):
        raise ValueError('A source changed during report generation')
    provenance = {'input_sha256': {str(path): hashlib.sha256(before).hexdigest() for path, before in originals.items()},
                  'sources_unchanged': True, 'article_source_type': 'real_public_listing_sample',
                  'traffic_source_type': 'synthetic_assessment', 'article_to_session_join_performed': False}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(findings[['section', 'numerator', 'denominator', 'percentage']].to_string(index=False))
    print('Note verdicts: AI hiring and Crypto attribution untestable; Guides inactivity contradicted on visible dates, with timing qualifications.')
    print(f'Sources unchanged. Saved combined report to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--articles', type=Path, default=ARTICLES)
    parser.add_argument('--traffic', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        run(args.articles, args.traffic, args.output_dir)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Report failed: {error}\n')
