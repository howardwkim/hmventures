#!/usr/bin/env python3
"""
Print ./ai-visibility/dashboard.html -> ./ai-visibility/dashboard.pdf via headless Chrome/Edge.
Python 3 stdlib only.
"""
import os, sys, subprocess, glob

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

OUT = os.path.join(os.getcwd(), "ai-visibility")
HTML = os.path.join(OUT, "dashboard.html")
PDF = os.path.join(OUT, "dashboard.pdf")

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
]


def find_browser():
    for c in CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def main():
    if not os.path.exists(HTML):
        sys.exit(f"{HTML} not found. Run render_dashboard.py first.")
    browser = find_browser()
    if not browser:
        sys.exit("No Chrome/Edge install found for PDF export. Install one or export manually via browser print.")
    url = "file:///" + HTML.replace("\\", "/")
    cmd = [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF}", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not os.path.exists(PDF):
        sys.exit(f"PDF export failed.\nstdout: {r.stdout}\nstderr: {r.stderr}")
    print(f"OK  dashboard PDF -> {PDF}")
    try:
        if sys.platform == "win32":
            os.startfile(PDF)
        elif sys.platform == "darwin":
            subprocess.run(["open", PDF])
        else:
            subprocess.run(["xdg-open", PDF])
    except Exception as e:
        print(f"(couldn't auto-open PDF: {e})")


if __name__ == "__main__":
    main()
