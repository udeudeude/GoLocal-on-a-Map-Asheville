# Changelog

## 0.2.0 - 2026-10-06

- Adds each published Go Local card benefit as a per-place Google Maps note.
- Adds `6_UPDATE_BENEFITS.command` to backfill or refresh deals on places already imported.
- Preserves personal note text while replacing/prepending the generated `Go Local:` line.
- Tracks benefit-note success and failure independently in `benefits_progress.json` and `benefits_failed.json`.
- Skips unchanged verified offers on later refreshes.
- Makes offer-note behavior configurable with `write_offer_notes` and `note_prefix`.

## 0.1.0 - 2026-10-06

- First public release.
- Collects current physical/mappable Asheville Go Local businesses from the public directory.
- Creates/reuses a normal Google Maps Saved list and adds businesses to it.
- Uses a dedicated Brave/Chrome profile, so normal browser profiles are untouched.
- Five-place test pass before full import.
- Resumable progress and retryable failures.
- User-configurable list name, icon, browser profile, port, and pacing.
- macOS one-file guided launcher plus manual step-by-step launchers.
