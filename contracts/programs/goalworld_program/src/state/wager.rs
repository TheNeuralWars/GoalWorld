// src/state/wager.rs
use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
pub struct Wager {
    pub player_a: Pubkey,
    pub player_b: Option<Pubkey>,
    pub amount: u64,
    pub timestamp: i64,
    pub bump: u8,
    pub state: WagerState,
    pub resolver: Pubkey,  // C1: Authority allowed to resolve
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq, InitSpace, Debug)]
pub enum WagerState {
    Pending,
    Accepted,
    Resolved,
}
