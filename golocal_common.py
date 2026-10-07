#!/usr/bin/env python3
import json
import os
import platform
import shutil
import socket
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "list_name": "Go Local Card",
    "list_emoji": "❣️",
    "maps_url": "https://www.google.com/maps",
    "cdp_port": 9223,
    "browser_profile": "~/.golocal-maps-browser",
    "test_limit": 5,
    "delay_min_seconds": 2.0,
    "delay_max_seconds": 5.0,
}


def load_config():
    cfg = dict(DEFAULTS)
    path = HERE / "config.json"
    if path.exists():
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(user, dict):
                cfg.update(user)
        except Exception as e:
            raise RuntimeError(f"Could not read config.json: {e}") from e
    return cfg


def find_browser():
    system = platform.system()
    candidates = []

    if system == "Darwin":
        candidates = [
            ("Brave", Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")),
            ("Google Chrome", Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")),
        ]
    elif system == "Windows":
        roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        roots = [Path(x) for x in roots if x]
        rels = [
            ("Brave", Path("BraveSoftware/Brave-Browser/Application/brave.exe")),
            ("Google Chrome", Path("Google/Chrome/Application/chrome.exe")),
        ]
        for root in roots:
            for name, rel in rels:
                candidates.append((name, root / rel))
    else:
        for name, exe in [
            ("Brave", "brave-browser"),
            ("Brave", "brave"),
            ("Google Chrome", "google-chrome"),
            ("Google Chrome", "google-chrome-stable"),
            ("Chromium", "chromium"),
            ("Chromium", "chromium-browser"),
        ]:
            found = shutil.which(exe)
            if found:
                return name, Path(found)

    for name, path in candidates:
        if path.exists():
            return name, path
    return None, None


def profile_path(cfg=None):
    cfg = cfg or load_config()
    return Path(os.path.expanduser(str(cfg.get("browser_profile", DEFAULTS["browser_profile"]))))


def port_is_open(port):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.35):
            return True
    except OSError:
        return False
