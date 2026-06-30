use anchor_lang::prelude::*;
use crate::constants::SEED_FIXTURE;

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum MatchStatus {
    Scheduled,
    Open,
    Closed,
    Completed,
    Cancelled,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum MatchResult {
    Pending,
    HomeWin,
    AwayWin,
    Draw,
}

#[account]
#[derive(InitSpace)]
pub struct Fixture {
    #[max_len(64)]
    pub match_id: String,
    #[max_len(32)]
    pub team_a: String,
    #[max_len(32)]
    pub team_b: String,
    pub start_timestamp: i64,
    pub pool_a: u64,
    pub pool_b: u64,
    pub pool_draw: u64,
    pub total_claimed: u64,
    pub total_refunded: u64,
    pub status: MatchStatus,
    pub result: MatchResult,
    pub bump: u8,
}

impl Fixture {
    pub const SEED: &'static [u8] = SEED_FIXTURE;
    pub const LEN: usize = 8 + Fixture::INIT_SPACE;
}
