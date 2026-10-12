# Vertical: GoalChain Soccer Manager (Side-Project)

Esta vertical alberga el desarrollo del juego de fútbol manager Web3 y su economía circular, consolidado como un side-project estratégico dentro del portafolio de GoalWorld.

## 🎯 Misión
Lanzar un simulador de fútbol manager donde los usuarios coleccionan y gestionan plantillas de **528 futbolistas reales** (NFTs), compiten en torneos y participan en una economía circular de "Zero Value Loss" respaldada por rendimientos de Liquid Staking en Solana.

## 🛠️ Componentes y Flujo de Datos
1. **Solana Smart Contracts (`contracts/`):** Programa Anchor que gestiona el minteo de jugadores, el staking en el Vault y la distribución de recompensas en $GCH.
2. **Sports Data Oracle (`oracle/`):** Sistema que recopila estadísticas de rendimiento real de los futbolistas para actualizar dinámicamente sus atributos en el juego.
3. **Transactional Play Webapp (`webapp/`):** Portal de juego React (`play.goalworld.fun`) donde los usuarios realizan apuestas en partidos, reclaman recompensas y gestionan su alineación.
4. **Ops API (`api/`):** Servidor Node.js que expone endpoints para la sincronización de datos del oráculo y métricas de la economía.

## 📋 Backlog Inmediato
- [ ] Mantener el Penalty Beta en Devnet para pruebas controladas de Nico y Lucas.
- [ ] Finalizar la optimización de tarifas de prioridad dinámica en `vault_crank.ts` usando Helius.
- [ ] Completar la localización al inglés de la interfaz de usuario de la webapp (Issue #296).
