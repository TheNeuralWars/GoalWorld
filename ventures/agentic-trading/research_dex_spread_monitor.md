# GW-TRADING-004 — DEX Spread Monitor: Research & Design Report

**Status:** Discovery / Research / Design
**Date:** 2026-08-10
**Author:** trader (Agentic Trading Engine)
**Scope:** Design a real-time spread monitor for cross-DEX arbitrage between Raydium and Meteora on Solana.

---

## 1. Objective

Design and prototype the **DEX Spread Monitor** component described in `ventures/agentic-trading/README.md`:

> *"Implementar un script de monitoreo de spreads en DEXs de Solana en `scripts/trading/dex_spread_monitor.py`."*

This monitor will track price discrepancies between **Raydium** (Solana's primary AMM/CLMM) and **Meteora** (Dynamic Pools and DLMM) for targeted token pairs (e.g., SOL/USDC, GCH/USDC, GCH/SOL), validating opportunities against the rules defined in `data/trading/risk_limits.json` before signaling the execution gateway.

---

## 2. DEX Architectures & Pricing Mechanics

To accurately monitor spreads, we must understand the distinct liquidity models of both DEXs:

### 2.1 Raydium
*   **AMM v4 (Standard):** Constant Product Formula ($x \cdot y = k$). High price impact for large trades; simple to calculate.
*   **CLMM (Concentrated Liquidity):** Similar to Uniswap v3. Liquidity is bounded within price ticks. Calculating exact swap outcomes requires tracking active tick arrays and tick bitmaps.
*   **Integration Path:** Raydium SDK (JS/Python) or direct decoding of the AMM/CLMM program state via RPC `getAccountInfo` / WebSocket subscriptions.

### 2.2 Meteora
*   **Dynamic AMM:** Constant product pools with dynamic fees that scale up during high volatility to protect LPs and scale down during low volatility to attract volume.
*   **DLMM (Discrete Liquidity Market Maker):** Liquidity is distributed in discrete price bins (Liquidity Book model). Zero slippage *within* a bin. Dynamic fee structure composed of a base fee and a variable surge fee.
*   **Integration Path:** Meteora DLMM SDK or decoding bin states from the DLMM program accounts.

---

## 3. Spread Calculation & Arbitrage Math

A naive price comparison (e.g., comparing mid-market prices) is insufficient for arbitrage because of **price impact**, **pool fees**, and **network transaction fees**.

### 3.1 Net Profit Formula
For a cross-DEX arbitrage trade starting with asset $A$, swapping to asset $B$ on DEX 1, and swapping back to asset $A$ on DEX 2:

$$\text{Net Profit} = \text{AmountOut}_{DEX2}(B \rightarrow A) - \text{AmountIn}_{DEX1}(A \rightarrow B) - \text{Fees}_{Tx}$$

Where:
*   $\text{AmountIn}_{DEX1}$ is the trade size (constrained by `max_trade_size_usd` in `risk_limits.json`).
*   $\text{AmountOut}_{DEX1}$ accounts for DEX 1's swap fees (e.g., 0.25% for Raydium AMM) and price impact.
*   $\text{AmountOut}_{DEX2}$ accounts for DEX 2's swap fees (including Meteora's dynamic/surge fees) and price impact.
*   $\text{Fees}_{Tx}$ includes Solana signature fees and Jito tip/prioritization fees required for atomic execution.

### 3.2 Threshold Validation
An opportunity is only valid if:
1.  $\text{Net Profit} > 0$
2.  $\text{Spread BPS} \ge \text{min\_profit\_margin\_bps}$ (15 bps as per `risk_limits.json`).
    $$\text{Spread BPS} = \left( \frac{\text{Net Profit}}{\\text{AmountIn}} \right) \times 10000$$
3.  Trade size fits within `max_trade_size_usd` and does not exceed `max_exposure_usd` for that token.

---

## 4. Data Fetching Strategies

| Strategy | Latency | Complexity | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **1. Jupiter Quote API** | ~100-300ms | Low | Handles all routing, fee calculations, and price impact automatically. | Latency might be too high for competitive arbitrage. |
| **2. RPC Polling / WS** | ~50-150ms | Medium | Real-time updates of pool accounts. | Requires local implementation of swap math for CLMM/DLMM. |
| **3. Geyser gRPC Stream** | <50ms | High | Direct stream of state changes from validator. | High infrastructure cost; requires specialized RPC provider. |

**Recommendation:** Implement a hybrid architecture. Use **Jupiter Quote API** for the prototype/validation layer, and **RPC WebSocket Account Subscriptions** for the low-latency monitoring loop of specific high-conviction pools.

---

## 5. System Architecture

```
+-----------------------------------------------------------------+
|                       DEX Spread Monitor                        |
+-----------------------------------------------------------------+
                                | (Polls/Streams)
                                v
+-----------------------------------------------------------------+
|        Data Ingest (Jupiter Quote API / RPC WebSockets)         |
+-----------------------------------------------------------------+
                                |
                                v
+-----------------------------------------------------------------+
|        Spread Engine (Simulates swaps & calculates BPS)         |
+-----------------------------------------------------------------+
                                |
                                v
+-----------------------------------------------------------------+
|  Risk Validator (Validates against data/trading/risk_limits.json)|
+-----------------------------------------------------------------+
                                |
                                v (If spread > 15 bps & limits OK)
+-----------------------------------------------------------------+
|     Execution Trigger (Jito Bundle / Transaction Builder)       |
+-----------------------------------------------------------------+
```

---

## 6. Prototype Implementation

We implement the prototype in `scripts/trading/dex_spread_monitor.py` using an asynchronous Python loop. It queries the Jupiter Quote API to simulate swaps of specific sizes on Raydium and Meteora, computes the net spread, and validates it against `risk_limits.json`.

### Key Features of the Prototype:
*   **Async execution** using `asyncio` and `aiohttp`.
*   **Risk limits integration** by loading and parsing `/data/apps/GoalWorld/data/trading/risk_limits.json`.
*   **Multi-size simulation** (e.g., $100, $500) to account for liquidity depth and price impact.
*   **Detailed logging** of spreads, fees, and validation status.

---

## 7. Next Steps & Roadmap

1.  **Deploy Prototype:** Run `scripts/trading/dex_spread_monitor.py` in dry-run mode on the VPS to gather baseline spread data.
2.  **Integrate Jito SDK:** Implement transaction building using Jito bundles to prevent frontrunning and ensure atomic execution (all-or-nothing).
3.  **Direct RPC Decoding:** Transition from Jupiter API to direct RPC account subscriptions for Raydium CLMM and Meteora DLMM to reduce latency to <100ms.
4.  **Alerting:** Connect the monitor to a Slack/Discord webhook or Hermes notification system to alert on high-spread events.
