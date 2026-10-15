"""Assessment traffic investigation: explicit counterfactuals, not unique-reader estimates."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from analyze_articles import date_details, read_articles, validate as validate_articles
from validate_data import CATEGORIES, DEFAULT_INPUT, load_traffic

ROOT = Path(__file__).resolve().parent
CONTROLS = ['AI', 'Markets', 'Breakthroughs', 'Policy']
DEFAULT_ARTICLES = ROOT / 'outputs' / 'techi_articles.csv'
DEFAULT_OUTPUT = ROOT / 'outputs' / 'traffic_investigation'


def pct(current, previous):
    return (current / previous - 1) * 100


def calculate(data):
    indexed = data.set_index('month')
    required = ['2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-08']
    if not set(required).issubset(indexed.index):
        raise ValueError('This assessment investigation requires the supplied September 2025–August 2026 months')
    pre = indexed.loc['2025-09':'2026-01', CATEGORIES]
    increments = pre.diff().iloc[1:]
    increments.index.name = 'month'
    increment_table = increments.reset_index().melt(id_vars='month', var_name='section', value_name='observed_increment')
    increment_table['used_for_central_calibration'] = increment_table.section.isin(CONTROLS)
    jan, feb = indexed.loc['2026-01'], indexed.loc['2026-02']
    ratios = pd.DataFrame({'january_sessions': jan[CATEGORIES], 'february_sessions': feb[CATEGORIES]})
    ratios['february_ratio'] = ratios.february_sessions / ratios.january_sessions
    ratios['reported_growth_pct'] = (ratios.february_ratio - 1) * 100
    calibration = ratios.copy()
    calibration['median_pre_change_increment'] = increments.median()
    calibration['forecast_february_sessions'] = calibration.january_sessions + calibration.median_pre_change_increment
    calibration['forecast_organic_growth_pct'] = pct(calibration.forecast_february_sessions, calibration.january_sessions)
    calibration['measurement_factor_estimate'] = calibration.february_sessions / calibration.forecast_february_sessions
    calibration['used_for_central_factor'] = calibration.index.isin(CONTROLS)
    factor = float(calibration.loc[CONTROLS, 'measurement_factor_estimate'].median())
    ratios.index.name = calibration.index.name = 'section'

    october_crypto, november_crypto, december_crypto = indexed.loc[['2025-10', '2025-11', '2025-12'], 'Crypto']
    baseline = (october_crypto + december_crypto) / 2
    excess = max(0, november_crypto - baseline)
    crypto = []
    for name, estimate in [('october_baseline', october_crypto), ('neighbor_midpoint', baseline), ('december_baseline', december_crypto)]:
        possible_excess = max(0, november_crypto - estimate)
        crypto.append({'baseline_method': name, 'october_crypto': october_crypto, 'november_crypto': november_crypto,
                       'december_crypto': december_crypto, 'estimated_baseline': estimate,
                       'possible_nonrecurring_excess': possible_excess,
                       'excess_pct_of_november_crypto': possible_excess / november_crypto * 100,
                       'excess_pct_of_november_all_sessions': possible_excess / indexed.loc['2025-11', CATEGORIES].sum() * 100})

    monthly = data[['month', 'newsletter_signups']].copy()
    monthly['reported_sessions'] = data[CATEGORIES].sum(axis=1)
    monthly['reported_absolute_change'] = monthly.reported_sessions.diff()
    monthly['reported_mom_pct'] = monthly.reported_sessions.pct_change(fill_method=None) * 100
    monthly['measurement_factor'] = monthly.month.ge('2026-02').map({True: factor, False: 1.0})
    monthly['measurement_adjusted_sessions'] = monthly.reported_sessions / monthly.measurement_factor
    monthly['recording_scale_difference'] = monthly.reported_sessions - monthly.measurement_adjusted_sessions
    monthly['estimated_crypto_excess_removed'] = monthly.month.eq('2025-11').astype(int) * excess
    monthly['adjusted_without_crypto_excess'] = monthly.measurement_adjusted_sessions - monthly.estimated_crypto_excess_removed
    monthly['adjusted_mom_pct'] = monthly.adjusted_without_crypto_excess.pct_change(fill_method=None) * 100
    monthly['signup_absolute_change'] = monthly.newsletter_signups.diff()
    monthly['signup_mom_pct'] = monthly.newsletter_signups.pct_change(fill_method=None) * 100
    monthly['signup_endpoint_change_pct'] = pct(monthly.newsletter_signups, monthly.newsletter_signups.iloc[0])
    monthly['signups_per_1000_reported_sessions'] = 1000 * monthly.newsletter_signups / monthly.reported_sessions
    monthly['signups_per_1000_adjusted_sessions'] = 1000 * monthly.newsletter_signups / monthly.adjusted_without_crypto_excess
    first_total, last_total = monthly.reported_sessions.iloc[[0, -1]]

    median_control_jump = float(ratios.loc[CONTROLS, 'february_ratio'].median())
    scenarios = [('central_trend_calibrated', None, factor), ('no_adjustment', None, 1.0), ('illustrative_1_5', None, 1.5)]
    scenarios += [(f'organic_{growth}_pct', growth, median_control_jump / (1 + growth / 100)) for growth in range(6)]
    sensitivity, joint, scenario_months = [], [], []
    for label, growth, adjustment in scenarios:
        adjusted = monthly.reported_sessions / monthly.month.ge('2026-02').map({True: adjustment, False: 1.0})
        sensitivity.append({'scenario': label, 'assumed_organic_growth_pct': growth,
                            'median_observed_control_february_ratio': median_control_jump,
                            'measurement_factor': adjustment, 'august_adjusted_sessions': adjusted.iloc[-1],
                            'september_sessions': first_total, 'adjusted_endpoint_pct': pct(adjusted.iloc[-1], first_total),
                            'adjusted_january_february_pct': pct(adjusted.iloc[5], adjusted.iloc[4])})
        for fraction in [0, 0.5, 1]:
            corrected = adjusted - monthly.month.eq('2025-11').astype(int) * excess * fraction
            joint.append({'measurement_scenario': label, 'measurement_factor': adjustment,
                          'removed_fraction_of_estimated_excess': fraction,
                          'november_excess_removed': excess * fraction, 'period_reported_total': monthly.reported_sessions.sum(),
                          'period_adjusted_total': corrected.sum(), 'endpoint_change_pct': pct(corrected.iloc[-1], corrected.iloc[0])})
        scenario_months.extend({'scenario': label, 'month': month, 'reported_sessions': reported,
                                'measurement_factor': adjustment if month >= '2026-02' else 1,
                                'measurement_adjusted_sessions': value}
                               for month, reported, value in zip(monthly.month, monthly.reported_sessions, adjusted))

    control_sensitivity = []
    choices = [('central_four', CONTROLS), ('all_except_crypto', [c for c in CATEGORIES if c != 'Crypto']), ('all_six', CATEGORIES)]
    choices += [(f'exclude_{c}', [other for other in CONTROLS if other != c]) for c in CONTROLS]
    for label, sections in choices:
        estimate = float(calibration.loc[sections, 'measurement_factor_estimate'].median())
        control_sensitivity.append({'control_set': label, 'sections': ' | '.join(sections), 'measurement_factor': estimate,
                                    'august_adjusted_sessions': last_total / estimate,
                                    'adjusted_endpoint_pct': pct(last_total / estimate, first_total)})

    section_rows, long_rows = [], []
    for section in CATEGORIES:
        series = indexed[section]
        section_rows.append({'section': section, 'september_sessions': series.iloc[0], 'august_reported_sessions': series.iloc[-1],
                             'reported_endpoint_pct': pct(series.iloc[-1], series.iloc[0]),
                             'august_adjusted_sessions': series.iloc[-1] / factor,
                             'adjusted_endpoint_pct': pct(series.iloc[-1] / factor, series.iloc[0]),
                             'february_to_august_pct': pct(series.loc['2026-08'], series.loc['2026-02']),
                             'march_to_april_pct': pct(series.loc['2026-04'], series.loc['2026-03']),
                             'september_share_pct': series.iloc[0] / first_total * 100,
                             'august_share_pct': series.iloc[-1] / last_total * 100})
        for position, (month, value) in enumerate(series.items()):
            adjustment = factor if month >= '2026-02' else 1
            removed = excess if month == '2025-11' and section == 'Crypto' else 0
            previous = series.iloc[position - 1] if position else None
            long_rows.append({'month': month, 'section': section, 'reported_sessions': value,
                              'previous_sessions': previous, 'absolute_change': value - previous if position else None,
                              'reported_mom_pct': pct(value, previous) if previous else None,
                              'measurement_factor': adjustment, 'measurement_adjusted_sessions': value / adjustment,
                              'crypto_excess_removed': removed, 'adjusted_without_crypto_excess': value / adjustment - removed})

    metrics = {'central_factor': factor, 'crypto_baseline': baseline, 'crypto_excess': excess,
               'crypto_excess_pct_of_november_total': excess / indexed.loc['2025-11', CATEGORIES].sum() * 100,
               'reported_endpoint_pct': pct(last_total, first_total), 'adjusted_august': last_total / factor,
               'adjusted_endpoint_pct': pct(last_total / factor, first_total),
               'signup_endpoint_pct': pct(monthly.newsletter_signups.iloc[-1], monthly.newsletter_signups.iloc[0]),
               'february_to_august_pct': pct(monthly.reported_sessions.iloc[-1], monthly.reported_sessions.iloc[5])}
    tables = {'monthly_calculations': monthly, 'section_monthly_calculations': pd.DataFrame(long_rows),
              'section_trends': pd.DataFrame(section_rows), 'february_ratios': ratios.reset_index(),
              'pre_change_increments': increment_table, 'tracking_calibration': calibration.reset_index(),
              'measurement_sensitivity': pd.DataFrame(sensitivity), 'control_selection_sensitivity': pd.DataFrame(control_sensitivity),
              'scenario_monthly_sessions': pd.DataFrame(scenario_months), 'crypto_spike_scenarios': pd.DataFrame(crypto),
              'joint_period_sensitivity': pd.DataFrame(joint)}
    return tables, metrics


def article_timeline(articles):
    rows = []
    for section in CATEGORIES:
        group = articles.loc[articles.section == section]
        details = group.date_shown.map(date_details)
        absolute = [date for kind, date in details if kind == 'absolute']
        rows.append({'section': section, 'sample_n': len(group), 'absolute_date_rows': len(absolute),
                     'relative_date_rows': sum(kind == 'relative' for kind, _ in details),
                     'unrecognized_date_rows': sum(kind == 'unrecognized' for kind, _ in details),
                     'earliest_absolute_shown_date': min(absolute) if absolute else '',
                     'latest_absolute_shown_date': max(absolute) if absolute else '',
                     'absolute_dates_during_traffic_period': sum('2025-09-01' <= date <= '2026-08-31' for date in absolute),
                     'absolute_dates_after_traffic_period': sum(date > '2026-08-31' for date in absolute),
                     'absolute_dates_in_march_april_2026': sum('2026-03-01' <= date <= '2026-04-30' for date in absolute)})
    return pd.DataFrame(rows)


def write_report(tables, metrics, output):
    from analyze_articles import markdown_table
    m = tables['monthly_calculations'].set_index('month')
    trends = tables['section_trends'].set_index('section')
    organic = tables['measurement_sensitivity'].dropna(subset=['assumed_organic_growth_pct'])
    low, high = organic.adjusted_endpoint_pct.min(), organic.adjusted_endpoint_pct.max()
    factor = metrics['central_factor']
    lines = ['# Traffic investigation: reported sessions versus comparable measurement', '',
             'The CSV is synthetic assessment data. Tracking replacement and aggregator exposure are context supplied by the assignment, not facts independently established by the CSV. Sessions are not unique readers.', '',
             '## Reported growth', '',
             'Monthly sessions = AI + Markets + Crypto + Breakthroughs + Policy + Guides. Newsletter signups are excluded.', '']
    lines += markdown_table(tables['monthly_calculations'][['month', 'reported_sessions', 'reported_absolute_change', 'reported_mom_pct', 'newsletter_signups']].round(4))
    lines += ['', f'January–February: (94,685 / 64,000 − 1) × 100 = {m.loc["2026-02", "reported_mom_pct"]:.5f}%. '
              f'September–August: (102,805 / 57,500 − 1) × 100 = {metrics["reported_endpoint_pct"]:.5f}%.', '',
              'These are 12 monthly observations with 11 intervals between the endpoints. There is no August 2025 or September 2024 comparison, so a 30% year-on-year claim cannot be verified. A complete annual total for the previous year is also absent.', '',
              '## February: common measurement effect is plausible', '']
    lines += markdown_table(tables['february_ratios'].round(6))
    lines += ['', 'Each ratio = February section sessions / January section sessions. Five sections jump by approximately 47.5–49.1%; Guides jumps less. Their synchronization with the supplied tracking-change note supports a possible common recording effect, but cannot identify its size or prove that all growth is artificial.', '',
              'Central calibration uses AI, Markets, Breakthroughs and Policy. Crypto is excluded because of the known temporary spike and reversal; Guides is excluded because its traffic trend may differ. These are judgment-based calibration sections, not a randomized control group.', '',
              'For each calibration section: take the median of its four September–January monthly absolute increments; forecast February = January + that median increment; estimate the measurement multiplier = observed February / forecast February. Take the median of the four estimated multipliers.', '']
    lines += markdown_table(tables['tracking_calibration'].round(6))
    lines += ['', f'This produces a multiplier of {factor:.8f}, rather than assuming 1.5. Divide only February–August sessions by this multiplier to express them on the earlier measurement scale. Earlier months and all newsletter counts remain unscaled. This assumes the break began in February, was multiplicative, persisted unchanged, and affected all six sections equally.', '',
              f'Central estimate: August comparable sessions = 102,805 / {factor:.8f} = {metrics["adjusted_august"]:,.2f}. '
              f'Underlying-session endpoint change = ({metrics["adjusted_august"]:,.2f} / 57,500 − 1) × 100 = {metrics["adjusted_endpoint_pct"]:.5f}%. '
              f'Adjusted February = {m.loc["2026-02", "measurement_adjusted_sessions"]:,.2f}; adjusted January–February growth = '
              f'{pct(m.loc["2026-02", "measurement_adjusted_sessions"], m.loc["2026-01", "reported_sessions"]):.5f}%.', '',
              'This is an assumption-dependent estimate of comparable sessions, not an identified causal effect or a count of additional readers. A tracking audit or simultaneous old/new measurement is needed to validate the multiplier.', '',
              '## Measurement sensitivity', '',
              'Alternative factors = median observed February/January ratio among the four calibration sections / (1 + assumed organic monthly growth). The 0–5% organic-growth range brackets their observed pre-change monthly growth but is an illustrative assumption range, not a confidence interval. It does not cover every plausible explanation. No-adjustment and a simple 1.5 multiplier are shown separately.', '']
    lines += markdown_table(tables['measurement_sensitivity'].fillna('').round(6))
    lines += ['', f'The 0–5% scenarios give endpoint comparable-session changes from {low:.2f}% to {high:.2f}%. '
              'This range excludes the separate no-adjustment scenario. Control-selection sensitivity includes leave-one-out, all non-Crypto, and all-six calculations; similar factors in those checks do not eliminate model uncertainty.', '',
              '## November Crypto: a temporary excess, not a whole month to discard', '',
              f'Observed Crypto: October 10,100; November 24,800; December 11,000. Central baseline = (10,100 + 11,000) / 2 = {metrics["crypto_baseline"]:,.0f}. '
              f'Possible non-recurring excess = max(0, 24,800 − {metrics["crypto_baseline"]:,.0f}) = {metrics["crypto_excess"]:,.0f}; '
              f'{metrics["crypto_excess"] / 24800 * 100:.2f}% of November Crypto and {metrics["crypto_excess_pct_of_november_total"]:.2f}% of November total sessions.', '']
    lines += markdown_table(tables['crypto_spike_scenarios'].round(4))
    lines += ['', 'Using October or December alone gives a possible excess of 14,700 or 13,800, respectively. The assignment note is consistent with a transient aggregator effect, but the monthly file cannot attribute individual sessions to it or measure retention. The midpoint is a local counterfactual assuming a roughly smooth neighboring trend, not a verified organic baseline.', '',
              f'Central de-spiked November total = 75,000 − 14,250 = {m.loc["2025-11", "adjusted_without_crypto_excess"]:,.0f}. '
              'November precedes the measurement break and is not divided by the February factor. Removing November excess changes period totals and apparent volatility, but has no effect on September–August endpoint growth.', '',
              'Joint sensitivity retains 100%, 50%, or 0% of the estimated excess (removing 0%, 50%, or 100%) for every measurement scenario. Period totals sum the corrected monthly figures; they are not unique-reader totals or year-on-year comparisons.', '',
              '## Newsletter: distinguish monthly acquisition from subscriber stock', '',
              f'Monthly signups increase from 820 to 1,140: (1,140 / 820 − 1) × 100 = {metrics["signup_endpoint_pct"]:.5f}%. '
              f'The file sums to {int(m.newsletter_signups.sum()):,} signups over the 12 months, not that many retained or unique subscribers. Opening subscribers, duplicates, unsubscribes, delivery and engagement are unknown.', '',
              f'Signups per 1,000 reported sessions = 1,000 × signups / reported sessions: September {m.loc["2025-09", "signups_per_1000_reported_sessions"]:.4f}, '
              f'August {m.loc["2026-08", "signups_per_1000_reported_sessions"]:.4f}. With the central comparable-session denominator: '
              f'August {m.loc["2026-08", "signups_per_1000_adjusted_sessions"]:.4f}. These are aggregate intensity ratios, not user-level conversion rates.', '',
              'The apparent signup/session divergence partly depends on the session measurement scale. Signups grow faster than the centrally adjusted endpoint sessions, so the raw divergence alone does not establish worsening conversion. Assume signup measurement itself is stable; verify it separately. Newsletter advertising should be evaluated using verified active, consented subscribers, delivered mail and engagement, not sessions or gross monthly acquisitions alone.', '',
              '## Guides recommendation', '']
    lines += markdown_table(tables['section_trends'].round(5))
    lines += ['', f'Guides falls from 4,100 to 725 reported sessions ({trends.loc["Guides", "reported_endpoint_pct"]:.2f}%). '
              f'On the central comparable scale, August is {trends.loc["Guides", "august_adjusted_sessions"]:,.0f} versus September 4,100 '
              f'({trends.loc["Guides", "adjusted_endpoint_pct"]:.2f}%). March–April falls from 4,930 to 2,175 '
              f'({trends.loc["Guides", "march_to_april_pct"]:.2f}%). February–August falls {trends.loc["Guides", "february_to_august_pct"]:.2f}%, '
              'a comparison unaffected by a constant post-February multiplier. The common measurement adjustment therefore does not explain away the section decline.', '',
              'Do not close Guides solely on this file. Prioritize a section-level audit around March–April: tracking coverage, URL/category mappings, redirects, search indexing, referrals and article-level landings. Check editorial history and refresh a small set of useful evergreen guides; assess that pilot with consistent measurement, engagement and newsletter acquisition. This file lacks costs, search impressions, reader cohorts and section-specific signups, so it cannot establish the cause, profitability or newsletter value of Guides.', '',
              f'Overall February–August growth is {metrics["february_to_august_pct"]:.5f}% under either raw sessions or a constant common multiplier. That is evidence of growth within the post-change recording regime, not proof of unique-reader growth.', '',
              '## October article snapshot versus the traffic timeline', '']
    if 'article_timeline' in tables:
        lines += markdown_table(tables['article_timeline'])
        lines += ['', 'The 20 Guides headlines have absolute shown dates from March 12 to September 22, 2026. AI reaches October 6; Markets, Crypto and Breakthroughs also have relative date labels, which are left unconverted. The Guides sample reaches farther back than several others. This is consistent with a thinner recent visible selection, not a quantified historical publication rate.', '',
                  'Traffic ends August 2026; collection occurred in October. September/October articles cannot explain traffic in March/April. Even older sampled article dates are a truncated sample of visible listings, not a complete publishing calendar, and dates can reflect site migration or updates. The evidence does not establish that Guides stopped publishing in March/April. Verify archived editorial records and URL-level traffic before making that claim. Section headline-format, company and number patterns are descriptive and cannot be assigned a traffic effect from these data.', '',
                  'The article timeline counts exact absolute shown dates within the traffic interval and after it; relative strings are counted separately and never guessed into dates. The two datasets are compared by section for context, not joined to manufacture article-level session figures.']
    else:
        lines += ['', 'Article input unavailable; no article-timeline claims were generated.']
    lines += ['', '## Reproduction and formula index', '',
              '- Run `python investigate_traffic.py` or `python analyze_traffic.py`. No live website requests are made.',
              '- monthly_calculations.csv: total = sum of six sections; absolute change = current − previous; percentage change = (current / previous − 1) × 100. First-month changes are undefined and blank.',
              '- section_monthly_calculations.csv: the same calculations per section; adjusted = reported / applicable multiplier − any November Crypto excess removed. Raw inputs are retained alongside derived estimates.',
              '- section_trends.csv: endpoint, February–August and March–April growth use the same percentage formula; shares = section sessions / all-section total × 100. A common within-month multiplier leaves shares unchanged.',
              '- pre_change_increments.csv and tracking_calibration.csv contain every observed increment, forecast and per-section multiplier used by the central method. The median of four values averages the middle two.',
              '- measurement_sensitivity.csv, control_selection_sensitivity.csv and scenario_monthly_sessions.csv retain alternative assumptions and all adjusted monthly values. joint_period_sensitivity.csv sums each scenario with three fractions of estimated November excess removed.',
              '- crypto_spike_scenarios.csv retains all three baselines, excess amounts and exact denominators.',
              '- article_timeline.csv is a section-level summary of saved visible date strings; it does not use dates inferred from headlines. Original date strings remain in the source article CSV.',
              '- metrics.json and provenance.json record headline metrics, assumptions and original input SHA-256 values. CSV calculations retain floating-point precision; displayed report values are rounded only for readability.',
              '- Neither source CSV is rewritten. The tracking and aggregator notes remain assumptions supplied by the assessment, not independently verified facts.', '']
    (output / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def run(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT, articles_path=DEFAULT_ARTICLES):
    input_path, output = Path(input_path), Path(output_dir)
    original = input_path.read_bytes()
    tables, metrics = calculate(load_traffic(input_path))
    article_original = None
    if articles_path is not None and Path(articles_path).exists():
        article_original = Path(articles_path).read_bytes()
        articles = read_articles(articles_path)
        checks, _ = validate_articles(articles)
        if not all(checks.values()):
            raise ValueError('Article CSV failed validation; do not draw timeline conclusions from it')
        tables['article_timeline'] = article_timeline(articles)
    output.mkdir(parents=True, exist_ok=True)
    artifact_names = [name + '.csv' for name in tables] + ['metrics.json', 'provenance.json', 'report.md', 'measurement_and_newsletter.png']
    sources = [input_path] + ([Path(articles_path)] if article_original is not None else [])
    if any(source.resolve() == (output / name).resolve() for source in sources for name in artifact_names):
        raise ValueError('Output would overwrite the source CSV')
    for name, table in tables.items():
        table.to_csv(output / (name + '.csv'), index=False)
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    write_report(tables, metrics, output)
    if input_path.read_bytes() != original or (article_original is not None and Path(articles_path).read_bytes() != article_original):
        raise ValueError('An input changed during the analysis')
    provenance = {'traffic_sha256': hashlib.sha256(original).hexdigest(),
                  'articles_sha256': hashlib.sha256(article_original).hexdigest() if article_original else None,
                  'input_files_unchanged': True, 'central_control_sections': CONTROLS,
                  'post_change_start': '2026-02', 'organic_sensitivity_pct': list(range(6)),
                  'crypto_excess_removal_fractions': [0, 0.5, 1],
                  'context_source': 'User-supplied assessment notes; not independent tracking/referral evidence'}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    monthly = tables['monthly_calculations']
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for column, label, style, marker in [('reported_sessions', 'Reported sessions', '-', 'o'), ('adjusted_without_crypto_excess', 'Central scenario: comparable sessions, November excess removed', '--', 's')]:
        axes[0].plot(monthly.month, monthly[column], color='black', linestyle=style, marker=marker, label=label)
    axes[0].set(ylabel='Sessions / estimated comparable sessions', title='Synthetic assessment: reported traffic and assumption-based adjustment')
    axes[0].legend(fontsize=8)
    for column, label, style, marker in [('reported_sessions', 'Reported sessions', '-', 'o'), ('adjusted_without_crypto_excess', 'Central comparable-session scenario', '--', 's'), ('newsletter_signups', 'Monthly newsletter signups', ':', '^')]:
        axes[1].plot(monthly.month, monthly[column] / monthly[column].iloc[0] * 100, color='black', linestyle=style, marker=marker, label=label)
    axes[1].set(ylabel='September 2025 = 100', xlabel='Month')
    axes[1].legend(fontsize=8)
    axes[1].tick_params(axis='x', rotation=45)
    fig.tight_layout()
    fig.savefig(output / 'measurement_and_newsletter.png', dpi=150)
    plt.close(fig)
    print(f'Reported endpoint growth: {metrics["reported_endpoint_pct"]:.5f}%')
    print(f'Central multiplier: {metrics["central_factor"]:.8f}; comparable-session endpoint change: {metrics["adjusted_endpoint_pct"]:.5f}%')
    print(f'Monthly signup endpoint change: {metrics["signup_endpoint_pct"]:.5f}%')
    print(f'Inputs unchanged. Saved report and calculations to {output}')
    return tables, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--articles', type=Path, default=DEFAULT_ARTICLES)
    args = parser.parse_args()
    try:
        run(args.input, args.output_dir, args.articles)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Investigation failed: {error}\n')


if __name__ == '__main__':
    main()
