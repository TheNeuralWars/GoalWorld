use anchor_lang::prelude::*;
use crate::state::*;
use crate::CreateWager;

pub fn handler(ctx: Context<CreateWager>, amount: u64) -> Result<()> {
    let wager = &mut ctx.accounts.wager;
    wager.player_a = ctx.accounts.initializer.key();
    wager.player_b = None;
    wager.amount = amount;
    wager.timestamp = Clock::get()?.unix_timestamp;
    wager.bump = ctx.bumps.wager;
    wager.state = WagerState::Pending;
    wager.resolver = ctx.accounts.initializer.key();  // C1: Set resolver as creator

    let cpi_context = CpiContext::new(
        ctx.accounts.system_program.key(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.initializer.to_account_info(),
            to: ctx.accounts.wager_vault.to_account_info(),
        },
    );
    anchor_lang::system_program::transfer(cpi_context, amount)?;

    Ok(())
}
