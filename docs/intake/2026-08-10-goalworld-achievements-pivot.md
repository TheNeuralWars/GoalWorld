# Registro de Decisión: Pivot Estratégico GoalWorld (Mundo de Logros)

- **Fecha:** 2026-08-10
- **Autor:** GoalWorld Manager (Hermes)
- **Aprobado por:** Nico (CEO)

---

## 1. Contexto y Problema
El repositorio de GoalWorld nació originalmente bajo el nombre de GoalChain, enfocado de forma exclusiva en un simulador de fútbol manager Web3 con una economía circular basada en el token $GCH y NFTs de futbolistas. 

Aunque el desarrollo técnico de esta vertical está avanzado (Penalty Beta en devnet, contratos Anchor listos, oráculo de datos deportivos operativo), centrar toda la marca y el esfuerzo de desarrollo en el fútbol limita el potencial de la infraestructura construida (flota de agentes Hermes, OmniRoute, gBrain, automatización de video).

## 2. Decisión
Reorientar la marca **GoalWorld** para que signifique **"World of Achievements" (Mundo de Logros)**. 
- GoalWorld se convierte en una **"Hoja en Blanco" (Venture Studio / Sandbox)** para el desarrollo de múltiples side-projects impulsados por IA y Solana.
- El fútbol manager original se renombra lógicamente como **GoalChain Soccer** y se relega a un **side-project** dentro del portafolio general.
- Se priorizan tres nuevas verticales creativas y financieras para su desarrollo inmediato.

## 3. Estructura del Portafolio (Ventures)
Se establece la taxonomía oficial de proyectos en el directorio `ventures/`:

1. **Publisher Lore & IP Tokenizer:** Generación de sagas literarias con IA, exportación a Amazon KDP (EPUB/PDF) y tokenización de propiedad intelectual en Solana.
2. **AI Cinema & Media Engine:** Producción de cortometrajes y trailers a partir de los guiones del Lore Engine, renderizados en el VPS y distribuidos en redes sociales.
3. **Agentic Trading Engine:** Operaciones autónomas de trading, Whale Tracking y arbitraje en DEXs de Solana y OKX.
4. **GoalChain Soccer (Side-Project):** El juego de fútbol manager Web3 original.

## 4. Acciones Técnicas Ejecutadas
1. Creación de la carpeta `ventures/` con READMEs detallados para cada vertical.
2. Actualización de `README.md` y `INDEX.md` en la raíz para reflejar la nueva estructura de portafolio.
3. Actualización de `CLAUDE.md` y `AGENTS.md` para reorientar el comportamiento de los agentes de IA (evitando que asuman que todo es fútbol).
4. Limpieza de tablas malformadas en la documentación de infraestructura.
5. Commit local de los cambios en la rama activa.

## 5. Próximos Pasos
- Adaptar la interfaz de la webapp (`webapp/`) para que actúe como un portal de navegación de side-projects.
- Diseñar el primer pipeline de generación de Lore en `ai_context/`.
- Configurar el set de herramientas de trading en el perfil de Hermes correspondiente.
