# GW-BRIDGE-001 — Lore ↔ NFT ↔ Yield Bible

**Status:** intake-ready (no code)  
**Owner:** product  
**Date:** 2026-08-21  
**Kanban:** `t_74a58a75`  
**English-only.** This is the join-key spec for GoalWorld correlation. It does not change tokenomics, the program ID, or the IDL.

---

## 1. Problem

Today a Neural Wars character, a Genesis Squad card, and a $GCH yield stream are three disconnected objects.

| Layer | Where it lives today | Identity today |
|---|---|---|
| Lore character | `docs/goalworld.html` dossiers, reader `the-neural-wars-book-1`, `ai_context/lore/schema/lore_schema.v0.json` | Free-text name. `characters[].id` exists in schema, unused in canon. |
| Genesis card | `docs/assets/data/players.json` (528 rows, ids `1…528`), Metaplex name `goalworld #001 - Lionel Satoshi` | Integer `id`. On-chain `ParodyPlayer.player_id` is a **string ≤32 bytes**, PDA `[b"player", player_id]`. |
| Yield stream | `ParodyPlayer.base_yield_rate` + `claim_daily_salary` (24h). Rarity table in `docs/ECONOMIC_CANONICAL_CONFIG.json` | No stream id. Yield is a field on the player PDA. |

`docs/intake/2026-08-21-mundo-completo-plan.md` already names the gap: a Fractured Code character can be a card, a yield, or a cutscene, and nothing joins them.

This bible defines **one shared id** so the three projections resolve without mixing venture business logic.

---

## 2. Decision

**One `gw_id`. Three projections. No fourth identifier.**

```
                    ┌──────────────────────┐
                    │   gw_id  (≤32 B)     │  single source of identity
                    └──────────┬───────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
   Lore character        Genesis card          Yield stream
   characters[].id       ParodyPlayer.player_id   same PDA
   saga dossier          Metaplex attr gw_id      base_yield_rate
   reader / cinema       players.json / NW card   claim_daily_salary
```

- Lore does **not** invent a parallel character slug.
- GoalChain does **not** invent a parallel yield-stream id.
- Cinema (later) binds cutscenes by the same `gw_id`. It is not a fourth key.

**Cardinality:** 1 `gw_id` ↔ 1 lore dossier ↔ 1 Genesis mint class ↔ 1 yield PDA.  
Editions / copies of the same card (Legendary 10×, Epic 100×) share the `gw_id`. They do **not** get a new id per print. On-chain, each minted edition is still one `ParodyPlayer` PDA (one owner, one claim clock) keyed by that same `gw_id`.

---

## 3. `gw_id` grammar

```
gw.<origin>.<slug>
```

| Part | Rules |
|---|---|
| `gw` | Literal. GoalWorld namespace. |
| `origin` | `nw` = Neural Wars / Publisher Lore origin. `gc` = GoalChain soccer origin. |
| `slug` | `[a-z0-9-]{1,24}`. No unicode. No `/`. |
| Total | **≤32 bytes** so it can be `ParodyPlayer.player_id` without a contract change. |
| Case | Always lowercase. Display names stay human (`Mileo Chen`, `Lionel Satoshi`). |

Reserved origins (do not issue yet): `cn` cinema, `tr` trading, `ag` genesis-agents. Same grammar when those verticals need a first-class asset.

**Forbidden as `gw_id`:** UUIDs, pubkeys, URLs, integer-only ids, spaces, uppercase.

### 3.1 Aliases (not ids)

A `gw_id` may have aliases. Aliases never become a second primary key.

| Alias type | Example | Purpose |
|---|---|---|
| Legacy catalog int | `1` | Current `players.json.id` |
| Display serial | `goalworld #001` | Metaplex `name` prefix |
| Saga-local id | `char_mileo_chen` | HTML asset filename, studio seed |
| Real-world ref | Transfermarkt `28003` | Oracle / image pipeline only. Never shown as the join key. |

The registry below is the only place aliases are legal.

---

## 4. Registry (platform-core, not a venture)

SSOT for the join is a **platform-core registry**, not GoalChain and not Publisher Lore.

- Spec (this file) is canonical until a machine file exists.
- Future machine file (out of scope here): `docs/registry/gw-bridge.json`.
- GoalChain `player_id`, lore `characters[].id`, and Metaplex attribute `gw_id` **must equal** the registry `gw_id` for every new mint.
- Existing 528 football rows keep their integer `players.json.id`. They gain a `gw_id` alias. **No remint. No PDA migration in this P1.**

Venture isolation (AGENTS.md + `ventures/goalchain-soccer/BOUNDARIES.md`):

| Venture | Owns | Must not own |
|---|---|---|
| Publisher Lore | Dossier, saga, KDP, IP hash | `$GCH` mint, salary, vault crank |
| GoalChain | NFT mint, `ParodyPlayer`, `claim_daily_salary`, sports oracle | Neural Wars prose, KDP metadata |
| Platform-core | `gw_id` registry + this bible | Either venture's business rules |
| AI Cinema | Cutscene / keyframe bound by `gw_id` | New identity scheme |

`$GCH` numbers stay in `docs/ECONOMIC_CANONICAL_CONFIG.json`. This bible does not change them.

---

## 5. How each layer binds

### 5.1 Lore (`characters[].id`)

Set `characters[].id = gw_id`.

- Saga: `the-neural-wars` (series). Book 1 reader id stays `the-neural-wars-book-1`.
- Required dossier fields: `name`, `role`, `biography`, plus `attributes.origin` (`nw` \| `gc`) and `attributes.gw_id` (duplicate of `id` for exporters that only read attributes).
- Relationships use `target_id = gw_id` of the other character.

### 5.2 Genesis card

Two series, one GoalWorld family. Symbol stays `GCH` because yield is $GCH.

| Series | Display name pattern | Who |
|---|---|---|
| `genesis-squad` | `goalworld #<NNN> - <Parody Name>` | 528 football cards |
| `neural-wars` | `neural-wars #<NNN> - <Canon Name>` | Lore-origin cards (Mileo, Kora, …) |

Required Metaplex attributes (add, do not replace existing traits):

```json
{ "trait_type": "gw_id", "value": "gw.nw.mileo" },
{ "trait_type": "origin", "value": "nw" },
{ "trait_type": "series", "value": "neural-wars" },
{ "trait_type": "saga", "value": "the-neural-wars" }
```

Football cards add the same four traits with `origin=gc`, `series=genesis-squad`, `saga=""` (or `genesis-squad-origins` when that lore lands).

On-chain for **new** mints: `ParodyPlayer.player_id = gw_id`.  
On-chain for **legacy** 528: `player_id` may remain the existing string; registry maps `gw.gc.0001` → that string. Dev must not rewrite live PDAs in this P1.

### 5.3 Yield stream

There is no separate stream id. The stream **is** the player PDA.

| Field | Binding |
|---|---|
| Stream key | `gw_id` |
| PDA | `[b"player", gw_id.as_bytes()]` (new mints) |
| Rate | `ParodyPlayer.base_yield_rate` from `rarity_base_yields_lamports` |
| Claim | Existing `claim_daily_salary` (24h). Do not wait for proposed `claim_player_yield`. |
| Sports oracle | **Only** `origin=gc`. Goals / assists / reds / elimination. |
| Lore oracle | **Only** `origin=nw`. Not specified in this P1. Until a lore-oracle exists, NW cards sit at **fixed rarity yield** (no +10% / +5% / −20%). |

Rarity → yield (do not fork):

| Rarity | Daily base (GCH) | Lamports |
|---|---|---|
| rare | 50 | 50_000_000 |
| epic | 250 | 250_000_000 |
| legendary | 1_000 | 1_000_000_000 |
| mythic | 5_000 | 5_000_000_000 |

Named Neural Wars principals are **mythic 1/1** (style guide: Mythic = 1/1). They do not consume a football catalog slot.

Vault / Infinity Engine / `vault_crank` is **protocol-level** yield (LST → buyback/burn). It is **not** keyed by `gw_id`. Do not attach a per-character vault stream. Character yield = salary PDA only.

---

## 6. Three example mappings

### 6.1 Mileo Chen — lore origin

| Field | Value |
|---|---|
| **gw_id** | `gw.nw.mileo` (12 bytes) |
| Display name | Mileo Chen |
| Origin / series | `nw` / `neural-wars` |
| Lore | Book I *Fractured Code*. Role `protagonist`. Title: Specialist L-7, Ex-NeuroSys Core, Resonance Architect. Quote on `docs/goalworld.html`. Asset `assets/img/neuralwars/char_mileo_chen.jpg`. |
| `characters[].id` | `gw.nw.mileo` |
| Saga | `the-neural-wars` / reader `the-neural-wars-book-1` |
| Genesis card | `neural-wars #001 - Mileo Chen`. Symbol `GCH`. Rarity **mythic**. 1/1. Not in `players.json` 1–528. |
| On-chain `player_id` | `gw.nw.mileo` (new mint) |
| Yield stream | Same `gw_id`. `base_yield_rate` = **5_000_000_000** (mythic). Sports oracle **off**. Claim via `claim_daily_salary`. |
| Aliases | `char_mileo_chen`, studio seed `Mileo Chen` |
| Cinema (later) | Keyframe_02 Quantum Console, Keyframe_04 Skybridge — bind by `gw.nw.mileo` |

Mileo is **not** a football parody and must not receive PAC/SHO/PAS or a Transfermarkt id.

### 6.2 Kora Vega — lore origin

| Field | Value |
|---|---|
| **gw_id** | `gw.nw.kora` (11 bytes) |
| Display name | Kora Vega |
| Origin / series | `nw` / `neural-wars` |
| Lore | Book I *Fractured Code*. Role `deuteragonist`. Title: Sensitive, Voice of the Void, Rebel biological bridge. 432 Hz resonance. Asset `assets/img/neuralwars/char_kora_vega.jpg`. |
| `characters[].id` | `gw.nw.kora` |
| Saga | `the-neural-wars` / reader `the-neural-wars-book-1` |
| Genesis card | `neural-wars #002 - Kora Vega`. Symbol `GCH`. Rarity **mythic**. 1/1. |
| On-chain `player_id` | `gw.nw.kora` (new mint) |
| Yield stream | Same `gw_id`. `base_yield_rate` = **5_000_000_000** (mythic). Sports oracle **off**. |
| Aliases | `char_kora_vega`, studio seed `Kora Vega` |
| Relationship | `{ "target_id": "gw.nw.mileo", "type": "bond" }` |
| Cinema (later) | Keyframe_06 432 Hz trance — bind by `gw.nw.kora` |

Kora is not a football card. Do not give her a nation_id from the 48 WC teams.

### 6.3 Lionel Satoshi — GoalChain origin (football card)

| Field | Value |
|---|---|
| **gw_id** | `gw.gc.0001` (10 bytes) |
| Display name | Lionel Satoshi |
| Origin / series | `gc` / `genesis-squad` |
| Legacy catalog | `players.json.id = 1`. Display `goalworld #001 - Lionel Satoshi`. Rarity **mythic**. Position FWD. Country Argentina. Captain. |
| Real-world ref (alias only) | Lionel Messi / Transfermarkt `28003` |
| Lore dossier (to create) | `characters[].id = gw.gc.0001`. Role `ensemble`. Biography: Genesis Squad origin — peak-athleticism node in The Neural Wars paradox (`docs/LORE_STRATEGY.md` pillar 3). Not a Fractured Code principal. |
| On-chain `player_id` | Legacy string as already minted (often `"1"`). Registry alias `1` → `gw.gc.0001`. New mints of this class use `gw.gc.0001`. |
| Yield stream | Same `gw_id`. `base_yield_rate` = **5_000_000_000** (mythic). Sports oracle **on** (+10% goal, +5% assist, −20% red, elimination → 0). `match_salary_gch` 1600 remains the UX salary figure; on-chain rate follows the rarity table. |
| Metaplex attrs to add | `gw_id=gw.gc.0001`, `origin=gc`, `series=genesis-squad` |
| Cinema (later) | Matchday / pack-open clips bind by `gw.gc.0001`, not by “Messi”. |

Padding is four digits because the live catalog is 528 and the style guide still cites 1,248. `gw.gc.1248` still fits in 32 bytes. Do not use `gw.gc.1` (unstable width).

---

## 7. Worked resolution (so Dev cannot invent a second key)

Given any one handle, resolve to the same row:

```
"Mileo Chen"          → registry.aliases → gw.nw.mileo
"neural-wars #001"    → registry.display  → gw.nw.mileo
PDA [player, gw.nw.mileo]                 → gw.nw.mileo
characters[].id gw.nw.mileo               → gw.nw.mileo
claim_daily_salary on that PDA            → gw.nw.mileo
```

```
players.json id 1     → registry.legacy_int → gw.gc.0001
"goalworld #001"      → registry.display    → gw.gc.0001
"Lionel Satoshi"      → registry.aliases    → gw.gc.0001
```

If two handles disagree, the registry `gw_id` wins. Display names are not unique keys.

---

## 8. Non-goals (this P1)

- No contract change. `player_id` max_len 32 is enough.
- No remint of the 528.
- No per-character vault / Jupiter stream.
- No lore-oracle percentages (chapter drops, cinema premieres) — track as a later product card.
- No IP-tokenizer / KDP royalty id. Publisher royalties stay in `ventures/publisher-lore/kdp_metadata_spec.md`. They may *cite* `gw_id` later; they must not mint a second key.
- No mixing of `$GCH` fee/burn math into the lore engine.
- No Spanish on this surface.

---

## 9. Acceptance

- [x] One `gw_id` grammar, ≤32 bytes, two issued origins (`nw`, `gc`).
- [x] Yield stream = player PDA, not a third id.
- [x] Three mappings: `gw.nw.mileo`, `gw.nw.kora`, `gw.gc.0001`.
- [x] Legacy 528 aliased, not reminted.
- [x] Venture isolation stated.
- [ ] Machine registry `docs/registry/gw-bridge.json` — **not this card**. Spawn Dev after CEO ack.
- [ ] Lore dossiers written into a saga JSON — Publisher Lore, after this bible.
- [ ] Metaplex attributes on live metadata — GoalChain, after this bible.

---

## 10. Downstream (do not implement here)

1. **Dev** — emit `docs/registry/gw-bridge.json` with the three rows + 528 `gw.gc.NNNN` aliases generated from `players.json`. Read-only. No program touch.
2. **Publisher Lore** — seed `the-neural-wars` saga JSON with `characters[].id` set to the two NW ids + Lionel ensemble stub.
3. **GoalChain** — add the four Metaplex traits on next metadata rewrite; use `gw_id` as `player_id` on any mint after the registry exists.
4. **Creative / Cinema** — keyframe and pack-open assets take `gw_id` in filenames going forward (`gw.nw.mileo_*.jpg`), no rename of existing Neural Wars art in this P1.

---

## 11. Canon sources (do not fork)

- `docs/ECONOMIC_CANONICAL_CONFIG.json` — yield table, program `FbDhM4itBS2Cco7c7PbNvC98Fx7Y5HxqXS1JuXdNcBwg`
- `contracts/programs/goalworld_program/src/state/player.rs` — `player_id` ≤32, `base_yield_rate`
- `docs/assets/data/players.json` — 528 football rows, Lionel = id 1 mythic
- `docs/METADATA_SPEC.md`, `docs/MINTING_STRATEGY.md`, `docs/NFT_STYLE_GUIDE.md`
- `docs/LORE_STRATEGY.md`, `docs/goalworld.html` dossiers, `ai_context/lore/schema/lore_schema.v0.json`
- `docs/infrastructure/05-achievements-manifesto.md`, `ventures/goalchain-soccer/BOUNDARIES.md`
- `docs/intake/2026-08-21-mundo-completo-plan.md` §4 correlation
