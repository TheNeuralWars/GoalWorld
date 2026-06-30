use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::ResolveWager;

pub fn handler(ctx: Context<ResolveWager>, _winner: Pubkey) -> Result<()> {
    let wager = &mut ctx.accounts.wager;
    require!(wager.state == WagerState::Accepted, GoalWorldError::WagerNotAccepted);
    require!(wager.player_b.is_some(), GoalWorldError::WagerNotAccepted);

    wager.state = WagerState::Resolved;

    let wager_key = wager.key();
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"wager_vault",
        wager_key.as_ref(),
        &[ctx.bumps.wager_vault],
    ]];

    // H1: Use checked_mul for payout
    let payout = wager.amount.checked_mul(2).ok_or(GoalWorldError::MathOverflow)?;

    let cpi_context = CpiContext::new_with_signer(
        ctx.accounts.system_program.key(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.wager_vault.to_account_info(),
            to: ctx.accounts.winner.to_account_info(),
        },
        signer_seeds,
    );
    anchor_lang::system_program::transfer(cpi_context, payout)?;

    Ok(())
}
