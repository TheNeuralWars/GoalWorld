use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::AcceptWager;

pub fn handler(ctx: Context<AcceptWager>) -> Result<()> {
    let wager = &mut ctx.accounts.wager;
    require!(wager.state == WagerState::Pending, GoalWorldError::WagerNotPending);
    wager.player_b = Some(ctx.accounts.opponent.key());
    wager.state = WagerState::Accepted;

    let cpi_context = CpiContext::new(
        ctx.accounts.system_program.key(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.opponent.to_account_info(),
            to: ctx.accounts.wager_vault.to_account_info(),
        },
    );
    anchor_lang::system_program::transfer(cpi_context, wager.amount)?;

    Ok(())
}
