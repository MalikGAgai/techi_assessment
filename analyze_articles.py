"""Validate and summarize the extracted CSV offline, without rewriting it."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import pandas as pd

from scrape_articles import COLUMNS, SECTIONS, headline_features

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / 'outputs' / 'techi_articles.csv'
DEFAULT_OUTPUT = ROOT / 'outputs' / 'article_analysis'
FORMATS = ['how_to', 'question', 'listicle', 'review', 'explainer', 'other']


def read_articles(path):
    # Keep source strings, including visible date whitespace and literal NA text.
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8')


def valid_url(value):
    try:
        parsed = urlparse(value)
        return (parsed.scheme == 'https' and parsed.hostname == 'www.techi.com'
                and parsed.port in (None, 443) and not parsed.username and not parsed.password
                and parsed.path not in ('', '/') and not parsed.fragment and not parsed.query
                and not re.search(r'\s|[<>"\\]', value)
                and not re.search(r'%(?![0-9a-fA-F]{2})', value))
    except ValueError:
        return False


def date_details(value):
    """Return type and an ISO date only when the visible string is absolute."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    match = re.fullmatch(r'([A-Z][a-z]{2}) (\d{1,2}), (\d{4})', value)
    if match and match[1] in months:
        try:
            return 'absolute', datetime(int(match[3]), months.index(match[1]) + 1, int(match[2])).date().isoformat()
        except ValueError:
            pass
    if re.fullmatch(r'\d+ (?:second|minute|hour|day|week|month|year)s? ago', value):
        return 'relative', ''
    return 'unrecognized', ''


def validate(data):
    checks, problems = {}, []

    def check(name, passed, detail):
        checks[name] = bool(passed)
        if not passed:
            problems.append({'csv_row': '', 'check': name, 'field': '', 'observed': detail, 'expected': ''})

    check('nine_columns_in_exact_order', list(data.columns) == COLUMNS,
          f'Observed columns: {list(data.columns)}; expected: {COLUMNS}')
    check('exactly_120_rows', len(data) == 120, f'Observed {len(data)} rows, expected 120')
    counts = data['section'].value_counts().to_dict() if 'section' in data else {}
    check('six_sections_with_20_each', counts == dict.fromkeys(SECTIONS, 20), str(counts))
    blanks = data.isna() | data.map(lambda value: isinstance(value, str) and not value.strip())
    check('no_blank_cells', not blanks.any().any(), f'{int(blanks.sum().sum())} blank cells')
    for row, column in zip(*blanks.to_numpy().nonzero()):
        problems.append({'csv_row': row + 2, 'check': 'blank_cell', 'field': data.columns[column],
                         'observed': '', 'expected': 'nonblank value'})
    if not set(COLUMNS).issubset(data.columns):
        return checks, pd.DataFrame(problems, columns=['csv_row', 'check', 'field', 'observed', 'expected'])
    check('valid_urls', data.url.map(valid_url).all(), 'URL syntax/domain/path check failed; no live requests are made')
    check('no_exact_duplicate_rows', not data.duplicated().any(), f'{int(data.duplicated().sum())} excess exact rows')
    duplicate_mask = data.duplicated(['section', 'url'], keep=False)
    check('no_within_section_url_duplicates', not duplicate_mask.any(),
          f'{int(duplicate_mask.sum())} rows involved in repeated section/URL pairs')
    consistent = data.groupby('url')[['headline', 'author']].nunique().le(1).all().all()
    check('cross_listed_headlines_and_authors_consistent', consistent,
          'A shared URL has conflicting headline or author values')
    check('shown_date_patterns_recognized', data.date_shown.map(lambda x: date_details(x)[0] != 'unrecognized').all(),
          'Unrecognized date strings are not converted or repaired')
    expected = pd.DataFrame([headline_features(title) for title in data.headline], index=data.index)
    names = {'headline_word_count': 'headline_word_counts', 'format': 'format_rules',
             'names_a_company': 'company_rules', 'contains_a_number': 'number_rules'}
    for field, name in names.items():
        matches = data[field].eq(expected[field].map(str))
        check(name, matches.all(), f'{int((~matches).sum())} mismatches against the documented rules')
        for index in data.index[~matches]:
            problems.append({'csv_row': int(index) + 2, 'check': name, 'field': field,
                             'observed': data.at[index, field], 'expected': str(expected.at[index, field])})
    for index in data.index[~data.url.map(valid_url)]:
        problems.append({'csv_row': int(index) + 2, 'check': 'valid_urls', 'field': 'url',
                         'observed': data.at[index, 'url'], 'expected': 'public TECHi HTTPS article URL'})
    return checks, pd.DataFrame(problems, columns=['csv_row', 'check', 'field', 'observed', 'expected'])


def summarize(data):
    """Produce derived tables using copies; never normalize the source CSV."""
    work = data.copy(deep=True)
    work['words'] = pd.to_numeric(work.headline_word_count)
    work['company'] = work.names_a_company.eq('True').astype(int)
    work['number'] = work.contains_a_number.eq('True').astype(int)
    details = work.date_shown.map(date_details)
    work['date_type'] = details.map(lambda value: value[0])
    work['absolute_date'] = details.map(lambda value: value[1])
    summary = work.groupby('section').agg(
        n=('url', 'size'), total_headline_words=('words', 'sum'),
        mean_words=('words', 'mean'), median_words=('words', 'median'),
        min_words=('words', 'min'), max_words=('words', 'max'),
        company_count=('company', 'sum'), number_count=('number', 'sum'),
        distinct_authors=('author', 'nunique')).reindex(SECTIONS).reset_index()
    for field in ['company', 'number']:
        summary[field + '_pct'] = 100 * summary[field + '_count'] / summary.n
    formats = pd.crosstab(work.section, work['format']).reindex(index=SECTIONS, columns=FORMATS, fill_value=0)
    formats = formats.rename_axis(index='section', columns='format').stack().rename('count').reset_index()
    formats['denominator'] = formats.section.map(work.section.value_counts())
    formats['pct'] = 100 * formats['count'] / formats.denominator
    authors = work.groupby(['section', 'author']).size().rename('count').reset_index()
    authors['denominator'] = authors.section.map(work.section.value_counts())
    authors['pct'] = 100 * authors['count'] / authors.denominator
    authors = authors.sort_values(['section', 'count', 'author'], ascending=[True, False, True])
    overall = work.groupby('author').agg(article_section_rows=('url', 'size'), distinct_articles=('url', 'nunique')).reset_index()
    overall['row_denominator'] = len(work)
    overall['row_pct'] = 100 * overall.article_section_rows / len(work)
    overall['distinct_article_denominator'] = work.url.nunique()
    overall['distinct_article_pct'] = 100 * overall.distinct_articles / work.url.nunique()
    overall = overall.sort_values(['article_section_rows', 'author'], ascending=[False, True])
    dates = work.groupby(['section', 'date_shown', 'date_type']).size().rename('count').reset_index()
    dates['denominator'] = dates.section.map(work.section.value_counts())
    dates['pct'] = 100 * dates['count'] / dates.denominator
    date_summary = []
    for section in SECTIONS:
        group = work.loc[work.section == section]
        absolute = group.loc[group.date_type == 'absolute', 'absolute_date']
        date_summary.append({'section': section, 'n': len(group), 'absolute_count': len(absolute),
                             'relative_count': int(group.date_type.eq('relative').sum()),
                             'unrecognized_count': int(group.date_type.eq('unrecognized').sum()),
                             'earliest_absolute_date': absolute.min() if len(absolute) else '',
                             'latest_absolute_date': absolute.max() if len(absolute) else ''})
    overlaps = work.groupby('url').agg(section_count=('section', 'nunique'),
                                      sections=('section', lambda values: ' | '.join(sorted(set(values)))),
                                      article_section_rows=('section', 'size')).reset_index()
    overlaps = overlaps.loc[overlaps.section_count > 1]
    duplicates = data.loc[data.duplicated(['section', 'url'], keep=False)].copy()
    return {'section_summary': summary, 'format_distribution': formats,
            'author_by_section': authors, 'author_overall': overall,
            'shown_date_counts': dates, 'shown_date_summary': pd.DataFrame(date_summary),
            'cross_section_overlaps': overlaps, 'within_section_duplicates': duplicates}


def markdown_table(data):
    """Small Markdown formatter without an extra tabulate dependency."""
    lines = ['| ' + ' | '.join(data.columns) + ' |', '| ' + ' | '.join(['---'] * len(data.columns)) + ' |']
    for row in data.itertuples(index=False, name=None):
        lines.append('| ' + ' | '.join(str(value).replace('|', '\\|') for value in row) + ' |')
    return lines


def run(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT):
    input_path, output_dir = Path(input_path), Path(output_dir)
    reserved = ['validation_issues.csv', 'report.md', 'validation_report.json'] + [
        name + '.csv' for name in ['section_summary', 'format_distribution', 'author_by_section',
                                  'author_overall', 'shown_date_counts', 'shown_date_summary',
                                  'cross_section_overlaps', 'within_section_duplicates']]
    if any(input_path.resolve() == (output_dir / name).resolve() for name in reserved):
        raise ValueError('Output path would overwrite the input; choose another output directory')
    original = input_path.read_bytes()
    fingerprint = hashlib.sha256(original).hexdigest()
    data = read_articles(input_path)
    checks, issues = validate(data)
    output_dir.mkdir(parents=True, exist_ok=True)
    issues.to_csv(output_dir / 'validation_issues.csv', index=False)
    lines = ['# Article validation and analysis', '', f'Input: `{input_path.name}`', '',
             f'Input SHA-256: `{fingerprint}`', '', 'Validation results:', '']
    lines += [f'- {"PASS" if passed else "FAIL"}: {name}' for name, passed in checks.items()]
    if all(checks.values()):
        tables = summarize(data)
        for name, table in tables.items():
            table.to_csv(output_dir / (name + '.csv'), index=False, float_format='%.4f')
        summary = tables['section_summary']
        overlaps = tables['cross_section_overlaps']
        lines += ['', f'All checks passed. {len(data)} rows, {data.url.nunique()} distinct URLs, '
                  f'{len(overlaps)} URLs shared across sections. Zero within-section URL duplicates.', '',
                  'Cross-section overlaps are legitimate article-section memberships, not extra distinct articles.', '',
                  '## Section results', '']
        lines += markdown_table(summary.round(2))
        lines += ['', '## Findings in this sample', '']
        for section in SECTIONS:
            row = summary.set_index('section').loc[section]
            formats = tables['format_distribution']
            other = int(formats.loc[(formats.section == section) & (formats['format'] == 'other'), 'count'].iloc[0])
            authors = tables['author_by_section'].loc[lambda x: x.section == section]
            maximum = authors['count'].max()
            leaders = ', '.join(authors.loc[authors['count'] == maximum, 'author'])
            lines.append(f'- {section}: company-dictionary matches {int(row.company_count)}/{int(row.n)} '
                         f'({row.company_pct:.1f}%); digit-containing headlines {int(row.number_count)}/{int(row.n)} '
                         f'({row.number_pct:.1f}%); other-format headlines {other}/{int(row.n)}. '
                         f'Top author(s): {leaders}, each {maximum}/{int(row.n)} rows.')
        highest = summary.loc[summary.mean_words.idxmax()]
        lowest = summary.loc[summary.mean_words.idxmin()]
        most_company = summary.loc[summary.company_count.idxmax()]
        least_company = summary.loc[summary.company_count.idxmin()]
        lines += [f'- Company matching differs across these samples: {most_company.section} has '
                  f'{int(most_company.company_count)}/{int(most_company.n)} ({most_company.company_pct:.1f}%) '
                  f'versus {least_company.section} with {int(least_company.company_count)}/{int(least_company.n)} '
                  f'({least_company.company_pct:.1f}%), a {most_company.company_pct - least_company.company_pct:.1f} '
                  'percentage-point difference under the same dictionary.']
        lines += [f'- {highest.section} has the highest average word count: '
                  f'{int(highest.total_headline_words)}/{int(highest.n)} = {highest.mean_words:.2f} words. '
                  f'{lowest.section} is one section at the minimum: '
                  f'{int(lowest.total_headline_words)}/{int(lowest.n)} = {lowest.mean_words:.2f} words. '
                  f'The difference is {highest.mean_words - lowest.mean_words:.2f} words.', '',
                  '## Shown dates', '']
        lines += markdown_table(tables['shown_date_summary'])
        lines += ['', 'The date table preserves exact visible strings. Absolute-date ranges exclude relative labels; '
                  'no relative date is converted into a calendar date.', '',
                  '## Calculations and limits', '',
                  '- Unit: one article-section row. Section percentages = matching rows / section n × 100; n = 20.',
                  '- Mean words = sum of stored, validated word counts / n. Median = middle count (average of the two middle counts for n = 20). Min/max are observed extrema.',
                  '- Word count, format, company and number rules are defined in SCRAPING_RULES.md and recomputed by headline_features; this analysis does not reclassify or repair the CSV.',
                  '- Format counts include zero-count formats. Format percentages use all 20 section rows, not just recognized special patterns.',
                  '- Company=True means a fixed-dictionary match; False does not prove that no company is named. Format labels describe headline patterns, not verified article genres.',
                  f'- Author shares use exact extracted bylines. Guest Author is a byline label, not evidence of one identifiable person. author_overall.csv gives separate denominators for all {len(data)} rows and the {data.url.nunique()} distinct URLs (calculated from the input).',
                  '- Overlaps group by URL and count distinct sections; within-section duplicates group by (section, URL). Cross-listed headlines and bylines must agree. Visible relative dates may legitimately vary with access time.',
                  '- Shown-date counts group exact strings within each section; percentages = count / 20 × 100. Date types distinguish absolute dates, relative labels, and unrecognized strings. Date-range endpoints use only recognized absolute dates.',
                  '- This is a fixed sample of the 20 newest visible articles per section, not a complete historical time series or a random sample. Different date spans cannot establish past publication rates, a slowdown, growth, or total output. No publication-rate calculation is made.',
                  '- URL checks verify syntax, the expected domain and article path offline. They do not prove current HTTP availability. No website requests or traffic-data joins are made.',
                  '- Summary tables use up to four decimal places; the report shows selected figures rounded to two or one. Counts and denominators are exact.', '']
    preserved = input_path.read_bytes() == original
    checks['input_bytes_unchanged'] = preserved
    lines += ['', f'Input bytes unchanged: {preserved}. The source CSV was never opened for writing.']
    (output_dir / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    report = {'input_sha256': fingerprint, 'rows': len(data), 'columns': list(data.columns),
              'section_counts': data.section.value_counts().to_dict() if 'section' in data else {},
              'rule_source_sha256': hashlib.sha256((ROOT / 'scrape_articles.py').read_bytes()).hexdigest(),
              'validation': checks, 'passed': all(checks.values()), 'issues': len(issues)}
    (output_dir / 'validation_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for check, passed in checks.items():
        print(f'{"PASS" if passed else "FAIL"}: {check}')
    print(f'Report and summary tables: {output_dir}')
    return all(checks.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        success = run(args.input, args.output_dir)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f'Analysis failed: {error}\n')
    if not success:
        parser.exit(1, 'Validation failed; see report and validation_issues.csv.\n')


if __name__ == '__main__':
    main()
