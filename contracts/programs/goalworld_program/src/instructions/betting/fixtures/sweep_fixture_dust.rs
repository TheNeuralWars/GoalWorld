use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::SweepFixtureDust;

pub fn handler(ctx: Context<SweepFixtureDust>) -> Result<()> {
    let fixture = &ctx.accounts.fixture;
    require!(
        fixture.status == MatchStatus::Completed || fixture.status == MatchStatus::Cancelled,
        GoalWorldError::MatchNotFinished
    );

    let vault_balance = ctx.accounts.fixture_vault.lamports();
    if vault_balance == 0 { return Ok(()); }

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
            to: ctx.accounts.admin.to_account_info(),
        },
        signer_seeds,
    );
    anchor_lang::system_program::transfer(cpi_context, vault_balance)?;

    Ok(())
}
