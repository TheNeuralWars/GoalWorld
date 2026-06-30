use anchor_lang::prelude::*;
use crate::state::*;
use crate::UpdateFixtureStatus;

pub fn handler(ctx: Context<UpdateFixtureStatus>, status: MatchStatus, result: MatchResult) -> Result<()> {
    let fixture = &mut ctx.accounts.fixture;
    fixture.status = status;
    fixture.result = result;
    Ok(())
}
