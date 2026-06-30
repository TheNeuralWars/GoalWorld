use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, TransferChecked};
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::ClaimMarketPayout;

pub fn handler(ctx: Context<ClaimMarketPayout>) -> Result<()> {
    let market = &ctx.accounts.market;
    let market_position = &mut ctx.accounts.market_position;

    require_eq!(
        market.status,
        MarketStatus::Closed,
        GoalWorldError::MarketNotClosed
    );
    require!(
        market.resolved_ts.is_some(),
        GoalWorldError::MarketNotResolved
    );
    require!(!market_position.claimed, GoalWorldError::AlreadyClaimed);

    let decimals = ctx.accounts.market_token_mint.decimals;
    let market_bump = market.bump;
    let market_id_bytes = market.market_id.to_le_bytes();
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"market",
        market_id_bytes.as_ref(),
        &[market_bump],
    ]];

    // H3: Implement proportional parimutuel payout
    let total_pool = market.pool_a
        .checked_add(market.pool_b)
        .and_then(|sum| sum.checked_add(market.pool_draw))
        .ok_or(GoalWorldError::MathOverflow)?;

    let winning_pool = match market.winner {
        Some(MatchResult::HomeWin) => market.pool_a,
        Some(MatchResult::AwayWin) => market.pool_b,
        Some(MatchResult::Draw) => market.pool_draw,
        _ => 0,
    };

    let payout = if winning_pool > 0 && market_position.prediction == market.winner.unwrap() {
        // Winner gets their principal back + proportional share of losing pool
        let losing_pool = total_pool.saturating_sub(winning_pool);
        let principal = market_position.amount;
        let profit = losing_pool
            .checked_mul(principal)
            .ok_or(GoalWorldError::MathOverflow)?
            .checked_div(winning_pool)
            .unwrap_or(0);
        principal.checked_add(profit).ok_or(GoalWorldError::MathOverflow)?
    } else {
        0
    };

    if payout > 0 {
        let cpi_accounts = TransferChecked {
            from: ctx.accounts.market_vault.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: market.to_account_info(),
            mint: ctx.accounts.market_token_mint.to_account_info(),
        };
        let cpi_ctx = CpiContext::new_with_signer(
            ctx.accounts.token_program.key(),
            cpi_accounts,
            signer_seeds,
        );
        token_interface::transfer_checked(cpi_ctx, payout, decimals)?;
    }

    let remainder = ctx.accounts.market_vault.amount;
    let treasury_share = remainder / 10;
    let jackpot_share = remainder / 20;

    if treasury_share > 0 {
        let cpi_accounts = TransferChecked {
            from: ctx.accounts.market_vault.to_account_info(),
            to: ctx.accounts.treasury_token_account.to_account_info(),
            authority: market.to_account_info(),
            mint: ctx.accounts.market_token_mint.to_account_info(),
        };
        let cpi_ctx = CpiContext::new_with_signer(
            ctx.accounts.token_program.key(),
            cpi_accounts,
            signer_seeds,
        );
        token_interface::transfer_checked(cpi_ctx, treasury_share, decimals)?;
    }

    if jackpot_share > 0 {
        let cpi_accounts = TransferChecked {
            from: ctx.accounts.market_vault.to_account_info(),
            to: ctx.accounts.jackpot_token_account.to_account_info(),
            authority: market.to_account_info(),
            mint: ctx.accounts.market_token_mint.to_account_info(),
        };
        let cpi_ctx = CpiContext::new_with_signer(
            ctx.accounts.token_program.key(),
            cpi_accounts,
            signer_seeds,
        );
        token_interface::transfer_checked(cpi_ctx, jackpot_share, decimals)?;
    }

    market_position.claimed = true;
    Ok(())
}
