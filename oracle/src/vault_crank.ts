import fs from "fs";
import path from "path";
import {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionInstruction,
  VersionedTransaction,
  sendAndConfirmTransaction,
} from "@solana/web3.js";
import { fetchWithTimeout, retrySendAndConfirm, getRpcUrl, getProgramId, getConnection } from "@goalworld/sdk";
import {
  executeVaultCrankBundle,
  PriorityTier,
  BLOCK_ENGINE_URLS,
} from "./jitoBundle.js";

/**
 * Simulates a transaction and throws a detailed error if simulation fails.
 * Used as a preflight check before submitting transactions on mainnet.
 */
async function simulateAndValidate(
  connection: Connection,
  tx: VersionedTransaction | Transaction,
  label: string
): Promise<void> {
  // Handle VersionedTransaction vs Transaction overloads with correct config shape
  let simResult: any;
  if (tx instanceof VersionedTransaction) {
    simResult = await connection.simulateTransaction(tx, {
      commitment: "confirmed",
      replaceRecentBlockhash: true,
      sigVerify: false,
    } as any);
  } else {
    simResult = await connection.simulateTransaction(tx, [], false);
  }

  if (simResult.value.err) {
    const logs = simResult.value.logs?.join("\n") || "No logs";
    throw new Error(`Simulation failed for ${label}: ${JSON.stringify(simResult.value.err)}\nLogs:\n${logs}`);
  }

  console.log(`[vault_crank] Simulation OK for ${label}: ${simResult.value.unitsConsumed} CU consumed`);
}

interface VaultCrankReport {
  timestamp_iso: string;
  mode: "dry-run" | "execute";
  principal_sol: number;
  current_sol: number;
  excess_sol: number;
  buyback_share: number;
  jackpot_share: number;
  reinvest_share: number;
  buyback_sol: number;
  jackpot_sol: number;
  reinvest_sol: number;
  gch_price_usd: number;
  estimated_gch_burned: number;
  tx_hashes: string[];
  notes: string[];
}

const BUYBACK_SHARE = Number(process.env.BUYBACK_SHARE_OF_YIELD || "0.60");
const JACKPOT_SHARE = Number(process.env.JACKPOT_SHARE_OF_YIELD || "0.10");
const REINVEST_SHARE = Number(process.env.REINVEST_SHARE_OF_YIELD || "0.30");

// Jito Bundle Configuration
const JITO_BUNDLE_ENABLED = process.env.JITO_BUNDLE_ENABLED === "1";
const JITO_BLOCK_ENGINE_URL = process.env.JITO_BLOCK_ENGINE_URL || BLOCK_ENGINE_URLS.devnet;
const JITO_PRIORITY_TIER = (process.env.JITO_PRIORITY_TIER as PriorityTier) || PriorityTier.STANDARD;
const JITO_MAX_POLL_ATTEMPTS = Number(process.env.JITO_MAX_POLL_ATTEMPTS || "30");

function clampShare(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

function fakeTx(prefix: string): string {
  const rand = Math.random().toString(36).slice(2, 18);
  return `${prefix}_${rand}`;
}

async function main() {
  const mode = process.env.VAULT_CRANK_EXECUTE === "1" ? "execute" : "dry-run";
  if (process.env.VAULT_CRANK_EXECUTE === "1") {
    throw new Error("CRITICAL: Real mainnet execution is disabled until vault crank is audited and fake transactions are removed.");
  }
  const principalSol = Number(process.env.VAULT_PRINCIPAL_SOL || "5000");
  const currentSol = Number(process.env.VAULT_CURRENT_SOL || "5032.7");
  const minExcessSol = Number(process.env.VAULT_MIN_EXCESS_SOL || "0.1");
  const gchPriceUsd = Number(process.env.GCH_PRICE_USD || "0.01");
  const solPriceUsd = Number(process.env.SOL_PRICE_USD || "180");

  const buybackShare = clampShare(BUYBACK_SHARE);
  const jackpotShare = clampShare(JACKPOT_SHARE);
  const reinvestShare = clampShare(REINVEST_SHARE);
  const shareSum = buybackShare + jackpotShare + reinvestShare;
  if (Math.abs(shareSum - 1) > 0.0001) {
    throw new Error(
      `Invalid share split: buyback+jackpot+reinvest must equal 1 (got ${shareSum})`,
    );
  }

  const excessSol = Math.max(0, currentSol - principalSol);
  let buybackSol = 0;
  let jackpotSol = 0;
  let reinvestSol = 0;
  let estimatedGchBurned = 0;
  const notes: string[] = [];
  const txHashes: string[] = [];

  if (excessSol < minExcessSol) {
    notes.push(
      `Excess SOL (${excessSol.toFixed(6)}) is below threshold (${minExcessSol}). No-op crank.`,
    );
  } else {
    buybackSol = excessSol * buybackShare;
    jackpotSol = excessSol * jackpotShare;
    reinvestSol = excessSol * reinvestShare;

    const buybackUsd = buybackSol * solPriceUsd;
    estimatedGchBurned = gchPriceUsd > 0 ? buybackUsd / gchPriceUsd : 0;

    if (mode === "execute") {
      notes.push("Initiating real execution path...");
      // Real mainnet execution is blocked by safety guard at start of main()
      notes.push("Execute mode disabled. Dry-run values computed above.");
    } else {
      txHashes.push(fakeTx("dryrun_harvest"));
      txHashes.push(fakeTx("dryrun_swap"));
      txHashes.push(fakeTx("dryrun_burn"));
      notes.push("Dry-run mode only: no on-chain state modified.");
    }
  }

  const report: VaultCrankReport = {
    timestamp_iso: new Date().toISOString(),
    mode,
    principal_sol: principalSol,
    current_sol: currentSol,
    excess_sol: excessSol,
    buyback_share: buybackShare,
    jackpot_share: jackpotShare,
    reinvest_share: reinvestShare,
    buyback_sol: buybackSol,
    jackpot_sol: jackpotSol,
    reinvest_sol: reinvestSol,
    gch_price_usd: gchPriceUsd,
    estimated_gch_burned: estimatedGchBurned,
    tx_hashes: txHashes,
    notes,
  };

  const outputPath = path.resolve(
    process.cwd(),
    "../docs/data/burn_tracker.json",
  );
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));

  console.log(`[vault_crank] report written: ${outputPath}`);
  console.log(JSON.stringify(report, null, 2));
}

main().catch((err) => {
  console.error("[vault_crank] error:", err.message);
  process.exit(1);
});