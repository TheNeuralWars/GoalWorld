# GW-TRADING-003 — Whale Tracker: Research Report

**Status:** Discovery / Research
**Date:** 2026-08-10
**Author:** trader (Agentic Trading Engine)
**Scope:** Investigate APIs and webhooks (Helius, Birdeye, etc.) for real-time smart-money monitoring on Solana.

---

## 1. Objective

Design the data layer for the **On-Chain Tracker** component described in `ventures/agentic-trading/README.md`:

> *"Módulos en Python que monitorean pools de Raydium/Meteora y transferencias de billeteras marcadas como 'smart money'."*

The goal is to identify the best providers, webhook/streaming mechanisms, and integration architecture to detect **whale / smart-money activity in real time** — large swaps, accumulation, insider buys, and wallet-label signals — feeding the trading engine's risk and alpha pipeline.

---

## 2. Provider Landscape (Shortlist)

| Provider | Type | Real-time | Cost model | Best for |
| :--- | :--- | :--- | :--- | :--- |
| **Helius** | RPC + Webhooks + Enhanced TX | Webhooks (push) | Freemium, tiered | Parsed transactions, account/address monitoring, DAS API |
| **Birdeye** | Market data API + WS | REST + WebSocket | Freemium, tiered | Token prices, OHLCV, wallet token holdings, top traders |
| **Solana RPC (Geyser)** | Raw RPC / gRPC | Polling / streaming | Self-host or provider | Full control, raw account/program data |
| **Jupiter API** | DEX aggregation | REST | Free | Swap quotes, price impact, route data |
| **Shyft.to** | RPC + Webhooks | Webhooks (push) | Freemium | Alternative to Helius for TX parsing |
| **Triton / QuickNode** | RPC + Geyser | Streaming | Tiered | High-throughput Geyser streams |
| **Dune / Flipside** | Analytics SQL | Batch | Freemium | Historical whale behavior, cohort analysis |
| **SolanaFM / Solscan** | Explorer + API | REST | Freemium | Wallet labels, token holders, enrichment |

**Recommendation:** **Helius (primary) + Birdeye (secondary)** for the MVP. Helius for real-time parsed transaction webhooks; Birdeye for market context, top-trader lists, and token holdings snapshots.

---

## 3. Helius — Deep Dive (Primary)

### 3.1 Enhanced Transaction Webhooks (Push)
- **What:** Helius parses raw Solana transactions into a human-readable `EnhancedTransaction` JSON and pushes them to your HTTPS endpoint via webhook.
- **Key fields for whale detection:** `type` (SWAP, TRANSFER, BURN, MINT...), `description` (e.g. "Swapped 5,000 SOL for 12,000 USDC"), `nativeTransfers`, `tokenTransfers` (with `fromUserAccount`, `toUserAccount`, `mint`, `tokenAmount`, `rawTokenAmount`), `signature`, `timestamp`, `fee`, `accountData`.
- **Filtering:** Webhooks can be scoped by:
  - **Account address** (watch a specific wallet or program).
  - **Transaction type** (e.g. only SWAP).
  - **Program** (Raydium, Meteora, Jupiter, Pump.fun, etc.).
- **Delivery:** HTTPS POST with retries; supports `encoding` and `transactionType` filters. Latency is near-real-time (sub-second to a few seconds).

### 3.2 Webhook Types
1. **Enhanced** — parsed transactions (recommended for smart-money logic).
2. **Raw** — raw transaction data (heavier, more parsing work).
3. **DAS API** — Digital Asset Standard (NFT/metadata) events.
4. **Account** — account state changes (useful for tracking a whale's balance).

### 3.3 Other Helius APIs
- **Enhanced Transactions (REST):** fetch parsed history for an address (`/v0/addresses/{address}/transactions`).
- **DAS API:** token/NFT metadata, owner lookups.
- **Webhook management API:** create/list/delete webhooks programmatically (`/v0/webhooks`).
- **Balance / account info:** standard RPC methods.

### 3.4 Pricing (typical tiers)
- Free tier: limited requests/min + limited webhooks.
- Paid tiers scale webhook volume, request rate, and add features (e.g. higher concurrency, priority fee support).
- *Verify current pricing at helius.dev — tiers change.*

### 3.5 Integration notes
- Requires an **HTTPS endpoint** to receive webhooks (the VPS must expose a public URL, or use a tunnel/relay).
- **Auth:** webhooks can include an `Authorization` header / HMAC signature to verify origin.
- **Retry/backoff:** implement idempotent processing keyed on `signature` to avoid double-counting.
- **Rate limits:** respect per-tier request caps; batch REST fetches.

---

## 4. Birdeye — Deep Dive (Secondary)

### 4.1 Capabilities
- **Token price / OHLCV:** real-time and historical price data for any SPL token.
- **Wallet token holdings:** current and historical holdings for a wallet address.
- **Top traders / smart money lists:** Birdeye surfaces top traders by token and "smart money" wallet lists (proprietary scoring).
- **Token security / metadata:** supply, holders, liquidity, market cap.
- **WebSocket:** real-time price/trade streams for subscribed tokens.

### 4.2 Relevance to Whale Tracker
- Use Birdeye to **enrich** Helius signals: when a Helius webhook fires a large swap, query Birdeye for the token's price impact, liquidity depth, and whether the buying wallet is a known "top trader."
- Use Birdeye's **top-trader / smart-money lists** to seed the watchlist of wallet addresses that Helius webhooks then monitor in real time.
- Use Birdeye **WebSocket** for live price feeds on the tokens GoalWorld trades (SOL, USDC, GCH, and any tracked alts).

### 4.3 Pricing
- Freemium; free tier has rate limits; paid tiers unlock higher rate limits and more endpoints.
- *Verify current tiers at birdeye.so / docs.birdeye.so.*

---

## 5. Architecture Proposal

### 5.1 Data flow
```
[Helius Webhook (push)] ──► [Ingest Service (FastAPI on VPS)]
        │                                │
        │  parsed EnhancedTransaction    │  validate HMAC, dedupe by signature
        ▼                                ▼
[Whale Detection Engine] ◄── [Redis / in-memory state]
        │  rules: amount threshold, wallet label, program, velocity
        ▼
[Signal Bus] ──► [Trading Engine / Risk Controller]  (data/trading/risk_limits.json)
        │
        ▼
[Postgres / SQLite]  (historical whale log for backtesting & P&L)
```

### 5.2 Components
1. **Ingest Service** (`scripts/trading/whale_ingest.py`): FastAPI endpoint receiving Helius webhooks; HMAC verification; dedupe by `signature`; normalize into a canonical `WhaleEvent` schema.
2. **Watchlist Manager** (`scripts/trading/whale_watchlist.py`): manages the set of wallet addresses + programs to monitor; seeded from Birdeye top-trader lists + manual curation; persisted to JSON/SQLite.
3. **Detection Engine** (`scripts/trading/whale_detector.py`): applies rules (min USD notional, min token amount, wallet label, program filter, velocity/accumulation window) to decide if an event is "smart-money-worthy."
4. **Enrichment Client** (`scripts/trading/birdeye_client.py`): queries Birdeye for price impact, liquidity, top-trader status, and token metadata.
5. **Signal Publisher**: emits structured signals (JSON) to the trading engine and logs to `data/trading/whale_events.log`.

### 5.3 Canonical WhaleEvent schema (draft)
```json
{
  "signature": "5x...",
  "timestamp": "2026-08-10T21:00:00Z",
  "type": "SWAP",
  "program": "Raydium",
  "wallet": "WhaleAddr...",
  "wallet_label": "top_trader_sol",
  "token_in": {"mint": "...", "amount": 5000, "symbol": "SOL"},
  "token_out": {"mint": "...", "amount": 12000, "symbol": "USDC"},
  "notional_usd": 120000.0,
  "price_impact_percent": 0.4,
  "liquidity_usd": 2500000.0,
  "confidence": 0.85,
  "flags": ["large_notional", "known_wallet", "accumulation"]
}
```

### 5.4 Risk & ops guardrails (aligned with `data/trading/risk_limits.json`)
- Whale signals are **informational / alpha input only** — never auto-execute trades from a single whale event without the Risk Controller's approval.
- Respect `max_exposure_usd`, `max_leverage`, and `require_cooldown_minutes` from `risk_limits.json`.
- Webhook ingest must be **idempotent** and **rate-limited** to avoid flooding the engine.
- Store raw + normalized events for auditability and backtesting.

---

## 6. Implementation Plan (Next Steps)

| Step | Task | Owner | Depends on |
| :--- | :--- | :--- | :--- |
| 1 | Create Helius account, generate API key, provision webhook endpoint on VPS | trader | — |
| 2 | Stand up FastAPI ingest service + HMAC verification | trader | 1 |
| 3 | Implement `whale_watchlist.py` (seed from Birdeye top traders) | trader | 1,2 |
| 4 | Implement `whale_detector.py` detection rules | trader | 2 |
| 5 | Implement `birdeye_client.py` enrichment | trader | 1 |
| 6 | Wire signals to trading engine + risk controller | trader | 4,5 |
| 7 | Add `data/trading/whale_events.log` + Postgres persistence | trader | 2 |
| 8 | Backtest detection rules against historical whale data | trader | 7 |

---

## 7. Open Questions / Decisions Needed

1. **Budget:** Which Helius/Birdeye paid tier is acceptable? (Free tier may be too rate-limited for production.)
2. **Endpoint exposure:** Confirm the VPS can expose a public HTTPS webhook URL (or use a tunnel).
3. **Watchlist source:** Should the initial watchlist be Birdeye top-trader lists, manual curation, or both?
4. **Signal consumption:** Does the trading engine consume signals via a message bus (Redis pub/sub), file, or direct API call?
5. **Scope of tokens:** Monitor only GoalWorld-relevant tokens (SOL, USDC, GCH) or a broader universe?

---

## 8. Summary

- **Helius Enhanced Transaction Webhooks** are the recommended primary mechanism for real-time smart-money monitoring: parsed, filterable, push-based, low latency.
- **Birdeye** complements Helius with market context, top-trader/smart-money lists, and live price feeds.
- A **FastAPI ingest service + detection engine + enrichment client** on the VPS provides a clean, auditable, risk-controlled pipeline.
- Implementation is staged (Section 6) and gated on the open questions (Section 7).

*Note: Live web research was unavailable during this run (search backend key not set). Provider capabilities and pricing reflect established knowledge as of the report date; verify current tiers and endpoints at helius.dev and docs.birdeye.so before implementation.*