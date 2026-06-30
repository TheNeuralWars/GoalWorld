use anchor_lang::prelude::*;
use crate::state::fixture::MatchResult;

#[account]
#[derive(InitSpace)]
pub struct UserBet {
    pub owner: Pubkey,
    pub fixture: Pubkey,
    pub amount: u64,
    pub prediction: MatchResult,
    pub bet_timestamp: i64,
    pub claimed: bool,
    pub bump: u8,
}
