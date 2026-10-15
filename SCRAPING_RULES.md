# TECHi collection rules

## Source and selection

The scraper reads `https://www.techi.com/robots.txt`, then the homepage's
`nav[aria-label="Primary"]`. It maps the actual visible navigation labels to
assessment section names. It does not derive URLs from names or request the
`/category/` landing page. These navigation links were verified with HTTP 200
during collection on 15 October 2026:

| Assessment section | Listing URL |
| --- | --- |
| AI | https://www.techi.com/category/ai-intelligence/ |
| Markets | https://www.techi.com/category/markets-equities/ |
| Crypto | https://www.techi.com/category/crypto-defi/ |
| Breakthroughs | https://www.techi.com/category/tech-breakthroughs/ |
| Policy | https://www.techi.com/category/policy-impact/ |
| Guides | https://www.techi.com/category/research-tools-guides/ |

Each verified listing has 24 visible `main article.techi-article-card` elements.
The scraper checks that their `time[datetime]` timestamps are newest-first and
selects the first 20 distinct article URLs in each section. Equal timestamps
retain page order. Duplicated image and headline links do not count twice: only
the link wrapping the card's `h2` is used. URL fragments are removed.

When more cards are needed, it follows an actual visible `Next` link or a
`rel="next"` link; it never constructs pagination URLs. This collection did not
need a second page. Pagination links and the reason for stopping are logged.
The script stops if ordering cannot be verified, a required field is absent,
pagination loops, robots.txt disallows a page, or a section has fewer than 20.

The user selected **newest 20 per section**: a cross-listed article is retained
in each applicable section. The dataset has exactly 120 article-section rows,
not necessarily 120 different URLs. Section membership comes from the listing,
not keywords in the headline. No older articles replace cross-listed ones.

## Exact output schema and field rules

`url,section,headline,author,date_shown,headline_word_count,format,names_a_company,contains_a_number`

- **url:** absolute HTTPS URL from the anchor wrapping the card's `h2`; fragments
  removed. Article detail pages are not fetched. This is the listing's real
  article link, not an independently verified canonical URL.
- **section:** assessment name mapped from the real navigation label.
- **headline:** visible card `h2` text; HTML entities are decoded and layout
  whitespace is collapsed to single spaces. No rewriting or title inference.
- **author:** visible card byline anchor whose href starts with `/@`. It is not
  inferred from the URL, author slug, article subject, or another article.
- **date_shown:** `time.get_text()` exactly, without stripping, reformatting,
  translating relative dates, or replacing it with the `datetime` attribute.
  It is the date displayed on the listing at access time. Relative strings
  naturally change on later live runs; saved HTML reproduces this snapshot.
- **headline_word_count:** split on whitespace and count tokens containing at
  least one Unicode letter or digit (`str.isalnum`). Hyphenated terms,
  possessives, `$1.87B`, and `4.7` each count as one token. Standalone punctuation
  such as an em dash does not count. This is a defined token count, not a
  linguistic segmentation model.
- **format:** headline-pattern classification, applied in the following order:
  `how_to` if it contains the whole phrase `how to`; otherwise `question` if its
  final non-whitespace character is `?`; otherwise `listicle` if it starts with
  digits followed by whitespace, optionally preceded by `Top `; otherwise
  `review` if it contains the whole word `review` or `reviews`; otherwise
  `explainer` if it starts with `how`, `why`, or `what`; otherwise `other`.
  Matches ignore case. These are mechanical headline labels, not assertions
  about the full article's editorial format. For example, a leading year also
  triggers `listicle`; `other` is a defined fallback, not a guessed genre.
- **names_a_company:** `True` if the headline contains an entry in the fixed
  `COMPANIES` dictionary in `scrape_articles.py`, matched without case and with
  word boundaries around the full entry; otherwise `False`. The exact dictionary
  is versioned in the source. Possessives match, substrings do not: `Apple` would
  not match `pineapple`. Products such as Grok, Copilot, and ChatGPT do not imply
  a company mention. A name not in the dictionary, including an unlisted ticker,
  returns `False`. The ambiguous generic word `strategy` is deliberately excluded.
  This flag means **dictionary match**, not exhaustive company recognition;
  ambiguous names can still produce false positives. Review it as a heuristic.
- **contains_a_number:** `True` if the headline contains a Unicode decimal digit
  (`re.search(r"\d", headline)`); otherwise `False`. Includes years, percentages,
  prices, decimals, versions and embedded digits such as LPDDR6. Spelled-out
  numbers such as `three` alone do not match.

Unknown source fields are errors; the scraper never supplies guessed authors,
dates, or titles. Derived fields are always recalculated from the source headline.
Boolean columns are written as `True`/`False`, not as missing values or estimates.

## Access, audit and reproducibility

Requests are serial, with at least 2.1 seconds between starts, including redirects.
The User-Agent is `TechAboutAssessment/1.0 (educational article-metadata collection;
1 request per 2 seconds)`. Robots.txt is checked for every page and any larger
advertised crawl delay is respected. No private APIs, authentication, access
controls, images or JavaScript execution are used.

TECHi's terms prohibit automated bulk scraping. That restriction was reported;
the user subsequently explicitly instructed proceeding despite it. This change
does not represent permission from the website owner. The prior terms inspection
is retained as historical evidence; it is not the status of the completed run.

`outputs/techi_audit/scrape_log.jsonl` records requests, access times in UTC,
responses, navigation discovery, selected source fields, card positions, order
timestamps, duplicate skips, pagination and validation. `pages/` contains each
raw response and its source URL, access time and SHA-256 in a companion JSON.
These snapshots support `--replay` without fetching the site. The script rejects
replay snapshots whose checksums or URLs do not match. Keep snapshots local to
this assessment rather than publishing copies of complete website pages.

`outputs/techi_scrape_report.json` is the latest run's count and validation report.
The original `inspection.json` and older discovery logs describe earlier work.
The final CSV is replaced only after all validation passes; a failed run leaves
any previous CSV in place, so consult the latest log before using an old output.

Public article metadata stays separate from `traffic_table.csv` and
`outputs/synthetic_traffic/`. Neither traffic numbers nor article records are
invented, and no connection between the sources is inferred.
