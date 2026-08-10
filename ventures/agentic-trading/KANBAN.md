# Kanban: Agentic Trading Engine

Tablero de desarrollo para la vertical de Trading Autónomo, Whale Tracking y Arbitraje.

## Tareas

### 🟢 In Progress
- [ ] **GW-TRADING-001 — Risk Limits Config**
  - *Prioridad*: Crítica
  - *Descripción*: Definir los límites de riesgo máximos (drawdown, stop-loss, exposición por token) en un archivo JSON consumido por los scripts de ejecución.
  - *Entregable*: `data/trading/risk_limits.json`

### 🟡 Ready
- [ ] **GW-TRADING-002 — OKX API Connector**
  - *Prioridad*: Alta
  - *Descripción*: Implementar el conector seguro con la API de OKX y realizar pruebas de conectividad y firma de transacciones en el VPS.

### 🔍 Discovery
- [ ] **GW-TRADING-003 — Whale Tracker**
  - *Descripción*: Investigar APIs y webhooks (Helius, Birdeye, etc.) para el monitoreo en tiempo real de smart money en Solana.
- [ ] **GW-TRADING-004 — DEX Spread Monitor**
  - *Descripción*: Diseñar el monitor de spreads para arbitraje entre Raydium y Meteora.
