# T4 — US line-editor brief (The Neural Wars, Book 1)

**Owner:** Nico (hire/approve) + Manager (source bids, ship files, verify deliverables)
**Blocks:** T5 (KDP listing). **Blocked by:** T3 (surgical continuity pass).
**Status:** prepared 2026-09-10 — ready to send the moment T3's manuscript is frozen.

---

## 1. What is being edited

Read the canonical verdict first: `docs/publishing/the_neural_wars_trilogy/BOOK_01_FRACTURED_CODE/SOURCE_OF_TRUTH.md` (produced by issue #878). The scope depends on it:

| If T2 declares canonical… | Words to edit | Edit type | Realistic bid range |
|---|---|---|---|
| `MANUSCRIPT/` — the full-length EN novel | **~146,000** | line edit + copyedit | **$1,100–2,900** (`$0.008–0.02`/word) |
| `ENGLISH_EDITION_2026/` — the condensed EN edition | **~16,900** | line edit + copyedit | **$140–340** (`$0.008–0.02`/word) |

Rule of thumb: a *line* edit (rhythm, register, sentence architecture) costs roughly `$0.010–0.020`/word; a *copy* edit (grammar, punctuation, consistency — including fixing the em-dash dialogue to US quotation marks) is roughly `$0.005–0.012`/word. Ask for a **paid 1,000-word sample** before contracting; reject samples that only fix commas.

## 2. Non-negotiable editor brief (send verbatim)

> This is a **line/copy edit of an English-language cyberpunk novel**, not a developmental edit, not a translation review of the plot, and not a rewrite.
>
> **Do:**
> 1. Convert dialogue from Spanish-style em-dash transcription to **US convention** (double quotation marks, comma inside, attribution tags). This is the single most visible tell in the manuscript.
> 2. Kill remaining calques and translation tells — e.g. "for three lustrums" must never survive. Flag every Spanish-to-English structural transplant you find.
> 3. Break 1:1 Spanish hypotaxis: one 70-word sentence where an American novelist would use four. Vary rhythm; keep the staccato where it is deliberate.
> 4. Cut ~15% of the sensory repetition (ozone / copper / indigo / frost / jasmine). It is currently a checklist on a timer.
> 5. Keep the plot, the chapter structure, character names and hard facts **exactly as supplied**. Continuity defects are already fixed and frozen — do not "improve" the story.
> 6. Preserve the author's voice where it lands. This is not an exercise in homogenising into house style.
>
> **Do not:** add scenes, cut chapters, change who dies, change the ending, or re-title anything.
>
> **Deliver:** marked-up manuscript (`.docx` with tracked changes) + a clean export + a 1-page editorial letter listing systematic issues and what you standardised. Also state, in one sentence, whether the English reads as **originally written** or as a **translated work** — we must credit this accurately on the Amazon listing.

## 3. Where to source (Nico, GUI)

- **Reedsy** (reedy.com/marketplace) — curated, live chat, filtered by genre; highest quality, highest rate.
- **Upwork** — filter "Science Fiction" + "Line Editing", require a paid sample.
- **ACES / Editorial Freelancers Association** (the-efa.org) — vetted US editors, good for the copy pass.
- Require: native/fluent US English, ≥ 3 published SF credits, sample chapter.

## 4. Acceptance test for the deliverable (Manager verifies)

- Tracked-changes `.docx` returned; clean export matches tracked version word-for-word.
- `grep -ric "lustrum" <edited tree>` == 0
- dialogue uses `"` not `—` for speech: `grep -c '^"' <edited tree>` > 0 and em-dash-initial dialogue lines == 0
- word count within ±10% of the source (a cut larger than that means the editor rewrote, not edited)
- editorial letter names the standardised rules and the "original vs translated" verdict.

## 5. Then hand to T5

Once accepted, the edited files go to T5: cover (1,600 × 2,560 px, RGB, < 50 MB, title legible at 200 px wide) + EPUB upload + metadata from `kdp_manifest.json`. Cover concepts are already drafted in `BOOK_01_FRACTURED_CODE/PRODUCTION/COVER_CONCEPTS_AND_PROMPTS.md`.
