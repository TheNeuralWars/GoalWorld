#!/usr/bin/env python3
"""GW-PITCH-001 regression: /pitch first slide, Next/Prev, Esc→hub, gc_lang guard.

Run from repo root:
  python3 tests/pitch_deck_qa.py

Requires playwright + chromium (Hermes venv is enough).
Exit 0 only when all acceptance checks pass.
"""
from __future__ import annotations

import http.server
import json
import socket
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / "docs"
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass


def serve() -> tuple[http.server.ThreadingHTTPServer, str]:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{port}/pitch.html"


def run() -> int:
    httpd, url = serve()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

            # --- default lang ---
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            slides = page.locator(".slide")
            active = page.locator(".slide.active")
            header = page.locator(".slide.active .slide-header")
            check("first_slide_in_dom", slides.count() >= 2, f"slides={slides.count()}")
            check("one_active_slide", active.count() == 1, f"active={active.count()}")
            # text_content = DOM source ("Our Vision"). inner_text follows
            # .slide-header { text-transform: uppercase } and is not the contract.
            check(
                "first_slide_visible",
                active.count() == 1 and active.first.is_visible(),
                f"header={header.text_content() if header.count() else None}",
            )
            title = (header.text_content() or "").strip() if header.count() else ""
            check(
                "first_slide_is_slide_1",
                title in ("Our Vision", "Nuestra Visión"),
                f"title={title!r}",
            )

            prev_btn = page.locator(".controls .btn-control").nth(0)
            next_btn = page.locator(".controls .btn-control").nth(1)
            check("prev_visible", prev_btn.count() == 1 and prev_btn.is_visible())
            check("next_visible", next_btn.count() == 1 and next_btn.is_visible())
            prev_text = prev_btn.inner_text().replace("\n", " ").strip() if prev_btn.count() else ""
            next_text = next_btn.inner_text().replace("\n", " ").strip() if next_btn.count() else ""
            check(
                "prev_labeled",
                "Previous" in prev_text or "Anterior" in prev_text,
                f"text={prev_text!r}",
            )
            check(
                "next_labeled",
                "Next" in next_text or "Siguiente" in next_text,
                f"text={next_text!r}",
            )

            if next_btn.count() and next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(200)
            after_next = (
                (page.locator(".slide.active .slide-header").text_content() or "").strip()
                if page.locator(".slide.active .slide-header").count()
                else ""
            )
            check(
                "next_advances_off_slide_1",
                after_next not in ("", title) and after_next in ("The Opportunity", "La Oportunidad"),
                f"after_next={after_next!r}",
            )
            if prev_btn.count() and prev_btn.is_visible():
                prev_btn.click()
                page.wait_for_timeout(200)
            after_prev = (
                (page.locator(".slide.active .slide-header").text_content() or "").strip()
                if page.locator(".slide.active .slide-header").count()
                else ""
            )
            check(
                "prev_returns_to_slide_1",
                bool(title) and after_prev == title,
                f"after_prev={after_prev!r} title={title!r}",
            )

            page.keyboard.press("Escape")
            try:
                page.wait_for_url(lambda u: "pitch" not in Path(u.split("?")[0]).name, timeout=8000)
            except Exception:
                pass
            esc_url = page.url
            check(
                "esc_to_hub",
                esc_url.rstrip("/").endswith("index.html") or esc_url.rstrip("/").endswith(f"{page.url.split('/')[2]}"),
                f"url={esc_url}",
            )
            # tighter hub check: not still on pitch
            check("esc_left_pitch", "pitch" not in Path(esc_url.split("?")[0]).name, f"url={esc_url}")
            ctx.close()

            # --- invalid gc_lang must still render EN slide 1 ---
            ctx2 = browser.new_context(viewport={"width": 1280, "height": 800})
            ctx2.add_init_script("localStorage.setItem('gc_lang', 'xx');")
            page2 = ctx2.new_page()
            page2.goto(url, wait_until="domcontentloaded", timeout=15000)
            h2 = page2.locator(".slide.active .slide-header")
            t2 = (h2.text_content() or "").strip() if h2.count() else ""
            check(
                "gc_lang_invalid_falls_back_en",
                page2.locator(".slide.active").count() == 1 and t2 == "Our Vision",
                f"title={t2!r} slides={page2.locator('.slide').count()}",
            )
            ctx2.close()
            browser.close()
    finally:
        httpd.shutdown()

    failed = [c for c in CHECKS if not c[1]]
    print(json.dumps({"passed": sum(1 for c in CHECKS if c[1]), "failed": len(failed), "total": len(CHECKS)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
