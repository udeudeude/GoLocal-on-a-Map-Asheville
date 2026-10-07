# Go Local on a Map: Asheville

Put Asheville Go Local Card businesses **inside ordinary Google Maps**, so the places that take your card stay visible while you browse, search for dinner, or look around town.

This is an unofficial community tool. It is not affiliated with Go Local Asheville or Google.

## What it does

1. Reads the current public [Go Local Asheville directory](https://golocalasheville.com/directory).
2. Keeps businesses that have a physical/mappable location.
3. Opens a separate Brave/Chrome profile and lets **you** sign into Google Maps directly.
4. Creates or reuses a normal Saved list named **Go Local Card**.
5. Adds each matching place to that list, verifying each save.
6. Adds the current **Go Local card benefit/deal as a per-place Google Maps note**, for example `❣️ Go Local: 10% off ...`.
7. Remembers progress, so you can stop, resume, retry failures, and refresh benefits later without starting over.

The result syncs through your Google account to Google Maps on iPhone and Android. The Mac is only the assembly line.

## Easiest setup on a Mac

Requirements:

- macOS
- Python 3
- Brave Browser or Google Chrome
- a Google account

Then:

1. Download this repository: **Code → Download ZIP**.
2. Unzip it.
3. Double-click **`START_HERE.command`**.
4. Follow the prompts.

The guided launcher installs the small Python dependencies into a local `.venv`, gathers the current Go Local directory, opens a dedicated Maps browser, runs a five-place test, and only then offers to continue with the full import. The test places should show both the saved-list marker and, when Go Local publishes one, the benefit note.

If macOS blocks the launcher, Control-click it and choose **Open**.

## Benefit notes

The Go Local directory publishes card offers for many businesses. The collector already captures those offers; `update_benefits.py` writes them into the note attached to that place in your **Go Local Card** list.

Example:

> ❣️ Go Local: 10% off purchases of $25+

Benefit notes are deliberately tracked separately from place-saving. If Google Maps refuses a note, the business remains saved to the list and the note failure is recorded for retry.

If the directory changes later, run **`1_COLLECT.command`** to refresh the source data, then **`6_UPDATE_BENEFITS.command`**. It revisits only places this tool has already imported and backfills or refreshes their benefit notes. It does **not** rebuild the list.

If a place already has personal note text, the updater preserves it. It replaces an existing `Go Local:` line when present; otherwise it prepends the current Go Local benefit above the personal note.

## Why a separate browser window?

The importer needs browser automation access, but it does **not** need or read your ordinary Brave/Chrome profile. It launches a dedicated profile at `~/.golocal-maps-browser`. You sign into Google inside that browser window yourself; this tool does not receive your Google password.

## What gets created locally

- `golocal_all.csv` - current source inventory
- `golocal_physical.json` - physical/mappable businesses selected for import, including captured card offers
- `golocal_skipped.csv` - listings without a usable map destination
- `progress.json` - successfully saved places
- `failed.json` - unresolved places and the reason they failed
- `benefits_progress.json` - verified benefit notes and the offer text used
- `benefits_failed.json` - benefit notes that could not be written or verified

These generated files are ignored by Git.

## Manual / advanced workflow

If you prefer to run each stage yourself:

1. `setup.command`
2. `1_COLLECT.command`
3. `2_OPEN_MAPS_BROWSER.command`
4. Sign into Google Maps in the dedicated browser window
5. `3_TEST_IMPORT.command`
6. Inspect **Google Maps → Saved/You → Go Local Card** and check the benefit notes
7. `4_IMPORT_ALL.command`
8. `5_STATUS.command`
9. Later, use `6_UPDATE_BENEFITS.command` whenever you want to backfill/refresh Go Local deals

Rerunning `4_IMPORT_ALL.command` is safe. Successful places are skipped and unresolved ones are retried. Benefit-note failures are retried independently and unchanged verified offers are skipped.

## Customize the list

Copy `config.example.json` to `config.json` and edit it before first import. The relevant defaults are:

```json
{
  "list_name": "Go Local Card",
  "list_emoji": "❣️",
  "write_offer_notes": true,
  "note_prefix": "❣️ Go Local: "
}
```

Changing the list icon later in Google Maps does **not** require re-importing anything. Set `write_offer_notes` to `false` if you want pins without deal notes.

## A note about failures

Google Maps and the Go Local directory do not always describe a business identically. Some businesses are renamed, moved, represented only as a search result, or simply do not have a savable Maps place. The importer deliberately refuses uncertain matches rather than quietly save the wrong business.

A second import pass often rescues transient Google Maps failures. Note-writing is similarly best-effort because it depends on Google's web interface; a note failure does not undo a successful place save.

## Privacy

This project does not send your Google credentials anywhere. Your Google login happens in the browser, and the progress/source files remain on your computer. The tool fetches public Go Local directory pages and automates the Google Maps web interface on your behalf.

## Maintenance

Google Maps does not provide an official API for writing personal Saved lists or their notes, so this project necessarily automates the Maps web interface. Google can change that interface. If it breaks, please open an issue with the Terminal output and, if useful, a screenshot with personal account details cropped out.

## License

MIT. See [LICENSE](LICENSE).
