import React, { lazy, Suspense } from 'react';
import { SimulationBadge } from '../components/SimulationBadge';

const FixturesPanel = lazy(() =>
  import('./FixturesPanel').then((m) => ({ default: m.FixturesPanel })),
);

/**
 * Stadium on Play: one job = bet.
 * Competing tabs (simulator / predictor / commentator / feed) were stripped.
 * Paper / Solana devnet only — no real-money copy.
 */
export function EstadioPortal() {
  return (
    <div className="play-page play-page--portal">
      <div className="portal-header glass-card">
        <div className="portal-badge">STADIUM</div>
        <SimulationBadge label="DEVNET / PAPER" />
        <h1>Bet</h1>
        <p className="portal-honesty-note">
          Paper / Solana devnet only. Not mainnet. No real-money copy. One job
          on this route: place, claim, or refund a fixture bet.
        </p>
        <p className="portal-subtitle">
          Connect a wallet, pick a side, size the stake. Explorer links open
          with cluster=devnet.
        </p>
      </div>

      <div className="portal-content-wrapper">
        <div className="portal-fade-in">
          <Suspense
            fallback={
              <div
                style={{
                  color: '#64748b',
                  padding: '2rem',
                  textAlign: 'center',
                }}
              >
                Loading fixtures…
              </div>
            }
          >
            <FixturesPanel />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
