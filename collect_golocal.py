#!/usr/bin/env python3
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from golocal_common import find_browser

BASE = 'https://golocalasheville.com'
DIRECTORY = BASE + '/directory'
OUT = Path(__file__).resolve().parent

STREET_SUFFIX = r'(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Way|Highway|Hwy\.?|Court|Ct\.?|Place|Pl\.?|Parkway|Pkwy\.?|Circle|Cir\.?|Square|Sq\.?|Trail|Trl\.?)'


def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def _business_hrefs(page):
    hrefs = page.locator('.facetwp-template a[href*="/business/"]').evaluate_all(
        '(els) => els.map(e => e.href)'
    )
    return sorted(set(u.split('#')[0] for u in hrefs if '/business/' in u))


def _goto_facet_page(page, target):
    page.evaluate(
        '''target => {
          window.__golocalFacetLoaded = false;
          document.addEventListener('facetwp-loaded', () => {
            window.__golocalFacetLoaded = true;
          }, { once: true });
          FWP.paged = target;
          FWP.soft_refresh = true;
          FWP.refresh();
        }''',
        target,
    )
    page.wait_for_function(
        '''target => window.__golocalFacetLoaded === true &&
                     window.FWP && FWP.settings && FWP.settings.pager &&
                     Number(FWP.settings.pager.page) === Number(target)''',
        arg=target,
        timeout=30000,
    )
    page.wait_for_timeout(250)


def collect_business_urls():
    urls = set()
    browser_name, browser_path = find_browser()
    if not browser_path:
        raise RuntimeError('Brave Browser or Google Chrome was not found.')

    print(f'Using browser: {browser_name}')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(browser_path), headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 1000})
        page.goto(DIRECTORY, wait_until='domcontentloaded', timeout=60000)

        page.wait_for_function(
            '''() => window.FWP && FWP.loaded && FWP.settings &&
                     FWP.settings.pager && FWP.settings.pager.total_pages''',
            timeout=30000,
        )
        total_pages = int(page.evaluate('Number(FWP.settings.pager.total_pages)'))
        total_rows = int(page.evaluate('Number(FWP.settings.pager.total_rows)'))
        print(f'Directory reports {total_rows} listings across {total_pages} pages.')

        if total_pages < 1 or total_pages > 250:
            raise RuntimeError(f'Unexpected FacetWP page count: {total_pages}')

        for page_num in range(1, total_pages + 1):
            if page_num > 1:
                before_page = int(page.evaluate('Number(FWP.settings.pager.page)'))
                _goto_facet_page(page, page_num)
                after_page = int(page.evaluate('Number(FWP.settings.pager.page)'))
                if after_page != page_num:
                    raise RuntimeError(
                        f'FacetWP failed to advance from page {before_page} to {page_num}; '
                        f'current page is {after_page}.'
                    )

            hrefs = _business_hrefs(page)
            if not hrefs:
                raise RuntimeError(f'No business links found on directory page {page_num}.')

            before = len(urls)
            urls.update(hrefs)
            added = len(urls) - before
            print(f'Directory page {page_num}/{total_pages}: +{added} ({len(urls)} total)')

            if page_num > 1 and page_num < total_pages and added == 0:
                raise RuntimeError(
                    f'Pagination reached page {page_num} but yielded no new business URLs; '
                    'stopping rather than collecting duplicate page data.'
                )

        browser.close()

    if len(urls) < max(100, int(total_rows * 0.80)):
        raise RuntimeError(
            f'Collected only {len(urls)} unique business URLs although the directory reports '
            f'{total_rows} listings. Stopping so an incomplete map is not imported.'
        )
    return sorted(urls)


def directions_destination(href):
    if not href:
        return ''
    m = re.search(r'/maps/dir//([^?#]+)', href)
    if not m:
        return ''
    return clean(unquote(m.group(1)).replace('+', ' '))


def derive_addressish(destination, name):
    d = clean(destination)
    n = clean(name)
    if n and d.lower().startswith(n.lower()):
        d = clean(d[len(n):])
    return d


def derive_anchor(addressish):
    if not addressish:
        return ''
    m = re.search(rf'\b\d+[A-Za-z-]*\s+.+?\b{STREET_SUFFIX}\b', addressish, re.I)
    if m:
        return clean(m.group(0))
    m = re.search(r'\b\d+[A-Za-z-]*(?:\s+[A-Za-z0-9.#-]+){1,4}', addressish)
    if m:
        return clean(m.group(0))
    m = re.search(r'\b\d{5}(?:-\d{4})?\b', addressish)
    return m.group(0) if m else ''


def extract_offer(text):
    text = clean(text)
    m = re.search(r'Go Local Card Offer\s*(.*?)\s*Get your Go Local card', text, re.I)
    return clean(m.group(1)) if m else ''


def parse_business(url, session):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    h1 = soup.find('h1')
    name = clean(h1.get_text(' ', strip=True)) if h1 else url.rstrip('/').split('/')[-1]

    get_dir = None
    for a in soup.find_all('a', href=True):
        if clean(a.get_text(' ', strip=True)).lower() == 'get directions':
            get_dir = a.get('href')
            break

    dest = directions_destination(get_dir)
    addressish = derive_addressish(dest, name)
    anchor = derive_anchor(addressish)
    offer = extract_offer(soup.get_text(' ', strip=True))

    return {
        'name': name,
        'source_url': url,
        'directions_url': get_dir or '',
        'maps_query': dest or name,
        'addressish': addressish,
        'anchor': anchor,
        'offer': offer,
        'physical': bool(get_dir and dest),
    }


def main():
    print('Collecting Go Local directory URLs...')
    urls = collect_business_urls()
    print(f'Found {len(urls)} unique business pages.')

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (GoLocal-on-a-Map-Asheville community tool)'})
    rows = []
    for i, url in enumerate(urls, 1):
        try:
            row = parse_business(url, session)
        except Exception as e:
            row = {
                'name': '', 'source_url': url, 'directions_url': '', 'maps_query': '',
                'addressish': '', 'anchor': '', 'offer': '', 'physical': False,
                'error': str(e),
            }
        rows.append(row)
        if i % 25 == 0 or i == len(urls):
            print(f'Parsed {i}/{len(urls)}')
        time.sleep(0.05)

    fields = [
        'name', 'physical', 'maps_query', 'addressish', 'anchor', 'offer',
        'source_url', 'directions_url', 'error',
    ]
    with (OUT / 'golocal_all.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

    physical = [r for r in rows if r.get('physical')]
    skipped = [r for r in rows if not r.get('physical')]

    with (OUT / 'golocal_physical.json').open('w', encoding='utf-8') as f:
        json.dump(physical, f, ensure_ascii=False, indent=2)
    with (OUT / 'golocal_skipped.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(skipped)

    print(f'Physical/mappable: {len(physical)}')
    print(f'No mappable address/directions link: {len(skipped)}')
    print('Wrote golocal_physical.json, golocal_all.csv, golocal_skipped.csv')


if __name__ == '__main__':
    main()
