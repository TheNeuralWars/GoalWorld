#!/usr/bin/env python3
"""
DEX Spread Monitor for Solana (Raydium vs Meteora)

This script monitors price spreads and arbitrage opportunities between Raydium and Meteora
for configured token pairs, respecting risk limits defined in risk_limits.json.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/data/apps/GoalWorld/data/trading/dex_spread_monitor.log", mode="a")
    ]
)
logger = logging.getLogger("DEXSpreadMonitor")

# Path constants
RISK_LIMITS_PATH = "/data/apps/GoalWorld/data/trading/risk_limits.json"

# Token Mint Addresses on Solana Mainnet
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "GCH": "GoalWorldGoalChainTokenMintAddressMock11111"  # Mock/placeholder for GoalWorld token
}

# Decimals configuration
TOKEN_DECIMALS = {
    "SOL": 9,
    "USDC": 6,
    "GCH": 9
}

class DEXSpreadMonitor:
    def __init__(self):
        self.risk_limits: Dict[str, Any] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.load_risk_limits()

    def load_risk_limits(self):
        try:
            with open(RISK_LIMITS_PATH, "r") as f:
                self.risk_limits = json.load(f)
            logger.info(f"Loaded risk limits version {self.risk_limits.get('version', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to load risk limits from {RISK_LIMITS_PATH}: {e}")
            # Fallback default limits if file not found
            self.risk_limits = {
                "global_limits": {
                    "min_profit_margin_bps": 15,
                    "max_slippage_pct": 1.0
                },
                "token_limits": {
                    "SOL": {"max_trade_size_usd": 500.0},
                    "USDC": {"max_trade_size_usd": 1000.0}
                }
            }

    async def get_jupiter_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        dex: str
    ) -> Optional[Dict[str, Any]]:
        """
        Queries Jupiter Quote API v6 forcing routing through a specific DEX (Raydium or Meteora).
        """
        url = "https://quote-api.jup.ag/v6/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": int(self.risk_limits.get("global_limits", {}).get("max_slippage_pct", 1.0) * 100),
            "onlyDirectRoutes": "true",
            "dexes": dex
        }
        try:
            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Jupiter API returned status {response.status} for {dex}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching quote from Jupiter for {dex}: {e}")
            return None

    async def monitor_pair(self, base_symbol: str, quote_symbol: str, trade_size_usd: float):
        """
        Monitors a single token pair for spreads between Raydium and Meteora.
        """
        base_mint = TOKEN_MINTS.get(base_symbol)
        quote_mint = TOKEN_MINTS.get(quote_symbol)
        if not base_mint or not quote_mint:
            logger.error(f"Invalid pair symbols: {base_symbol} -> {quote_symbol}")
            return

        base_decimals = TOKEN_DECIMALS.get(base_symbol, 9)
        
        # Mock price estimation to determine input amount
        estimated_price = 150.0 if base_symbol == "SOL" else 1.0
        input_amount_tokens = trade_size_usd / estimated_price
        input_amount_raw = int(input_amount_tokens * (10 ** base_decimals))

        logger.debug(f"Checking spread for {base_symbol}/{quote_symbol} with size {trade_size_usd} USD ({input_amount_tokens} {base_symbol})")

        # Fetch quotes in parallel
        raydium_task = self.get_jupiter_quote(base_mint, quote_mint, input_amount_raw, "Raydium")
        meteora_task = self.get_jupiter_quote(base_mint, quote_mint, input_amount_raw, "Meteora")
        
        raydium_quote, meteora_quote = await asyncio.gather(raydium_task, meteora_task)

        if not raydium_quote or not meteora_quote:
            logger.warning(f"Could not retrieve quotes for both DEXs for {base_symbol}/{quote_symbol}")
            return

        try:
            raydium_out = int(raydium_quote["outAmount"])
            meteora_out = int(meteora_quote["outAmount"])
        except KeyError:
            logger.warning("Invalid quote structure returned from Jupiter API")
            return

        # Calculate spread
        diff = abs(raydium_out - meteora_out)
        min_out = min(raydium_out, meteora_out)
        spread_bps = (diff / min_out) * 10000

        cheaper_dex = "Raydium" if raydium_out > meteora_out else "Meteora"
        more_expensive_dex = "Meteora" if raydium_out > meteora_out else "Raydium"

        min_profit_bps = self.risk_limits.get("global_limits", {}).get("min_profit_margin_bps", 15)
        is_profitable = spread_bps >= min_profit_bps

        log_msg = (
            f"Pair: {base_symbol}/{quote_symbol} | Size: ${trade_size_usd} | "
            f"Raydium Out: {raydium_out} | Meteora Out: {meteora_out} | "
            f"Spread: {spread_bps:.2f} BPS | Profitable: {is_profitable}"
        )

        if is_profitable:
            logger.info(f"🔥 ARBITRAGE OPPORTUNITY DETECTED! {log_msg}")
            logger.info(f"Action: Buy on {more_expensive_dex} and Sell on {cheaper_dex} (or vice versa depending on route)")
        else:
            logger.info(log_msg)

    async def run(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            logger.info("Starting DEX Spread Monitor loop...")
            while True:
                self.load_risk_limits()
                await self.monitor_pair("SOL", "USDC", 500.0)
                cooldown = self.risk_limits.get("execution_rules", {}).get("require_cooldown_seconds", 30)
                await asyncio.sleep(cooldown)

if __name__ == "__main__":
    try:
        monitor = DEXSpreadMonitor()
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
    except Exception as e:
        logger.critical(f"Unhandled exception in monitor: {e}", exc_info=True)
