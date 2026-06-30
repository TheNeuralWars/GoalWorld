use anchor_lang::prelude::*;
use anchor_spl::token_interface::{TokenAccount, TokenInterface, Mint};

declare_id!("GWorLD11111111111111111111111111111111111111");

pub mod state;
pub mod instructions;
pub mod errors;
pub mod constants;

use state::*;
use errors::GoalWorldError;

#[program]
pub mod goalworld {
    use super::*;

    // ─── Config ───

    pub fn initialize_config(
        ctx: Context<InitializeConfig>,
        oracle_authority: Pubkey,
        treasury_token_account: Pubkey,
        jackpot_token_account: Pubkey,
        fee_bps: u16,
        cutoff_buffer_seconds: i64,
        max_sol_per_user: u64,
        presale_active: bool,
    ) -> Result<()> {
        instructions::config::initialize_config(
            ctx, oracle_authority, treasury_token_account,
            jackpot_token_account, fee_bps, cutoff_buffer_seconds,
            max_sol_per_user, presale_active,
        )
    }

    pub fn update_config(
        ctx: Context<UpdateConfig>,
        oracle_authority: Pubkey,
        treasury_token_account: Pubkey,
        jackpot_token_account: Pubkey,
        fee_bps: u16,
        cutoff_buffer_seconds: i64,
        max_sol_per_user: u64,
        presale_active: bool,
    ) -> Result<()> {
        instructions::config::update_config(
            ctx, oracle_authority, treasury_token_account,
            jackpot_token_account, fee_bps, cutoff_buffer_seconds,
            max_sol_per_user, presale_active,
        )
    }

    // ─── Wager ───

    pub fn create_wager(ctx: Context<CreateWager>, amount: u64) -> Result<()> {
        instructions::betting::wager::create_wager::handler(ctx, amount)
    }

    pub fn accept_wager(ctx: Context<AcceptWager>) -> Result<()> {
        instructions::betting::wager::accept_wager::handler(ctx)
    }

    pub fn resolve_wager(ctx: Context<ResolveWager>, winner: Pubkey) -> Result<()> {
        instructions::betting::wager::resolve_wager::handler(ctx, winner)
    }

    // ─── Fixtures ───

    pub fn initialize_fixture(ctx: Context<InitializeFixture>, match_id: String) -> Result<()> {
        instructions::betting::fixtures::initialize_fixture::handler(ctx, match_id)
    }

    pub fn place_bet(
        ctx: Context<PlaceBet>,
        amount: u64,
        prediction: MatchResult,
    ) -> Result<()> {
        instructions::betting::fixtures::place_bet::handler(ctx, amount, prediction)
    }

    pub fn update_fixture_status(
        ctx: Context<UpdateFixtureStatus>,
        status: MatchStatus,
        result: MatchResult,
    ) -> Result<()> {
        instructions::betting::fixtures::update_fixture_status::handler(ctx, status, result)
    }

    pub fn claim_bet_payout(ctx: Context<ClaimBetPayout>) -> Result<()> {
        instructions::betting::fixtures::claim_bet_payout::handler(ctx)
    }

    pub fn refund_bet(ctx: Context<RefundBet>) -> Result<()> {
        instructions::betting::fixtures::refund_bet::handler(ctx)
    }

    pub fn sweep_fixture_dust(ctx: Context<SweepFixtureDust>) -> Result<()> {
        instructions::betting::fixtures::sweep_fixture_dust::handler(ctx)
    }

    // ─── Live Markets / Oracle ───

    pub fn oracle_upsert_live_state(
        ctx: Context<OracleUpsertLiveState>,
        minute: u16,
        score_a: u8,
        score_b: u8,
        is_ht: bool,
        is_ft: bool,
    ) -> Result<()> {
        instructions::betting::live_markets::oracle_upsert_live_state::handler(ctx, minute, score_a, score_b, is_ht, is_ft)
    }

    pub fn oracle_create_market(
        ctx: Context<OracleCreateMarket>,
        market_id: u8,
        fixture: Pubkey,
        token_mint: Pubkey,
        delay_seconds: i64,
        cooldown_seconds: i64,
        close_minute: u16,
        max_goal_diff: u8,
        require_tied: bool,
    ) -> Result<()> {
        instructions::betting::live_markets::oracle_create_market::handler(ctx, market_id, fixture, token_mint, delay_seconds, cooldown_seconds, close_minute, max_goal_diff, require_tied)
    }

    pub fn oracle_update_market_status(
        ctx: Context<OracleUpdateMarketStatus>,
        new_status: MarketStatus,
        winner: Option<MatchResult>,
    ) -> Result<()> {
        instructions::betting::live_markets::oracle_update_market_status::handler(ctx, new_status, winner)
    }

    // ─── Market Betting ───

    pub fn place_market_bet(
        ctx: Context<PlaceMarketBet>,
        ticket_id: u64,
        amount: u64,
        prediction: MatchResult,
    ) -> Result<()> {
        instructions::betting::live_markets::place_market_bet::handler(ctx, ticket_id, amount, prediction)
    }

    pub fn claim_market_payout(ctx: Context<ClaimMarketPayout>) -> Result<()> {
        instructions::betting::live_markets::claim_market_payout::handler(ctx)
    }
}

// ═══════════════════════════════════════════════════════════════
// #[derive(Accounts)] structs — MUST live at crate root
// ═══════════════════════════════════════════════════════════════

// ─── Config ───

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        init,
        payer = admin,
        space = 8 + GlobalConfig::INIT_SPACE,
        seeds = [b"config"],
        bump
    )]
    pub config: Account<'info, GlobalConfig>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        mut,
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.admin == admin.key()
    )]
    pub config: Account<'info, GlobalConfig>,
}

// ─── Wager ───

#[derive(Accounts)]
pub struct CreateWager<'info> {
    #[account(mut)]
    pub initializer: Signer<'info>,
    #[account(
        init,
        payer = initializer,
        space = 8 + Wager::INIT_SPACE,
        seeds = [b"wager", initializer.key().as_ref()],
        bump
    )]
    pub wager: Account<'info, Wager>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"wager_vault", wager.key().as_ref()],
        bump
    )]
    pub wager_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AcceptWager<'info> {
    #[account(mut)]
    pub opponent: Signer<'info>,
    #[account(mut, constraint = wager.player_a != opponent.key())]
    pub wager: Account<'info, Wager>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"wager_vault", wager.key().as_ref()],
        bump
    )]
    pub wager_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ResolveWager<'info> {
    #[account(mut)]
    pub resolver: Signer<'info>,
    #[account(
        mut,
        constraint = wager.resolver == resolver.key() @ GoalWorldError::UnauthorizedResolver
    )]
    pub wager: Account<'info, Wager>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"wager_vault", wager.key().as_ref()],
        bump
    )]
    pub wager_vault: UncheckedAccount<'info>,
    /// CHECK: winner must be one of the wager parties
    #[account(
        constraint = winner.key() == wager.player_a || winner.key() == wager.player_b.unwrap()
            @ GoalWorldError::InvalidWinner
    )]
    pub winner: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

// ─── Fixtures ───

#[derive(Accounts)]
#[instruction(match_id: String)]
pub struct InitializeFixture<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.admin == admin.key() @ GoalWorldError::UnauthorizedAdmin
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(
        init,
        payer = admin,
        space = 8 + Fixture::INIT_SPACE,
        seeds = [b"fixture", match_id.as_bytes()],
        bump
    )]
    pub fixture: Account<'info, Fixture>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct PlaceBet<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub fixture: Account<'info, Fixture>,
    #[account(
        init,
        payer = user,
        space = 8 + UserBet::INIT_SPACE,
        seeds = [b"user_bet", user.key().as_ref(), fixture.key().as_ref()],
        bump
    )]
    pub user_bet: Account<'info, UserBet>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"fixture_vault", fixture.key().as_ref()],
        bump
    )]
    pub fixture_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateFixtureStatus<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.admin == admin.key() @ GoalWorldError::UnauthorizedAdmin
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub fixture: Account<'info, Fixture>,
}

#[derive(Accounts)]
pub struct ClaimBetPayout<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    pub fixture: Account<'info, Fixture>,
    #[account(
        mut,
        constraint = user_bet.owner == user.key() && user_bet.fixture == fixture.key()
    )]
    pub user_bet: Account<'info, UserBet>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"fixture_vault", fixture.key().as_ref()],
        bump
    )]
    pub fixture_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RefundBet<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    pub fixture: Account<'info, Fixture>,
    #[account(
        mut,
        constraint = user_bet.owner == user.key() && user_bet.fixture == fixture.key()
    )]
    pub user_bet: Account<'info, UserBet>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"fixture_vault", fixture.key().as_ref()],
        bump
    )]
    pub fixture_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SweepFixtureDust<'info> {
    #[account(mut)]
    pub admin: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.admin == admin.key() @ GoalWorldError::UnauthorizedAdmin
    )]
    pub config: Account<'info, GlobalConfig>,
    pub fixture: Account<'info, Fixture>,
    /// CHECK: PDA vault
    #[account(
        mut,
        seeds = [b"fixture_vault", fixture.key().as_ref()],
        bump
    )]
    pub fixture_vault: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

// ─── Live Markets / Oracle ───

#[derive(Accounts)]
#[instruction(minute: u16, score_a: u8, score_b: u8, is_ht: bool, is_ft: bool)]
pub struct OracleUpsertLiveState<'info> {
    #[account(mut)]
    pub oracle_authority: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.oracle_authority == oracle_authority.key() @ GoalWorldError::UnauthorizedOracle
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub fixture: Account<'info, Fixture>,
    #[account(
        init_if_needed,
        payer = oracle_authority,
        space = 8 + LiveMatchState::INIT_SPACE,
        seeds = [b"live_state", fixture.key().as_ref()],
        bump
    )]
    pub live_state: Account<'info, LiveMatchState>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(
    market_id: u8,
    fixture: Pubkey,
    token_mint: Pubkey,
    delay_seconds: i64,
    cooldown_seconds: i64,
    close_minute: u16,
    max_goal_diff: u8,
    require_tied: bool
)]
pub struct OracleCreateMarket<'info> {
    #[account(mut)]
    pub oracle_authority: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.oracle_authority == oracle_authority.key() @ GoalWorldError::UnauthorizedOracle
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(
        init,
        payer = oracle_authority,
        space = 8 + Market::INIT_SPACE,
        seeds = [b"market", market_id.to_le_bytes().as_ref()],
        bump
    )]
    pub market: Account<'info, Market>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(new_status: MarketStatus, winner: Option<MatchResult>)]
pub struct OracleUpdateMarketStatus<'info> {
    #[account(mut)]
    pub oracle_authority: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump,
        constraint = config.oracle_authority == oracle_authority.key() @ GoalWorldError::UnauthorizedOracle
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub market: Account<'info, Market>,
}

// ─── Market Betting ───

#[derive(Accounts)]
#[instruction(ticket_id: u64, amount: u64, prediction: MatchResult)]
pub struct PlaceMarketBet<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub market: Account<'info, Market>,
    #[account(
        init,
        payer = user,
        space = 8 + MarketPosition::INIT_SPACE,
        seeds = [b"market_position", user.key().as_ref(), market.key().as_ref(), ticket_id.to_le_bytes().as_ref()],
        bump
    )]
    pub market_position: Account<'info, MarketPosition>,
    #[account(mut)]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(
        init_if_needed,
        payer = user,
        token::mint = market_token_mint,
        token::authority = market,
        seeds = [b"market_vault", market.key().as_ref()],
        bump
    )]
    pub market_vault: InterfaceAccount<'info, TokenAccount>,
    pub market_token_mint: InterfaceAccount<'info, Mint>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ClaimMarketPayout<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        seeds = [b"config"],
        bump = config.bump
    )]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub market: Account<'info, Market>,
    #[account(
        mut,
        constraint = market_position.owner == user.key() && market_position.market == market.key()
    )]
    pub market_position: Account<'info, MarketPosition>,
    #[account(mut)]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(mut)]
    pub market_vault: InterfaceAccount<'info, TokenAccount>,
    #[account(
        mut,
        constraint = treasury_token_account.key() == config.treasury_token_account @ GoalWorldError::InvalidTreasury
    )]
    pub treasury_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(
        mut,
        constraint = jackpot_token_account.key() == config.jackpot_token_account @ GoalWorldError::InvalidJackpot
    )]
    pub jackpot_token_account: InterfaceAccount<'info, TokenAccount>,
    pub market_token_mint: InterfaceAccount<'info, Mint>,
    pub token_program: Interface<'info, TokenInterface>,
}
