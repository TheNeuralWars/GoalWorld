use anchor_lang::prelude::*;
use crate::state::*;
use crate::InitializeFixture;

pub fn handler(ctx: Context<InitializeFixture>, match_id: String) -> Result<()> {
    let fixture = &mut ctx.accounts.fixture;
    fixture.match_id = match_id;
    fixture.team_a = String::new();
    fixture.team_b = String::new();
    fixture.start_timestamp = Clock::get()?.unix_timestamp;
    fixture.pool_a = 0;
    fixture.pool_b = 0;
    fixture.pool_draw = 0;
    fixture.total_claimed = 0;
    fixture.total_refunded = 0;
    fixture.status = MatchStatus::Scheduled;
    fixture.result = MatchResult::Pending;
    fixture.bump = ctx.bumps.fixture;
    Ok(())
}
