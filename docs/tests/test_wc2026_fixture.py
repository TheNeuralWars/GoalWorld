#!/usr/bin/env python3
"""GW-FIX-002: Matchday wc2026_fixture.json must use FIFA Groups A–L.

The stub at docs/assets/data/wc2026_fixture.json historically put México /
Ee.uu. / Canadá / Argentina in Group A and duplicated teams across groups.
Group-stage membership must match WC_GROUPS_EN (same 12 FIFA sets).
Pairings / dates / venues come from FIFA schedule pages, not from the
webapp simulated-score file. Scores, if present, must not be invented.
"""
from __future__ import annotations

import json
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
REPO = DOCS.parent
FIXTURE = DOCS / "assets" / "data" / "wc2026_fixture.json"
APP_JS = DOCS / "assets" / "js" / "app.js"
WEBAPP_SIM = REPO / "webapp" / "src" / "config" / "wc2026_fixture.json"

# FIFA official English names (scores-fixtures / calendar) → WC_GROUPS_EN.
FIFA_TO_WC_GROUPS_EN = {
    "mexico": "Mexico",
    "south africa": "South Africa",
    "korea republic": "South Korea",
    "south korea": "South Korea",
    "czechia": "Czech Republic",
    "czech republic": "Czech Republic",
    "canada": "Canada",
    "bosnia and herzegovina": "Bosnia",
    "bosnia": "Bosnia",
    "qatar": "Qatar",
    "switzerland": "Switzerland",
    "brazil": "Brazil",
    "morocco": "Morocco",
    "haiti": "Haiti",
    "scotland": "Scotland",
    "usa": "United States",
    "united states": "United States",
    "australia": "Australia",
    "paraguay": "Paraguay",
    "türkiye": "Türkiye",
    "turkiye": "Türkiye",
    "turkey": "Türkiye",
    "germany": "Germany",
    "curaçao": "Curaçao",
    "curacao": "Curaçao",
    "côte d'ivoire": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "ivory coast": "Ivory Coast",
    "ecuador": "Ecuador",
    "netherlands": "Netherlands",
    "japan": "Japan",
    "tunisia": "Tunisia",
    "sweden": "Sweden",
    "belgium": "Belgium",
    "egypt": "Egypt",
    "ir iran": "Iran",
    "iran": "Iran",
    "new zealand": "New Zealand",
    "spain": "Spain",
    "cabo verde": "Cape Verde",
    "cape verde": "Cape Verde",
    "saudi arabia": "Saudi Arabia",
    "uruguay": "Uruguay",
    "france": "France",
    "senegal": "Senegal",
    "iraq": "Iraq",
    "norway": "Norway",
    "argentina": "Argentina",
    "algeria": "Algeria",
    "austria": "Austria",
    "jordan": "Jordan",
    "portugal": "Portugal",
    "colombia": "Colombia",
    "uzbekistan": "Uzbekistan",
    "congo dr": "DR Congo",
    "dr congo": "DR Congo",
    "england": "England",
    "croatia": "Croatia",
    "ghana": "Ghana",
    "panama": "Panama",
}

# Stale stub / Spanish leftovers that must not appear as Group A (or any group).
STALE_STUB_TEAMS = {
    "ee.uu.",
    "méxico",
    "mexico vs usa",
    "italia",
    "italy",
    "bolivia",
    "nigeria",
    "congo",  # bare "Congo" is not Congo DR
}


def _norm(name: str) -> str:
    return " ".join(name.replace("\u2019", "'").strip().lower().split())


def canonical_team(name: str) -> str:
    key = _norm(name)
    if key not in FIFA_TO_WC_GROUPS_EN:
        raise AssertionError(f"unmapped team name {name!r} (norm={key!r})")
    return FIFA_TO_WC_GROUPS_EN[key]


def parse_wc_groups_en(src: str) -> dict[str, set[str]]:
    block = re.search(r"const WC_GROUPS_EN = \{([\s\S]*?)\n    \};", src)
    if not block:
        raise AssertionError("WC_GROUPS_EN block not found in app.js")
    groups: dict[str, set[str]] = {}
    for letter, rest in re.findall(r"([A-L]):\s*(\[\[.*\]\])", block.group(1)):
        names = re.findall(r",'([^']+)'\]", rest)
        groups[letter] = {canonical_team(n) for n in names}
    if set(groups) != set("ABCDEFGHIJKL"):
        raise AssertionError(f"WC_GROUPS_EN parse incomplete: {sorted(groups)}")
    return groups


def load_fixture() -> list[dict]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise AssertionError("fixture must be a JSON array")
    return data


def group_matches(rows: list[dict]) -> list[dict]:
    return [m for m in rows if m.get("phase") == "group"]


class Wc2026FixtureFifaGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app_js = APP_JS.read_text(encoding="utf-8")
        cls.wc_groups = parse_wc_groups_en(cls.app_js)
        cls.rows = load_fixture()
        cls.group_rows = group_matches(cls.rows)

    def test_wc_groups_en_still_twelve_fifa_sets(self) -> None:
        """Do not silently rewrite Matchday cards in this task."""
        self.assertEqual(set(self.wc_groups), set("ABCDEFGHIJKL"))
        self.assertEqual(self.wc_groups["A"], {"Mexico", "South Africa", "South Korea", "Czech Republic"})
        self.assertEqual(self.wc_groups["L"], {"England", "Croatia", "Ghana", "Panama"})

    def test_group_stage_has_72_matches_six_per_group(self) -> None:
        self.assertEqual(len(self.group_rows), 72, "12 groups × 6 matches")
        by_group = Counter(m.get("group") for m in self.group_rows)
        self.assertEqual(set(by_group), set("ABCDEFGHIJKL"))
        self.assertTrue(all(n == 6 for n in by_group.values()), by_group)

    def test_group_team_sets_match_wc_groups_en(self) -> None:
        got: dict[str, set[str]] = defaultdict(set)
        for m in self.group_rows:
            got[str(m["group"])].add(canonical_team(str(m["home"])))
            got[str(m["group"])].add(canonical_team(str(m["away"])))
        for letter in "ABCDEFGHIJKL":
            self.assertEqual(
                got[letter],
                self.wc_groups[letter],
                f"Group {letter} teams {got[letter]} != WC_GROUPS_EN {self.wc_groups[letter]}",
            )

    def test_no_team_appears_in_two_groups(self) -> None:
        owner: dict[str, str] = {}
        for letter, teams in self.wc_groups.items():
            # Use fixture-derived sets so a stale stub fails here too.
            pass
        got: dict[str, set[str]] = defaultdict(set)
        for m in self.group_rows:
            got[str(m["group"])].add(canonical_team(str(m["home"])))
            got[str(m["group"])].add(canonical_team(str(m["away"])))
        seen: dict[str, str] = {}
        for letter, teams in got.items():
            for team in teams:
                if team in seen:
                    self.fail(f"{team} appears in Group {seen[team]} and Group {letter}")
                seen[team] = letter
        self.assertEqual(len(seen), 48)

    def test_each_group_is_a_complete_round_robin(self) -> None:
        pairs: dict[str, set[frozenset[str]]] = defaultdict(set)
        for m in self.group_rows:
            a = canonical_team(str(m["home"]))
            b = canonical_team(str(m["away"]))
            self.assertNotEqual(a, b)
            pair = frozenset({a, b})
            self.assertNotIn(pair, pairs[str(m["group"])], f"duplicate pairing {a} vs {b}")
            pairs[str(m["group"])].add(pair)
        for letter in "ABCDEFGHIJKL":
            self.assertEqual(len(pairs[letter]), 6)

    def test_stale_stub_group_a_is_gone(self) -> None:
        group_a = [m for m in self.group_rows if m.get("group") == "A"]
        names = {_norm(str(m["home"])) for m in group_a} | {_norm(str(m["away"])) for m in group_a}
        self.assertNotIn("ee.uu.", names)
        self.assertNotIn("canadá", names)
        self.assertNotIn("canada", names)
        self.assertNotIn("argentina", names)
        self.assertTrue({"mexico", "south africa"} <= names or {"méxico", "sudáfrica"} <= names)

    def test_opening_match_is_fifa_mexico_south_africa(self) -> None:
        """FIFA opening match: Mexico vs South Africa, 11 June 2026, Mexico City Stadium."""
        openers = [
            m
            for m in self.group_rows
            if {canonical_team(str(m["home"])), canonical_team(str(m["away"]))}
            == {"Mexico", "South Africa"}
        ]
        self.assertEqual(len(openers), 1)
        m = openers[0]
        self.assertEqual(m["date"], "2026-06-11")
        self.assertIn("Mexico City", str(m["venue"]))
        self.assertIn("Mexico City", str(m["city"]))
        self.assertEqual(canonical_team(str(m["home"])), "Mexico")
        self.assertEqual(canonical_team(str(m["away"])), "South Africa")

    def test_required_schedule_fields_come_from_fifa_shape(self) -> None:
        for m in self.group_rows:
            for key in ("id", "phase", "group", "date", "home", "away", "status", "venue", "city"):
                self.assertTrue(m.get(key), f"missing {key} on {m}")
            self.assertRegex(str(m["date"]), r"^2026-06-(1[1-9]|2[0-8])$")
            self.assertNotIn(str(m["venue"]).strip(), {"", "TBD", "tbd"})
            self.assertNotIn(str(m["city"]).strip(), {"", "TBD", "tbd"})

    def test_scores_if_present_are_official_not_invented_stub(self) -> None:
        """Do not invent scores. Official FIFA FT scores are allowed."""
        opener = next(
            m
            for m in self.group_rows
            if {canonical_team(str(m["home"])), canonical_team(str(m["away"]))}
            == {"Mexico", "South Africa"}
        )
        if "scoreHome" in opener or "scoreAway" in opener:
            self.assertEqual(opener.get("scoreHome"), 2)
            self.assertEqual(opener.get("scoreAway"), 0)
            self.assertEqual(opener.get("status"), "completed")
        cze_rsa = [
            m
            for m in self.group_rows
            if {canonical_team(str(m["home"])), canonical_team(str(m["away"]))}
            == {"Czech Republic", "South Africa"}
        ]
        self.assertEqual(len(cze_rsa), 1)
        if "scoreHome" in cze_rsa[0]:
            # FIFA: Czechia 1-1 South Africa. Webapp sim had Sudáfrica 2-1 Chequia.
            self.assertEqual(cze_rsa[0].get("scoreHome"), 1)
            self.assertEqual(cze_rsa[0].get("scoreAway"), 1)

    def test_pairings_are_not_copied_from_webapp_simulated_file(self) -> None:
        if not WEBAPP_SIM.is_file():
            self.skipTest("webapp simulated fixture missing")
        sim = [m for m in json.loads(WEBAPP_SIM.read_text(encoding="utf-8")) if m.get("phase") == "group"]
        # Webapp Group A MD2 is México vs Corea del Sur at Estadio Azteca on 2026-06-16.
        # FIFA plays that pairing at Guadalajara Stadium (not Azteca).
        mex_kor = next(
            m
            for m in self.group_rows
            if {canonical_team(str(m["home"])), canonical_team(str(m["away"]))}
            == {"Mexico", "South Korea"}
        )
        self.assertIn("Guadalajara", str(mex_kor["venue"]))
        self.assertNotEqual(mex_kor["date"], "2026-06-16")
        sim_a_venues = {m.get("venue") for m in sim if m.get("group") == "A"}
        self.assertNotIn("Estadio Azteca", str(mex_kor["venue"]))
        self.assertNotIn(mex_kor["venue"], sim_a_venues)

    def test_no_stale_unmapped_stub_countries_in_group_stage(self) -> None:
        names = {_norm(str(m["home"])) for m in self.group_rows} | {
            _norm(str(m["away"])) for m in self.group_rows
        }
        for bad in ("italia", "italy", "bolivia", "nigeria", "ee.uu."):
            self.assertNotIn(bad, names)


if __name__ == "__main__":
    unittest.main()
