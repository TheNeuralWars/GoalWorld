use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::ClaimBetPayout;

pub fn handler(ctx: Context<ClaimBetPayout>) -> Result<()> {
    let user_bet = &mut ctx.accounts.user_bet;
    let fixture = &ctx.accounts.fixture;

    require!(fixture.status == MatchStatus::Completed, GoalWorldError::FixtureNotCompleted);
    require!(!user_bet.claimed, GoalWorldError::AlreadyClaimed);

    let won = user_bet.prediction == fixture.result && fixture.result != MatchResult::Pending;
    require!(won, GoalWorldError::BetLost);

    // H2: Use checked_mul for payout
    let payout = user_bet.amount.checked_mul(2).ok_or(GoalWorldError::MathOverflow)?;

    let fixture_key = fixture.key();
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"fixture_vault",
        fixture_key.as_ref(),
        &[ctx.bumps.fixture_vault],
    ]];

    let cpi_context = CpiContext::new_with_signer(
        ctx.accounts.system_program.key(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.fixture_vault.to_account_info(),
            to: ctx.accounts.user.to_account_info(),
        },
        signer_seeds,
    );
    anchor_lang::system_program::transfer(cpi_context, payout)?;

    user_bet.claimed = true;
    Ok(())
}
