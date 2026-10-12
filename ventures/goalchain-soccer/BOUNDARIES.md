# GoalChain Soccer — Boundary Doc

Status snapshot: frozen for audit as of 2026-08-10.

This document defines the formal boundary of the GoalChain Soccer side-project inside the GoalWorld monorepo. It is intentionally conservative: if a file, directory, or runtime service is not explicitly listed here, it must be treated as outside the GoalChain boundary until reviewed and added in a future audit.

## 1) Scope statement

GoalChain Soccer is the sports side-project of GoalWorld. Its remit is the Web3 football manager experience, including:
- player/NFT gameplay mechanics
- on-chain program logic for GoalChain-specific assets and flows
- supporting SDK and client code for GoalChain interactions
- oracle and backend services that directly feed GoalChain gameplay
- documentation that defines GoalChain's canonical economy, program ID, IDL, and operating rules

GoalChain is not the owner of the broader GoalWorld platform. Shared platform concerns remain shared unless they are explicitly re-homed here.

## 2) Included boundary

The following repository areas belong to GoalChain when they contain GoalChain-specific code or canonical references:

- `contracts/`
  - Anchor programs, instructions, accounts, tests, migrations, and build artifacts for GoalChain
- `oracle/`
  - sports-data ingestion, scoring, settlement helpers, and any GoalChain-specific oracle worker
- `webapp/`
  - GoalChain UI routes, components, wallet interactions, and client-side gameplay views
- `api/`
  - GoalChain endpoints, settlement APIs, game-state APIs, and supporting server logic
- `sdk/`
  - client SDK, program bindings, generated IDL consumers, and GoalChain program constants
- `docs/`
  - GoalChain canonical configuration and operating documents, especially:
    - `docs/ECONOMIC_CANONICAL_CONFIG.json`
    - `docs/infrastructure/05-achievements-manifesto.md`
    - any GoalChain-specific audit, migration, or runbook documents
- `ventures/goalchain-soccer/`
  - all GoalChain venture documentation, audit notes, and frozen boundary artifacts

## 3) Explicitly shared platform boundary

These areas are shared GoalWorld platform infrastructure and are not GoalChain-owned unless a file is explicitly GoalChain-specific:

- `ai_context/`
- `scripts/`
- `data/marketing_pipeline/`
- `ops/hermes/`
- `docs/infrastructure/` docs that describe platform-wide concerns only
- generic CI/CD, observability, or workspace tooling that does not implement GoalChain gameplay or settlement

If a shared file contains GoalChain constants, it is a bridge dependency, not an ownership transfer.

## 4) Canonical GoalChain anchors

The following values are treated as source-of-truth anchors for GoalChain-related code and docs:

- Program ID: `FbDhM4itBS2Cco7c7PbNvC98Fx7Y5HxqXS1JuXdNcBwg`
- IDL source of truth: `sdk/src/goalworld_program.json`
- Economy source of truth: `docs/ECONOMIC_CANONICAL_CONFIG.json`

Any code that hard-codes, duplicates, or overrides these anchors must be reviewed against this boundary document.

## 5) Freeze rules

While this boundary is frozen for audit:

1. Do not expand GoalChain ownership to new directories without a documented review.
2. Do not move shared platform files into GoalChain unless the migration is explicitly approved.
3. Do not infer GoalChain ownership from folder proximity alone; the inclusion must be documented.
4. Do not change canonical constants in multiple places. Update the source of truth first, then propagate intentionally.

## 6) Audit checklist

Before approving a change as GoalChain-scoped, verify:
- the file lives in an included boundary path, or is explicitly documented as GoalChain-owned
- the change does not blur shared platform concerns into the venture boundary
- program ID / IDL / economy references match canonical sources
- tests cover any settlement, payout, or state-transition logic changed
- docs and code agree on ownership and runtime scope

## 7) Out of scope

The following are outside GoalChain unless a future review explicitly moves them in:
- publisher/lore content pipelines
- AI cinema generation workflows
- agentic trading infrastructure
- generic infrastructure utilities used by multiple ventures
- user-facing marketing docs that only describe GoalWorld at the umbrella level

## 8) Notes for future auditors

This boundary is a snapshot, not a license to expand the venture silently. If a new GoalChain module appears, first decide whether it is truly venture-specific or only a shared platform utility with GoalChain dependencies.

If the repo structure changes, update this document together with the corresponding architecture docs so the ownership map remains auditable.
