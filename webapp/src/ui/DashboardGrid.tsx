import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { EconomyConfigBanner } from './EconomyConfigBanner';
import { OpsStatusPanel } from './OpsStatusPanel';
import { SimulationBadge } from '../components/SimulationBadge';
import { useUser } from '../contexts/UserContext';
import { useTranslation } from '../i18n';

export function DashboardGrid() {
  const navigate = useNavigate();
  const { user } = useUser();
  const { t } = useTranslation();
  const [showOpsConsole, setShowOpsConsole] = useState(false);

  return (
    <div className="inicio-portal">
      <EconomyConfigBanner />
      {/* Welcome Hero Banner */}
      <div className="welcome-hero glass-card portal-fade-in">
        <div className="welcome-hero-content">
          <div className="welcome-hero-badge">🏆 SPORTSFI PROTOCOL V2.0</div>
          <h1>
            {user ? (
              <>
                ¡Hola, <span className="text-neon-green">{user.avatar} @{user.username}</span>!
              </>
            ) : (
              'Bienvenido a goalworld'
            )}
          </h1>
          <p className="welcome-hero-sub">
            Dirige tu club, haz apuestas deportivas on-chain con el cronista IA y opera liquidez con nuestro DeFi Swarm de agentes autónomos.
          </p>
          {!user && (
            <Link to="/club" className="btn-neon-green welcome-hero-btn">
              ✨ Configurar mi Manager
            </Link>
          )}
        </div>
        <div className="welcome-hero-stats">
          <div className="hero-stat-box">
            <span className="hero-stat-val">1240</span>
            <span className="hero-stat-label">Managers Activos <SimulationBadge label="demo" /></span>
          </div>
          <div className="hero-stat-box">
            <span className="hero-stat-val text-neon-purple">$2.4M</span>
            <span className="hero-stat-label">Volumen Total <SimulationBadge label="demo" /></span>
          </div>
        </div>
      </div>

      {/* Developer Ops Collapsible Panel */}
      <div className="ops-collapsible-wrapper glass-card">
        <button 
          onClick={() => setShowOpsConsole(prev => !prev)}
          className="ops-toggle-btn"
          aria-expanded={showOpsConsole}
        >
          <span className="ops-toggle-dot"></span>
          <span className="ops-toggle-label">Consola de Operaciones &amp; Estado del Protocolo</span>
          <span className="ops-toggle-chevron">{showOpsConsole ? '▲ Ocultar' : '▼ Mostrar Detalles de Devnet'}</span>
        </button>
        {showOpsConsole && (
          <div className="ops-collapsible-content portal-fade-in">
            <OpsStatusPanel />
          </div>
        )}
      </div>

      {/* Core Portals Launcher Grid */}
      <div className="launcher-grid">
        {/* Estadio Card */}
        <div className="launcher-card glass-card card-hover-stadium" onClick={() => navigate('/estadio')}>
          <div className="launcher-card-header">
            <div className="launcher-card-icon">🏟️</div>
            <div className="launcher-card-badge">PORTAL ACTIVO</div>
          </div>
          <h3>Stadium — Bet</h3>
          <p>
            One job: place a World Cup fixture bet on Solana devnet. Paper only. Not mainnet. No real-money copy.
          </p>
          <div className="launcher-card-footer">
            <span className="launcher-card-status">Devnet / paper</span>
            <span className="launcher-card-btn text-neon-green">Place a bet →</span>
          </div>
        </div>

        {/* DeFi Card */}
        <div className="launcher-card glass-card card-hover-defi" onClick={() => navigate('/defi')}>
          <div className="launcher-card-header">
            <div className="launcher-card-icon">💱</div>
            <div className="launcher-card-badge launcher-card-badge--defi">DEFI SWARM</div>
            <SimulationBadge />
          </div>
          <h3>DeFi Terminal</h3>
          <p>
            Negocia tokens con Vibe Swap, configura bots automatizados de arbitraje y deposita en las bóvedas de rendimiento Swarm para generar retornos del protocolo.
          </p>
          <div className="launcher-card-footer">
            <span className="launcher-card-status text-neon-purple">TVL demo (simulación)</span>
            <span className="launcher-card-btn text-neon-purple">Operar DeFi →</span>
          </div>
        </div>

        {/* Mi Club Card */}
        <div className="launcher-card glass-card card-hover-club" onClick={() => navigate('/club')}>
          <div className="launcher-card-header">
            <div className="launcher-card-icon">👕</div>
            <div className="launcher-card-badge launcher-card-badge--club">MI CLUB</div>
          </div>
          <h3>Mi Club &amp; Squad</h3>
          <p>
            Administra tu plantilla completa de jugadores estrella (NFTs), mejora sus habilidades de juego, personaliza tu perfil de Manager y sube en los rangos globales.
          </p>
          <div className="launcher-card-footer">
            <span className="launcher-card-status">
              {user ? `Rol: ${user.role}` : 'Sin Cuenta Creada'}
            </span>
            <span className="launcher-card-btn text-neon-red">Ver Mi Club →</span>
          </div>
        </div>

        {/* Hub Completo Card */}
        <div className="launcher-card glass-card card-hover-hub" onClick={() => navigate('/hub')}>
          <div className="launcher-card-header">
            <div className="launcher-card-icon">🗂️</div>
            <div className="launcher-card-badge" style={{ background: 'rgba(20,241,149,0.15)', color: '#14f195' }}>HUB ALPHA</div>
          </div>
          <h3>Hub Completo</h3>
          <p>
            Vista de navegación rápida hacia todos los módulos del protocolo: fixtures, trading, squad, vaults, cronista IA y más.
          </p>
          <div className="launcher-card-footer">
            <span className="launcher-card-status text-neon-green">Todos los módulos</span>
            <span className="launcher-card-btn text-neon-green">Explorar Hub →</span>
          </div>
        </div>
      </div>

      {/* GW-XSC-001: canned matchday tweets — FICTION until a real radar markdown is wired */}
      <div className="xscout-stream glass-card" data-xscout-source="fiction">
        <div className="xscout-stream-header">
          <div className="xscout-badge xscout-badge--fiction">
            🤖 X-SCOUT · {t('xscout_fiction_badge')}
          </div>
          <SimulationBadge label={t('xscout_fiction_badge')} />
          <h3>{t('xscout_stream_title')}</h3>
          <p>{t('xscout_stream_desc')}</p>
        </div>
        <div className="xscout-stream-content">
          <div className="xscout-post xscout-post--fiction">
            <div className="xscout-post-meta">
              <span className="xscout-avatar">🕵️‍♂️</span>
              <span className="xscout-username">@x-scout_bot</span>
              <span className="xscout-fiction-chip">{t('xscout_fiction_badge')}</span>
              <span className="xscout-time">{t('xscout_post_time')}</span>
            </div>
            <p className="xscout-post-text">{t('xscout_post_1_text')}</p>
          </div>
          <div className="xscout-post xscout-post--fiction">
            <div className="xscout-post-meta">
              <span className="xscout-avatar">🕵️‍♂️</span>
              <span className="xscout-username">@x-scout_bot</span>
              <span className="xscout-fiction-chip">{t('xscout_fiction_badge')}</span>
              <span className="xscout-time">{t('xscout_post_time')}</span>
            </div>
            <p className="xscout-post-text">{t('xscout_post_2_text')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
