use anchor_lang::prelude::*;
use crate::constants::SEED_MARKET;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum MarketType {
    MatchResultLive,
    NextGoal,
    Custom,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum MarketStatus {
    Open,
    Closed,
    Resolved,
    Cancelled,
}

impl std::fmt::Display for MarketStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

#[account]
#[derive(InitSpace)]
pub struct Market {
    pub fixture: Pubkey,
    pub market_id: u8,
    pub market_type: MarketType,
    pub status: MarketStatus,
    pub token_mint: Pubkey,
    pub delay_seconds: i64,
    pub cooldown_seconds: i64,
    pub close_minute: u16,
    pub max_goal_diff: u8,
    pub require_tied: bool,
    pub pool_a: u64,
    pub pool_b: u64,
    pub pool_draw: u64,
    pub winner: Option<crate::state::fixture::MatchResult>,
    pub last_bet_ts: i64,
    pub resolved_ts: Option<i64>,
    pub bump: u8,
}

impl Market {
    pub const SEED: &'static [u8] = SEED_MARKET;
    pub const LEN: usize = 8 + Market::INIT_SPACE;
}