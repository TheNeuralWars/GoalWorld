# GoalWorld Betting System Security Audit Report

## Overview
This report details the security audit of the betting-related instructions in the GoalWorld Solana program. The audit focuses on the following functions:
- `create_wager`
- `accept_wager`
- `resolve_wager`
- `place_bet`
- `claim_bet_payout`
- `refund_bet`

## Critical Issues

### 1. Non-deterministic PDA Seeds in `create_wager`
**Location:** `CreateWager` struct, seeds for `wager` account: `[b"wager", player_a.key().as_ref(), timestamp.to_le_bytes().as_ref()]`
**Risk:** 
- The timestamp is provided by the user as an instruction argument and is not validated against the current time.
- This allows a user to grind for PDA collisions (though difficult) or to create wagers with arbitrary timestamps that may be used in other attacks (e.g., replay attacks if the timestamp is used elsewhere).
- The reference suggests using deterministic seeds (e.g., a nonce) to prevent grinding and replay attacks.

### 2. Missing Constraints on `UncheckedAccount` Usage
**Location:** 
- `ClaimBetPayout`: `user_token_account`, `fixture_vault`, `treasury_token_account`, `jackpot_token_account` are declared as `UncheckedAccount<'info>`.
- `RefundBet`: `user_token_account`, `fixture_vault` are `UncheckedAccount<'info>`.
**Risk:**
- These accounts are not validated to be owned by the token program, to have the correct mint, or to be the correct PDA-derived accounts.
- An attacker could pass in arbitrary accounts and potentially steal tokens or manipulate the program state.
- The comments indicate that manual validation is performed in the handler, but relying on manual validation is error-prone and goes against Anchor best practices.

### 3. Missing PDA-Associated Account Constraints
**Location:**
- In `AcceptWager` and `ResolveWager`, the `wager_vault` account is not constrained to be the PDA derived from the `wager` account.
- In `ClaimBetPayout` and `RefundBet`, the `fixture_vault` account is not constrained to be the PDA derived from the `fixture` account.
**Risk:**
- An attacker could pass in a different token account as the vault and steal funds that are meant to be locked in the vault.

### 4. Missing State Transition Checks (Double Claim Vulnerability)
**Location:** 
- The `UserBet` account (seen in `PlaceBet`, `ClaimBetPayout`, `RefundBet`) does not appear to have a status field to track whether the bet has been paid out or refunded.
**Risk:**
- An attacker could call `claim_bet_payout` and then `refund_bet` (or vice versa) for the same bet, leading to double withdrawal of funds.
- The reference suggests adding a `status` field to `UserBet` and enforcing state transitions (e.g., `Resolved` -> `PayoutClaimed` or `Refunded`).

### 5. Missing Signer Check on Mutable Accounts in `ResolveWager`
**Location:** 
- The `wager` and `wager_vault` accounts are mutable in `ResolveWager` but are not required to be signed by the `oracle_authority`.
**Risk:**
- While the `oracle_authority` is validated as a signer and must match the config, the `wager` and `wager_vault` accounts are not explicitly constrained to be modified only by the oracle. However, since the oracle is the only signer that can pass the config check, and the wager and vault are mut, this may be acceptable if the handler logic ensures that only the oracle can modify them. But it is better practice to explicitly require the oracle to sign for any mutation of the wager and vault accounts.

### 6. Potential Missing Owner Checks on Token Accounts
**Location:** 
- In `ClaimBetPayout` and `RefundBet`, the `user_token_account` is not checked to belong to the user (i.e., that the token account's owner is the user's public key).
**Risk:**
- An attacker could specify a token account that belongs to another user and steal funds from that account.

## Recommendations

### 1. Replace Timestamp with Nonce in `create_wager`
- Remove the `timestamp` instruction argument from `create_wager`.
- Introduce a nonce mechanism, such as:
  - Adding a `nonce` field to a global config or to the user's account (if we have a user account model).
  - Using a counter that is incremented each time a wager is created (stored in the config or in a separate PDA).
  - Using the current slot (from `Clock::get()?`) as part of the seeds (note: the slot is not under user control, but it changes every block).
- Example seeds: `[b"wager", player_a.key().as_ref(), &[nonce]]` where `nonce` is a u8 or u64 that we increment.

### 2. Replace `UncheckedAccount` with Constrained Accounts
- For `user_token_account` in `ClaimBetPayout` and `RefundBet`:
  ```rust
  #[account(
      mut,
      constraint = user_token_account.owner == user.key() @ goalworldError::InvalidTokenOwner,
      constraint = user_token_account.mint == token_mint.key() @ goalworldError::InvalidMint
  )]
  pub user_token_account: Account<'info, TokenAccount>,
  ```
- For `fixture_vault` in `ClaimBetPayout` and `RefundBet`:
  ```rust
  #[account(
      mut,
      seeds = [b"fixture_vault", fixture.key().as_ref()],
      bump = fixture_vault.bump,
      constraint = fixture_vault.mint == token_mint.key() @ goalworldError::InvalidMint,
      constraint = fixture_vault.authority == fixture.key() @ goalworldError::InvalidAuthority
  )]
  pub fixture_vault: Account<'info, TokenAccount>,
  ```
  Note: We need to store the bump in the `fixture_vault` account? Actually, we can use the constraint `constraint = fixture_vault.bump == expected_bump` but we don't have the expected bump stored anywhere. Alternatively, we can use the seeds constraint without storing the bump in the account, and then in the handler we can verify the bump by deriving the PDA and checking. However, Anchor allows us to use `bump = fixture_vault.bump` in the seeds constraint to check that the account's bump matches the one we expect (which we can derive from the seeds and the program ID). But we don't have the expected bump stored in the account. We can instead use:
  ```rust
  #[account(
      mut,
      address = Pubkey::find_program_address(&[b"fixture_vault", fixture.key().as_ref()], program_id).0 @ goalworldError::InvalidVault
  )]
  ```
  However, the `address` constraint is available in Anchor.

- For `treasury_token_account` and `jackpot_token_account` in `ClaimBetPayout`:
  ```rust
  #[account(
      mut,
      constraint = treasury_token_account.key() == config.treasury_token_account @ goalworldError::InvalidTreasury,
      constraint = treasury_token_account.mint == token_mint.key() @ goalworldError::InvalidMint,
      constraint = treasury_token_account.owner == token_program.key() @ goalworldError::InvalidTokenOwner
  )]
  pub treasury_token_account: Account<'info, TokenAccount>,
  ```
  Similarly for `jackpot_token_account`.

### 3. Add PDA-Associated Account Constraints
- In `AcceptWager` and `ResolveWager`, add a constraint to `wager_vault`:
  ```rust
  #[account(
      mut,
      seeds = [b"wager_vault", wager.key().as_ref()],
      bump = wager_vault.bump,
      token::mint = token_mint,
      token::authority = wager
  )]
  pub wager_vault: Account<'info, TokenAccount>,
  ```
  Note: We are changing from `InterfaceAccount` to `Account` and adding the seeds constraint.

- In `ClaimBetPayout` and `RefundBet`, we already propose to change `fixture_vault` to a constrained account as above.

### 4. Add Status Field to `UserBet` to Prevent Double Claims
- Add a `status` field to the `UserBet` struct (in `state/` directory) with possible values: `Active`, `Resolved`, `PayoutClaimed`, `Refunded`.
- In `place_bet`, set status to `Active`.
- In `resolve_wager`, after determining the winner, set the status of the losing bet to `Resolved` (or maybe we don't need to change the losing bet? Actually, the losing bet is not claimed, so we may not need to change its status. But the winning bet will be claimed or refunded).
- In `claim_bet_payout`, check that the status is `Resolved`, then set it to `PayoutClaimed` before transferring tokens.
- In `refund_bet`, check that the status is `Resolved` (or maybe `Active` if the fixture was canceled?), then set it to `Refunded` before transferring tokens.

### 5. Explicitly Require Signer for Mutable Accounts in `ResolveWager` (Optional but Recommended)
- Change the `wager` and `wager_vault` accounts in `ResolveWager` to require the `oracle_authority` as a signer? However, note that the `wager` account is not owned by the oracle; it is owned by the system (since it's a PDA). So we cannot require the oracle to sign for the wager account because the wager account is a PDA and cannot sign. Instead, we should ensure that the handler logic only allows the oracle to modify the wager and vault by checking that the oracle_authority signer matches the config and then performing the mutation. This is already done by the config constraint. So this may be acceptable.

  However, to be explicit, we can add a constraint that the `wager` account is mutable and that the `oracle_authority` is the signer (but we cannot require the wager account to be signed by the oracle because it's not a signer account). So we rely on the config constraint and the fact that the handler is the only place that mutates the wager.

  Alternatively, we can note that the `wager` account is a PDA derived from `[b"wager", player_a.key(), nonce]` (after we fix the nonce) and thus its authority is the program. So only the program can modify it via CPI? Actually, the wager account is owned by the program (since it's a PDA), so only the program can modify it. The instruction is calling the program, so the program is allowed to modify its own PDA. Therefore, we do not need an external signer to modify the wager account. The same applies to the wager_vault (which is a token account owned by the wager PDA). So the only signer we need is the oracle_authority to authorize the action via the config check.

  Therefore, the missing signer check on the wager and wager_vault is not a vulnerability because they are PDAs owned by the program. However, we must ensure that the PDA seeds are correct and that we are indeed loading the correct PDA. This is why we recommend adding the PDA-associated account constraints (as in point 3).

### 6. Add Owner Check for `user_token_account`
- As shown in recommendation 2, add a constraint that `user_token_account.owner == user.key()`.

## Additional Notes
- The `config` account loading via seeds is safe because we use the bump stored in the account itself.
- The `fixture` account in `PlaceBet`, `ClaimBetPayout`, `RefundBet` is loaded as a mutable account but we do not check that it is the correct fixture? Actually, we pass the fixture account and we rely on the user to pass the correct one. However, we have constraints in the bet and user_bet that tie the fixture to the bet. So if the user passes a wrong fixture, the constraints on `user_bet` (which checks that user_bet.fixture == fixture.key()) will fail. So it is safe.

## Conclusion
The betting system has several critical vulnerabilities that could lead to token theft or double claiming. The most critical issues are the use of `UncheckedAccount` for token accounts and vaults without sufficient constraints, and the non-deterministic PDA seeds in `create_wager`. We recommend implementing the fixes outlined above to secure the betting system.

## Next Steps
1. Update the `CreateWager` struct to use a nonce instead of timestamp.
2. Replace all `UncheckedAccount` usages with constrained `Account` types.
3. Add PDA-associated account constraints for vaults.
4. Add a status field to the `UserBet` struct and enforce state transitions.
5. Update the handlers accordingly to reflect the new constraints and state transitions.
6. Write unit tests to verify the fixes and to test for edge cases (double claim, invalid accounts, etc.).