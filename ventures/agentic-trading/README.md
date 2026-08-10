# Vertical: Agentic Trading Engine

Esta vertical se enfoca en el desarrollo y operación de agentes autónomos de trading e inteligencia de mercado sobre Solana y exchanges centralizados (OKX).

## 🎯 Misión
Desplegar agentes de Hermes especializados en el análisis de sentimiento social, rastreo de flujos on-chain (Whale Tracking) y ejecución de estrategias de arbitraje y provisión de liquidez, operando bajo estrictos controles de riesgo automatizados.

## 🛠️ Componentes y Flujo de Datos
1. **Market Intelligence (X-Scout / Radar):** Agentes que escanean X (Twitter) y foros de investigación para detectar tendencias tempranas y sentimiento de mercado.
2. **On-Chain Tracker:** Módulos en Python que monitorean pools de Raydium/Meteora y transferencias de billeteras marcadas como "smart money".
3. **Execution Gateway:** Conectores seguros con la API de OKX y RPCs de Solana para enviar transacciones firmadas de forma rápida.
4. **Risk Controller:** Módulo de seguridad local que valida límites de exposición, stop-loss y balance de colateral antes de autorizar cualquier transacción.

## 📋 Backlog Inmediato
- [ ] Configurar el set de herramientas de trading (`trader` toolset) en el perfil de Hermes correspondiente.
- [ ] Implementar un script de monitoreo de spreads en DEXs de Solana en `scripts/trading/dex_spread_monitor.py`.
- [ ] Definir el archivo de configuración de límites de riesgo en `data/trading/risk_limits.json`.
