use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::RefundBet;

pub fn handler(ctx: Context<RefundBet>) -> Result<()> {
    let user_bet = &mut ctx.accounts.user_bet;
    let fixture = &ctx.accounts.fixture;

    require!(fixture.status == MatchStatus::Cancelled, GoalWorldError::FixtureNotCancelled);
    require!(!user_bet.claimed, GoalWorldError::AlreadyClaimed);

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
    anchor_lang::system_program::transfer(cpi_context, user_bet.amount)?;

    user_bet.claimed = true;
    Ok(())
}
