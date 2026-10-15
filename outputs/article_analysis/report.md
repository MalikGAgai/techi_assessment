# Article validation and analysis

Input: `techi_articles.csv`

Input SHA-256: `dfd32c2dbbc8cbf969849ed716388b08603617c5459e71f349b289d9a7d81b64`

Validation results:

- PASS: nine_columns_in_exact_order
- PASS: exactly_120_rows
- PASS: six_sections_with_20_each
- PASS: no_blank_cells
- PASS: valid_urls
- PASS: no_exact_duplicate_rows
- PASS: no_within_section_url_duplicates
- PASS: cross_listed_headlines_and_authors_consistent
- PASS: shown_date_patterns_recognized
- PASS: headline_word_counts
- PASS: format_rules
- PASS: company_rules
- PASS: number_rules

All checks passed. 120 rows, 109 distinct URLs, 11 URLs shared across sections. Zero within-section URL duplicates.

Cross-section overlaps are legitimate article-section memberships, not extra distinct articles.

## Section results

| section | n | total_headline_words | mean_words | median_words | min_words | max_words | company_count | number_count | distinct_authors | company_pct | number_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI | 20 | 191 | 9.55 | 9.5 | 7 | 13 | 19 | 12 | 8 | 95.0 | 60.0 |
| Markets | 20 | 191 | 9.55 | 10.0 | 8 | 11 | 19 | 12 | 6 | 95.0 | 60.0 |
| Crypto | 20 | 214 | 10.7 | 10.0 | 7 | 16 | 7 | 10 | 7 | 35.0 | 50.0 |
| Breakthroughs | 20 | 199 | 9.95 | 10.0 | 7 | 12 | 13 | 9 | 7 | 65.0 | 45.0 |
| Policy | 20 | 226 | 11.3 | 11.0 | 7 | 16 | 14 | 7 | 7 | 70.0 | 35.0 |
| Guides | 20 | 195 | 9.75 | 9.0 | 5 | 14 | 8 | 9 | 9 | 40.0 | 45.0 |

## Findings in this sample

- AI: company-dictionary matches 19/20 (95.0%); digit-containing headlines 12/20 (60.0%); other-format headlines 17/20. Top author(s): Umair Aslam, each 5/20 rows.
- Markets: company-dictionary matches 19/20 (95.0%); digit-containing headlines 12/20 (60.0%); other-format headlines 20/20. Top author(s): Fatima Fakhar, each 5/20 rows.
- Crypto: company-dictionary matches 7/20 (35.0%); digit-containing headlines 10/20 (50.0%); other-format headlines 17/20. Top author(s): Muhammad Zeshan Sarwar, each 7/20 rows.
- Breakthroughs: company-dictionary matches 13/20 (65.0%); digit-containing headlines 9/20 (45.0%); other-format headlines 20/20. Top author(s): Saba Javed, each 6/20 rows.
- Policy: company-dictionary matches 14/20 (70.0%); digit-containing headlines 7/20 (35.0%); other-format headlines 19/20. Top author(s): Saba Javed, each 6/20 rows.
- Guides: company-dictionary matches 8/20 (40.0%); digit-containing headlines 9/20 (45.0%); other-format headlines 14/20. Top author(s): Zoha Imdad Ali, each 7/20 rows.
- Company matching differs across these samples: AI has 19/20 (95.0%) versus Crypto with 7/20 (35.0%), a 60.0 percentage-point difference under the same dictionary.
- Policy has the highest average word count: 226/20 = 11.30 words. AI is one section at the minimum: 191/20 = 9.55 words. The difference is 1.75 words.

## Shown dates

| section | n | absolute_count | relative_count | unrecognized_count | earliest_absolute_date | latest_absolute_date |
| --- | --- | --- | --- | --- | --- | --- |
| AI | 20 | 20 | 0 | 0 | 2026-09-22 | 2026-10-06 |
| Markets | 20 | 7 | 13 | 0 | 2026-10-06 | 2026-10-07 |
| Crypto | 20 | 19 | 1 | 0 | 2026-07-23 | 2026-10-07 |
| Breakthroughs | 20 | 19 | 1 | 0 | 2026-07-15 | 2026-09-26 |
| Policy | 20 | 20 | 0 | 0 | 2026-08-19 | 2026-09-29 |
| Guides | 20 | 20 | 0 | 0 | 2026-03-12 | 2026-09-22 |

The date table preserves exact visible strings. Absolute-date ranges exclude relative labels; no relative date is converted into a calendar date.

## Calculations and limits

- Unit: one article-section row. Section percentages = matching rows / section n × 100; n = 20.
- Mean words = sum of stored, validated word counts / n. Median = middle count (average of the two middle counts for n = 20). Min/max are observed extrema.
- Word count, format, company and number rules are defined in SCRAPING_RULES.md and recomputed by headline_features; this analysis does not reclassify or repair the CSV.
- Format counts include zero-count formats. Format percentages use all 20 section rows, not just recognized special patterns.
- Company=True means a fixed-dictionary match; False does not prove that no company is named. Format labels describe headline patterns, not verified article genres.
- Author shares use exact extracted bylines. Guest Author is a byline label, not evidence of one identifiable person. author_overall.csv gives separate denominators for all 120 rows and the 109 distinct URLs (calculated from the input).
- Overlaps group by URL and count distinct sections; within-section duplicates group by (section, URL). Cross-listed headlines and bylines must agree. Visible relative dates may legitimately vary with access time.
- Shown-date counts group exact strings within each section; percentages = count / 20 × 100. Date types distinguish absolute dates, relative labels, and unrecognized strings. Date-range endpoints use only recognized absolute dates.
- This is a fixed sample of the 20 newest visible articles per section, not a complete historical time series or a random sample. Different date spans cannot establish past publication rates, a slowdown, growth, or total output. No publication-rate calculation is made.
- URL checks verify syntax, the expected domain and article path offline. They do not prove current HTTP availability. No website requests or traffic-data joins are made.
- Summary tables use up to four decimal places; the report shows selected figures rounded to two or one. Counts and denominators are exact.


Input bytes unchanged: True. The source CSV was never opened for writing.
