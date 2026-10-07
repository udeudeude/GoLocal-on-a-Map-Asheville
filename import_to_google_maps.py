#!/usr/bin/env python3
import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from golocal_common import load_config

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / 'golocal_physical.json'
PROGRESS_FILE = HERE / 'progress.json'
FAIL_FILE = HERE / 'failed.json'
CONFIG = load_config()
LIST_NAME = str(CONFIG['list_name'])
LIST_EMOJI = str(CONFIG['list_emoji'])
MAPS = str(CONFIG['maps_url'])


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def normalize(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def name_looks_ok(expected, actual):
    e, a = normalize(expected), normalize(actual)
    if not e or not a:
        return False
    if e == a or e in a or a in e:
        return True
    et = set(e.split())
    at = set(a.split())
    return len(et & at) >= max(1, min(2, len(et)))


def address_looks_ok(expected, actual):
    """Compare an address fragment against Maps text despite common abbreviations."""
    def canon(text):
        t = normalize(text)
        replacements = {
            'street': 'st', 'avenue': 'ave', 'road': 'rd', 'drive': 'dr',
            'boulevard': 'blvd', 'lane': 'ln', 'highway': 'hwy', 'court': 'ct',
            'place': 'pl', 'parkway': 'pkwy', 'circle': 'cir', 'square': 'sq',
            'trail': 'trl',
        }
        toks = [replacements.get(tok, tok) for tok in t.split()]
        return ' '.join(toks)

    e, a = canon(expected), canon(actual)
    if not e or not a:
        return False
    if e in a:
        return True
    et = e.split()
    if not et:
        return False
    number = next((x for x in et if any(ch.isdigit() for ch in x)), '')
    if number and number not in a.split():
        return False
    words = [x for x in et if x != number]
    if not words:
        return bool(number)
    aset = set(a.split())
    hits = sum(1 for x in words if x in aset)
    return hits >= max(1, len(words) - 1)


def open_saved(page):
    page.goto(MAPS, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(2500)
    page.locator('button[jsaction="navigationrail.saved"]').first.click(force=True)
    page.wait_for_timeout(2200)


def ensure_list(page):
    open_saved(page)
    main = page.locator('[role="main"]').first
    text = main.inner_text(timeout=15000)
    created = False
    if LIST_NAME not in text:
        page.get_by_role('button', name='New list').click()
        page.wait_for_timeout(1200)
        h1 = page.locator('h1').first
        h1.click()
        page.keyboard.press('Meta+A')
        page.keyboard.type(LIST_NAME)
        page.keyboard.press('Tab')
        page.keyboard.press('Enter')
        page.wait_for_timeout(2500)
        created = True

    if not page.locator('h1').filter(has_text=LIST_NAME).count():
        open_saved(page)
        page.get_by_text(LIST_NAME, exact=True).first.click()
        page.wait_for_timeout(1800)

    try:
        btn = page.locator('button[aria-label="Choose icon"], button[aria-label="Edit icon"]').first
        if btn.count() and btn.is_visible():
            btn.click()
            page.wait_for_timeout(900)
            em = page.locator(
                '[role="dialog"][aria-label="Emoji characters palette"] [aria-label="%s"]' % LIST_EMOJI
            ).first
            if em.count():
                em.scroll_into_view_if_needed()
                em.click()
                page.wait_for_timeout(900)
    except Exception:
        pass

    if created:
        print('Created Google Maps list:', LIST_NAME)
        page.wait_for_timeout(8000)
    else:
        print('Using existing Google Maps list:', LIST_NAME)


def locate_place_main(page, expected_name):
    mains = page.locator('[role="main"]')
    for i in range(mains.count()):
        m = mains.nth(i)
        try:
            if m.locator('button[aria-label="Save"], button:has-text("Saved")').count():
                return m
        except Exception:
            pass
    return page.locator('[role="main"]').first


def save_one(page, row):
    page.goto(MAPS, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(1600)
    search = page.locator('input[name="q"][role="combobox"], #searchboxinput').first
    search.click()
    search.fill('')
    search.type(row['maps_query'])
    page.keyboard.press('Enter')
    page.wait_for_timeout(4300)

    main = locate_place_main(page, row['name'])
    if not main.locator('button[aria-label="Save"], button:has-text("Saved")').count():
        candidates = page.locator('a[aria-label]')
        picked = False
        for i in range(min(candidates.count(), 80)):
            c = candidates.nth(i)
            try:
                label = c.get_attribute('aria-label') or ''
                if name_looks_ok(row['name'], label):
                    c.click()
                    page.wait_for_timeout(3500)
                    picked = True
                    break
            except Exception:
                pass
        if picked:
            main = locate_place_main(page, row['name'])

    header = ''
    try:
        header = page.locator('h1').first.inner_text(timeout=3000).strip()
    except Exception:
        pass

    body = page.locator('body').inner_text()
    anchor = row.get('anchor', '').strip()
    header_ok = bool(header and name_looks_ok(row['name'], header))
    anchor_ok = (not anchor) or address_looks_ok(anchor, body)

    if not header_ok and not anchor_ok:
        raise RuntimeError(
            f'place mismatch: expected name={row["name"]!r}, anchor={anchor!r}; '
            f'Maps header={header!r}'
        )
    if header_ok and anchor and not anchor_ok:
        print(f'  warning: address text differs, but Maps title matches: {header!r}')
    elif header and not header_ok and anchor_ok:
        print(f'  warning: Maps title {header!r} differs from Go Local {row["name"]!r}; address matches')

    save_btn = main.locator('button[aria-label="Save"], button:has-text("Saved")').first
    if not save_btn.count():
        raise RuntimeError('no Save/Saved button on resolved place')
    save_btn.click()
    page.wait_for_timeout(1500)

    item = page.locator('[role="menuitemradio"]:visible').filter(has_text=LIST_NAME).first
    if not item.count():
        page.keyboard.press('Escape')
        page.wait_for_timeout(1200)
        save_btn.click()
        page.wait_for_timeout(1500)
        item = page.locator('[role="menuitemradio"]:visible').filter(has_text=LIST_NAME).first
        if not item.count():
            raise RuntimeError(f'{LIST_NAME} list missing from Save menu')

    already = item.get_attribute('aria-checked') == 'true'
    if not already:
        item.click()
        page.wait_for_timeout(1300)
    page.keyboard.press('Escape')

    save_btn = locate_place_main(page, row['name']).locator(
        'button[aria-label="Save"], button:has-text("Saved")'
    ).first
    save_btn.click()
    page.wait_for_timeout(1000)
    item2 = page.locator('[role="menuitemradio"]:visible').filter(has_text=LIST_NAME).first
    ok = item2.count() and item2.get_attribute('aria-checked') == 'true'
    page.keyboard.press('Escape')
    if not ok:
        raise RuntimeError('save did not verify in list menu')
    return 'already' if already else 'saved', header


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=int(CONFIG['cdp_port']))
    ap.add_argument('--limit', type=int, default=0, help='For a test run; 0 means all')
    args = ap.parse_args()

    if not DATA_FILE.exists():
        sys.exit('Run collect_golocal.py first; golocal_physical.json is missing.')
    rows = load_json(DATA_FILE, [])
    if args.limit:
        rows = rows[:args.limit]
    progress = load_json(PROGRESS_FILE, {})
    failed = load_json(FAIL_FILE, {})

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{args.port}')
        ctx = browser.contexts[0]
        page = next((pg for pg in ctx.pages if 'google.com/maps' in pg.url), None) or ctx.new_page()
        page.bring_to_front()
        ensure_list(page)

        for i, row in enumerate(rows, 1):
            key = row['source_url']
            if key in progress:
                continue
            print(f'[{i}/{len(rows)}] {row["name"]}')
            try:
                status, maps_header = save_one(page, row)
                progress[key] = {
                    'status': status,
                    'name': row['name'],
                    'maps_header': maps_header,
                }
                failed.pop(key, None)
                print(' ', status)
            except Exception as e:
                failed[key] = {
                    'name': row['name'],
                    'error': str(e),
                    'query': row.get('maps_query', ''),
                    'anchor': row.get('anchor', ''),
                }
                print('  FAILED:', e)
            save_json(PROGRESS_FILE, progress)
            save_json(FAIL_FILE, failed)
            time.sleep(
                random.uniform(
                    float(CONFIG['delay_min_seconds']),
                    float(CONFIG['delay_max_seconds']),
                )
            )

    print(f'Done. Success/already: {len(progress)}; unresolved failures: {len(failed)}')
    print('Rerun the same command to resume. Failed entries are in failed.json.')


if __name__ == '__main__':
    main()
