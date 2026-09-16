# Kanban: Agentic Trading Engine

Tablero de desarrollo para la vertical de Trading Autónomo, Whale Tracking y Arbitraje.

## Tareas

### ✅ Done
- [x] **GW-TRADING-001 — Risk Limits Config**
  - *Prioridad*: Crítica
  - *Descripción*: Definir los límites de riesgo máximos (drawdown, stop-loss, exposición por token) en un archivo JSON consumido por los scripts de ejecución.
  - *Entregable*: `data/trading/risk_limits.json`
  - *Estado*: Completado (v1.1.0) — límites globales, por token (SOL/USDC/GCH/BTC/ETH), reglas de ejecución y checks del Risk Controller.

### 🟡 Ready
- [ ] **GW-TRADING-002 — OKX API Connector**
  - *Prioridad*: Alta
  - *Descripción*: Implementar el conector seguro con la API de OKX y realizar pruebas de conectividad y firma de transacciones en el VPS.

### 🔍 Discovery
- [x] **GW-TRADING-003 — Whale Tracker**
  - *Descripción*: Investigar APIs y webhooks (Helius, Birdeye, etc.) para el monitoreo en tiempo real de smart money en Solana.
  - *Entregable*: `ventures/agentic-trading/research_whale_tracker.md`
- [x] **GW-TRADING-004 — DEX Spread Monitor**
  - *Descripción*: Diseñar el monitor de spreads para arbitraje entre Raydium y Meteora.
  - *Entregables*:
    - `ventures/agentic-trading/research_dex_spread_monitor.md` (Documento de diseño y análisis)
    - `scripts/trading/dex_spread_monitor.py` (Script prototipo de monitoreo)
