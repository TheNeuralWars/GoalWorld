use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, TransferChecked};
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::PlaceMarketBet;

pub fn handler(ctx: Context<PlaceMarketBet>, ticket_id: u64, amount: u64, prediction: MatchResult) -> Result<()> {
    let user = &ctx.accounts.user;
    let market = &mut ctx.accounts.market;
    let market_position = &mut ctx.accounts.market_position;

    require!(market.status == MarketStatus::Open, GoalWorldError::BettingClosed);
    require!(amount > 0, GoalWorldError::InvalidAmount);

    let bet_amount = amount;
    let decimals = ctx.accounts.market_token_mint.decimals;
    let cpi_accounts = TransferChecked {
        from: ctx.accounts.user_token_account.to_account_info(),
        to: ctx.accounts.market_vault.to_account_info(),
        authority: user.to_account_info(),
        mint: ctx.accounts.market_token_mint.to_account_info(),
    };
    let cpi_ctx = CpiContext::new(ctx.accounts.token_program.key(), cpi_accounts);
    token_interface::transfer_checked(cpi_ctx, bet_amount, decimals)?;

    market_position.owner = user.key();
    market_position.market = market.key();
    market_position.ticket_id = ticket_id;
    market_position.amount = bet_amount;
    market_position.prediction = prediction;
    market_position.bet_ts = Clock::get()?.unix_timestamp;
    market_position.claimed = false;
    market_position.bump = ctx.bumps.market_position;

    match prediction {
        MatchResult::HomeWin => market.pool_a += bet_amount,
        MatchResult::AwayWin => market.pool_b += bet_amount,
        MatchResult::Draw => market.pool_draw += bet_amount,
        _ => return Err(GoalWorldError::InvalidBetOutcome.into()),
    }
    market.last_bet_ts = Clock::get()?.unix_timestamp;

    Ok(())
}
