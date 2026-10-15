"""Collect 20 newest visible article cards per TECHi section, with audit evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import pandas as pd
import requests

BASE = 'https://www.techi.com/'
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'outputs' / 'techi_articles.csv'
AUDIT = ROOT / 'outputs' / 'techi_audit'
SECTIONS = ['AI', 'Markets', 'Crypto', 'Breakthroughs', 'Policy', 'Guides']
NAV_LABELS = {'AI': 'AI', 'Markets': 'Markets', 'Crypto': 'Crypto',
              'Tech Breakthroughs': 'Breakthroughs', 'Policy': 'Policy', 'Research Guides': 'Guides'}
COLUMNS = ['url', 'section', 'headline', 'author', 'date_shown', 'headline_word_count',
           'format', 'names_a_company', 'contains_a_number']
USER_AGENT = 'TechAboutAssessment/1.0 (educational article-metadata collection; 1 request per 2 seconds)'
# Explicit matching dictionary, not complete named-entity recognition. Products are excluded.
COMPANIES = ['Adobe', 'Advantest', 'Akamai', 'Alphabet', 'Amazon', 'AMD', 'Anthropic',
 'AppLovin', 'ARM', 'ASML', 'Astera Labs', 'Bernstein', 'Black Forest Labs', 'BlueStar',
 'Cerebras', 'C.H. Robinson', 'Ciena', 'Circle', 'CME', 'Coinbase', 'CyberTAN', 'DeepSeek',
 'Dell', 'Einride', 'Elisity', 'Firebird', 'FormFactor', 'GitHub', 'Google', 'Grayscale',
 'Grain', 'Gumloop', 'Huawei', 'Intel', 'IonQ', 'Iridium', 'Marvell', 'Meta', 'Micron',
 'Microsoft', 'MicroStrategy', 'Mistral', 'Nvidia', 'OpenAI', 'Palantir', 'Pfizer', 'PTC',
 'Rambus', 'Robinhood', 'Roblox', 'Rocket Lab', 'RXO', 'Samsung', 'Schneider Electric',
 'Semrush', 'SpaceX', 'Square Enix', 'Strive', 'TD SYNNEX',
 'Teradyne', 'Tesla', 'TSMC', 'Unity', 'Verona', 'xAI', 'Z.ai']
COMPANY_PATTERN = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(x) for x in COMPANIES) + r')(?!\w)', re.I)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def log_event(event, **details):
    AUDIT.mkdir(parents=True, exist_ok=True)
    with (AUDIT / 'scrape_log.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'logged_at_utc': utc_now(), 'event': event, **details}, ensure_ascii=False) + '\n')


class PublicPages:
    """Serial requests, robots checks, saved responses, and offline replay."""
    def __init__(self, replay=False):
        self.replay = replay
        self.last_request = None
        self.robots = None
        self.delay = 2.1

    def get(self, url):
        for _ in range(5):
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'www.techi.com':
                raise ValueError(f'Not a public TECHi HTTPS URL: {url}')
            if self.robots and not self.robots.can_fetch(USER_AGENT, url):
                raise ValueError(f'robots.txt disallows {url}')
            key = hashlib.sha256(url.encode()).hexdigest()
            path = AUDIT / 'pages' / key
            if self.replay:
                meta = json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
                html = path.with_suffix('.html').read_text(encoding='utf-8')
                if meta['source_url'] != url or hashlib.sha256(html.encode()).hexdigest() != meta['sha256']:
                    raise ValueError('Snapshot URL or checksum mismatch')
                log_event('replay', **meta)
                return html, meta['source_url']
            if self.last_request is not None:
                time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            accessed_at = utc_now()
            log_event('request', url=url, accessed_at_utc=accessed_at, user_agent=USER_AGENT)
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=40, allow_redirects=False)
            log_event('response', url=url, status=response.status_code)
            if response.is_redirect:
                url = urljoin(url, response.headers['Location'])
                log_event('redirect', destination=url)
                continue
            response.raise_for_status()
            response.encoding = 'utf-8'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_suffix('.html').write_text(response.text, encoding='utf-8')
            meta = {'source_url': url, 'accessed_at_utc': accessed_at, 'http_status': response.status_code,
                    'sha256': hashlib.sha256(response.text.encode()).hexdigest()}
            path.with_suffix('.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            return response.text, url
        raise ValueError('Too many redirects')

    def check_robots(self):
        text, url = self.get(urljoin(BASE, 'robots.txt'))
        self.robots = RobotFileParser(url)
        self.robots.parse(text.splitlines())
        self.delay = max(self.delay, self.robots.crawl_delay(USER_AGENT) or 0)
        log_event('robots', delay_seconds=self.delay, source_url=url)


def discover_sections(html):
    soup = BeautifulSoup(html, 'html.parser')
    found = {}
    for link in soup.select('nav[aria-label="Primary"] a[href]'):
        section = NAV_LABELS.get(link.get_text(' ', strip=True))
        if section:
            found[section] = urljoin(BASE, link['href'])
    if set(found) != set(SECTIONS):
        raise ValueError(f'Missing section(s) in real navigation: {set(SECTIONS) - set(found)}')
    return found


def parse_listing(html, source_url):
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('main article.techi-article-card')
    if not cards:
        raise ValueError(f'No verified article cards: {source_url}')
    records = []
    for position, card in enumerate(cards, 1):
        heading = card.select_one('h2')
        link = heading.find_parent('a', href=True) if heading else None
        author = card.select_one('a[href^="/@"]')
        date = card.select_one('time[datetime]')
        if not all([heading, link, author, date]):
            raise ValueError(f'Unverified card fields at {source_url} position {position}')
        headline = heading.get_text(' ', strip=True)
        author_text = author.get_text(' ', strip=True)
        date_shown = date.get_text()  # Visible date text, never datetime= or an inferred date.
        if not headline or not author_text or not date_shown.strip():
            raise ValueError(f'Empty card field at {source_url} position {position}')
        timestamp = datetime.fromisoformat(date['datetime'].replace('Z', '+00:00'))
        if timestamp.tzinfo is None:
            raise ValueError('Cannot verify date ordering without a timezone')
        records.append({'url': urldefrag(urljoin(source_url, link['href']))[0],
                        'headline': headline, 'author': author_text, 'date_shown': date_shown,
                        'timestamp': timestamp, 'position': position})
    next_urls = {urljoin(source_url, a['href']) for a in soup.select('main a[href]')
                 if a.get('rel') == ['next'] or a.get_text(' ', strip=True).startswith('Next')}
    if len(next_urls) > 1:
        raise ValueError('Conflicting pagination links')
    return records, next(iter(next_urls), None)


def headline_features(headline):
    lowered = headline.casefold()
    if re.search(r'\bhow to\b', lowered):
        format_name = 'how_to'
    elif headline.rstrip().endswith('?'):
        format_name = 'question'
    elif re.match(r'^(?:top\s+)?\d+\s+', lowered):
        format_name = 'listicle'
    elif re.search(r'\breviews?\b', lowered):
        format_name = 'review'
    elif re.match(r'^(?:how|why|what)\b', lowered):
        format_name = 'explainer'
    else:
        format_name = 'other'
    return {'headline_word_count': sum(any(c.isalnum() for c in token) for token in headline.split()),
            'format': format_name, 'names_a_company': bool(COMPANY_PATTERN.search(headline)),
            'contains_a_number': bool(re.search(r'\d', headline))}


def validate_articles(data):
    return {
        'exact_column_order': list(data.columns) == COLUMNS,
        'exactly_120_rows': len(data) == 120,
        '20_in_every_section': data['section'].value_counts().to_dict() == dict.fromkeys(SECTIONS, 20),
        'distinct_within_each_section': not data.duplicated(['section', 'url']).any(),
        'no_missing_values': not data.isna().any().any() and not data.astype(str).map(lambda x: not x.strip()).any().any(),
        'public_article_urls': data['url'].map(lambda x: urlparse(x).scheme == 'https' and urlparse(x).hostname == 'www.techi.com').all(),
        'derived_fields_recompute': all(all(row[key] == value for key, value in headline_features(row['headline']).items())
                                        for row in data.to_dict('records')),
    }


def collect(replay=False):
    client = PublicPages(replay)
    log_event('run_started', replay=replay,
              terms_decision='User instructed proceeding despite terms restriction; robots and rate limit retained.')
    client.check_robots()
    html, _ = client.get(BASE)
    listing_urls = discover_sections(html)
    log_event('navigation_discovered', listing_urls=listing_urls)
    rows = []
    for section in SECTIONS:
        page = listing_urls[section]
        seen_pages, seen_articles = set(), set()
        selected = []
        previous_timestamp = None
        while page and len(selected) < 20:
            if page in seen_pages:
                raise ValueError(f'Pagination loop in {section}')
            seen_pages.add(page)
            html, source = client.get(page)
            records, next_page = parse_listing(html, source)
            for record in records:
                stamp = record['timestamp']
                if previous_timestamp is not None and stamp > previous_timestamp:
                    raise ValueError(f'Listing not newest-first: {source}')
                previous_timestamp = stamp
                if record['url'] in seen_articles:
                    log_event('duplicate_skipped', section=section, source_url=source, url=record['url'])
                    continue
                seen_articles.add(record['url'])
                if len(selected) == 20:
                    continue
                row = {key: record[key] for key in ['url', 'headline', 'author', 'date_shown']}
                row.update(section=section, **headline_features(row['headline']))
                selected.append(row)
                log_event('article_selected', source_url=source, position=record['position'],
                          timestamp=stamp.isoformat(), **row)
            log_event('pagination', section=section, source_url=source, visible_cards=len(records),
                      next_url=next_page, followed=len(selected) < 20 and bool(next_page),
                      reason='20 distinct articles reached' if len(selected) == 20 else 'Need more articles')
            page = next_page
        if len(selected) != 20:
            raise ValueError(f'Only {len(selected)} verified distinct articles for {section}')
        rows.extend(selected)
        print(f'{section}: {len(selected)}')
    data = pd.DataFrame(rows, columns=COLUMNS)
    checks = validate_articles(data)
    report = {'status': 'success' if all(checks.values()) else 'failed', 'completed_at_utc': utc_now(),
              'replay': replay, 'section_counts': data.section.value_counts().to_dict(),
              'listing_urls': listing_urls, 'rows': len(data), 'distinct_urls': data.url.nunique(),
              'cross_listing_rule': 'Preserve newest 20 per section; cross-listed URLs are retained.',
              'validation': {key: bool(value) for key, value in checks.items()}}
    (OUTPUT.parent / 'techi_scrape_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if not all(checks.values()):
        raise ValueError('Dataset validation failed; final CSV not written')
    temporary = OUTPUT.with_suffix('.tmp')
    data.to_csv(temporary, index=False, encoding='utf-8', lineterminator='\n')
    temporary.replace(OUTPUT)
    log_event('output_saved', path=str(OUTPUT), **report)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', action='store_true', help='Reproduce saved HTML without network requests')
    args = parser.parse_args()
    try:
        data = collect(args.replay)
    except (requests.RequestException, OSError, ValueError, KeyError) as error:
        log_event('run_failed', error=str(error))
        parser.exit(1, f'Collection failed: {error}\nFinal CSV not replaced; see audit log.\n')
    print(f'Saved {len(data)} article-section rows ({data.url.nunique()} distinct URLs) to {OUTPUT}')


if __name__ == '__main__':
    main()
