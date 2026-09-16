# GW-FIX-001 — WC2026 Groups A–L audit (Matchday vs FIFA)

**Date:** 2026-08-21 (UTC)
**Task:** `t_f7ff3452`
**Scope:** Matchday Groups A–L vs FIFA World Cup 2026 official pots/groups.
**Patch rule:** membership errors only. Naming aliases and display order were not patched.
**Confidence:** HIGH (12/12 group sets match FIFA primary pages).[15]

## Verdict

Matchday group cards in `docs/assets/js/app.js` (`WC_GROUPS` / `WC_GROUPS_EN`) have the **correct 48-team, 12-group membership** versus FIFA's confirmed groups.[15]
FIFA group-in-focus pages name the same twelve sections A–L as those cards.[3][4][5]
NBC Sports independently lists the same completed 12 groups.[15]
**No patch applied** to `WC_GROUPS` / `WC_GROUPS_EN`.
Exonyms (Czechia vs Czech Republic, Bosnia vs Bosnia and Herzegovina, Cabo Verde vs Cape Verde) are the same associations, not wrong teams.[3][4][10]
A **separate** Matchday artifact, `docs/assets/data/wc2026_fixture.json`, is a stale 24-match stub whose group labels contradict FIFA Group A (Mexico, South Africa, Korea Republic, Czechia).[3]
That stub was **not rewritten** here because replacing it is a full fixture/results job, not a groups-membership patch.

## Methodology

Matchday Groups A–L were read from `docs/assets/js/app.js` (`WC_GROUPS`, `WC_GROUPS_EN`) and set-checked against the webapp group-stage file `webapp/src/config/wc2026_fixture.json`.
Set-equality used FIFA.com group-in-focus pages plus the 5 Dec 2025 Final Draw and the 25 Nov 2025 pot list.[1][2]
NBC Sports and the draw-day AP tables corroborate the completed groups and the original pot-4 placeholders.[15][16]
Scores, venues, and the knockout bracket are out of scope.

Play-off Path D landed Czechia in Group A.[3]
Play-off Path A landed Bosnia and Herzegovina in Group B.[4]
Play-off Path C landed Türkiye in Group D.[6]
Play-off Path B landed Sweden in Group F.[8]
FIFA Play-Off 2 landed Iraq in Group I.[11]
FIFA Play-Off 1 landed Congo DR in Group K.[13]
AP listed those six slots as placeholders on 5 Dec 2025.[16]

## Groups A–L (set equality)

FIFA names in the FIFA column follow the group-in-focus pages and the Final Draw.[1][3]
Matchday names are as shipped in `WC_GROUPS_EN`. Status `MATCH` means the same four associations.

| Group | FIFA official (confirmed) | FIFA pots (1–4) | Matchday (`WC_GROUPS_EN`) | Status |
| --- | --- | --- | --- | --- |
| A | Mexico, South Africa, Korea Republic, Czechia[3] | Mexico (1), Korea Republic (2), South Africa (3), Czechia (UEFA PO D → 4)[2][3] | Mexico, South Africa, South Korea, Czech Republic | MATCH |
| B | Canada, Bosnia and Herzegovina, Qatar, Switzerland[4] | Canada (1), Switzerland (2), Qatar (3), Bosnia and Herzegovina (UEFA PO A → 4)[2][4] | Canada, Switzerland, Qatar, Bosnia | MATCH |
| C | Brazil, Morocco, Haiti, Scotland[5] | Brazil (1), Morocco (2), Scotland (3), Haiti (4)[2][5] | Brazil, Morocco, Haiti, Scotland | MATCH |
| D | USA, Australia, Paraguay, Türkiye[6] | USA (1), Australia (2), Paraguay (3), Türkiye (UEFA PO C → 4)[2][6] | United States, Paraguay, Australia, Türkiye | MATCH |
| E | Germany, Curaçao, Côte d'Ivoire, Ecuador[7] | Germany (1), Ecuador (2), Côte d'Ivoire (3), Curaçao (4)[2][7] | Germany, Curaçao, Ivory Coast, Ecuador | MATCH |
| F | Netherlands, Japan, Tunisia, Sweden[8] | Netherlands (1), Japan (2), Tunisia (3), Sweden (UEFA PO B → 4)[2][8] | Netherlands, Japan, Tunisia, Sweden | MATCH |
| G | Belgium, Egypt, IR Iran, New Zealand[9] | Belgium (1), IR Iran (2), Egypt (3), New Zealand (4)[2][9] | Belgium, Egypt, Iran, New Zealand | MATCH |
| H | Spain, Cabo Verde, Saudi Arabia, Uruguay[10] | Spain (1), Uruguay (2), Saudi Arabia (3), Cabo Verde (4)[2][10] | Spain, Cape Verde, Saudi Arabia, Uruguay | MATCH |
| I | France, Senegal, Iraq, Norway[11] | France (1), Senegal (2), Norway (3), Iraq (FIFA PO 2 → 4)[2][11] | France, Senegal, Norway, Iraq | MATCH |
| J | Argentina, Algeria, Austria, Jordan[12] | Argentina (1), Austria (2), Algeria (3), Jordan (4)[2][12] | Argentina, Algeria, Austria, Jordan | MATCH |
| K | Portugal, Colombia, Uzbekistan, Congo DR[13] | Portugal (1), Colombia (2), Uzbekistan (3), Congo DR (FIFA PO 1 → 4)[2][13] | Portugal, Colombia, Uzbekistan, DR Congo | MATCH |
| L | England, Croatia, Ghana, Panama[1][15] | England (1), Croatia (2), Panama (3), Ghana (4)[1][2] | England, Croatia, Ghana, Panama | MATCH |

The Final Draw page still lists some pot-4 **placeholders** (UEFA paths A–D and the two FIFA play-off tournaments).[1] Those slots are filled on the later group-in-focus pages cited above. AP published the same placeholder table on draw day, 5 Dec 2025.[16]

## Naming aliases (not patched)

These are FIFA vs Matchday **exonyms**, not wrong countries (FIFA: Czechia, Korea Republic, Bosnia and Herzegovina).[3][4][17]
Left as-is under the patch rule.

| FIFA | Matchday EN | Matchday ES |
| --- | --- | --- |
| Czechia | Czech Republic | Rep. Checa |
| Korea Republic | South Korea | Corea del Sur |
| Bosnia and Herzegovina | Bosnia | Bosnia |
| Côte d'Ivoire | Ivory Coast | Costa de Marfil |
| Cabo Verde | Cape Verde | Cabo Verde |
| IR Iran | Iran | Irán |
| Congo DR | DR Congo | RD Congo |
| USA | United States | Estados Unidos |
| Qatar | Qatar | Catar |
| Curaçao | Curaçao | Curazao |
| Türkiye | Türkiye | Turquía |

Display order inside a Matchday card is not FIFA pot order (pot 1 hosts Mexico A1, Canada B1, USA D1).[2]
That is not a membership error.

## Other Matchday / repo surfaces

| Surface | Group membership vs FIFA | Action |
| --- | --- | --- |
| `docs/assets/js/app.js` `WC_GROUPS` / `WC_GROUPS_EN` | MATCH (12/12) | No patch |
| `webapp/src/config/wc2026_fixture.json` group-stage team **sets** | MATCH (same 12 sets as Matchday cards) | No patch (scores/venues out of scope) |
| `docs/assets/data/wc2026_fixture.json` | **FAIL** — stub with internally duplicated teams (Mexico, Argentina, USA, Canada, Brazil, Spain, etc. each appear in two groups). Group A is México / Ee.uu. / Canadá / Argentina, which is not FIFA Group A.[3] | Not patched in this task |

The stub is loaded by `docs/assets/js/ai_agent.js` (`/fixture`).
Users of that path still see non-FIFA groups (for example México vs Ee.uu. as Group A) even though the Matchday group cards match FIFA.[3]

## What was not patched (and why)

**No membership error** exists in `WC_GROUPS` / `WC_GROUPS_EN` versus FIFA Groups A–L.[15]
**Exonyms** such as Czechia / Czech Republic are not confirmed wrong teams.[3][17]
**`docs/assets/data/wc2026_fixture.json`** is a confirmed group-membership failure against FIFA Group A, but replacing it requires a 72-match FIFA schedule rewrite.[3]

## Recommendations

Keep Matchday group cards as the source of truth for Groups A–L.[15]
Queue a follow-up to replace `docs/assets/data/wc2026_fixture.json` from FIFA's match schedule, not from the webapp's simulated scores.
Optional later: align EN/ES labels to FIFA official names (Czechia, Bosnia and Herzegovina, Cabo Verde, IR Iran, Congo DR).[3][4][10]

## Fact-check summary

Twelve group-membership claims were checked against FIFA primary pages and NBC Sports.[15]
All twelve Matchday card sets verified; zero `WC_GROUPS` corrections; zero remaining card errors.
Data-derived hard fails: 0. Confidence: HIGH.

## Sources

[1] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/final-draw-results
    > "Mexico South Africa Korea Republic Czechia/Denmark/North Macedonia /Republic of Ireland"
    > "Canada Bosnia and Herzegovina/Italy/Northern Ireland /Wales Qatar Switzerland"
    > "Brazil Morocco Haiti Scotland"
    > "Germany Curaçao Côte d'Ivoire Ecuador"
    > "Belgium Egypt IR Iran New Zealand"
    > "Spain Cabo Verde Saudi Arabia Uruguay"
    > "Argentina Algeria Austria Jordan"
    > "England Croatia Ghana Panama"
[2] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/procedures-pots-final-draw
    > "Pot 1: Canada, Mexico, USA, Spain, Argentina, France, England, Brazil, Portugal, Netherlands, Belgium, Germany"
    > "Pot 2: Croatia, Morocco, Colombia, Uruguay, Switzerland, Japan, Senegal, IR Iran, Korea Republic, Ecuador, Austria, Australia"
    > "Pot 3: Norway, Panama, Egypt, Algeria, Scotland, Paraguay, Tunisia, Côte d’Ivoire, Uzbekistan, Qatar, Saudi Arabia, South Africa"
    > "Pot 4: Jordan, Cabo Verde, Ghana, Curaçao, Haiti, New Zealand, European Play-Off A, B, C and D, FIFA Play-Off Tournament 1 and 2"
[3] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-a-focus-teams-fixtures-standings
    > "Co-hosts Mexico will face South Africa, Korea Republic and Czechia."
[4] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-b-preview-stats-fixtures
    > "Co-hosts Canada will take on Bosnia and Herzegovina, Qatar and Switzerland in Group B."
[5] https://www.fifa.com/en/articles/group-c-focus-teams-fixtures-standings
    > "Brazil will face Haiti, Morocco and Scotland."
[6] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-d-focus-teams-fixtures-standings
    > "Co-hosts USA will face Australia, Paraguay and Türkiye."
[7] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-e-focus-teams-fixtures-standings
    > "Germany will face debutants Curaçao plus Côte d’Ivoire and Ecuador."
[8] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-f-focus-teams-fixtures-standings
    > "Netherlands sauntered through European qualifying, but have been dealt tough opposition in Japan, Sweden and Tunisia."
[9] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-g-focus-teams-fixtures-standings
    > "European heavyweights Belgium will face Egypt, IR Iran and New Zealand."
[10] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-h-teams-fixtures-standings
    > "European title holders Spain will take on Cabo Verde, Saudi Arabia and Uruguay."
[11] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-i-focus-teams-fixtures-standings
    > "Two-time winners France will face Senegal, Iraq and Norway."
[12] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-j-focus-teams-fixtures-standings
    > "Lionel Scaloni's all-conquering side have been placed in Group J with Algeria, Austria and tournament debutants Jordan."
[13] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/group-k-focus-teams-fixtures-standings
    > "Cristiano Ronaldo's Portugal will face Colombia, Uzbekistan and Congo DR."
[15] https://www.nbcsports.com/soccer/news/2026-world-cup-groups-confirmed-full-draw-groups-details
    > "Group A : Mexico, South Korea, South Africa, Czechia Group B : Canada, Switzerland, Qatar, Bosnia-Herzegovina Group C : Brazil, Morocco, Scotland, Haiti Group D : USA, Paraguay, Australia, Turkiye Group E : Germany, Ecuador, Ivory Coast, Curacao Group F : Netherlands, Japan, Tunisia, Sweden Group G : Belgium, Iran, Egypt, New Zealand Group H : Spain, Uruguay, Saudi Arabia, Cape Verde Group I : France, Senegal, Norway, Iraq Group J : Argentina, Austria, Algeria, Jordan Group K : Portugal, Colombia, Uzbekistan, DR Congo Group L : England, Croatia, Panama, Ghana"
[16] https://apnews.com/article/soccer-fifa-world-cup-71e2e67ed31d81eac08b81b515b09da7
    > "GROUP A Mexico South Africa Korea Republic Winner of European Play-Off D GROUP B Canada Winner of European Play-Off A Qatar Switzerland GROUP C Brazil Morocco Haiti Scotland GROUP D United States Paraguay Australia Winner of European Play-Off C GROUP E Germany Curacao Cote d’Ivoire Ecuador GROUP F Netherlands Japan Winner of European Play-Off B Tunisia GROUP G Belgium Egypt IR Iran New Zealand GROUP H Spain Cabo Verde Saudi Arabia Uruguay GROUP I France Senegal Winner of FIFA Play-Off Tournament 2 Norway GROUP J Argentina Algeria Austria Jordan GROUP K Portugal Winner of FIFA Play-Off Tournament 1 Uzbekistan Colombia GROUP L England Croatia Ghana Panama"
[17] https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A
    > "The group consisted of national football teams representing Mexico(co-host), South Africa, South Korea, and the Czech Republic."
