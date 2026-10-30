import React from 'react';
import { Link } from 'react-router-dom';

const VENTURE_CARDS = [
  {
    id: 'lore',
    title: 'Lore & IP Engine',
    description:
      'Browse saga assets, character lore, prompt templates, and publishing tools for the fantasy IP pipeline.',
    to: '/presskit',
    cta: 'Open Lore tools',
  },
  {
    id: 'cinema',
    title: 'Cinema & Media Engine',
    description:
      'Launch the content automation stack for visuals, clips, and social-ready media production.',
    to: '/marketing-control',
    cta: 'Open Cinema tools',
  },
  {
    id: 'trading',
    title: 'Trading Engine',
    description:
      'Jump into the DeFi terminal, staking flows, and autonomous market operations.',
    to: '/defi',
    cta: 'Open Trading tools',
  },
  {
    id: 'goalchain',
    title: 'GoalChain Soccer',
    description:
      'Enter the core SportsFi experience for squad management, fixtures, and protocol gameplay.',
    to: '/',
    cta: 'Open GoalChain',
  },
];

export function Ventures() {
  return (
    <div className="play-page play-page--grid">
      <div className="play-page-hero play-page-hero--compact">
        <h1>Ventures Portal</h1>
        <p className="play-page-sub">
          A single launch surface for the four active GoalWorld verticals.
        </p>
      </div>

      <main className="play-page-main play-page-main--left">
        <section
          style={{
            display: 'grid',
            gap: '1rem',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          }}
        >
          {VENTURE_CARDS.map((card) => (
            <article
              key={card.id}
              style={{
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '20px',
                padding: '1.25rem',
                background: 'rgba(15, 23, 42, 0.6)',
                boxShadow: '0 18px 40px rgba(15, 23, 42, 0.35)',
                minHeight: '180px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1rem',
              }}
            >
              <div>
                <p style={{ margin: 0, color: '#14f195', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                  {card.id}
                </p>
                <h2 style={{ margin: '0.4rem 0 0.75rem', fontSize: '1.35rem' }}>{card.title}</h2>
                <p style={{ margin: 0, color: '#cbd5e1', lineHeight: 1.6 }}>{card.description}</p>
              </div>

              <Link
                to={card.to}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  alignSelf: 'flex-start',
                  padding: '0.8rem 1rem',
                  borderRadius: '999px',
                  background: 'linear-gradient(135deg, #14f195, #0ea5e9)',
                  color: '#04111f',
                  fontWeight: 800,
                  textDecoration: 'none',
                }}
              >
                {card.cta}
              </Link>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}

export default Ventures;
