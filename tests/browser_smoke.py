# /// script
# requires-python = ">=3.13"
# dependencies = ["websockets>=16"]
# ///
"""Optional real-Chrome smoke: uv run tests/browser_smoke.py after a strict build.

Uses an isolated temporary profile and localhost server; never the user's profile.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from websockets.sync.client import connect


def contrast(foreground: str, background: str) -> float:
    def luminance(color):
        channels = [float(c) / 255 for c in re.findall(r"[\d.]+", color)[:3]]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    a, b = sorted((luminance(foreground), luminance(background)))
    return (b + 0.05) / (a + 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chrome",
        default=shutil.which("google-chrome")
        or shutil.which("chromium")
        or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    public = root / "docs/_site"
    if not (public / "index.html").is_file():
        parser.error("Run the strict site build first.")
    if not Path(args.chrome).is_file():
        parser.error("Install Chrome or pass --chrome with its executable path.")
    with tempfile.TemporaryDirectory(prefix="kis-browser-") as temporary:
        work = Path(temporary)
        web = work / "web"
        web.mkdir()
        (web / "keep-it-simple").symlink_to(public, target_is_directory=True)
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(web))
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        profile = work / "profile"
        with (work / "chrome.log").open("w") as log:
            process = subprocess.Popen(
                [
                    args.chrome,
                    "--headless",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--remote-debugging-port=0",
                    "--remote-debugging-address=127.0.0.1",
                    f"--user-data-dir={profile}",
                    "about:blank",
                ],
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            try:
                active = profile / "DevToolsActivePort"
                deadline = time.monotonic() + 25
                while not active.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                port = active.read_text().splitlines()[0]
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/json/list", timeout=10
                ) as response:
                    targets = json.load(response)
                target = next(t for t in targets if t["type"] == "page")
                with connect(target["webSocketDebuggerUrl"], max_size=None) as websocket:
                    counter = 0

                    def call(method, params=None):
                        nonlocal counter
                        counter += 1
                        ident = counter
                        websocket.send(
                            json.dumps({"id": ident, "method": method, "params": params or {}})
                        )
                        while True:
                            result = json.loads(websocket.recv(timeout=15))
                            if result.get("id") == ident:
                                if "error" in result:
                                    raise RuntimeError(result["error"])
                                return result.get("result", {})

                    def value(expression):
                        result = call(
                            "Runtime.evaluate", {"expression": expression, "returnByValue": True}
                        )
                        return result["result"].get("value")

                    def screenshot(name):
                        if args.screenshots:
                            args.screenshots.mkdir(parents=True, exist_ok=True)
                            data = call("Page.captureScreenshot", {"format": "png"})["data"]
                            (args.screenshots / f"{name}.png").write_bytes(base64.b64decode(data))

                    call("Page.enable")
                    call(
                        "Emulation.setDeviceMetricsOverride",
                        {"width": 390, "height": 900, "deviceScaleFactor": 1, "mobile": True},
                    )
                    call(
                        "Page.navigate",
                        {"url": f"http://127.0.0.1:{server.server_port}/keep-it-simple/"},
                    )
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if value(
                            "document.readyState === 'complete' && "
                            "!!document.querySelector('.lead p')"
                        ):
                            break
                        time.sleep(0.1)
                    assert value("document.body.classList.contains('quarto-dark')"), (
                        "Fresh visits must default to dark mode"
                    )
                    assert value("innerWidth") == 390
                    assert value("document.documentElement.scrollWidth <= innerWidth")
                    screenshot("mobile")
                    call(
                        "Emulation.setDeviceMetricsOverride",
                        {"width": 1440, "height": 1100, "deviceScaleFactor": 1, "mobile": False},
                    )
                    assert value(
                        "Array.from(document.querySelectorAll('.work-media figcaption'))"
                        ".every(el => getComputedStyle(el).display === 'none')"
                    ), "Thumbnail alternative text should not also appear as a visible caption"
                    value("document.querySelector('.quarto-color-scheme-toggle').click()")
                    time.sleep(0.5)
                    assert value("document.body.classList.contains('quarto-light')")
                    call("Page.reload")
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if value("document.readyState === 'complete'"):
                            break
                        time.sleep(0.1)
                    assert value("document.body.classList.contains('quarto-light')"), (
                        "An explicit light-mode choice must survive reload"
                    )
                    value("document.querySelector('.quarto-color-scheme-toggle').click()")
                    time.sleep(0.5)
                    assert value("document.body.classList.contains('quarto-dark')")
                    foreground = value("getComputedStyle(document.querySelector('.lead p')).color")
                    background = value("getComputedStyle(document.body).backgroundColor")
                    ratio = contrast(foreground, background)
                    assert ratio >= 4.5, f"Dark lead contrast {ratio:.2f}:1 is below 4.5:1"
                    screenshot("dark")
                    print(
                        "Browser smoke passed: dark-first, saved preference, "
                        "390px without overflow, "
                        f"contrast {ratio:.2f}:1"
                    )
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    main()
