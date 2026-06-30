use anchor_lang::prelude::*;

#[error_code]
pub enum GoalWorldError {
    #[msg("Wager is not pending")]
    WagerNotPending,
    #[msg("Wager already accepted")]
    WagerAlreadyAccepted,
    #[msg("Wager not accepted yet")]
    WagerNotAccepted,
    #[msg("Invalid oracle")]
    InvalidOracle,
    #[msg("Fixture already open")]
    FixtureAlreadyOpen,
    #[msg("Fixture not open")]
    FixtureNotOpen,
    #[msg("Fixture not completed")]
    FixtureNotCompleted,
    #[msg("Fixture not cancelled")]
    FixtureNotCancelled,
    #[msg("Bet lost")]
    BetLost,
    #[msg("Wager exceeded max allowed amount")]
    WagerExceededMaxAmount,
    #[msg("Invalid fixture result")]
    InvalidFixtureResult,
    #[msg("Invalid bet outcome")]
    InvalidBetOutcome,
    #[msg("Math overflow")]
    MathOverflow,
    #[msg("Invalid fee")]
    InvalidFee,
    #[msg("Invalid configuration")]
    InvalidConfig,
    #[msg("Unauthorized oracle")]
    UnauthorizedOracle,
    #[msg("Invalid market config")]
    InvalidMarketConfig,
    #[msg("Invalid market")]
    InvalidMarket,
    #[msg("Betting is closed")]
    BettingClosed,
    #[msg("Market is not closed")]
    MarketNotClosed,
    #[msg("Market is not resolved")]
    MarketNotResolved,
    #[msg("Already claimed")]
    AlreadyClaimed,
    #[msg("Invalid treasury account")]
    InvalidTreasury,
    #[msg("Invalid jackpot account")]
    InvalidJackpot,
    #[msg("Invalid vault")]
    InvalidVault,
    #[msg("Match not finished")]
    MatchNotFinished,
    // Security fixes (C1-H4)
    #[msg("Unauthorized admin")]
    UnauthorizedAdmin,
    #[msg("Unauthorized resolver")]
    UnauthorizedResolver,
    #[msg("Invalid winner")]
    InvalidWinner,
    #[msg("Invalid amount")]
    InvalidAmount,
    #[msg("Market not open")]
    MarketNotOpen,
    // New errors for Medium fixes (M1-M3)
    #[msg("Bet amount must be greater than zero")]
    BetAmountZero,
    #[msg("Exceeded maximum SOL per user limit")]
    ExceededMaxSol,
    #[msg("Betting cutoff time has passed")]
    BetTooLate,
}
