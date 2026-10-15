# TECHi: is traffic actually up?

Start with **memo.md** (under 700 words), **method.txt** (under 300 words), and
`outputs/final_audit/report.md`. The memo addresses the YoY claim, an underlying
session-growth estimate, and whether to retire Guides. It includes two measured
article findings, the recommendation's cost if wrong, a change-my-mind condition,
and a free next measurement. The exact supplied rubric is mapped in
`outputs/final_audit/rubric_checklist.csv`; no self-awarded score is claimed.

## Setup

Tested on Windows with Python 3.10.11. From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The five requested direct dependencies are pinned. `requirements-lock.txt`
records the tested direct and transitive versions; install that file instead
for the closest repeat of the tested environment. No activation is necessary.
No credentials, account, private analytics, paid services or secrets are used.

## Reproduce offline

```powershell
# Optional: verify/recreate the same 120 rows from saved HTML, without network
.\.venv\Scripts\python.exe scrape_articles.py --replay

# Regenerate article validation, traffic calculations, charts and combined notes
.\.venv\Scripts\python.exe analysis.py

# Audit all outputs, word limits and source hashes; run every pytest test
.\.venv\Scripts\python.exe audit_assessment.py

# Package allowed files and verify archive contents and SHA-256 hashes
.\.venv\Scripts\python.exe package_assessment.py
```

`analysis.py` runs `validate_data.py`, `analyze_articles.py`, `analyze_traffic.py`
and `combine_evidence.py`. The detailed traffic investigation can also be run
with `investigate_traffic.py`. All analysis is offline. Individual scripts expose
path arguments through `--help`. Re-running the analyses leaves source CSV bytes
unchanged; replay reconstructs the original article snapshot byte-for-byte.
Derived outputs are overwritten. Audit test attempts are saved separately,
including failures and warnings; use the latest audit result for current status.

## Data separation and outputs

| Source/output | Meaning |
| --- | --- |
| `traffic_table.csv` | Original invented monthly sessions and signup counts; unchanged |
| `outputs/techi_articles.csv` | Real October 2026 public listing sample; nine required columns |
| `outputs/techi_audit/` | Saved public HTML, URL/access metadata, checksums and extraction logs |
| `outputs/article_analysis/` | Article-only validation and descriptive tables |
| `outputs/synthetic_traffic/` | Invented-session totals, section summaries and chart 1 |
| `outputs/traffic_investigation/` | Invented-session adjustment scenarios, newsletter tables and chart 2 |
| `outputs/combined_evidence/` | Side-by-side interpretation with explicit source types; no article/session join |
| `outputs/final_audit/` | Rubric mapping, public spot checks, independent arithmetic checks and actual pytest logs |

The archive also places a byte-identical `techi_articles.csv` at its root for the
submission deliverable; it is copied from the public sample, not combined with
traffic. Its original `outputs/` path remains so scripts and tests run unchanged.
Root Python files contain analysis, scraping, audit and packaging code. `tests/`
contains offline tests and clearly labelled artificial HTML fixtures. Fixtures
are never exported as collected articles.

There are exactly two final PNG figures. The six-section plot uses black lines
in separate, labelled panels with individual y scales. The measurement/newsletter
figure distinguishes black lines using dashes and markers, labels adjustment as
a scenario, and uses a September=100 panel to compare differently scaled series.
No additional chart is included in the submission.

## Collection decisions and tradeoffs

Run `scrape_articles.py` without `--replay` only to request current public pages.
It discovers section links from actual homepage navigation, checks robots.txt,
uses a descriptive User-Agent and waits at least 2.1 seconds between request
starts, including redirects. The six working URLs and exact field rules are in
`SCRAPING_RULES.md`. It follows actual pagination links only when needed; each
first listing supplied 24 cards, so this sample required no pagination request.

Select the newest 20 distinct URLs **within each section**, verifying descending
listing timestamps. Preserve cross-listed articles: 120 memberships represent
109 URLs, with zero within-section duplicates. The user explicitly chose this
over selecting older articles to force global uniqueness. Author and date come
from the visible listing; missing values stop extraction rather than being guessed.
`date_shown` is verbatim listing text, including relative labels. Headline text
collapses layout whitespace. Detail pages may show a different date presentation
or primary category; that does not replace the listing fields.

Word counts use whitespace tokens containing a letter/digit. Format is a
documented, ordered headline-pattern heuristic, and company mentions use a fixed
dictionary rather than a broad language model. Digit detection includes years,
versions and embedded digits. These choices are explainable and reproducible,
but can miss companies or classify a leading-year headline as a listicle.

Techi's terms prohibit automated bulk scraping. This was reported; the user
subsequently instructed proceeding despite it. That is not site-owner permission.
Robots checks and rate limits remained in force. Saved HTML is included for
private assessment review/replay, not as permission to republish the site.

## Analysis decisions and limitations

Totals sum the six section counts and exclude newsletter signups. Whether section
counts are mutually exclusive sessions is unspecified; totals assume additivity.
Sessions do not measure unique readers. The table has 12 observations but only
11 endpoint intervals; absent prior-year months prevent verification of 30% YoY.

The February central adjustment uses four sections' pre-change median increments
to forecast February, then takes the median observed/forecast multiplier: 1.45.
It applies only after the stated February tracking replacement. All six ratios,
control-choice sensitivity and 0–5% assumed organic-growth scenarios are saved.
A synchronized jump supports a common recording effect, but cannot causally
prove the snippet's size or effect. The 23.30% central comparable-session growth
is an assumption-dependent estimate, not measured unique-reader growth.

November Crypto excess uses the October/December midpoint, with both individual
neighbors as alternatives. Partial-removal scenarios are saved. These are
counterfactual excess estimates, not observed aggregator or article-level sessions.
The original Crypto values are retained. Monthly signups are acquisitions, not
subscriber stock, retained subscribers or user-level conversion rates. Pricing
and near-zero Guides advertising are supplied commercial premises, not verified
revenue. No financial amount is invented.

The exact note says a second AI writer joined September 2025. October's recent
bylines cannot verify that employment event or its traffic effect. Eighteen of
20 Guides shown dates are after March, including 15 in April–August: they challenge
“almost nothing since March” on visible dates. Publication-versus-update dates,
complete historical frequency and causation remain uncertain. The November
article and referral attribution remain untestable. Newest-20 samples are not
random or complete historical calendars; absence from the sample is not absence
from the site. No October article is assigned synthetic historical traffic.

## Tests and audit evidence

Run `python -m pytest -q` for the suite alone. Tests cover malformed data,
calculations with known totals, preservation of both CSVs, source-field parsing,
classification precedence, cross-listing, robots denials, request spacing,
snapshot integrity, deterministic replay and report generation. Integration
checks verify reproducible CSV tables. Snapshot comparisons check all 120
exported rows; three live detail pages were manually spot-reviewed.

The independent audit recomputes numeric traffic cells using Python arithmetic
and `statistics.median`, rather than calling the production calculation function.
`traffic_cell_checks.csv` records each observed and expected value. Actual suite
totals, warnings, word counts and pass/fail checks are in the final audit report
and JSON. Matplotlib/pyparsing dependency deprecation warnings are retained, not
suppressed. See those files for the actual final results, not a claimed grade.

## Future improvements and submission

- Verify the old/new analytics definitions with controlled browser events and,
  if available, parallel tracking. Do not estimate reader identities from sessions.
- Obtain historical editorial/byline records and the November referral URL/logs.
- Clarify original versus updated dates and category/session overlap definitions.
- Test a bounded Guides refresh using consistent tracking and newsletter outcomes.
- Broaden and review company aliases; replace format heuristics only if labelled
  evaluation data justify the complexity. Resolve dependency deprecation warnings
  through a separately tested environment update.

Review the memo and code and be ready to explain each choice; this submission
uses original task-specific analysis, not copied tutorial material. The private
submission page has not been opened or submitted. Enter your actual time taken
yourself; no unmeasured time claim is supplied. The ZIP excludes `.venv`, caches,
local configuration, credentials and the archive itself. Its manifest and external
SHA-256 permit integrity checking after transfer.
