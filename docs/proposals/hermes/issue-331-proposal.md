# OA Proposal — Issue #331

## Title
[OPENCODE] Program: Update goalworld-sdk IDL generation + sync script

## Source
GitHub issue #331

## Objective
## Objective
Sync SDK with new modular program IDL:

## Scope
1. Create `packages/program/scripts/sync-idl.ts`:
   - Run `anchor build`
   - Copy `target/idl/goalworld_program.json` → `../goalworld-sdk/src/goalworld_program.json`
   - Copy `target/types/goalworld_program.ts` → `../goalworld-sdk/src/goalworld_program.ts`
   - Run `cd ../goalworld-sdk && npm run build`
2. Update `goalworld-sdk/package.json` build script to include IDL sync
3. Verify `goalworld_oracle` imports work with new types

## Acceptance Criteria
- IDL matches deployed program exactly
- SDK builds without errors
- Oracle imports @goalworld/sdk types successfully
- No breaking changes to public API

## Skill Hint
Follow gstack review pass before opening draft PR.

## Owner
opencode

## Priority
P0

## Context
Requested by Nico via Manager (WhatsApp/OpenClaw). Keep scope tight and aligned with goalworld orchestration rules.

## Required output
- Proposed file list
- Risks/regressions + rollback
- Exact test commands

## Workflow
- One implementer only
- Branch naming:
  - cursor: `feat/*` or `fix/*`
  - antigravity: `exp/antigravity-*`

## OA Plan (draft)
- Analyze repository constraints and META alignment.
- Implement minimal safe changes first.
- Run local checks where feasible.
- Prepare draft PR for Cursor review.

## Risk / rollback
- Risk: scope drift or unstable dependencies.
- Rollback: revert main commit linked to issue #331
