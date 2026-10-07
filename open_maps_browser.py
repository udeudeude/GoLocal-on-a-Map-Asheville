#!/usr/bin/env python3
import subprocess
import sys
import time

from golocal_common import find_browser, load_config, port_is_open, profile_path


def main():
    cfg = load_config()
    port = int(cfg["cdp_port"])
    maps_url = str(cfg["maps_url"])
    name, browser = find_browser()
    if not browser:
        sys.exit("Brave or Google Chrome was not found. Install one, then run this again.")

    if port_is_open(port):
        print(f"A Go Local browser session is already listening on port {port}.")
        print("Leave that browser window open and continue with the importer.")
        return

    profile = profile_path(cfg)
    profile.mkdir(parents=True, exist_ok=True)
    args = [
        str(browser),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        maps_url,
    ]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Opened a dedicated {name} window for Go Local on a Map.")
    print("Sign into the Google account whose Maps you want to modify.")
    print("This uses a separate browser profile and does not read your normal browser profile.")
    for _ in range(20):
        if port_is_open(port):
            return
        time.sleep(0.25)
    print("The browser opened, but the automation port is not responding yet. Give it a few seconds.")


if __name__ == "__main__":
    main()
