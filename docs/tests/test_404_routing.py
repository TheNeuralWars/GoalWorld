#!/usr/bin/env python3
"""GW-404-001: docs Vercel 404 chrome + trailing-slash rules.

Unknown marketing paths must render GoalWorld chrome, never the black Play
SPA shell (empty #root) or the /go Play redirect page.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
VERCEL = DOCS / "vercel.json"
NOT_FOUND = DOCS / "404.html"
GO_PLAY_SHELL = DOCS / "go" / "index.html"


class Docs404Routing(unittest.TestCase):
    def test_vercel_json_exists_and_is_object(self) -> None:
        self.assertTrue(VERCEL.is_file(), "docs/vercel.json must exist (Vercel root=docs)")
        data = json.loads(VERCEL.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)

    def test_trailing_slash_and_clean_urls(self) -> None:
        data = json.loads(VERCEL.read_text(encoding="utf-8"))
        self.assertIs(data.get("trailingSlash"), False)
        self.assertIs(data.get("cleanUrls"), True)

    def test_no_spa_catchall_to_index_or_play_shell(self) -> None:
        data = json.loads(VERCEL.read_text(encoding="utf-8"))
        for key in ("rewrites", "redirects", "routes"):
            for rule in data.get(key) or []:
                if not isinstance(rule, dict):
                    continue
                source = str(rule.get("source") or rule.get("src") or "")
                dest = str(rule.get("destination") or rule.get("dest") or "")
                catchall = bool(re.search(r"\(\.\*\)|/:path\*?$", source)) or source in (
                    "/(.*)",
                    "/:path*",
                    "/:path(.*)",
                )
                if not catchall:
                    continue
                self.assertFalse(
                    dest in {"/", "/index", "/index.html", "/go", "/go/", "/go/index.html"},
                    f"{key} catch-all {source!r} must not fall through to {dest!r} (Play/hub shell)",
                )

    def test_404_html_is_goalworld_chrome(self) -> None:
        self.assertTrue(NOT_FOUND.is_file(), "docs/404.html is required")
        html = NOT_FOUND.read_text(encoding="utf-8")
        self.assertIn("<html", html.lower())
        self.assertIn('lang="en"', html)
        self.assertIn("GoalWorld", html)
        self.assertIn("/assets/img/logo_3d_clean.png", html)
        self.assertIn("/assets/js/gw-shell.js", html)
        self.assertIn("/assets/css/gw-shell.css", html)
        self.assertRegex(html, r'href=["\']/?["\']')
        self.assertIn("noindex", html.lower())
        self.assertNotRegex(
            html,
            r'<meta[^>]+http-equiv=["\']refresh["\']',
            "404 must not auto-redirect (that is the Play shell pattern)",
        )
        self.assertNotIn('id="root"', html)
        self.assertNotIn("location.replace", html)
        self.assertNotIn("location.href =", html)
        self.assertNotIn("location.assign", html)

    def test_404_assets_are_root_absolute(self) -> None:
        """Nested unknown paths (/foo/bar) break relative asset URLs."""
        html = NOT_FOUND.read_text(encoding="utf-8")
        for attr in re.findall(r"""(?:src|href)=["']([^"']+)["']""", html):
            if attr.startswith(("http://", "https://", "data:", "mailto:", "#")):
                continue
            if attr in {"/", "/map", "/goalchain", "/goalchain.html", "/map.html"}:
                continue
            if attr.startswith("/") and not attr.startswith("//"):
                continue
            self.fail(f"404 asset/link must be root-absolute, got {attr!r}")

    def test_go_play_redirect_is_not_the_404_page(self) -> None:
        self.assertTrue(GO_PLAY_SHELL.is_file())
        go = GO_PLAY_SHELL.read_text(encoding="utf-8")
        not_found = NOT_FOUND.read_text(encoding="utf-8")
        self.assertNotEqual(go.strip(), not_found.strip())
        self.assertIn("play.goalworld.fun", go)


if __name__ == "__main__":
    unittest.main()
