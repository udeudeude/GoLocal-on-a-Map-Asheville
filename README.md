# Go Local on a Map: Asheville

Put Asheville Go Local Card businesses **inside ordinary Google Maps**, so the places that take your card stay visible while you browse, search for dinner, or look around town.

This is an unofficial community tool. It is not affiliated with Go Local Asheville or Google.

## What it does

1. Reads the current public [Go Local Asheville directory](https://golocalasheville.com/directory).
2. Keeps businesses that have a physical/mappable location.
3. Opens a separate Brave/Chrome profile and lets **you** sign into Google Maps directly.
4. Creates or reuses a normal Saved list named **Go Local Card**.
5. Adds each matching place to that list, verifying each save.
6. Remembers progress, so you can stop, resume, and retry failures without starting over.

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

The guided launcher installs the small Python dependencies into a local `.venv`, gathers the current Go Local directory, opens a dedicated Maps browser, runs a five-place test, and only then offers to continue with the full import.

If macOS blocks the launcher, Control-click it and choose **Open**.

## Why a separate browser window?

The importer needs browser automation access, but it does **not** need or read your ordinary Brave/Chrome profile. It launches a dedicated profile at `~/.golocal-maps-browser`. You sign into Google inside that browser window yourself; this tool does not receive your Google password.

## What gets created locally

- `golocal_all.csv` - current source inventory
- `golocal_physical.json` - physical/mappable businesses selected for import
- `golocal_skipped.csv` - listings without a usable map destination
- `progress.json` - successfully saved places
- `failed.json` - unresolved places and the reason they failed

These generated files are ignored by Git.

## Manual / advanced workflow

If you prefer to run each stage yourself:

1. `setup.command`
2. `1_COLLECT.command`
3. `2_OPEN_MAPS_BROWSER.command`
4. Sign into Google Maps in the dedicated browser window
5. `3_TEST_IMPORT.command`
6. Inspect **Google Maps → Saved/You → Go Local Card**
7. `4_IMPORT_ALL.command`
8. `5_STATUS.command`

Rerunning `4_IMPORT_ALL.command` is safe. Successful places are skipped and unresolved ones are retried.

## Customize the list

Copy `config.example.json` to `config.json` and edit it before first import. The defaults are:

```json
{
  "list_name": "Go Local Card",
  "list_emoji": "❣️"
}
```

Changing the icon later in Google Maps does **not** require re-importing anything.

## A note about failures

Google Maps and the Go Local directory do not always describe a business identically. Some businesses are renamed, moved, represented only as a search result, or simply do not have a savable Maps place. The importer deliberately refuses uncertain matches rather than quietly save the wrong business.

A second import pass often rescues transient Google Maps failures. The rest can simply be left unresolved.

## Privacy

This project does not send your Google credentials anywhere. Your Google login happens in the browser, and the progress/source files remain on your computer. The tool fetches public Go Local directory pages and automates the Google Maps web interface on your behalf.

## Maintenance

Google Maps is not offering an official API for writing personal Saved lists, so this project necessarily automates the Maps web interface. Google can change that interface. If it breaks, please open an issue with the Terminal output and, if useful, a screenshot with personal account details cropped out.

## License

MIT. See [LICENSE](LICENSE).
