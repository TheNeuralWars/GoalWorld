# T5 — KDP listing runbook (Kindle first, no paperback)

**Owner:** Nico (KDP dashboard, GUI only — no CLI) + Manager (QA of the live listing)
**Blocks:** the first dollar. **Blocked by:** T1 (#877 reader gate, must be live), T3 (continuity), T4 (line edit + cover).
**Status:** prepared 2026-09-10.

---

## 0. Pre-flight (do not skip)

| Check | How | Must be true |
|---|---|---|
| The free full manuscript is gone from the web | open `https://goalworld.fun/go/reader/` | shows only a sample + price; `curl -s https://goalworld.fun/go/reader/ \| wc -c` < 60,000 |
| Manuscript is the canonical, edited tree | `SOURCE_OF_TRUTH.md` + T4 acceptance | no "lustrum", US dialogue punctuation, one frequency, one Martin thread |
| Cover is KDP-legal | your image editor | 1,600 × 2,560 px, RGB, < 50 MB, JPEG/TIFF, title legible at 200 px wide on white |
| Metadata source | `kdp_manifest.json` (in `GoalChain-faceless/data/publishing/`) | title, author, BISAC, keywords copied from there — not improvised |

**Never** keep the giveaway edition live while KU is on: KDP Select requires digital exclusivity, and a public full-text mirror is a terms violation, not a marketing choice.

## 1. Account (one time, ~20 min)

1. Sign in at `kdp.amazon.com` with the GoalWorld Amazon account (or create one; do not use a personal shopping account you cannot hand over).
2. **Author/publisher name:** `Nico Pez & The Neural Wars Studio` (per manifest). **Publisher/imprint:** `Aethelgard Press / GoalWorld Media`.
3. **Tax interview:** Tax Information → complete **W-8BEN** (non-US person). Answer as an individual unless a Delaware C-Corp exists by then — if the C-Corp lands first, use the EIN and a W-8BEN-E instead.
4. **Banking:** add the payout account (ARS account may not be supported — verify; a USD account via Wise/Payoneer is the usual workaround). Amazon pays ~60 days after month-end, so **the sale is fast and the cash is slow**. Say it out loud before treating this as cash flow.
5. Set the **royalty default** to 70% (requires list price $2.99–$9.99) or 35% (allows $0.99).

## 2. The listing (per book)

1. Kindle eBook → **Create**.
2. **Language:** English. Title exactly `The Neural Wars: Fractured Code`, subtitle `Foundational Novella (Book 1)` **only if** T2 declared the novella canonical; if T2 declared `MANUSCRIPT/` the canonical novel, drop "Novella" and drop any short-read framing.
3. **Series:** `The Neural Wars`, book `1`.
4. **Author:** as §1. **Contributors:** add a **Translator** entry if T4's editor says the English reads as a translation — that is an honesty line, not a marketing line.
5. **Description:** from `PRODUCTION/PITCH_PACKET.md`, rewritten to the declared length. The promise must match the page count.
6. **Categories (exactly three, per manifest):** *Fiction / Science Fiction / Cyberpunk*, *Fiction / Dystopian*, *Fiction / Science Fiction / Genetic Engineering*. **Do not** file under Hard Science Fiction — the manifest explicitly excludes it.
7. **Keywords:** the six from the manifest (`neural interface`, `cyberpunk novella`, `quantum AI`, `dystopian city`, `techno thriller`, `kindle short read`) — swap `kindle short read` out if the listing is a novel.
8. **Cover upload:** the T4 cover.
9. **Manuscript upload:** EPUB from `docs/publishing/KDP_EXPORT.md`. Run **Kindle Previewer** on it and check: TOC, chapter breaks, no stray `[Cosmic]`/`[Reflection]` tags, no orphaned Spanish punctuation.
10. **Price:** `$2.99` regular with a `$0.99` pre-order if you can hold it; **never** `$4.99+` for an 80-page text (that is the chargeback scenario the 2026-09-02 audit described). KDP's generated **ASIN replaces the placeholder `B0DXNEURAL1`** — nothing may link to the placeholder.
11. Publish. Then enroll in **KDP Select / KU** — only after §0's reader check passes in production.

## 3. Spanish edition (decide consciously)

If T2 declares `EDICION_2026` (or the full ES `MANUSCRIPT/`) canonical in Spanish, list it as a **separate language edition** with its own title (`The Neural Wars: Código Fracturado`) and its own ASIN. ES is the original language and the least-saturated market; the same cover family, translated description. Do not announce a "bilingual edition" that does not exist as one product.

## 4. Verification (Manager runs, then reports to Nico)

- `amazon.com/dp/<ASIN>` returns 200 and shows: the correct title, the correct author, exactly 3 categories, `Look Inside` working, price = the intended price.
- The ASIN no longer matches `B0DXNEURAL1`; the real ASIN is written back into the manifest.
- The sample (first 10%) does **not** contain the withheld chapters, and the reader page still serves only the sample.
- Royalty report shows a non-zero KENP/units line within 72h of the first sale.
- First-dollar metric (from the audit): **≥ $100 gross or ≥ 10,000 KU page-reads in 45 days, ≥ 5 organic reviews at ≥ 4.0 average.**

## 5. Rollback

Unpublish from the KDP Bookshelf (takes ~72 h to disappear from search) if a continuity or metadata defect ships. Keep the manuscript tree frozen during any live listing — no silent edits to a published book.
