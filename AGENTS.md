# 🤖 GoalWorld: AI Agent Master Instructions

**Source of Truth.** Priority over any other README. Read this file before doing anything.

---

## 🎯 What is GoalWorld

GoalWorld is a **World of Achievements**: a multi-project venture studio built on Solana. It operates as a blank canvas for AI agents, creative IP, media automation, and decentralized finance.

The project is structured into four active verticals (ventures):
1. **Publisher Lore & IP Tokenizer:** AI-generated sagas, KDP export, and Solana IP tokenization.
2. **AI Cinema & Media Engine:** Automated video production pipeline (screenplays, storyboards, renders, and social distribution).
3. **Agentic Trading Engine:** Autonomous Hermes trading profiles operating on Solana DEXs and OKX.
4. **GoalChain Soccer (Side-Project):** The original Web3 football manager game (NFTs, Vault, Liquid Staking, and $GCH circular economy).

---

## 📂 Where each piece lives (TL;DR)

| Layer / Venture | Path | Purpose |
| :--- | :--- | :--- |
| **Platform Core** | `INDEX.md`, `README.md`, `docs/infrastructure/` | Shared infrastructure, OmniRoute, Hermes profiles, gBrain. |
| **Publisher Lore** | `ai_context/`, `ventures/publisher-lore/` | Sagas, character databases, prompt templates. |
| **AI Cinema** | `scripts/video_automation/`, `data/marketing_pipeline/` | Video generation scripts, PM2 daemon, Buffer schedules. |
| **Agentic Trading** | `scripts/`, `ventures/agentic-trading/` | Market intelligence, DEX trackers, risk controls. |
| **GoalChain Soccer** | `contracts/`, `oracle/`, `webapp/`, `api/`, `sdk/` | Solana smart contracts, sports data oracle, transactional play webapp. |

Full architecture details: `docs/infrastructure/01-memory-map.md` and `docs/infrastructure/05-achievements-manifesto.md`.

---

## 🏛️ Architecture non-negotiables

1. **Venture Isolation:** Do not mix business logic between verticals. Keep trading scripts separate from video automation, and do not reference GoalChain's $GCH tokenomics inside the Lore engine.
2. **Single Source of Truth for GoalChain Economy:** `docs/ECONOMIC_CANONICAL_CONFIG.json`. Any change in tokenomics, fees, mint gates, or burn ratios must start here.
3. **Single Source of Truth for the IDL:** `sdk/src/goalworld_program.json` (rebuilt from `contracts/programs/goalworld_program/src/lib.rs`). After any `anchor build`, copy the regenerated IDL into the SDK and run `cd sdk && npm run build`.
4. **Single Program ID for GoalChain:** `FbDhM4itBS2Cco7c7PbNvC98Fx7Y5HxqXS1JuXdNcBwg`. Hard-coded in `Anchor.toml`, `sdk/src/index.ts`, and `contracts/programs/.../lib.rs`.
5. **Never read or commit** `.env`, `fcc.secrets.env`, `config.env`, or any keypair file.

---

## 🛠️ Build & run order (GoalChain Soccer)

```bash
# 1. SDK first
cd sdk && npm run build

# 2. Start the API
cd ../api && npm run dev    # port 3001

# 3. Start the webapp
cd ../webapp && npm run dev # port 5173
```

---

## 🚨 Critical operational rules

1. **English-only on public surfaces** (Discord, X, Zealy, ads, docs marketing copy). Zero Spanish.
2. **Channel-overload discipline** — each info gets one channel; never cross-blast identical blocks.
3. **VPS-only writes** for `/data/apps/GoalWorld`. Local edits can happen for preview but deploys come from the VPS repo.
4. **One implementer per task** — Hermes CEO pipeline, draft PRs only. Never merge to main unless the issue body has `cambio urgente`.


---

## 🧰 Verification matrix

| Package | Command |
|---------|---------|
| `goalworld-sdk` | `npm run lint` (tsc --noEmit) |
| `goalworld_api` | `npm run lint` (tsc --noEmit) |
| `goalworld_oracle` | `npm run lint` (tsc --noEmit) |
| `goalworld_program` | `anchor build` |
| `goalworld_webapp` | `npx tsc --noEmit` (known wallet-adapter JSX typings warning is OK) |

Known gotcha: the webapp has a React 18 + `@solana/wallet-adapter-react` types mismatch on `ConnectionProvider`. **It does not block Vite dev.** Don't try to "fix" it — work around the typing.

---

## 🔁 Future migration (deferred)

After this reorganization, the following steps are **queued** but **NOT executed**:

- Migrate `goalworld_api/src/index.ts` import of `Connection` to use `@goalworld/sdk/goalworld_program_environment`.
- Migrate `goalworld_webapp/src/lib/goalworldClient.ts` to use the same wrapper.
- Migrate `goalworld_oracle/src/initialize_tokens.ts` and `src/vault_crank.ts` to read RPC_URL + PROGRAM_ID from the env wrapper instead of dotenv.
- Replace hard-coded `PROGRAM_ID` in older `docs/assets/js/*.js` snippets with the wrapper import.

Each migration must ship in its own PR after a successful `anchor test` and the frontend type check.

---

## 📚 Where to read next

- `ai_context/REPO_ARCHITECTURE.md` — full layer map and decision rules.
- `ai_context/META_CHARTER.md` — engineering principles.
- `ai_context/AGENT_ORCHESTRATION.md` — who merges what.
- `docs/ECONOMIC_CANONICAL_CONFIG.json` — economy canonical config.
- `WORKFLOW.md` — task workflow rules.
- `CLAUDE.md` — FCC-specific instructions.
- `AGENT_TOOLS_GUIDE.md` — tools cheat sheet.

---

**Last updated:** 2026-06-19 (Reorganization v1.0 — merged AGENTS.md + old AGENT_GUIDE.md into this single root file).
