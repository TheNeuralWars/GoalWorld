# Issue #311: Oracle - Extract Scraper Module

## Objective
Extract data ingestion logic into `packages/oracle/src/scraper/` with provider abstraction, rate limiting, retry logic, and fixture deduplication.

---

## Current State Analysis

### Existing Files (to refactor/extract from)
| File | Lines | Purpose |
|------|-------|---------|
| `goalworld_oracle/src/runScraperOracle.ts` | 92 | Main scraper loop: reads JSON file, initializes fixture, updates live state, completes fixture |
| `goalworld_oracle/fixture_oracle.js` | 64 | Standalone fixture initialization script (raw Solana instructions) |
| `goalworld_oracle/src/fixtures/*.ts` | ~176 | Fixture operations: initialize, upsert live state, complete, record player match |

### Key Observations
- No external API providers currently exist (football-data.org, API-Football, Chainlink, Drift)
- `runScraperOracle.ts` reads from a local JSON file (`scripts/oracle_match_state.json`) — this is the "scraper output" placeholder
- Fixture initialization is idempotent-checking on-chain (PDA existence) but not deduplicated at application level
- No rate limiting, retry logic, or configurable poll intervals exist

---

## Proposed File Structure

```
packages/oracle/src/scraper/
├── types.ts                    # FixtureData, ScraperConfig, ProviderResponse, Provider interface
├── runScraperOracle.ts         # Main entry point (CLI daemon)
├── fixtureOracle.ts            # Fixture data ingestion from external APIs
├── scraper.ts                  # ScraperService class (composition root)
├── providers/
│   ├── index.ts                # Provider registry & factory
│   ├── sportsApi.ts            # Football-data.org, API-Football integration
│   ├── chainlink.ts            # Chainlink feed consumption
│   └── drift.ts                # Drift oracle price feeds
```

---

## Detailed Design

### 1. `types.ts` — Core Types & Provider Interface
```typescript
// Provider abstraction for easy swap/mock
export interface FixtureData {
  matchId: string;
  teamA: string;
  teamB: string;
  startTime: number;           // Unix timestamp
  league?: string;
  venue?: string;
  status: FixtureStatus;       // 'scheduled' | 'live' | 'ht' | 'ft' | 'postponed' | 'cancelled'
  scoreA?: number;
  scoreB?: number;
  minute?: number;
  isHt?: boolean;
  isFt?: boolean;
  participantPlayerIds?: string[];
  source: string;              // Provider identifier
  fetchedAt: number;           // Unix timestamp
}

export type FixtureStatus = 'scheduled' | 'live' | 'ht' | 'ft' | 'postponed' | 'cancelled';

export interface ProviderResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  rateLimitRemaining?: number;
  rateLimitReset?: number;
}

export interface ScraperConfig {
  pollIntervalMs: number;           // Default: 60000 (1 min)
  fixturePollIntervalMs: number;    // Default: 300000 (5 min)
  maxRetries: number;               // Default: 3
  retryBaseDelayMs: number;         // Default: 1000
  enableSportsApi: boolean;         // Default: true
  enableChainlink: boolean;         // Default: false
  enableDrift: boolean;             // Default: false
  sportsApiKey?: string;            // From env
  apiFootballKey?: string;          // From env
  chainlinkRpcUrl?: string;         // From env
  driftRpcUrl?: string;             // From env
}

export interface FixtureProvider {
  name: string;
  fetchFixtures(config: ScraperConfig): Promise<ProviderResponse<FixtureData[]>>;
  fetchLiveFixture(matchId: string, config: ScraperConfig): Promise<ProviderResponse<FixtureData | null>>;
  getRateLimitInfo(): { remaining: number; reset: number };
}
```

### 2. `providers/sportsApi.ts` — Football-data.org & API-Football
- Implements `FixtureProvider` interface
- Rate limiting: respect `X-RateLimit-Remaining` headers
- Retry with exponential backoff on 429/5xx
- Map provider-specific responses to `FixtureData`
- Configurable via `SPORTS_API_PROVIDER` env (`football-data` | `api-football`)

### 3. `providers/chainlink.ts` — Chainlink Feed Consumption
- Implements `FixtureProvider` interface (for price feeds, not fixtures)
- Consumes Chainlink Price Feeds for token prices (GCH/USDC, etc.)
- Used for market settlement oracle data
- Configurable feed addresses via env

### 4. `providers/drift.ts` — Drift Oracle Price Feeds
- Implements `FixtureProvider` interface (for price feeds)
- Consumes Drift Protocol oracle accounts for perp market prices
- Used for market settlement oracle data
- Configurable market indexes via env

### 5. `fixtureOracle.ts` — Fixture Data Ingestion
- Orchestrates multiple `FixtureProvider` instances
- Deduplication: maintains in-memory cache of seen `matchId` + `fetchedAt` window
- Idempotent `initializeFixture`: checks on-chain PDA existence before submitting
- Transforms provider data → `FixtureData` → calls `OracleService.initializeFixture/upsertLiveState/completeFixture`
- Emits events for monitoring

### 6. `scraper.ts` — ScraperService Class
```typescript
export class ScraperService {
  constructor(
    private oracle: OracleService,
    private config: ScraperConfig,
    private providers: FixtureProvider[]
  ) {}

  async start(): Promise<void>           // Main loop
  async stop(): Promise<void>            // Graceful shutdown
  async runFixturePoll(): Promise<void>  // Periodic fixture discovery
  async runLivePoll(matchId: string): Promise<void>  // Live match updates
  private deduplicateFixtures(fixtures: FixtureData[]): FixtureData[]
}
```

### 7. `runScraperOracle.ts` — CLI Entry Point
- Loads config from env (with defaults)
- Instantiates providers based on enabled flags
- Creates `ScraperService` and starts it
- Handles SIGTERM/SIGINT for graceful shutdown
- Replaces current `runScraperOracle.ts` (file-based) with provider-based approach

---

## Environment Variables (New)

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_POLL_INTERVAL_MS` | `60000` | Live match poll interval |
| `SCRAPER_FIXTURE_POLL_INTERVAL_MS` | `300000` | Fixture discovery poll interval |
| `SCRAPER_MAX_RETRIES` | `3` | Max retry attempts |
| `SCRAPER_RETRY_BASE_DELAY_MS` | `1000` | Base delay for exponential backoff |
| `SPORTS_API_PROVIDER` | `football-data` | `football-data` \| `api-football` |
| `SPORTS_API_KEY` | — | API key for football-data.org |
| `API_FOOTBALL_KEY` | — | API key for API-Football |
| `ENABLE_CHAINLINK` | `false` | Enable Chainlink price feeds |
| `CHAINLINK_RPC_URL` | — | RPC for Chainlink feeds |
| `ENABLE_DRIFT` | `false` | Enable Drift oracle |
| `DRIFT_RPC_URL` | — | RPC for Drift |

---

## Acceptance Criteria Mapping

| Criteria | Implementation |
|----------|----------------|
| Each file < 200 lines | Modular design, each file ~50-150 lines |
| Provider abstraction | `FixtureProvider` interface in `types.ts` |
| Rate limiting & retry | In `sportsApi.ts`, `chainlink.ts`, `drift.ts` |
| Fixture deduplication | In-memory cache in `fixtureOracle.ts` + on-chain PDA check |
| Configurable poll intervals via env | `ScraperConfig` loaded from env in `runScraperOracle.ts` |

---

## Risks & Regressions

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing `runScraperOracle.ts` CLI | Medium | High | Keep old file as `runScraperOracle.legacy.ts` during transition; new file has same CLI interface |
| Missing provider API keys in CI/dev | High | Medium | Graceful degradation: log warning, skip provider if key missing |
| Rate limit exhaustion | Medium | High | Exponential backoff + respect headers + configurable limits |
| Fixture deduplication false positives | Low | Medium | Use composite key: `matchId` + `status` + time window |
| On-chain PDA race condition | Low | High | Idempotent `initializeFixture` checks account existence before tx |

### Rollback Plan
1. Revert `goalworld_oracle/src/runScraperOracle.ts` to original
2. Delete `packages/oracle/src/scraper/` directory
3. No database migrations needed (all state on-chain)

---

## Test Commands

```bash
# Lint (typecheck)
cd goalworld_oracle && npm run lint

# Build
cd goalworld_oracle && npm run build

# Unit tests for scraper module (to be created)
cd goalworld_oracle && npm test -- --testPathPattern="scraper"

# Integration test (requires RPC + API keys)
cd goalworld_oracle && npm run test:integration

# Manual CLI test
cd goalworld_oracle && npx ts-node src/scraper/runScraperOracle.ts
```

---

## Implementation Order (Small Safe Steps)

1. **Create `types.ts`** — Core types & `FixtureProvider` interface
2. **Create `providers/index.ts`** — Provider registry & factory
3. **Create `providers/sportsApi.ts`** — Football-data.org / API-Football (stub with mock first)
3. **Create `providers/chainlink.ts`** — Chainlink feeds (stub)
4. **Create `providers/drift.ts`** — Drift oracle (stub)
5. **Create `fixtureOracle.ts`** — Fixture ingestion + deduplication
6. **Create `scraper.ts`** — `ScraperService` composition
7. **Create `runScraperOracle.ts`** — New CLI entry point
8. **Update `package.json`** — Add test script, verify build
9. **Run lint/build** — Verify no regressions

---

## GStack Investigate Workflow (Root Cause)

**Root Cause:** Data ingestion logic is scattered across `runScraperOracle.ts`, `fixture_oracle.js`, and `fixtures/*.ts` with no provider abstraction, making it impossible to swap data sources or add rate limiting.

**Fix Attempts (max 3):**
1. Extract provider interface → implement sports API provider
2. Add retry/rate-limit logic to provider base
3. Compose into `ScraperService` with deduplication

**Failure Modes Documented:** API key missing, rate limit hit, on-chain race, provider response schema change.

---

## Branch & PR

- **Branch:** `exp/opencode-issue-311` (direct main push per `cambio urgente`)
- **PR:** Draft PR titled `[OPENCODE] Issue #311: Extract Oracle Scraper Module`
- **Reviewers:** Antigravity (merge), Nico (approval)