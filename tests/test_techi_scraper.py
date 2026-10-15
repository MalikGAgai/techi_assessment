"""Artificial HTML fixtures stay in tests, never in the collected dataset."""
import pandas as pd
import pytest
from urllib.robotparser import RobotFileParser

import scrape_articles as scraper

from scrape_articles import (
    COLUMNS, SECTIONS, headline_features, discover_sections, parse_listing,
    validate_articles,
)


def card(title="Fixture headline", date=" 1 day ago ", author="Fixture Author"):
    return f'''<article class="techi-article-card"><a href="/fixture/">
    <h2>{title}</h2></a><a href="/@fixture/">{author}</a>
    <time datetime="2026-10-13T10:00:00Z">{date}</time></article>'''


def test_date_is_not_normalized():
    records, next_url = parse_listing('<main>' + card() + '</main>', 'https://www.techi.com/section/')
    assert records[0]['date_shown'] == ' 1 day ago '
    assert records[0]['author'] == 'Fixture Author'
    assert next_url is None


def test_explicit_pagination_link():
    html = '<main>' + card() + '<a href="?page=2">Next →</a></main>'
    assert parse_listing(html, 'https://www.techi.com/section/')[1] == 'https://www.techi.com/section/?page=2'


@pytest.mark.parametrize('field', ['author', 'date', 'headline'])
def test_unverified_fields_fail(field):
    html = card(author='' if field == 'author' else 'Fixture Author',
                date='' if field == 'date' else 'Oct 13, 2026',
                title='' if field == 'headline' else 'Fixture')
    with pytest.raises(ValueError):
        parse_listing('<main>' + html + '</main>', 'https://www.techi.com/')


@pytest.mark.parametrize('headline,expected', [
    ('How to use Microsoft’s AI in 2026', (7, 'how_to', True, True)),
    ('Why NVIDIA’s AI matters?', (4, 'question', True, False)),
    ('5 AI-memory tools — tested', (4, 'listicle', False, True)),
    ('A pineapple grows', (3, 'other', False, False)),
    ('Grok 4.7 review: what changed', (5, 'review', False, True)),
    ('What Meta changes', (3, 'explainer', True, False)),
    ('A new strategy for AI', (5, 'other', False, False)),
    ('Three chips use LPDDR6', (4, 'other', False, True)),
])
def test_headline_rules(headline, expected):
    features = headline_features(headline)
    assert tuple(features.values()) == expected


def test_navigation_does_not_guess_missing_sections():
    with pytest.raises(ValueError, match='navigation'):
        discover_sections('<nav aria-label="Primary"><a href="/real/">AI</a></nav>')


def test_validation_rejects_short_dataset():
    checks = validate_articles(pd.DataFrame(columns=COLUMNS))
    assert not all(checks.values())


def test_cross_listing_is_valid_but_duplicate_section_url_is_not():
    rows = []
    for section in SECTIONS:
        for number in range(20):
            title = f'Fixture {number}'
            rows.append(dict(url=f'https://www.techi.com/fixture-{number}/', section=section,
                             headline=title, author='Fixture Author', date_shown='Oct 1, 2026',
                             **headline_features(title)))
    data = pd.DataFrame(rows, columns=COLUMNS)
    assert all(validate_articles(data).values())
    data.loc[1, 'url'] = data.loc[0, 'url']
    assert not validate_articles(data)['distinct_within_each_section']


def test_rate_limit_and_replay_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(scraper, 'AUDIT', tmp_path)
    sleeps, requests = [], []
    monkeypatch.setattr(scraper.time, 'monotonic', lambda: 100.0)
    monkeypatch.setattr(scraper.time, 'sleep', sleeps.append)

    class Response:
        is_redirect = False
        status_code = 200
        text = '<html>fixture only</html>'
        def raise_for_status(self):
            pass

    def fake_get(url, **kwargs):
        requests.append((url, kwargs))
        return Response()

    monkeypatch.setattr(scraper.requests, 'get', fake_get)
    client = scraper.PublicPages()
    client.get('https://www.techi.com/')
    client.get('https://www.techi.com/second/')
    assert sleeps == [2.1]
    assert len(requests) == 2
    assert requests[0][1]['allow_redirects'] is False
    assert requests[0][1]['headers']['User-Agent'] == scraper.USER_AGENT
    text, url = scraper.PublicPages(replay=True).get('https://www.techi.com/')
    assert text == Response.text
    assert len(requests) == 2
    for path in (tmp_path / 'pages').glob('*.html'):
        path.write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='checksum mismatch'):
        scraper.PublicPages(replay=True).get('https://www.techi.com/')


def test_robots_denial_stops_before_request(tmp_path, monkeypatch):
    monkeypatch.setattr(scraper, 'AUDIT', tmp_path)
    client = scraper.PublicPages()
    client.robots = RobotFileParser()
    client.robots.parse(['User-agent: *', 'Disallow: /private/'])
    def unexpected_request(*args, **kwargs):
        pytest.fail('robots.txt denial must happen before a request')
    monkeypatch.setattr(scraper.requests, 'get', unexpected_request)
    with pytest.raises(ValueError, match='robots.txt disallows'):
        client.get('https://www.techi.com/private/')
