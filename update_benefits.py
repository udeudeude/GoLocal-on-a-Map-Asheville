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
from import_to_google_maps import ensure_list, save_one

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / 'golocal_physical.json'
IMPORT_PROGRESS_FILE = HERE / 'progress.json'
BENEFITS_PROGRESS_FILE = HERE / 'benefits_progress.json'
BENEFITS_FAIL_FILE = HERE / 'benefits_failed.json'
CONFIG = load_config()
LIST_NAME = str(CONFIG['list_name'])
WRITE_OFFER_NOTES = bool(CONFIG.get('write_offer_notes', True))
NOTE_PREFIX = str(CONFIG.get('note_prefix', '❣️ Go Local: '))


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def generated_note(row):
    offer = (row.get('offer') or '').strip()
    if not offer:
        return ''
    return f'{NOTE_PREFIX}{offer}'.strip()


def merge_note(existing, generated):
    """Refresh our Go Local line while preserving a user's own note text."""
    existing = (existing or '').strip()
    generated = (generated or '').strip()
    if not existing:
        return generated

    lines = existing.splitlines()
    marker = re.compile(r'^\s*.*?Go\s+Local\s*:\s*.*$', re.I)
    for i, line in enumerate(lines):
        if marker.match(line):
            lines[i] = generated
            return '\n'.join(lines).strip()

    return f'{generated}\n\n{existing}'


def visible_note_action(page):
    patterns = (
        re.compile(r'^Add (?:a )?note', re.I),
        re.compile(r'^Edit (?:the )?note', re.I),
        re.compile(r'^Add note', re.I),
        re.compile(r'^Edit note', re.I),
    )
    for pattern in patterns:
        for role in ('button', 'link'):
            loc = page.get_by_role(role, name=pattern)
            for i in range(loc.count()):
                candidate = loc.nth(i)
                try:
                    if candidate.is_visible():
                        return candidate
                except Exception:
                    pass
        loc = page.get_by_text(pattern)
        for i in range(loc.count()):
            candidate = loc.nth(i)
            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                pass
    return None


def find_note_editor(page):
    selectors = (
        'textarea:visible',
        'input[placeholder*="note" i]:visible',
        '[contenteditable="true"]:visible',
    )
    for selector in selectors:
        loc = page.locator(selector)
        if loc.count():
            return loc.last
    return None


def editor_text(editor):
    tag = (editor.evaluate('(el) => el.tagName') or '').lower()
    if tag in ('textarea', 'input'):
        return editor.input_value()
    return editor.inner_text()


def fill_editor(page, editor, text):
    try:
        editor.fill(text)
        return
    except Exception:
        pass
    editor.click()
    page.keyboard.press('Meta+A')
    page.keyboard.insert_text(text)


def click_note_save(page):
    dialog = page.locator('[role="dialog"]:visible')
    scopes = [dialog.last] if dialog.count() else []
    scopes.append(page)
    labels = (
        re.compile(r'^Save$', re.I),
        re.compile(r'^Save note$', re.I),
        re.compile(r'^Done$', re.I),
    )
    for scope in scopes:
        for label in labels:
            buttons = scope.get_by_role('button', name=label)
            for i in reversed(range(buttons.count())):
                candidate = buttons.nth(i)
                try:
                    if candidate.is_visible():
                        candidate.click()
                        page.wait_for_timeout(900)
                        return True
                except Exception:
                    pass
    return False


def set_benefit_note(page, row):
    generated = generated_note(row)
    if not generated:
        return 'no offer'

    action = visible_note_action(page)
    if action is None:
        body = page.locator('body').inner_text()
        if generated in body:
            return 'already'
        raise RuntimeError('saved place has no Add note/Edit note control')

    action.scroll_into_view_if_needed()
    action.click()
    page.wait_for_timeout(700)
    editor = find_note_editor(page)
    if editor is None:
        raise RuntimeError('note editor did not appear')

    existing = editor_text(editor)
    target = merge_note(existing, generated)
    if existing.strip() == target.strip():
        page.keyboard.press('Escape')
        return 'already'

    fill_editor(page, editor, target)
    if not click_note_save(page):
        # Some Maps note editors save on blur.
        page.keyboard.press('Tab')
        page.wait_for_timeout(900)

    body = page.locator('body').inner_text()
    if generated in body:
        return 'updated'

    # Verify by reopening the editor if the note is not rendered in the place panel.
    action = visible_note_action(page)
    if action is not None:
        action.click()
        page.wait_for_timeout(600)
        verify_editor = find_note_editor(page)
        if verify_editor is not None and generated in editor_text(verify_editor):
            page.keyboard.press('Escape')
            return 'updated'
        page.keyboard.press('Escape')

    raise RuntimeError('note save could not be verified')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=int(CONFIG['cdp_port']))
    ap.add_argument('--limit', type=int, default=0, help='Process only the first N collected rows')
    ap.add_argument('--force', action='store_true', help='Recheck notes even when the current offer was already verified')
    args = ap.parse_args()

    if not WRITE_OFFER_NOTES:
        print('Benefit notes are disabled in config.json (write_offer_notes=false).')
        return
    if not DATA_FILE.exists():
        sys.exit('Run 1_COLLECT.command first; golocal_physical.json is missing.')
    if not IMPORT_PROGRESS_FILE.exists():
        sys.exit('Import some places first; progress.json is missing.')

    rows = load_json(DATA_FILE, [])
    if args.limit:
        rows = rows[:args.limit]
    import_progress = load_json(IMPORT_PROGRESS_FILE, {})
    done = load_json(BENEFITS_PROGRESS_FILE, {})
    failed = load_json(BENEFITS_FAIL_FILE, {})

    eligible = [
        row for row in rows
        if row.get('source_url') in import_progress and generated_note(row)
    ]
    print(f'{len(eligible)} imported places currently have a published Go Local benefit.')

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{args.port}')
        context = browser.contexts[0]
        page = next((pg for pg in context.pages if 'google.com/maps' in pg.url), None) or context.new_page()
        page.bring_to_front()
        ensure_list(page)

        for i, row in enumerate(eligible, 1):
            key = row['source_url']
            offer = (row.get('offer') or '').strip()
            prior = done.get(key, {})
            if not args.force and prior.get('offer') == offer and prior.get('status') in ('updated', 'already'):
                continue

            print(f'[{i}/{len(eligible)}] {row["name"]}')
            try:
                save_status, maps_header = save_one(page, row)
                note_status = set_benefit_note(page, row)
                done[key] = {
                    'name': row['name'],
                    'offer': offer,
                    'status': note_status,
                    'place_status': save_status,
                    'maps_header': maps_header,
                }
                failed.pop(key, None)
                print('  benefit note:', note_status)
            except Exception as e:
                failed[key] = {
                    'name': row['name'],
                    'offer': offer,
                    'error': str(e),
                }
                print('  BENEFIT NOTE FAILED:', e)

            save_json(BENEFITS_PROGRESS_FILE, done)
            save_json(BENEFITS_FAIL_FILE, failed)
            time.sleep(
                random.uniform(
                    float(CONFIG['delay_min_seconds']),
                    float(CONFIG['delay_max_seconds']),
                )
            )

    print(f'Done. Benefit notes verified: {len(done)}; unresolved note failures: {len(failed)}.')
    print('Rerunning this command is safe; unchanged verified offers are skipped.')


if __name__ == '__main__':
    main()
