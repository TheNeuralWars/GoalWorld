use anchor_lang::prelude::*;
use crate::state::*;
use crate::errors::GoalWorldError;
use crate::OracleUpdateMarketStatus;

pub fn handler(ctx: Context<OracleUpdateMarketStatus>, new_status: MarketStatus, winner: Option<MatchResult>) -> Result<()> {
    let market = &mut ctx.accounts.market;

    // Only allow transition from Open to Closed/Resolved
    require!(market.status == MarketStatus::Open, GoalWorldError::MarketNotOpen);
    require!(new_status == MarketStatus::Closed || new_status == MarketStatus::Resolved, GoalWorldError::InvalidMarketConfig);

    market.status = new_status;
    market.winner = winner;
    market.resolved_ts = Some(Clock::get()?.unix_timestamp);

    Ok(())
}
