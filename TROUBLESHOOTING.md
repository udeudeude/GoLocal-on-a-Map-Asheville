# Troubleshooting

## macOS says the command cannot be opened

Control-click the `.command` file, choose **Open**, then confirm. macOS may quarantine scripts downloaded from the internet.

## Brave / Chrome not found

Install Brave Browser or Google Chrome in `/Applications`, then rerun the launcher.

## The collector stops on pagination

That is intentional. The collector verifies that the Go Local directory actually advanced to the next page rather than quietly importing duplicates. The site may have changed; open an issue with the Terminal output.

## Some businesses fail to import

A few failures are normal. Google Maps may represent a business under a different name, return a results page instead of a place, or have no savable place for it. Run the importer again once; transient failures often resolve. Successful places are skipped.

## I want a different list icon

Edit `config.json` before the list is created, or change the icon later in Google Maps. Changing the icon never requires re-importing the businesses.

## I want to start over

Delete `progress.json` and `failed.json`. If you also want a fresh Google Maps list, delete or rename the old list in Google Maps first.

## Nothing happens when I rerun the five-place test

If those five places are already recorded in `progress.json`, the importer correctly skips them. Run the full importer or delete the progress file if you truly want a clean test.
