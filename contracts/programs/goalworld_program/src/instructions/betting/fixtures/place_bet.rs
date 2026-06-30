use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::PlaceBet;

pub fn handler(ctx: Context<PlaceBet>, amount: u64, prediction: MatchResult) -> Result<()> {
    let config = &ctx.accounts.config;
    let fixture = &mut ctx.accounts.fixture;
    
    // M1: Validate amount > 0
    require!(amount > 0, GoalWorldError::BetAmountZero);
    
    // M2: Validate against max_sol_per_user limit
    // Sum existing bets for this user on this fixture
    let user_bet = &mut ctx.accounts.user_bet;
    let existing_amount = user_bet.amount; // This is 0 for new bet, but we check anyway
    require!(
        existing_amount.saturating_add(amount) <= config.max_sol_per_user,
        GoalWorldError::ExceededMaxSol
    );
    
    // M3: Validate cutoff time - betting must close before match starts
    let current_ts = Clock::get()?.unix_timestamp;
    let cutoff_ts = current_ts.saturating_add(config.cutoff_buffer_seconds);
    require!(
        cutoff_ts < fixture.start_timestamp,
        GoalWorldError::BetTooLate
    );
    
    require!(fixture.status == MatchStatus::Open, GoalWorldError::FixtureNotOpen);

    user_bet.owner = ctx.accounts.user.key();
    user_bet.fixture = fixture.key();
    user_bet.amount = amount;
    user_bet.prediction = prediction;
    user_bet.bump = ctx.bumps.user_bet;
    user_bet.bet_timestamp = current_ts;
    user_bet.claimed = false;

    let cpi_context = CpiContext::new(
        ctx.accounts.system_program.key(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.user.to_account_info(),
            to: ctx.accounts.fixture_vault.to_account_info(),
        },
    );
    anchor_lang::system_program::transfer(cpi_context, amount)?;

    Ok(())
}
