# Ops note: Fractured Code second half (2026-10-03/04, Grok Bot overnight)

**Scope:** plan the film from where v3_ax stops (EDICION Cap.4 L49) to the Epílogo, plus a 3:12 trailer/episode. Hermes reviews every step. Generation test, then an S09 pilot only if the API works. **Nothing published, nothing deployed, nothing existing modified, nothing committed.**

## Where the film stops
- Master `FILM/renders/_conform_v3/FC_full_conform_v3_ax.mp4` (407.6 s) ends on **FC-S08-07**: Sierra's palm on the Node 17 hatch = `EDICION_2026/FC-04` **Cap.4 L49** (41.2% of the edition by words; the word midpoint is Cap.5 L39).
- FC-S08 is really 7/8 rendered (JSON/docs say 6/8). FC-S08-08 was never rendered and is covered by the new FC-S09-01.

## New files (all new; GoalChain tree untouched otherwise, nothing staged)
`FILM/plans/`:
- `FC_WHOLE_BOOK_MAP_20261003.md`
- `FC_PRODUCED_SCENES_INVENTORY_20261003.md`
- `FC_SECOND_HALF_PLAN_20261003.md` (§9 Hermes review log, §10 cross-check, §11 generation)
- `FC_SECOND_HALF_SHOTS_20261003.json`
- `FC_NARRATION_SCRIPT_DRAFT_20261003.md`
- `fc_second_half_crosscheck_20261003.py`
- `fc_s09_pilot_runner_20261003.py` (v1, audit record of the first 403 call)
- `fc_s09_pilot_runner_v2_20261003.py` (gated, 2–3 refs via `/v1/images/edits`, single attempt, stops on the first error)
- `PROPOSED_LOCATION_NODE_17_SERVER_CATHEDRAL_20261003.md` (proposal only; also proposes registering `the_architect`)

`FILM/reports/`:
- `hermes_review_*_20261003.md`
- `FC_SECOND_HALF_CROSSCHECK_20261003.{md,json}`

`FILM/renders/FC-S09_pilot_20261003/`: `pilot_log.jsonl`, `STOPPED.json`, `STOPPED_v2_20261003T225220.json` (no renders).

## Generation
Two minimal calls, both the S09-01 still; each stopped at once with no retry:
1. 2026-10-03 23:31 CEST, runner v1: `POST /v1/images/generations` (grok-imagine-image).
2. 2026-10-04 00:52 CEST, runner v2 `--test`: `POST /v1/images/edits` (grok-imagine-image-quality, 2 refs).

Both returned **HTTP 403 `{"code":"unauthenticated:bad-credentials","error":"The OAuth2 access token could not be validated."}`**.
- This is an auth error, not quota. `~/.grok/auth.json` was last written 2026-09-25 13:22 CEST, so the access token has expired.
- **Fix (owner):** log in again, or run the token refresh used by `scripts/video_automation/nw_regen_20260914/xai_client.py` (it rotates the refresh token and rewrites auth.json; I deliberately did not run it).
- **Then:**
  1. `cd FILM/plans`
  2. `python3 fc_s09_pilot_runner_v2_20261003.py --test`
  3. `--stills --approve-gates needs_location_token:node_17_server_cathedral` (after approving the location proposal and the spend)
  4. `--videos …`
  5. ContinuityGuard into `FILM/reports/continuity_S09_pilot_20261003`, then a Hermes review, then Director approval.
- S09 (8 shots) is `queued_blocked_auth`; S10–S18 are planned and gated on new locks/locations and spend.

## Hermes reviews (raw in FILM/reports, logged with fixes in plan §9)
- R1 map: PASS WITH FIXES (6/6 fixed).
- R2 inventory: 6 of 7 fixed, 1 rejected with evidence.
- R3 plan: 12/12 fixed.
- R4 narration: PASS WITH FIXES (6/6 fixed).
- R5 S09 pilot package: FAIL → 21 fixed, 1 rejected, 1 kept by design. This led to runner v2, gates, multi-ref anchors and the full VISUAL_BIBLE negatives.

## Final cross-check
`reports/FC_SECOND_HALF_CROSSCHECK_20261003.md`: **PASS, 0 errors, 0 warnings**.
- EDL 58 segments, contiguous to 192.5 s.
- v3_ax rebuilt at 407.6 s; SSIM 0.80–0.99.
- 23 narration beats within pace and gap limits; 9 quotes verbatim.
- 76 shots with locks and negatives; docs mirror the manifest.

## Hermes access note
- API `:8642` with the staged `hermes-api.env` key → `gateway_auth_failed` (key rotated?). The staged key needs refreshing for API use.
- Reviews ran via the documented SSH-relay route instead: `hermes -z` on the default model deepseek/deepseek-v4.1-flash. No grok-4.6 was used.

## Discrepancies for the owner
- FC-S08 JSON says `rendered_6_8`, but 7/8 are rendered. FC-S06A JSON says `ready_for_render`, but it is rendered and cut.
- The live minifilm URL file is 542.1 s; the repo copy at `GoalWorld/docs/assets/img/neuralwars/FC_minifilm_239_v3.mp4` is 530.2 s.
- ContinuityGuard pulses still scan the old 848×480 `_cut_v1` cuts.
- `NODE_17_SANITATION_LOCK.md` says the hatch is steel; the book (Cap.4 L49) and S08-07 say titanium.
- `the_architect` has a lock sheet but no WORLD_TOKENS key.
- The lock-sheet pipeline note says a 403 means quota, but this 403 body is an auth error.
- The climax (Mileo becomes the network) is not on the page in EDICION_2026. It is adapted from `MANUSCRIPT/FC-07-Chapter.md` L315–L451.

## Addendum 2026-10-04 (06:00–06:30 CEST): S09 rendered after Nico's re-auth and approvals
- **Approved and registered** `node_17_server_cathedral`. This is additive only:
  - new `FILM/locks/locations/NODE_17_SERVER_CATHEDRAL.md`
  - new key in `FILM/WORLD_TOKENS.json` (+23/−0)
  - +1 row in `locks/locations/README.md`
  - backups in `/data/backups/goals/*.bak-20261004-035816`
  - Uncommitted. The pre-existing uncommitted LOCK_SHEET edits from 2026-09-24 are not mine.
- **Runner v2.1/v2.2** (`FILM/plans/fc_s09_pilot_runner_v2_20261003.py`): 8/8 stills and 8/8 videos OK.
  - Only error: **HTTP 400 `Cannot set both 'url' and 'file_id' on an image input; they are mutually exclusive`** when 3 refs were sent to `/v1/images/edits`. Fixed by capping at 2 refs.
  - No auth errors after the re-auth. The keepalive cron was not touched.
- **Outputs:** `FILM/renders/FC-S09_pilot_20261003/FC-S09-0{1..8}.{png,mp4}` plus `README_PILOT_RESULTS_20261004.md`.
- **Review copy (local VPS only):** `FILM/renders/FC-S09_pilot_20261003/review_20261004/FC-S09_rough_assembly_20261004.mp4`, 46.458 s.
- **ContinuityGuard:** `FILM/reports/continuity_S09_pilot_20261004/`. S09 physics 0 flags; face S08↔S09 0.8832 (threshold 0.88).
- **Hermes R6:** `FILM/reports/hermes_review_s09_renders_20261004.md`. **FAIL for director review**: keep 07, keep-with-note 04, regen 01/02/03/05/06/08.
- **Regen queue (NOT run, needs spend approval):** `FILM/plans/FC_S09_REGEN_QUEUE_20261004.json`.
- **Cross-check** re-run: PASS, 0 errors.
- **Scratch:** moved to `~/fc_grokbot_20261004/` (the VPS rebooted at 02:43 CEST and wiped `/tmp/fc_grokbot_20261003/`).

## Addendum 2 2026-10-04 (10:25–10:40 CEST): S09 r2 regen (spend approved)
- **Regens:** 6/6 stills + 6/6 videos as `_r2` via `--queue FC_S09_REGEN_QUEUE_20261004.json`. No errors, no retries.
- **Assembly:** `FILM/renders/FC-S09_pilot_20261003/review_20261004_r2/FC-S09_r2_rough_assembly_20261004.mp4`, 46.458 s.
  - Web copy `FC-S09_r2_review_web.mp4` (960×540, H.264 Main, CRF 26) is in the same folder, plus a box copy at `/workspace/fc_s09/`.
- **ContinuityGuard:** `FILM/reports/continuity_S09_r2_20261004/`. Physics 0 flags; face FLAG 0.8308 < 0.88.
- **Hermes R7:** `FILM/reports/hermes_review_s09_r2_20261004.md`. FAIL: 5/8 approvable; 01r2, 05r2, 08r2 still fail. No auto-regen.

## Addendum 3 2026-10-04 (10:44–10:55 CEST): S09 r3 for 01/05/08 (approved)
- **Generation:** 3/3 stills + 3/3 videos `_r3`, no errors.
- **Assembly:** `FILM/renders/FC-S09_pilot_20261003/review_20261004_r3/FC-S09_r3_rough_assembly_20261004.mp4`, 46.458 s. Web copy in the same folder, plus a box copy at `/workspace/fc_s09/FC-S09_r3_review_web.mp4`.
- **ContinuityGuard:** `FILM/reports/continuity_S09_r3_20261004/`. Physics 0; face FLAG 0.8333.
- **Hermes R8:** `FILM/reports/hermes_review_s09_r3_20261004.md`. FAIL: 7/8 approvable; 08r3 still fails. No auto-regen.

## Addendum 4 2026-10-04 (11:15–11:27 CEST): S09-08 split into 08a/08b (r4, approved)
- **Generation:**
  - 08a OK.
  - 08b: first still rejected in QC (muzzle aimed at Mileo); single retry `_r4retry` used.
  - No API errors.
- **Assembly:** `FILM/renders/FC-S09_pilot_20261003/review_20261004_r4/FC-S09_r4_rough_assembly_20261004.mp4`, 47.625 s. Web copy is in the same folder, plus a box copy at `/workspace/fc_s09/FC-S09_r4_review_web.mp4` (7.2 MB).
- **ContinuityGuard:** `FILM/reports/continuity_S09_r4_20261004/`. Physics 0; face FLAG 0.8445.
- **Hermes R9:** `FILM/reports/hermes_review_s09_r4_20261004.md`. PASS WITH NOTES; 08b strike not shown and Sierra forearm glow are director calls.

## Addendum 5 2026-10-05: Riv blood kept
- **Director decision (Nico):** KEEP the blood on Riv's face in S09 shots 01 and 03 — it is from the fight. No regen.
- Logged in plan §4.1 and §9 (R7/R8 notes closed).

## Addendum 6 2026-10-05: Sierra hair tied back as S08
- **Director decision (Nico):** Sierra's hair is **tied / pulled back as in S08**. No S09 regen for hair alone.
- **Updated (backups first):**
  - `FILM/locks/LOCK_SHEET_SIERRA_CATALANO.md` (Hair row, prompt constraint, new §9)
  - `FILM/WORLD_TOKENS.json` (`sierra_catalano.invariants` hair string + `hair` + `hair_continuity_note`)
- **Backups:** `/data/backups/goals/FILM_LOCK_SHEET_SIERRA_CATALANO.md.bak-20261005-174834`, `FILM_WORLD_TOKENS.json.bak-20261005-174834`
- Logged in plan §4.1.

## Addendum 7 2026-10-06 (08:00–08:03 CEST): S09-08b r5 (approved, 2 attempts)
- **Generation:** two stills, both HTTP 200, no API errors: `FC-S09-08b_r5.png` and `FC-S09-08b_r5b.png` in `FILM/renders/FC-S09_pilot_20261003/`.
- **QC:** both FAIL. The model drew a normal firing grip with the muzzle aimed down at Mileo's neck/cable, and the strike is absent. No video generated; attempts exhausted.
- **Hermes R10:** `FILM/reports/hermes_review_s09_r5_20261006.md`. FAIL both; keep 08b_r4retry; suggests a composite/inpaint or a severed-connector insert.
- **Not produced:** r5 assembly, ContinuityGuard run, r5 web copy (no new clip).

## Addendum 8 2026-10-06 (08:14–09:10 CEST): S09-08c insert + r6 assembly (approved by Nico)
- **New shot 08c** (insert, Nico's brief: EPP connector at Mileo's nape severing on the butt strike — EDICION Cap.4 L89–L91 — sparks, cable jumping; no barrel/muzzle; only Mileo glows; steady red alarm light, no flashes; S09 palette; max 2 attempts).
- **Attempt 1 `_r6`** (generated 06:14–06:15Z by the Grok Bot runner before this pass): action ✓ in motion, look ✗ (blue strike window, grip lingers). **Attempt 2 `_r6b`** (06:43–06:45Z): look ✓ (red even wash measured), action ✗ (static, no severing). Attempts exhausted.
- **Final insert `FC-S09-08c_r6g.mp4` (1.917 s)** = `_r6` window [0.45→2.35 s] + red-wash grade matched to the `_r6b` look. Review vs L89–L91: the culatazo cutting the cable reads. New files only; nothing approved modified.
- **Montage:** 08b [0→2.5 s] (pistol lowering starts at 2.5 s) → hard cut → 08c → 08b tail [2.8→6.042 s] (red sweep 2.8–3.2 s + Mileo falling). 08b turns blue→red at 2.4–3.0 s (measured with 1×1 RGB probes), so the insert lands on the alarm turn.
- **Assembly:** `renders/FC-S09_pilot_20261003/review_20261006_r6/FC-S09_r6_rough_assembly_20261006.mp4`, 58.461 s. **Web copy** `FC-S09_r6_review_web.mp4`: 960×540 H.264 Main yuv420p faststart CRF26, 7,649,722 B.
- **ContinuityGuard** `FILM/reports/continuity_S09_r6_20261006/`: physics 0 flags (cut + 12 clips); face Sierra S08↔S09 0.8432 FLAG (known ref/hair drift, notes closed by Nico 2026-10-05).
- **Ops incident 1:** xAI OAuth token in `~/.grok/auth.json` expired 06:17Z → first r6b call got HTTP 403 `unauthenticated:bad-credentials`. Refreshed with the crontab keepalive command (`cd .../nw_regen_20260914 && python3 -c "import xai_client as x; x.get_token(force=True)"`), new expiry 12:43Z. The 8-hourly keepalive (:17 every 8 h) leaves a 2-hour expiry gap — consider hourly.
- **Ops incident 2:** `cg-venv` broke mid-run (`No module named 'numpy._core._multiarray_umath'`, numpy 2.4.3 vs opencv 4.14) and self-healed to numpy 2.5.3 before the face pass re-ran. Watch it.
- Logged: plan §4.1, §9 (R11), §11.6; `renders/FC-S09_pilot_20261003/README_R6_RESULTS_20261006.md`. No locks/WORLD_TOKENS touched → no backups needed. No git, no publishing. S10 not started.

## Addendum 9 2026-10-06 (09:37–09:55 CEST): S09 r7, ungraded 08c in book order + r6 duration fix (Nico's decision, ffmpeg only)
- **Decision (Nico):** ungraded 08c, book order (no red in the insert; red after/with Mileo's fall, L89–91).
- **New inserts:**
  - `FILM/renders/FC-S09_pilot_20261003/FC-S09-08c_r7.mp4`: same r6g window, no grade, 1.917 s. Its last 0.6 s shows a small red ceiling strip, which lights on the plate at 1.75 s.
  - `FC-S09-08c_r7n.mp4`: 1.5 s strict no-red window.
- **Duration:** r6's 58.461 s = r4's 47.625 + 7.167 (r6 used a plain concat; it dropped r4's 0.8 s xfades at 9 joins) + 3.667 (08b slot 4.0→7.667 s). No trims lost. r7 restores the xfades; the section keeps its internal hard cuts.
- **Book order fix:** 08b is fully red from 3.75 s, but Mileo only starts falling at ~4.5 s, so the tail now starts at 4.5 s (was 2.8 s).
- **Assembly:** `review_20261006_r7/FC-S09_r7_rough_assembly_20261006.mp4`, **49.583 s**. Web copy `FC-S09_r7_review_web.mp4`: 960×540 H.264 Main yuv420p faststart CRF26, 7,425,083 B. Box copy `/workspace/fc_s09/FC-S09_r7_review_web.mp4`.
- **Alt:** `FC-S09_r7n_*` 49.208 s, web 7,387,606 B, box copy `/workspace/fc_s09/FC-S09_r7n_review_web.mp4`.
- **ContinuityGuard:**
  - `FILM/reports/continuity_S09_r7_20261006/`: pass1 2 flags (ratios 3.0/3.2), both on the intentional 08b→08c and 08c→tail hard cuts; pass2 0; face 0.8453 FLAG (known).
  - r7n: 1 / 0 / 0.846.
- **Scripts:** `~/fc_grokbot_20261004/src/{make_08c_r7,assemble_s09_r7,cg_r7}.sh`. Logs: `~/fc_grokbot_20261004/logs/{make_08c_r7,assemble_r7,assemble_r7n,cg_r7,cg_r7n}.log`.
- **Logged:** plan §4.1, §9 (R12), §11.7; `README_R7_RESULTS_20261006.md`. Backups of both docs are in `/data/backups/goals/*.bak-20261006-094845`.
- **Untouched:** no approved files, no git, no publishing, no generation, no xAI calls.
- **Note:** the r6 run left an untracked staging stub `FILM/scenes/FC-S09.json` (182 B, Hermes 07:04Z). r7 did not use or change it.
