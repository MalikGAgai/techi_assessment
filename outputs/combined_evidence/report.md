# Combined assessment: real articles and synthetic traffic

## Evidence boundaries

**Real public article sample:** 120 article-section rows collected in October 2026, with 20 per section and 109 distinct URLs. Headlines, bylines and shown dates describe the saved public listings at access time. They are not independent verification of the events reported in the stories.

**Synthetic assessment traffic:** monthly section sessions and newsletter signups from September 2025 through August 2026. Calculations verify the numbers in the supplied invented dataset, not actual TECHi analytics. Context about staffing, tracking and referrals is an assessment note, not independently measured evidence.

The sources are compared side by side. They have no supplied article-to-session key; no sessions or signups are assigned to individual sampled articles, writers or formats.

## Two quantified findings from the article rows

1. **AI byline concentration:** Umair Aslam has the largest visible byline count: **5/20 × 100 = 25.00%**. There are 8 distinct AI byline labels. Calculation: filter AI rows, group exact extracted author labels, count rows and select the largest group. This is a contribution share within the recent sample, not a traffic share or a measure of writer productivity. It connects to the AI writer note, but cannot establish who was employed historically, when they joined, or whether they caused a traffic change. All 20/20 AI rows have explicit shown dates after August 2026, so they do not overlap the traffic period.

2. **Guides date mix:** **18/20 × 100 = 90.00%** of sampled Guides rows have explicit shown dates within September 1, 2025–August 31, 2026. Of these, 15/20 are dated April?August and 3/20 are dated after the traffic period. Guides' visible dates span 2026-03-12 to 2026-09-22, versus AI's 2026-09-22 to 2026-10-06. Calculation: filter Guides rows, parse only explicit absolute shown dates and count those on or after April 1, 2026. This challenges the assessment's 'almost nothing since Mar 2026' note on visible dates. It does not quantify a change in historical publishing frequency or establish the cause of the synthetic traffic decline.

These percentages use all 20 rows in the relevant section, not 120 pooled rows or the 109-URL denominator. Both findings have exact source-row selection rules in quantified_article_findings.csv.

## Assessment notes: verified, contradicted or untestable?

**Verified** means directly observable within the stated dataset and scope. **Contradicted** means directly inconsistent with that evidence, not merely unsupported. **Untestable** means the required identity, period, measurement or causal evidence is absent. Consistency is not verification; lack of evidence is not contradiction.

| Assessment note | Verdict on the note | What the available data establish |
| --- | --- | --- |
| A second AI writer joined September 2025 | Untestable historical staffing and impact | The recent AI sample has eight bylines and a largest byline share of 5/20. It cannot establish hiring, a departure or causal traffic impact. |
| November Crypto article gained temporary aggregator exposure | Untestable attribution; consistent with the synthetic pattern | Crypto sessions rise from 10,100 to 24,800 then fall to 11,000. The spike exists in the invented table, but it does not identify an article or an aggregator. |
| Guides has published almost nothing since March 2026 | Contradicted as a blanket inactivity claim on visible dates; historical rate and causation remain untestable | Guides sessions fall from 4,930 in March to 2,175 in April: (2,175/4,930 − 1) × 100 = -55.88%. The October Guides sample reaches farther back than AI's. Eighteen of 20 Guides shown dates are after March, including 15 in April?August. This challenges inactivity but does not establish a complete monthly count or reduced rate. |

**Verified:** the byline/date observations are verified in the real sample; the spike and decline are verified only as patterns in the synthetic file. **Contradicted on visible dates:** the Guides inactivity note is challenged by 18 post-March rows, with publication-versus-update ambiguity retained. **Untestable:** the AI hiring event, Crypto article attribution, historical publishing-rate change and all proposed traffic causes. Multiple recent AI bylines do not disprove hiring a second writer in September 2025.

The Crypto sample has 0/20 rows with an explicit November 2025 shown date; its earliest absolute shown date is 2026-07-23, and 1 row has a recent relative label at October access time. Thus it cannot identify or inspect the alleged November article. This is an evidence-coverage gap, not a contradiction of the note.

## How the traffic calculations inform the evaluation

The Crypto midpoint counterfactual is (10,100 + 11,000)/2 = 10,550. The possible November excess is 24,800 − 10,550 = 14,250. This is an estimate under a smooth-neighboring-baseline assumption, not measured aggregator sessions or a per-article count. It cannot be attached to any of the October-sampled articles. See outputs/traffic_investigation/crypto_spike_scenarios.csv for alternative baselines.

The synthetic February jump occurs across sections. The trend-calibrated common measurement factor is 1.45, yielding 23.30% September–August comparable-session growth under that model. It does not identify an AI writer effect or extra unique readers. A constant post-February multiplier cancels in Guides' March–April ratio, so that decline remains within the same assumed recording regime. A section-specific tracking problem, referral change or search loss remains possible. Sensitivity assumptions and every traffic calculation are saved separately in outputs/traffic_investigation/.

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
