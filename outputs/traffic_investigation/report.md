# Traffic investigation: reported sessions versus comparable measurement

The CSV is synthetic assessment data. Tracking replacement and aggregator exposure are context supplied by the assignment, not facts independently established by the CSV. Sessions are not unique readers.

## Reported growth

Monthly sessions = AI + Markets + Crypto + Breakthroughs + Policy + Guides. Newsletter signups are excluded.

| month | reported_sessions | reported_absolute_change | reported_mom_pct | newsletter_signups |
| --- | --- | --- | --- | --- |
| 2025-09 | 57500 | nan | nan | 820 |
| 2025-10 | 59000 | 1500.0 | 2.6087 | 840 |
| 2025-11 | 75000 | 16000.0 | 27.1186 | 860 |
| 2025-12 | 62400 | -12600.0 | -16.8 | 890 |
| 2026-01 | 64000 | 1600.0 | 2.5641 | 920 |
| 2026-02 | 94685 | 30685.0 | 47.9453 | 950 |
| 2026-03 | 96570 | 1885.0 | 1.9908 | 980 |
| 2026-04 | 95845 | -725.0 | -0.7508 | 1010 |
| 2026-05 | 97440 | 1595.0 | 1.6641 | 1040 |
| 2026-06 | 99035 | 1595.0 | 1.6369 | 1070 |
| 2026-07 | 100920 | 1885.0 | 1.9034 | 1100 |
| 2026-08 | 102805 | 1885.0 | 1.8678 | 1140 |

January–February: (94,685 / 64,000 − 1) × 100 = 47.94531%. September–August: (102,805 / 57,500 − 1) × 100 = 78.79130%.

These are 12 monthly observations with 11 intervals between the endpoints. There is no August 2025 or September 2024 comparison, so a 30% year-on-year claim cannot be verified. A complete annual total for the previous year is also absent.

## February: common measurement effect is plausible

| section | january_sessions | february_sessions | february_ratio | reported_growth_pct |
| --- | --- | --- | --- | --- |
| AI | 21200 | 31610 | 1.491038 | 49.103774 |
| Markets | 13400 | 19865 | 1.482463 | 48.246269 |
| Crypto | 11400 | 16820 | 1.475439 | 47.54386 |
| Breakthroughs | 8500 | 12615 | 1.484118 | 48.411765 |
| Policy | 5800 | 8555 | 1.475 | 47.5 |
| Guides | 3700 | 5220 | 1.410811 | 41.081081 |

Each ratio = February section sessions / January section sessions. Five sections jump by approximately 47.5–49.1%; Guides jumps less. Their synchronization with the supplied tracking-change note supports a possible common recording effect, but cannot identify its size or prove that all growth is artificial.

Central calibration uses AI, Markets, Breakthroughs and Policy. Crypto is excluded because of the known temporary spike and reversal; Guides is excluded because its traffic trend may differ. These are judgment-based calibration sections, not a randomized control group.

For each calibration section: take the median of its four September–January monthly absolute increments; forecast February = January + that median increment; estimate the measurement multiplier = observed February / forecast February. Take the median of the four estimated multipliers.

| section | january_sessions | february_sessions | february_ratio | reported_growth_pct | median_pre_change_increment | forecast_february_sessions | forecast_organic_growth_pct | measurement_factor_estimate | used_for_central_factor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI | 21200 | 31610 | 1.491038 | 49.103774 | 700.0 | 21900.0 | 3.301887 | 1.443379 | True |
| Markets | 13400 | 19865 | 1.482463 | 48.246269 | 300.0 | 13700.0 | 2.238806 | 1.45 | True |
| Crypto | 11400 | 16820 | 1.475439 | 47.54386 | 350.0 | 11750.0 | 3.070175 | 1.431489 | False |
| Breakthroughs | 8500 | 12615 | 1.484118 | 48.411765 | 200.0 | 8700.0 | 2.352941 | 1.45 | True |
| Policy | 5800 | 8555 | 1.475 | 47.5 | 100.0 | 5900.0 | 1.724138 | 1.45 | True |
| Guides | 3700 | 5220 | 1.410811 | 41.081081 | -100.0 | 3600.0 | -2.702703 | 1.45 | False |

This produces a multiplier of 1.45000000, rather than assuming 1.5. Divide only February–August sessions by this multiplier to express them on the earlier measurement scale. Earlier months and all newsletter counts remain unscaled. This assumes the break began in February, was multiplicative, persisted unchanged, and affected all six sections equally.

Central estimate: August comparable sessions = 102,805 / 1.45000000 = 70,900.00. Underlying-session endpoint change = (70,900.00 / 57,500 − 1) × 100 = 23.30435%. Adjusted February = 65,300.00; adjusted January–February growth = 2.03125%.

This is an assumption-dependent estimate of comparable sessions, not an identified causal effect or a count of additional readers. A tracking audit or simultaneous old/new measurement is needed to validate the multiplier.

## Measurement sensitivity

Alternative factors = median observed February/January ratio among the four calibration sections / (1 + assumed organic monthly growth). The 0–5% organic-growth range brackets their observed pre-change monthly growth but is an illustrative assumption range, not a confidence interval. It does not cover every plausible explanation. No-adjustment and a simple 1.5 multiplier are shown separately.

| scenario | assumed_organic_growth_pct | median_observed_control_february_ratio | measurement_factor | august_adjusted_sessions | september_sessions | adjusted_endpoint_pct | adjusted_january_february_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| central_trend_calibrated |  | 1.48329 | 1.45 | 70900.0 | 57500 | 23.304348 | 2.03125 |
| no_adjustment |  | 1.48329 | 1.0 | 102805.0 | 57500 | 78.791304 | 47.945312 |
| illustrative_1_5 |  | 1.48329 | 1.5 | 68536.666667 | 57500 | 19.194203 | -1.369792 |
| organic_0_pct | 0.0 | 1.48329 | 1.48329 | 69308.758529 | 57500 | 20.536971 | -0.258685 |
| organic_1_pct | 1.0 | 1.48329 | 1.468604 | 70001.846114 | 57500 | 21.742341 | 0.738729 |
| organic_2_pct | 2.0 | 1.48329 | 1.454206 | 70694.9337 | 57500 | 22.947711 | 1.736142 |
| organic_3_pct | 3.0 | 1.48329 | 1.440088 | 71388.021285 | 57500 | 24.15308 | 2.733555 |
| organic_4_pct | 4.0 | 1.48329 | 1.426241 | 72081.10887 | 57500 | 25.35845 | 3.730968 |
| organic_5_pct | 5.0 | 1.48329 | 1.412657 | 72774.196455 | 57500 | 26.56382 | 4.728381 |

The 0–5% scenarios give endpoint comparable-session changes from 20.54% to 26.56%. This range excludes the separate no-adjustment scenario. Control-selection sensitivity includes leave-one-out, all non-Crypto, and all-six calculations; similar factors in those checks do not eliminate model uncertainty.

## November Crypto: a temporary excess, not a whole month to discard

Observed Crypto: October 10,100; November 24,800; December 11,000. Central baseline = (10,100 + 11,000) / 2 = 10,550. Possible non-recurring excess = max(0, 24,800 − 10,550) = 14,250; 57.46% of November Crypto and 19.00% of November total sessions.

| baseline_method | october_crypto | november_crypto | december_crypto | estimated_baseline | possible_nonrecurring_excess | excess_pct_of_november_crypto | excess_pct_of_november_all_sessions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| october_baseline | 10100 | 24800 | 11000 | 10100.0 | 14700.0 | 59.2742 | 19.6 |
| neighbor_midpoint | 10100 | 24800 | 11000 | 10550.0 | 14250.0 | 57.4597 | 19.0 |
| december_baseline | 10100 | 24800 | 11000 | 11000.0 | 13800.0 | 55.6452 | 18.4 |

Using October or December alone gives a possible excess of 14,700 or 13,800, respectively. The assignment note is consistent with a transient aggregator effect, but the monthly file cannot attribute individual sessions to it or measure retention. The midpoint is a local counterfactual assuming a roughly smooth neighboring trend, not a verified organic baseline.

Central de-spiked November total = 75,000 − 14,250 = 60,750. November precedes the measurement break and is not divided by the February factor. Removing November excess changes period totals and apparent volatility, but has no effect on September–August endpoint growth.

Joint sensitivity retains 100%, 50%, or 0% of the estimated excess (removing 0%, 50%, or 100%) for every measurement scenario. Period totals sum the corrected monthly figures; they are not unique-reader totals or year-on-year comparisons.

## Newsletter: distinguish monthly acquisition from subscriber stock

Monthly signups increase from 820 to 1,140: (1,140 / 820 − 1) × 100 = 39.02439%. The file sums to 11,620 signups over the 12 months, not that many retained or unique subscribers. Opening subscribers, duplicates, unsubscribes, delivery and engagement are unknown.

Signups per 1,000 reported sessions = 1,000 × signups / reported sessions: September 14.2609, August 11.0890. With the central comparable-session denominator: August 16.0790. These are aggregate intensity ratios, not user-level conversion rates.

The apparent signup/session divergence partly depends on the session measurement scale. Signups grow faster than the centrally adjusted endpoint sessions, so the raw divergence alone does not establish worsening conversion. Assume signup measurement itself is stable; verify it separately. Newsletter advertising should be evaluated using verified active, consented subscribers, delivered mail and engagement, not sessions or gross monthly acquisitions alone.

## Guides recommendation

| section | september_sessions | august_reported_sessions | reported_endpoint_pct | august_adjusted_sessions | adjusted_endpoint_pct | february_to_august_pct | march_to_april_pct | september_share_pct | august_share_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI | 18400 | 36830 | 100.16304 | 25400.0 | 38.04348 | 16.51376 | 2.67857 | 32.0 | 35.82511 |
| Markets | 12200 | 22475 | 84.22131 | 15500.0 | 27.04918 | 13.13869 | 2.14286 | 21.21739 | 21.86178 |
| Crypto | 9800 | 18995 | 93.82653 | 13100.0 | 33.67347 | 12.93103 | 1.68067 | 17.04348 | 18.47673 |
| Breakthroughs | 7600 | 14355 | 88.88158 | 9900.0 | 30.26316 | 13.7931 | 2.24719 | 13.21739 | 13.96333 |
| Policy | 5400 | 9425 | 74.53704 | 6500.0 | 20.37037 | 10.16949 | 1.66667 | 9.3913 | 9.16784 |
| Guides | 4100 | 725 | -82.31707 | 500.0 | -87.80488 | -86.11111 | -55.88235 | 7.13043 | 0.70522 |

Guides falls from 4,100 to 725 reported sessions (-82.32%). On the central comparable scale, August is 500 versus September 4,100 (-87.80%). March–April falls from 4,930 to 2,175 (-55.88%). February–August falls -86.11%, a comparison unaffected by a constant post-February multiplier. The common measurement adjustment therefore does not explain away the section decline.

Do not close Guides solely on this file. Prioritize a section-level audit around March–April: tracking coverage, URL/category mappings, redirects, search indexing, referrals and article-level landings. Check editorial history and refresh a small set of useful evergreen guides; assess that pilot with consistent measurement, engagement and newsletter acquisition. This file lacks costs, search impressions, reader cohorts and section-specific signups, so it cannot establish the cause, profitability or newsletter value of Guides.

Overall February–August growth is 8.57580% under either raw sessions or a constant common multiplier. That is evidence of growth within the post-change recording regime, not proof of unique-reader growth.

## October article snapshot versus the traffic timeline

| section | sample_n | absolute_date_rows | relative_date_rows | unrecognized_date_rows | earliest_absolute_shown_date | latest_absolute_shown_date | absolute_dates_during_traffic_period | absolute_dates_after_traffic_period | absolute_dates_in_march_april_2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI | 20 | 20 | 0 | 0 | 2026-09-22 | 2026-10-06 | 0 | 20 | 0 |
| Markets | 20 | 7 | 13 | 0 | 2026-10-06 | 2026-10-07 | 0 | 7 | 0 |
| Crypto | 20 | 19 | 1 | 0 | 2026-07-23 | 2026-10-07 | 4 | 15 | 0 |
| Breakthroughs | 20 | 19 | 1 | 0 | 2026-07-15 | 2026-09-26 | 15 | 4 | 0 |
| Policy | 20 | 20 | 0 | 0 | 2026-08-19 | 2026-09-29 | 2 | 18 | 0 |
| Guides | 20 | 20 | 0 | 0 | 2026-03-12 | 2026-09-22 | 17 | 3 | 2 |

The 20 Guides headlines have absolute shown dates from March 12 to September 22, 2026. AI reaches October 6; Markets, Crypto and Breakthroughs also have relative date labels, which are left unconverted. The Guides sample reaches farther back than several others. This is consistent with a thinner recent visible selection, not a quantified historical publication rate.

Traffic ends August 2026; collection occurred in October. September/October articles cannot explain traffic in March/April. Even older sampled article dates are a truncated sample of visible listings, not a complete publishing calendar, and dates can reflect site migration or updates. The evidence does not establish that Guides stopped publishing in March/April. Verify archived editorial records and URL-level traffic before making that claim. Section headline-format, company and number patterns are descriptive and cannot be assigned a traffic effect from these data.

The article timeline counts exact absolute shown dates within the traffic interval and after it; relative strings are counted separately and never guessed into dates. The two datasets are compared by section for context, not joined to manufacture article-level session figures.

## Reproduction and formula index

- Run `python investigate_traffic.py` or `python analyze_traffic.py`. No live website requests are made.
- monthly_calculations.csv: total = sum of six sections; absolute change = current − previous; percentage change = (current / previous − 1) × 100. First-month changes are undefined and blank.
- section_monthly_calculations.csv: the same calculations per section; adjusted = reported / applicable multiplier − any November Crypto excess removed. Raw inputs are retained alongside derived estimates.
- section_trends.csv: endpoint, February–August and March–April growth use the same percentage formula; shares = section sessions / all-section total × 100. A common within-month multiplier leaves shares unchanged.
- pre_change_increments.csv and tracking_calibration.csv contain every observed increment, forecast and per-section multiplier used by the central method. The median of four values averages the middle two.
- measurement_sensitivity.csv, control_selection_sensitivity.csv and scenario_monthly_sessions.csv retain alternative assumptions and all adjusted monthly values. joint_period_sensitivity.csv sums each scenario with three fractions of estimated November excess removed.
- crypto_spike_scenarios.csv retains all three baselines, excess amounts and exact denominators.
- article_timeline.csv is a section-level summary of saved visible date strings; it does not use dates inferred from headlines. Original date strings remain in the source article CSV.
- metrics.json and provenance.json record headline metrics, assumptions and original input SHA-256 values. CSV calculations retain floating-point precision; displayed report values are rounded only for readability.
- Neither source CSV is rewritten. The tracking and aggregator notes remain assumptions supplied by the assessment, not independently verified facts.

