# GoalWorld Ventures

GoalWorld es un **Mundo de Logros (World of Achievements)**: una incubadora de proyectos en blanco (Venture Studio) donde agentes autónomos de IA, infraestructura de Solana, IP creativa y automatización financiera se consolidan en side-projects independientes y monetizables.

El fútbol (GoalChain) ya no es la marca central del repositorio, sino una vertical especializada dentro de este portafolio.

---

## 🗺️ Mapa de Proyectos Activos

| Proyecto / Vertical | Propósito | Estado | Directorio / Código | Documentación |
| :--- | :--- | :--- | :--- | :--- |
| **Publisher Lore** | Escritura de sagas literarias con IA, exportación KDP (EPUB/PDF) y tokenización de IP en Solana. | Incubación | `ai_context/` | `[[ventures/publisher-lore/README.md]]` |
| **AI Cinema** | Producción de cortometrajes, trailers y storyboards a partir de sagas literarias generadas. | Incubación | `scripts/video_automation/` | `[[ventures/ai-cinema/README.md]]` |
| **Agentic Trading** | Agentes autónomos de Hermes operando en DEXs de Solana y CEXs (OKX) mediante Whale Tracking. | Operaciones | `scripts/` | `[[ventures/agentic-trading/README.md]]` |
| **GoalChain Soccer** | Juego de fútbol manager Web3 basado en 528 futbolistas reales (NFTs) y economía circular $GCH. | Side-Project / MVP | `contracts/`, `oracle/`, `webapp/`, `api/` | `[[ventures/goalchain-soccer/README.md]]` |

---

## ⚙️ Directrices de Desarrollo de la Flota de Agentes

1. **Independencia de Código:** No se deben mover físicamente los directorios de código existentes (`contracts/`, `oracle/`, `api/`, `webapp/`) de forma abrupta para no romper los despliegues de Vercel, PM2 o Anchor. La reestructuración es **lógica** a nivel de arquitectura de portafolio.
2. **Triage de Issues:** Cuando Nico o Lucas soliciten una tarea en `#dev-room`, el agente debe clasificarla primero en una de estas cuatro verticales y consultar su README correspondiente antes de codificar.
3. **Foco del Core:** Cualquier cambio en la infraestructura compartida (OmniRoute, base de datos de gBrain, configuraciones de Hermes) pertenece a la plataforma común de GoalWorld.
