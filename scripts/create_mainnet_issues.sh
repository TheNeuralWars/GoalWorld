#!/bin/bash
# Batch create GitHub issues for GoalWorld Mainnet Launch

# Ensure we are in the repo directory
cd /data/apps/GoalWorld

MILESTONE="Mainnet Launch"

create_issue() {
  local title="$1"
  local body="$2"
  local priority="$3" # priority:P0, priority:P1, priority:P2
  
  echo "Creating issue: $title ($priority)..."
  gh issue create \
    --title "$title" \
    --body "$body" \
    --label "$priority" \
    --label "mainnet" \
    --milestone "$MILESTONE"
}

# --- PHASE 0: HARDENING (P0) ---
create_issue "[P0] Audit env migration completeness - remove stale dotenv reads from API/Oracle" \
"Audit all packages (API, Webapp, Oracle, and marketing scripts) to ensure they use the unified \`@goalworld/sdk/goalworld_program_environment\` wrapper instead of scattered dotenv/process.env reads. Remove any stale/hardcoded RPC and Program ID strings." \
"priority:P0"

create_issue "[P0] Vault Crank: throw on execute mode until real Jupiter/SPL burn implemented" \
"The current vault_crank.ts implements a fake execute path using mock transactions and lacks a real SPL Token burn instruction for GCH. Modify the execute path to throw an explicit error ('Mainnet execution not implemented') until a secure, audited Jupiter swap + SPL burn mechanism is built." \
"priority:P0"

create_issue "[P0] Deploy program to mainnet-beta with multisig upgrade authority" \
"Deploy the goalworld Anchor program to Solana mainnet-beta. Immediately transfer the program upgrade authority to a secure Squads v4 multisig (3/5 threshold) to prevent single-key compromise." \
"priority:P0"

create_issue "[P0] Initialize GCH SPL mint + treasury/jackpot token accounts on mainnet" \
"Create the GCH SPL token mint on mainnet-beta (with metadata). Initialize the treasury and jackpot token accounts, and update the global config account on-chain to point to these mainnet addresses." \
"priority:P0"

create_issue "[P0] Engage security auditor (Neodyme/OtterSec) - kickoff this sprint" \
"Initiate outreach to reputable Solana security auditors (Neodyme, OtterSec, Sec3) to schedule a comprehensive audit of the Anchor program and the oracle/vault crank codebase." \
"priority:P0"

create_issue "[P0] Token sale contract - initialize_token_sale, buy_tokens, vesting instructions" \
"Design and implement a secure token sale program (or instructions within the main program) to handle GCH presale, vesting schedules, cliffs, whitelists, and hard/soft caps." \
"priority:P0"

create_issue "[P0] Genesis NFT collection deploy - Metaplex Core for 528 players" \
"Deploy the Genesis NFT collection (528 parody players) using Metaplex Core or Token Metadata standard on mainnet. Ensure metadata is frozen and creator royalties are correctly configured." \
"priority:P0"

create_issue "[P0] KYC/AML integration (Persona or on-chain KYC)" \
"Integrate a KYC/AML provider (e.g., Persona, Veriff, or Civic) into the token sale and NFT minting frontend flow to ensure regulatory compliance across targeted jurisdictions." \
"priority:P0"

# --- PHASE 1: SECURITY & CONTRACTS (P1) ---
create_issue "[P1] Legal review - token classification, terms of sale, privacy policy" \
"Obtain a formal legal opinion/memo classifying the GCH token and NFTs. Draft and publish Terms of Sale, Terms of Service, and a Privacy Policy on the marketing site." \
"priority:P1"

create_issue "[P1] Enterprise RPC - Triton/Helius/QuickNode with SLA + failover" \
"Provision enterprise-grade Solana RPC nodes (Helius, Triton, or QuickNode) with guaranteed SLAs, high rate limits, and automatic failover to handle peak traffic during the World Cup." \
"priority:P1"

create_issue "[P1] Monitoring stack - Helius webhooks -> alerting -> PagerDuty" \
"Set up Helius transaction webhooks to monitor program instructions (bets, claims, config updates) and vault crank executions. Route alerts to Sentry/Datadog and PagerDuty for 24/7 on-call coverage." \
"priority:P1"

create_issue "[P1] Remove all SimulationBadge and 'EN MIGRACIÓN' copy from frontend" \
"Clean up the webapp UI before public release. Remove all 'Simulation' badges, mock cash purchase options, and 'Hub en Migración' placeholders. Ensure all UI elements reflect live mainnet operations." \
"priority:P1"

create_issue "[P1] Load testing - simulate 10k+ concurrent bettors for Mundial traffic" \
"Perform load and stress testing using k6 or Gatling to simulate 10,000+ concurrent users placing bets and claiming payouts. Identify and fix bottlenecks in the API and RPC integration." \
"priority:P1"

create_issue "[P1] Incident runbook - program pause, emergency withdraw, oracle failure" \
"Write a detailed operational runbook for emergency scenarios: how to pause the program, how to perform emergency withdrawals of treasury funds, and how to recover from oracle/scraper failures." \
"priority:P1"

create_issue "[P1] Hermes CEO mainnet deploy + 48h soak test" \
"Deploy the Hermes CEO autonomous manager daemon to the production VPS. Run a 48-hour soak test in dry-run mode on mainnet to verify credential maintenance, X-Scout, and video automation pipelines." \
"priority:P1"

# --- PHASE 2: LAUNCH PREP (P2) ---
create_issue "[P2] Marketing site mainnet CTAs - update docs/ links" \
"Update all call-to-action (CTA) links on the goalworld.fun marketing site (docs/ folder) to point to the live play.goalworld.fun mainnet dApp instead of devnet/local URLs." \
"priority:P2"

create_issue "[P2] Soft launch (whitelist 48h) -> monitor -> public launch" \
"Execute a 48-hour soft launch restricted to whitelisted users/early supporters. Monitor RPC load, transaction success rates, and oracle sync. Resolve any minor issues before opening to the general public." \
"priority:P2"

echo "All issues created successfully!"
