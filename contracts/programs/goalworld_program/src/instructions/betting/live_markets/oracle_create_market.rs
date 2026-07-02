use anchor_lang::prelude::*;
use crate::state::*;
use crate::OracleCreateMarket;

pub fn handler(
    ctx: Context<OracleCreateMarket>,
    market_id: u8,
    delay_seconds: i64,
    cooldown_seconds: i64,
    close_minute: u16,
    max_goal_diff: u8,
    require_tied: bool,
) -> Result<()> {
    let market = &mut ctx.accounts.market;
    market.fixture = ctx.accounts.fixture.key();
    market.market_id = market_id;
    market.market_type = MarketType::MatchResultLive;
    market.status = MarketStatus::Open;
    market.token_mint = ctx.accounts.token_mint.key();
    market.delay_seconds = delay_seconds;
    market.cooldown_seconds = cooldown_seconds;
    market.close_minute = close_minute;
    market.max_goal_diff = max_goal_diff;
    market.require_tied = require_tied;
    market.pool_a = 0;
    market.pool_b = 0;
    market.pool_draw = 0;
    market.winner = None;
    market.resolved_ts = None;
    market.last_bet_ts = 0;
    market.bump = ctx.bumps.market;

    Ok(())
}
