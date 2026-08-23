# Mainnet Launch Roadmap - GoalWorld

## Phase 0: Environment & Security (Current)
- [ ] Remove all hardcoded network references (`new Connection`, `clusterApiUrl`) across all packages.
- [ ] Finalize environment migration (PR #25).
- [ ] Audit and revoke exposed secrets (E2B API Key).
- [ ] Clean up simulation/devnet visual indicators in the webapp.

## Phase 1: Auditor Handover
- [ ] Outreach to Neodyme and OtterSec with this Roadmap.
- [ ] Provide codebase access and documentation.
- [ ] Address auditor findings.

## Phase 2: Multisig & Treasury Setup
- [ ] Configure Squads v4 multisig.
- [ ] Prepare `deploy-mainnet.sh` script.
- [ ] Document treasury and jackpot account management.

## Phase 3: Mainnet Deployment & Smoke Tests
- [ ] Deploy Oracle and API to Mainnet.
- [ ] Execute smoke tests (E2E).
- [ ] Final verify of production configuration.

## Phase 4: Post-Launch Monitoring
- [ ] Set up monitoring for Oracle crank and API health.
- [ ] Establish incident response procedures.
