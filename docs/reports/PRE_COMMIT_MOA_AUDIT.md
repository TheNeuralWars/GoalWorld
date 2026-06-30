# Pre-Commit Security Audit & Expansion Blueprint

**Program**: GoalWorld Solana Program (`goalworld_program`)
**Repository**: `/data/apps/GoalWorld/contracts`
**Audit Date**: 2026-06-29
**Anchor Version**: 1.0.2
**Rust Edition**: 2021
**Auditor**: GoalWorld Manager (Hermes Agent, MoA pipeline)

---

## Executive Summary

The GoalWorld Solana program compiles cleanly (`cargo build` → 0 errors, 0 warnings), passes tests (1/1), and has zero clippy errors. The modular refactor successfully separated state structs into `src/state/` and instruction handlers into `src/instructions/betting/{wager,fixtures,live_markets}/`, with `#[derive(Accounts)]` structs at the crate root for Anchor 1.0 macro compatibility.

However, the security audit identifies **5 Critical**, **4 High**, **5 Medium**, and **3 Low** severity issues that must be addressed before mainnet deployment. The program also contains two partially-developed feature areas (staking and NFT rentals) with state structs defined but no instruction handlers.

**Verdict**: NOT ready for mainnet. Fix Critical and High issues before devnet deployment.

---

## 1. Build & Architecture Validation

### 1.1 Compilation Status

| Check | Result |
|-------|--------|
| `cargo build` | ✅ 0 errors, 0 warnings |
| `cargo test` | ✅ 1/1 pass |
| `cargo clippy` | ✅ 0 errors (cosmetic warnings only) |
| `cargo test --no-run` | ✅ Compiles test binary |

### 1.2 Modular Structure

```
src/
├── lib.rs                    — #[program] + #[derive(Accounts)] structs (crate root)
├── constants.rs              — PDA seeds + economy constants
├── errors.rs                 — GoalWorldError enum (22 variants)
├── state/
│   ├── mod.rs                — Re-exports all state types
│   ├── config.rs             — GlobalConfig
│   ├── wager.rs              — Wager, WagerState
│   ├── fixture.rs            — Fixture, MatchStatus, MatchResult
│   ├── user_bet.rs           — UserBet
│   ├── market.rs             — Market, MarketType, MarketStatus
│   ├── position.rs           — MarketPosition
│   ├── live_state.rs         — LiveMatchState
│   ├── stake_pool.rs         — UserStake (NO handlers)
│   ├── player.rs             — ParodyPlayer, RentalListing (NO handlers)
│   ├── player_match.rs       — PlayerMatchRecord (NO handlers)
│   ├── builder_fund.rs       — BuilderFund, ContributorScore, etc. (NO handlers)
│   ├── reward_pool.rs        — ManagerState, StadiumState (NO handlers)
│   ├── contributor.rs        — Re-exports ContributorScore
│   └── vault.rs              — Vault seed constants
├── instructions/
│   ├── mod.rs                — pub mod betting; pub mod config;
│   ├── config.rs             — initialize_config, update_config
│   └── betting/
│       ├── mod.rs            — pub mod wager; pub mod fixtures; pub mod live_markets;
│       ├── claims.rs         — Empty placeholder (documented)
│       ├── wager/            — create_wager, accept_wager, resolve_wager
│       ├── fixtures/         — initialize_fixture, place_bet, update_fixture_status,
│       │                       claim_bet_payout, refund_bet, sweep_fixture_dust
│       └── live_markets/     — oracle_upsert_live_state, oracle_create_market,
│                               oracle_update_market_status, place_market_bet,
│                               claim_market_payout
```

### 1.3 Duplicate Definition Check

- ✅ No duplicate struct definitions across modules
- ✅ `claims.rs` is intentionally empty with documentation pointing to modularized locations
- ✅ `contributor.rs` re-exports `ContributorScore` from `builder_fund.rs` (no duplicate definition)
- ✅ All `mod.rs` files declare and re-export correctly

### 1.4 Anchor 1.0 Best Practices Compliance

| Practice | Status | Notes |
|----------|--------|-------|
| `declare_id!` at crate root | ✅ | `GWorLD11111111111111111111111111111111111111` |
| `#[derive(Accounts)]` at crate root | ✅ | Required for Anchor 1.0 `#[program]` macro |
| `InitSpace` derive on all accounts | ✅ | All `#[account]` structs derive `InitSpace` |
| `#[max_len]` on String/Vec fields | ✅ | `Fixture.match_id` (64), `team_a`/`team_b` (32), `ParodyPlayer.name` (32), `player_id` (32) |
| `transfer_checked` for Token-2022 | ✅ | All SPL token transfers use `TransferChecked` with mint + decimals |
| `InterfaceAccount` for Token-2022 | ✅ | Used for `TokenAccount` and `Mint` in market betting |
| `init_if_needed` feature | ✅ | Enabled in Cargo.toml; used for `live_state` and `market_vault` |
| Overflow checks in release | ✅ | `overflow-checks = true` in `Cargo.toml` `[profile.release]` |

---

## 2. Security Audit Findings

### CRITICAL

#### C1: `resolve_wager` — No Authority Check on Resolver

**File**: `instructions/betting/wager/resolve_wager.rs`
**Severity**: CRITICAL
**Status**: Unfixed

The `ResolveWager` accounts struct marks `resolver` as a `Signer` but does **not** verify that the resolver is authorized by either wager party. Any account can call `resolve_wager` and drain the vault.

```rust
// CURRENT (VULNERABLE)
#[derive(Accounts)]
pub struct ResolveWager<'info> {
    #[account(mut)]
    pub resolver: Signer<'info>,        // Anyone can sign!
    #[account(mut)]
    pub wager: Account<'info, Wager>,   // No constraint linking resolver to wager
    ...
}
```

**Impact**: Complete loss of wager funds. Any attacker can resolve any accepted wager and send the vault to their own `winner` account.

**Fix**: Add a resolver authority field to `Wager` state and enforce it:
```rust
// In state/wager.rs — add field:
pub resolver: Pubkey,  // Authority allowed to resolve

// In create_wager handler — set it:
wager.resolver = ctx.accounts.initializer.key();  // Or a designated oracle

// In ResolveWager accounts struct:
#[account(
    mut,
    constraint = wager.resolver == resolver.key() @ GoalWorldError::UnauthorizedResolver
)]
pub wager: Account<'info, Wager>,
```

---

#### C2: `update_fixture_status` — No Admin Authorization

**File**: `instructions/betting/fixtures/update_fixture_status.rs`
**Severity**: CRITICAL
**Status**: Unfixed

The `UpdateFixtureStatus` struct requires `admin: Signer` but does **not** verify that the signer is the admin stored in `GlobalConfig`. Any account can update fixture status and result, allowing them to set the result to match their bet.

```rust
// CURRENT (VULNERABLE)
#[derive(Accounts)]
pub struct UpdateFixtureStatus<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,  // Just a Signer, not verified against config!
    #[account(mut)]
    pub fixture: Account<'info, Fixture>,
}
```

**Impact**: Match fixing. An attacker can set `fixture.result` to match their own bet prediction, then claim payout.

**Fix**: Add `GlobalConfig` to the accounts struct and verify:
```rust
#[derive(Accounts)]
pub struct UpdateFixtureStatus<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.admin == admin.key() @ GoalWorldError::UnauthorizedAdmin
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub fixture: Account<'info, Fixture>,
}
```

---

#### C3: `sweep_fixture_dust` — No Admin Authorization

**File**: `instructions/betting/fixtures/sweep_fixture_dust.rs`
**Severity**: CRITICAL
**Status**: Unfixed

Same issue as C2. The `admin: Signer` is not verified against `GlobalConfig.admin`. Any account can sweep remaining vault lamports.

```rust
// CURRENT (VULNERABLE)
#[derive(Accounts)]
pub struct SweepFixtureDust<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,  // Not verified!
    pub fixture: Account<'info, Fixture>,
    ...
}
```

**Impact**: Vault drain. An attacker can sweep all remaining lamports from any fixture vault.

**Fix**: Same pattern as C2 — add `GlobalConfig` with `config.admin == admin.key()` constraint.

---

#### C4: `resolve_wager` — Winner Not Validated Against Wager Parties

**File**: `instructions/betting/wager/resolve_wager.rs`
**Severity**: CRITICAL
**Status**: Unfixed

The `winner: UncheckedAccount` is not constrained to be either `wager.player_a` or `wager.player_b`. The resolver can send funds to any arbitrary address.

```rust
// CURRENT (VULNERABLE)
/// CHECK: winner address
pub winner: UncheckedAccount<'info>,  // No constraint!
```

**Impact**: Fund diversion. Even with a proper resolver authority check (C1), the winner could be set to an attacker-controlled account.

**Fix**:
```rust
/// CHECK: winner must be one of the wager parties
#[account(
    constraint = winner.key() == wager.player_a || 
                 winner.key() == wager.player_b.unwrap() 
                 @ GoalWorldError::InvalidWinner
)]
pub winner: UncheckedAccount<'info>,
```

---

#### C5: `place_market_bet` — Hardcoded Bet Amount, No User Input

**File**: `instructions/betting/live_markets/place_market_bet.rs`
**Severity**: CRITICAL
**Status**: Unfixed

The bet amount is hardcoded to `1_000_000u64` and the prediction is hardcoded to `MatchResult::HomeWin`. Users cannot choose their bet amount or prediction.

```rust
// CURRENT (VULNERABLE)
let bet_amount = 1_000_000u64;  // Hardcoded!
...
market_position.prediction = MatchResult::HomeWin;  // Hardcoded!
```

**Impact**: Non-functional instruction. Users are forced to bet 1M units on HomeWin regardless of intent. This also means pool_b and pool_draw are never updated, breaking payout calculations.

**Fix**: Add `amount: u64` and `prediction: MatchResult` as instruction arguments:
```rust
pub fn place_market_bet(
    ctx: Context<PlaceMarketBet>,
    ticket_id: u64,
    amount: u64,
    prediction: MatchResult,
) -> Result<()> {
    ...
    require!(amount > 0, GoalWorldError::InvalidAmount);
    let bet_amount = amount;
    ...
    market_position.prediction = prediction;
    match prediction {
        MatchResult::HomeWin => market.pool_a += bet_amount,
        MatchResult::AwayWin => market.pool_b += bet_amount,
        MatchResult::Draw => market.pool_draw += bet_amount,
        _ => return Err(GoalWorldError::InvalidBetOutcome.into()),
    }
}
```

---

### HIGH

#### H1: `resolve_wager` — Unchecked Arithmetic on Payout

**File**: `instructions/betting/wager/resolve_wager.rs`
**Severity**: HIGH
**Status**: Unfixed

```rust
anchor_lang::system_program::transfer(cpi_context, wager.amount * 2)?;
```

`wager.amount * 2` can overflow `u64`. While `overflow-checks = true` is set in release profile, this will cause a runtime panic (program abort), not a graceful error. Use checked math.

**Fix**:
```rust
let payout = wager.amount.checked_mul(2).ok_or(GoalWorldError::MathOverflow)?;
anchor_lang::system_program::transfer(cpi_context, payout)?;
```

---

#### H2: `claim_bet_payout` — Unchecked Arithmetic on Payout

**File**: `instructions/betting/fixtures/claim_bet_payout.rs`
**Severity**: HIGH
**Status**: Unfixed

```rust
let payout = user_bet.amount * 2;
```

Same overflow risk as H1.

**Fix**: `let payout = user_bet.amount.checked_mul(2).ok_or(GoalWorldError::MathOverflow)?;`

---

#### H3: `claim_market_payout` — Payout Does Not Account for Pool Proportions

**File**: `instructions/betting/live_markets/claim_market_payout.rs`
**Severity**: HIGH
**Status**: Unfixed

The payout simply returns `market_position.amount` if the prediction matches the winner. This is a 1:1 return — the user gets back exactly what they bet. A proper parimutuel system should distribute the losing pool proportionally among winners.

```rust
// CURRENT — returns bet amount only, no profit
let payout = match market.winner {
    Some(MatchResult::HomeWin) => {
        if market_position.prediction == MatchResult::HomeWin {
            market_position.amount  // Just returns principal, no winnings
        } else { 0 }
    }
    ...
};
```

**Impact**: Users receive no winnings for correct predictions. The losing pool remains in the vault and gets swept to treasury/jackpot.

**Fix**: Implement proportional payout:
```rust
let total_pool = market.pool_a + market.pool_b + market.pool_draw;
let winning_pool = match market.winner.unwrap() {
    MatchResult::HomeWin => market.pool_a,
    MatchResult::AwayWin => market.pool_b,
    MatchResult::Draw => market.pool_draw,
    _ => 0,
};
let losing_pool = total_pool.saturating_sub(winning_pool);
// payout = principal + proportional share of losing pool
let payout = market_position.amount
    .checked_add(
        losing_pool.checked_mul(market_position.amount).unwrap_or(0)
            .checked_div(winning_pool).unwrap_or(0)
    ).unwrap_or(0);
```

---

#### H4: `oracle_update_market_status` — Hardcoded Status, No State Machine

**File**: `instructions/betting/live_markets/oracle_update_market_status.rs`
**Severity**: HIGH
**Status**: Unfixed

The handler unconditionally sets `market.status = MarketStatus::Closed` and `resolved_ts`. It does not:
- Accept the new status or winner as instruction arguments
- Validate that the current status is `Open` (prevents closing already-closed markets)
- Set `market.winner`

```rust
// CURRENT — hardcoded, no args
pub fn handler(ctx: Context<OracleUpdateMarketStatus>) -> Result<()> {
    let market = &mut ctx.accounts.market;
    market.status = MarketStatus::Closed;  // Always closes
    market.resolved_ts = Some(Clock::get()?.unix_timestamp);
    Ok(())
}
```

**Impact**: Markets cannot be properly resolved — `market.winner` is never set, so `claim_market_payout` always returns 0 payout. Markets can be "closed" multiple times.

**Fix**: Add instruction arguments and state validation:
```rust
pub fn handler(
    ctx: Context<OracleUpdateMarketStatus>,
    new_status: MarketStatus,
    winner: Option<MatchResult>,
) -> Result<()> {
    let market = &mut ctx.accounts.market;
    require!(market.status == MarketStatus::Open, GoalWorldError::MarketNotOpen);
    market.status = new_status;
    if new_status == MarketStatus::Closed || new_status == MarketStatus::Resolved {
        market.winner = winner;
        market.resolved_ts = Some(Clock::get()?.unix_timestamp);
    }
    Ok(())
}
```

---

### MEDIUM

#### M1: `place_bet` — No Bet Amount Validation

**File**: `instructions/betting/fixtures/place_bet.rs`
**Severity**: MEDIUM
**Status**: Unfixed

No `require!(amount > 0)` check. A user can place a zero-amount bet, creating a `UserBet` account that can later be used to claim a payout (getting `0 * 2 = 0` — harmless but wastes rent).

**Fix**: Add `require!(amount > 0, GoalWorldError::InvalidAmount);` at the top of the handler.

---

#### M2: `place_bet` — No Max Bet Check Against `GlobalConfig.max_sol_per_user`

**File**: `instructions/betting/fixtures/place_bet.rs`
**Severity**: MEDIUM
**Status**: Unfixed

`GlobalConfig.max_sol_per_user` is stored but never enforced. Users can bet unlimited amounts.

**Fix**: Add config to `PlaceBet` accounts struct and check:
```rust
require!(amount <= config.max_sol_per_user, GoalWorldError::WagerExceededMaxAmount);
```

---

#### M3: `place_bet` — No Cutoff Time Check

**File**: `instructions/betting/fixtures/place_bet.rs`
**Severity**: MEDIUM
**Status**: Unfixed

`GlobalConfig.cutoff_buffer_seconds` is stored but never used. Bets can be placed after the match starts.

**Fix**: Check `Clock::get()?.unix_timestamp + cutoff_buffer_seconds < fixture.start_timestamp`.

---

#### M4: `oracle_upsert_live_state` — Hardcoded Zero Values

**File**: `instructions/betting/live_markets/oracle_upsert_live_state.rs`
**Severity**: MEDIUM
**Status**: Unfixed

The handler hardcodes `minute = 0`, `score_a = 0`, `score_b = 0`, etc. It should accept these as instruction arguments from the oracle.

**Fix**: Add instruction arguments: `minute: u16, score_a: u8, score_b: u8, is_ht: bool, is_ft: bool`.

---

#### M5: `oracle_create_market` — Hardcoded Default Values

**File**: `instructions/betting/live_markets/oracle_create_market.rs`
**Severity**: MEDIUM
**Status**: Unfixed

`market.fixture` is set to `Pubkey::default()` and `market.token_mint` is set to `Pubkey::default()`. The market is not linked to a fixture or token, making it non-functional.

**Fix**: Accept `fixture: Pubkey`, `token_mint: Pubkey`, `market_type: MarketType` as instruction arguments.

---

### LOW

#### L1: `claim_market_payout` — Unused Variable `_market_key`

**File**: `instructions/betting/live_markets/claim_market_payout.rs`
**Severity**: LOW
**Status**: Unfixed

`let _market_key = market.key();` is computed but never used. Remove it.

---

#### L2: `InitializeFixture` — No Admin Authorization

**File**: `lib.rs` (Accounts struct)
**Severity**: LOW
**Status**: Unfixed

`InitializeFixture` requires `admin: Signer` but does not verify against `GlobalConfig.admin`. Since this is an `init` (PDA collision prevents duplicate creation), the impact is limited to unauthorized fixture creation, not fund theft.

**Fix**: Add `GlobalConfig` with admin constraint for consistency.

---

#### L3: `CreateWager` — Unused `#[instruction(amount: u64)]`

**File**: `lib.rs` (Accounts struct)
**Severity**: LOW
**Status**: Unfixed

The `#[instruction(amount: u64)]` attribute is present but `amount` is not used in any seed derivation. Remove it to avoid confusion.

---

## 3. Expansion Blueprint

### 3.1 Staking & Liquid Yield (Jito/Liquid Staking Integration)

#### Current State

`src/state/stake_pool.rs` defines `UserStake`:
```rust
pub struct UserStake {
    pub owner: Pubkey,
    pub amount: u64,
    pub start_timestamp: i64,
    pub unclaimed_rewards: u64,
}
```

Constants `SEED_STAKE` and `SEED_STAKE_VAULT` exist. No instruction handlers, no `StakePool` global account, no yield accrual logic, no Jito integration.

#### Phase 1: Basic SOL Staking Pool

**New files**:
- `src/instructions/staking/mod.rs`
- `src/instructions/staking/initialize_stake_pool.rs`
- `src/instructions/staking/stake.rs`
- `src/instructions/staking/unstake.rs`
- `src/instructions/staking/claim_rewards.rs`

**State modifications** (`src/state/stake_pool.rs`):

```rust
#[account]
#[derive(InitSpace)]
pub struct StakePool {
    pub authority: Pubkey,           // Admin who can adjust params
    pub token_mint: Pubkey,          // SPL token mint (or native SOL wrapper)
    pub total_staked: u64,           // Sum of all active stakes
    pub reward_rate_bps: u16,        // Annual reward rate in basis points
    pub last_reward_ts: i64,         // Last global reward update
    pub reward_per_token_stored: u128, // Accumulated reward per token (ERC-4626 style)
    pub fee_bps: u16,                // Platform fee on rewards
    pub fee_vault: Pubkey,           // Where fees go
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct UserStake {
    pub owner: Pubkey,
    pub pool: Pubkey,
    pub amount: u64,
    pub start_timestamp: i64,
    pub reward_debt: u128,           // Snapshot of reward_per_token at deposit
    pub unclaimed_rewards: u64,
    pub bump: u8,
}
```

**New constants**:
```rust
pub const SEED_STAKE_POOL: &[u8] = b"stake_pool";
pub const SEED_STAKE_POSITION: &[u8] = b"stake_position";
```

**Instruction: `initialize_stake_pool`**
- PDA: `[b"stake_pool"]` (singleton)
- Admin creates pool with token mint, reward rate, fee config
- Accounts: `admin: Signer`, `config: GlobalConfig` (admin check), `stake_pool: init`, `system_program`

**Instruction: `stake`**
- PDA: `[b"stake_position", user.key(), stake_pool.key()]`
- User transfers SPL tokens to `stake_vault` PDA (`[b"stake_vault", stake_pool.key()]`)
- Update `UserStake.amount`, `reward_debt = pool.reward_per_token_stored`
- Update `StakePool.total_staked`
- CPI: `token_interface::transfer_checked` from user ATA to vault ATA

**Instruction: `unstake`**
- Calculate pending rewards: `rewards = user_stake.amount * (pool.reward_per_token_stored - user_stake.reward_debt) / 1e12`
- Transfer staked tokens + rewards back to user
- Deduct platform fee → fee_vault
- Update `total_staked`, close `UserStake` account
- CPI: `token_interface::transfer_checked` with PDA signer seeds

**Instruction: `claim_rewards`**
- Same reward calculation as unstake, but principal stays
- Update `reward_debt` and `unclaimed_rewards`

**Reward accrual mechanism**:
- Off-chain keeper calls `distribute_rewards(amount)` periodically
- Or: platform fee share from wager/market pools auto-deposited via CPI
- `reward_per_token_stored += (rewards_distributed * 1e12) / total_staked`

#### Phase 2: Jito Liquid Staking Integration

**Concept**: Instead of holding SOL idle, the stake pool deposits SOL into JitoSOL vault to earn MEV + staking yield.

**New state fields**:
```rust
// Add to StakePool:
pub jito_vault: Option<Pubkey>,     // Jito vault account
pub jito_shares: u64,               // Shares held by pool in Jito vault
pub jito_exchange_rate: u128,       // Cached JitoSOL/SOL rate
```

**New instruction: `deposit_to_jito`**
- Admin/keeper deposits accumulated SOL from `stake_vault` into Jito vault
- CPI to Jito's `Deposit` instruction (requires Jito program IDL)
- Records `jito_shares` and updates `jito_exchange_rate`

**New instruction: `withdraw_from_jito`**
- When users unstake and vault has insufficient SOL, withdraw from Jito
- CPI to Jito's `Withdraw` instruction
- Burns JitoSOL shares, receives SOL

**Yield distribution**:
- Jito yield accrues to the pool automatically (JitoSOL appreciates vs SOL)
- On unstake, user gets `principal * (current_jito_rate / deposit_jito_rate)` — profit
- Platform takes `fee_bps` of the yield portion

**Integration points**:
- Jito program ID: `J1to1oZs5...` (mainnet) — add to constants
- Requires `jito-vault` SDK or manual CPI construction
- Alternative: integrate with Marinade (mSOL) for simpler SDK

**Files to create/modify**:
| File | Action |
|------|--------|
| `src/instructions/staking/mod.rs` | Create |
| `src/instructions/staking/initialize_stake_pool.rs` | Create |
| `src/instructions/staking/stake.rs` | Create |
| `src/instructions/staking/unstake.rs` | Create |
| `src/instructions/staking/claim_rewards.rs` | Create |
| `src/instructions/staking/deposit_to_jito.rs` | Create (Phase 2) |
| `src/instructions/staking/withdraw_from_jito.rs` | Create (Phase 2) |
| `src/instructions/mod.rs` | Add `pub mod staking;` |
| `src/state/stake_pool.rs` | Add `StakePool` struct, update `UserStake` |
| `src/constants.rs` | Add `SEED_STAKE_POOL`, `SEED_STAKE_POSITION` |
| `src/errors.rs` | Add staking error variants |
| `src/lib.rs` | Add `#[derive(Accounts)]` structs + `#[program]` entries |

---

### 3.2 NFT Rentals/Leasing (ParodyPlayer & RentalListing)

#### Current State

`src/state/player.rs` defines:

```rust
pub struct ParodyPlayer {
    pub owner: Pubkey,
    pub last_claim_timestamp: i64,
    pub name: String,              // #[max_len(32)]
    pub player_id: String,         // #[max_len(32)]
    pub real_world_goals: u8,
    pub real_world_assists: u8,
    pub matches_played: u8,
    pub speed: u8,
    pub shot_power: u8,
    pub base_yield_rate: u64,
    pub current_stamina: u8,
    pub is_eliminated: bool,
    pub equipped_stadium_id: Option<Pubkey>,
    pub nation_id: u8,
    pub visual_background: u8,
    pub equipped_jersey: Option<Pubkey>,
    pub equipped_boots: Option<Pubkey>,
    pub win_streak: u8,
    pub last_match_result: u8,
    pub has_shield_jersey: bool,
    pub bump: u8,
}

pub struct RentalListing {
    pub owner: Pubkey,
    pub price_per_match: u64,
    pub current_borrower: Option<Pubkey>,
    pub is_active: bool,
}
```

Constants `SEED_PLAYER` and `SEED_RENTAL` exist. No instruction handlers. `RentalListing` lacks duration, escrow, and fee fields.

#### Phase 1: Player Minting & Basic Rentals

**New files**:
- `src/instructions/rental/mod.rs`
- `src/instructions/rental/mint_player.rs`
- `src/instructions/rental/create_listing.rs`
- `src/instructions/rental/rent_player.rs`
- `src/instructions/rental/end_rental.rs`
- `src/instructions/rental/cancel_listing.rs`

**State modifications** (`src/state/player.rs`):

```rust
#[account]
#[derive(InitSpace)]
pub struct RentalListing {
    pub owner: Pubkey,
    pub player: Pubkey,              // ParodyPlayer being rented
    pub price_per_match: u64,        // Cost per match in lamports/tokens
    pub matches_rented: u8,          // How many matches included
    pub current_borrower: Option<Pubkey>,
    pub rental_start_ts: Option<i64>,
    pub rental_end_ts: Option<i64>,
    pub is_active: bool,
    pub platform_fee_bps: u16,       // Platform cut of rental fee
    pub bump: u8,
}
```

**New constants**:
```rust
pub const SEED_RENTAL_ESCROW: &[u8] = b"rental_escrow";
pub const DEFAULT_RENTAL_FEE_BPS: u16 = 500; // 5% platform fee
```

**Instruction: `mint_player`**
- PDA: `[b"player", player_id.as_bytes()]`
- Admin mints a new ParodyPlayer with initial stats
- Requires `GlobalConfig.admin` authorization
- Sets `owner` to the recipient
- Accounts: `admin: Signer`, `config: GlobalConfig`, `player: init`, `recipient: UncheckedAccount`, `system_program`

**Instruction: `create_listing`**
- PDA: `[b"rental", player.key()]`
- Owner of a `ParodyPlayer` creates a rental listing
- Validates `player.owner == signer.key()`
- Sets `price_per_match`, `matches_rented`, `is_active = true`
- Accounts: `owner: Signer`, `player: Account<ParodyPlayer>` (mut, owner check), `listing: init`, `system_program`

**Instruction: `rent_player`**
- Renter pays `price_per_match * matches_rented` to escrow PDA
- Escrow PDA: `[b"rental_escrow", listing.key()]`
- Sets `current_borrower`, `rental_start_ts`, `rental_end_ts`
- Transfers rental fee: renter → escrow vault (system program transfer or SPL transfer_checked)
- Platform fee deducted immediately → treasury
- Accounts: `renter: Signer`, `listing: mut`, `player: mut` (update `current_borrower`), `escrow_vault: init`, `treasury: UncheckedAccount`, `system_program`

**Instruction: `end_rental`**
- Called by owner or borrower after `rental_end_ts`
- Releases player back to owner: `listing.current_borrower = None`
- Transfers escrowed funds to owner (minus platform fee, already taken)
- Closes escrow account, reclaims rent
- Accounts: `caller: Signer`, `listing: mut`, `player: mut`, `escrow_vault: mut`, `owner: UncheckedAccount`, `system_program`

**Instruction: `cancel_listing`**
- Owner cancels active listing before rental starts
- If `current_borrower.is_some()`, reject (must use `end_rental` instead)
- Closes listing account, reclaims rent
- Accounts: `owner: Signer`, `listing: mut`, `system_program`

#### Phase 2: Advanced Features

**Yield-bearing players**:
- `ParodyPlayer.base_yield_rate` determines daily token yield for the owner
- New instruction: `claim_player_yield` — owner claims accumulated yield based on `last_claim_timestamp` and `base_yield_rate`
- Yield funded from platform revenue (wager fees, market fees)

**Equipment system**:
- `equipped_stadium_id`, `equipped_jersey`, `equipped_boots` are `Option<Pubkey>` pointing to NFT item accounts
- New instructions: `equip_item`, `unequip_item`
- Items modify player stats (speed, shot_power, etc.)

**Match integration**:
- `PlayerMatchRecord` (already defined in `state/player_match.rs`) tracks which players participated in which fixtures
- New instruction: `record_player_match` — oracle links player to fixture, applies stat changes
- Rental bonus: borrowed players earn yield for borrower, not owner, during rental period

**Files to create/modify**:
| File | Action |
|------|--------|
| `src/instructions/rental/mod.rs` | Create |
| `src/instructions/rental/mint_player.rs` | Create |
| `src/instructions/rental/create_listing.rs` | Create |
| `src/instructions/rental/rent_player.rs` | Create |
| `src/instructions/rental/end_rental.rs` | Create |
| `src/instructions/rental/cancel_listing.rs` | Create |
| `src/instructions/rental/claim_player_yield.rs` | Create (Phase 2) |
| `src/instructions/mod.rs` | Add `pub mod rental;` |
| `src/state/player.rs` | Update `RentalListing` with new fields |
| `src/constants.rs` | Add `SEED_RENTAL_ESCROW`, `DEFAULT_RENTAL_FEE_BPS` |
| `src/errors.rs` | Add rental error variants |
| `src/lib.rs` | Add `#[derive(Accounts)]` structs + `#[program]` entries |

---

## 4. Risk Mitigation Checklist (Pre-Commit)

### Must Fix Before Devnet

- [ ] **C1**: Add `resolver` field to `Wager` state, enforce in `ResolveWager` constraint
- [ ] **C2**: Add `GlobalConfig` to `UpdateFixtureStatus`, verify `config.admin == admin.key()`
- [ ] **C3**: Add `GlobalConfig` to `SweepFixtureDust`, verify `config.admin == admin.key()`
- [ ] **C4**: Constrain `winner` in `ResolveWager` to be `wager.player_a` or `wager.player_b`
- [ ] **C5**: Add `amount` and `prediction` as instruction args to `place_market_bet`
- [ ] **H1**: Use `checked_mul(2)` in `resolve_wager` payout
- [ ] **H2**: Use `checked_mul(2)` in `claim_bet_payout` payout
- [ ] **H4**: Add `new_status` and `winner` args to `oracle_update_market_status`, validate state transition

### Should Fix Before Mainnet

- [ ] **H3**: Implement proportional parimutuel payout in `claim_market_payout`
- [ ] **M1**: Add `require!(amount > 0)` to `place_bet`
- [ ] **M2**: Enforce `max_sol_per_user` from `GlobalConfig` in `place_bet`
- [ ] **M3**: Enforce `cutoff_buffer_seconds` in `place_bet`
- [ ] **M4**: Accept live state params as instruction args in `oracle_upsert_live_state`
- [ ] **M5**: Accept `fixture`, `token_mint`, `market_type` as args in `oracle_create_market`

### Nice to Have

- [ ] **L1**: Remove unused `_market_key` variable
- [ ] **L2**: Add admin auth to `InitializeFixture`
- [ ] **L3**: Remove unused `#[instruction(amount: u64)]` from `CreateWager`
- [ ] Add `UnauthorizedAdmin` and `InvalidWinner` error variants to `GoalWorldError`
- [ ] Add `UnauthorizedResolver` error variant
- [ ] Implement staking Phase 1 (4 new instructions)
- [ ] Implement rental Phase 1 (5 new instructions)

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GoalWorld Program (lib.rs)                       │
│  declare_id!("GWorLD11111111111111111111111111111111111111111")    │
├─────────────────────────────────────────────────────────────────────┤
│  #[program] module — 17 instruction entry points                    │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   Config     │    Wager     │   Fixtures   │    Live Markets       │
│ (2 instrs)   │  (3 instrs)  │  (6 instrs)  │    (5 instrs)         │
│              │              │              │                       │
│ init_config  │ create_wager │ init_fixture │ oracle_upsert_live    │
│ update_config│ accept_wager │ place_bet    │ oracle_create_market  │
│              │ resolve_wager│ update_status│ oracle_update_status  │
│              │              │ claim_payout │ place_market_bet      │
│              │              │ refund_bet   │ claim_market_payout   │
│              │              │ sweep_dust   │                       │
├──────────────┴──────────────┴──────────────┴───────────────────────┤
│                    State Layer (src/state/)                         │
│  GlobalConfig · Wager · Fixture · UserBet · Market · MarketPosition │
│  LiveMatchState · UserStake (unused) · ParodyPlayer (unused)        │
│  RentalListing (unused) · BuilderFund (unused) · ManagerState       │
├─────────────────────────────────────────────────────────────────────┤
│              Future Expansion (not yet implemented)                 │
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ Staking & Yield     │  │ NFT Rentals                          │ │
│  │ Phase 1: SOL stake  │  │ Phase 1: mint, list, rent, end       │ │
│  │ Phase 2: Jito LST   │  │ Phase 2: yield, equipment, matches   │ │
│  └─────────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Audit conducted by GoalWorld Manager (Hermes Agent) using the `solana-anchor-security-audit` skill framework. All findings based on source code inspection and build verification as of 2026-06-29.*
