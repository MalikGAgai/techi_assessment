# Supplied TechAbout assessment requirements

This records the requirements supplied by the user during the final audit.
It is not a score awarded by TechAbout.

- Context: invented monthly traffic; investigate the claim that TECHi is up
  30% year on year. The stated timebox is five to six hours; actual time taken
  must be reported truthfully by the applicant, not inferred here.
- Part 1: newest 20 articles in each of AI, Markets, Crypto, Breakthroughs,
  Policy and Guides; 120 complete rows. Columns: url, section, headline, author,
  date_shown verbatim, headline_word_count, format, names_a_company,
  contains_a_number. Public pages only, no login, at most one request per two
  seconds. Navigation, rather than guessed patterns, locates working sections.
- Part 2 notes: a second AI writer joined September 2025; a Crypto explainer
  received 36 hours on a major aggregator's front page in November 2025;
  the analytics snippet was replaced site-wide on February 1, 2026 and not
  checked since; Guides has published almost nothing since March 2026;
  advertising pays per session, near zero on Guides; newsletter slots are
  priced on subscribers. These are assessment premises to evaluate, not
  independently verified facts or rates.
- Answer: whether 30% YoY is true; best estimate of underlying change;
  whether to retire Guides. Show arithmetic and flag notes challenged by the
  public sample. Do not invent measurements or infer unmeasured article traffic.
- Deliver: one ZIP/folder containing techi_articles.csv, reproducible method.txt
  at most 300 words, intact analysis code/formulas, at most two charts and
  memo.md/PDF at most 700 words. The memo needs two quantified article findings,
  a link between rows and notes/table, recommendation and cost if wrong,
  a line beginning “I would change my mind if...”, and the next free number.
- README: setup, decisions, tradeoffs, tests and future improvements. Name
  sample limits and ambiguities; distinguish real and invented evidence. Keep
  secrets, credentials, private/client data and copied tutorials/AI boilerplate
  out. Include evidence for offline review and be able to explain the work.
- Submission is through the applicant's private assessment link, with actual
  time taken and approach. No private submission has been performed here.

| Rubric category | Subcriteria | Available points |
| --- | --- | --- |
| Dataset | Complete rows 8; reproducible method 7; sample limits 7 | 22 |
| Traffic | Measurement/readers 12; November 6; underlying arithmetic 7; signups 5 | 30 |
| Findings | Two numeric findings 10; connection to table/notes 6 | 16 |
| Memo | Recommendation/cost 8; change-my-mind 4; next number 4 | 16 |
| Charts | Axes/B&W 4; main point 4 | 8 |
| Honesty | Source separation 3; uncertainty/no invention 3; ambiguity 2 | 8 |
| Total | | 100 |

The 17-row evidence checklist in outputs/final_audit/rubric_checklist.csv expands
these weights. Evidence for a measurement effect is strong conditional on the
supplied snippet-change note, but monthly aggregates cannot mathematically
identify how much is recording versus genuine activity without assumptions.
