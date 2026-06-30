use anchor_lang::prelude::*;
use crate::OracleUpsertLiveState;

pub fn handler(
    ctx: Context<OracleUpsertLiveState>,
    minute: u16,
    score_a: u8,
    score_b: u8,
    is_ht: bool,
    is_ft: bool,
) -> Result<()> {
    let fixture = &ctx.accounts.fixture;
    let live_state = &mut ctx.accounts.live_state;

    live_state.fixture = fixture.key();
    live_state.minute = minute;
    live_state.score_a = score_a;
    live_state.score_b = score_b;
    live_state.is_ht = is_ht;
    live_state.is_ft = is_ft;
    live_state.last_update_ts = Clock::get()?.unix_timestamp;
    live_state.bump = ctx.bumps.live_state;

    Ok(())
}
