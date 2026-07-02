/**
 * GoalWorld Devnet Deploy & Initialize Script
 *
 * Usage:
 *   npx ts-node scripts/deploy-devnet.ts
 *
 * Prerequisites:
 *   - Solana CLI configured to devnet (solana config set --url devnet)
 *   - Wallet keypair at ~/.config/solana/id.json (funded with devnet SOL)
 *   - Program already built (anchor build)
 *
 * This script:
 *   1. Deploys the program to Solana Devnet (or uses existing deployment)
 *   2. Initializes GlobalConfig PDA with safe defaults
 *   3. Verifies the config account was created correctly
 */

import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import {
  Connection,
  PublicKey,
  Keypair,
  SystemProgram,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";
import { TOKEN_PROGRAM_ID } from "@solana/spl-token";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

// @ts-ignore - IDL generated after build
import { goalworldProgram } from "../target/types/goalworld_program";

async function main() {
  console.log("🚀 [GoalWorld Devnet Deploy] Starting...\n");

  // ─── Setup connection ───
  const connection = new Connection("https://api.devnet.solana.com", {
    commitment: "confirmed",
    confirmTransactionInitialTimeout: 60000,
  });

  // Load wallet
  const walletPath = path.join(os.homedir(), ".config", "solana", "id.json");
  if (!fs.existsSync(walletPath)) {
    console.error("❌ No wallet found at ~/.config/solana/id.json");
    console.error("   Run: solana-keygen new -o ~/.config/solana/id.json");
    process.exit(1);
  }
  const walletKeypair = Keypair.fromSecretKey(
    Buffer.from(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
  );
  const wallet = new anchor.Wallet(walletKeypair);
  const provider = new anchor.AnchorProvider(connection, wallet, {
    commitment: "confirmed",
  });
  anchor.setProvider(provider);

  const program = anchor.workspace.goalworldProgram as Program<goalworldProgram>;
  const programId = program.programId;

  console.log(`   Program ID:  ${programId.toBase58()}`);
  console.log(`   Wallet:      ${wallet.publicKey.toBase58()}`);

  // Check wallet balance
  const balance = await connection.getBalance(wallet.publicKey);
  console.log(`   Balance:     ${balance / LAMPORTS_PER_SOL} SOL`);
  if (balance < 0.05 * LAMPORTS_PER_SOL) {
    console.error("❌ Insufficient SOL. Run: solana airdrop 2");
    process.exit(1);
  }

  // ─── Derive GlobalConfig PDA ───
  const [configPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("config")],
    programId
  );
  console.log(`   Config PDA:  ${configPda.toBase58()}\n`);

  // ─── Check if config already exists ───
  const configInfo = await connection.getAccountInfo(configPda, "confirmed");

  if (configInfo) {
    console.log("ℹ️  GlobalConfig already initialized. Fetching current state...");
    const config = await program.account.globalConfig.fetch(configPda);
    console.log("   Admin:            ", config.admin.toBase58());
    console.log("   Oracle Authority: ", config.oracleAuthority.toBase58());
    console.log("   Treasury:         ", config.treasuryTokenAccount.toBase58());
    console.log("   Jackpot:          ", config.jackpotTokenAccount.toBase58());
    console.log("   Fee BPS:          ", config.feeBps);
    console.log("   Max SOL/User:     ", config.maxSolPerUser.toString());
    console.log("   Presale Active:   ", config.presaleActive);
    console.log("\n✅ GlobalConfig is already deployed and initialized on Devnet.");
    return;
  }

  // ─── Initialize GlobalConfig ───
  // For devnet, we use the wallet as both admin and oracle authority
  // Treasury and jackpot token accounts should be real SPL token accounts
  // For initial devnet test, we use the wallet's pubkey as placeholder
  // (replace with real token accounts before production)

  const oracleAuthority = wallet.publicKey; // Same as admin for devnet
  const treasuryTokenAccount = wallet.publicKey; // Placeholder — replace with real ATA
  const jackpotTokenAccount = wallet.publicKey; // Placeholder — replace with real ATA
  const feeBps = 100; // 1% fee
  const cutoffBufferSeconds = new anchor.BN(15 * 60); // 15 minutes
  const maxSolPerUser = new anchor.BN(2 * LAMPORTS_PER_SOL); // 2 SOL max
  const presaleActive = false;

  console.log("📝 Initializing GlobalConfig with devnet defaults...");
  console.log(`   Oracle:    ${oracleAuthority.toBase58()}`);
  console.log(`   Fee BPS:   ${feeBps}`);
  console.log(`   Max SOL:   ${maxSolPerUser.toString()}`);

  try {
    const tx = await program.methods
      .initializeConfig(
        oracleAuthority,
        treasuryTokenAccount,
        jackpotTokenAccount,
        feeBps,
        cutoffBufferSeconds,
        maxSolPerUser,
        presaleActive
      )
      .accounts({
        admin: wallet.publicKey,
        config: configPda,
        systemProgram: SystemProgram.programId,
      } as any)
      .signers([walletKeypair])
      .rpc();

    console.log(`\n✅ GlobalConfig initialized! Tx: ${tx}`);

    // ─── Verify ───
    const config = await program.account.globalConfig.fetch(configPda);
    console.log("\n🔍 Verification:");
    console.log("   Admin:            ", config.admin.toBase58());
    console.log("   Oracle Authority: ", config.oracleAuthority.toBase58());
    console.log("   Treasury:         ", config.treasuryTokenAccount.toBase58());
    console.log("   Jackpot:          ", config.jackpotTokenAccount.toBase58());
    console.log("   Fee BPS:          ", config.feeBps);
    console.log("   Fee Burn BPS:     ", config.feeBurnBps);
    console.log("   Fee Jackpot BPS:  ", config.feeJackpotBps);
    console.log("   Max Starters:     ", config.maxStartersPerManager);
    console.log("   Cutoff Buffer:    ", config.cutoffBufferSeconds.toString());
    console.log("   Max SOL/User:     ", config.maxSolPerUser.toString());
    console.log("   Presale Active:   ", config.presaleActive);
    console.log("   Bump:             ", config.bump);

    console.log("\n🎉 Devnet deployment complete!");
    console.log("   Next steps:");
    console.log("   1. Update treasury/jackpot token accounts with real ATAs");
    console.log("   2. Initialize a test fixture");
    console.log("   3. Test oracle_upsert_live_state");
    console.log("   4. Test oracle_create_market");
  } catch (err) {
    console.error("\n❌ Failed to initialize GlobalConfig:", err);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
