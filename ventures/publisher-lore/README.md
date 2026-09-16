# Vertical: Publisher Lore & IP Tokenizer

Esta vertical se enfoca en la creación artística literaria asistida por IA y su posterior tokenización en Solana como activos de propiedad intelectual (IP Assets).

## 🎯 Misión
Permitir la generación autónoma de universos narrativos complejos (sagas de fantasía, ciencia ficción, lore de juegos), su compilación en formatos profesionales listos para publicación física/digital (Amazon KDP EPUB/PDF), y la distribución de su propiedad intelectual mediante contratos inteligentes en Solana.

## 🛠️ Componentes y Flujo de Datos
1. **Lore Engine:** Agentes de Hermes especializados en escritura creativa que generan personajes, tramas y capítulos de forma estructurada en `ai_context/`.
2. **KDP Compiler:** Scripts de compilación que toman el Markdown de los agentes y generan archivos EPUB y PDF listos para imprenta, aplicando hojas de estilo profesionales.
3. **Solana IP Registry:** Contratos en Solana que registran el hash de la obra literaria y emiten tokens de copropiedad o licencias de uso digital.

## 📋 Backlog Inmediato
- [ ] Diseñar el esquema de metadatos para personajes y tramas en `ai_context/lore_schema.json`.
- [ ] Crear script de compilación Markdown → EPUB usando librerías de Python en el VPS.
- [ ] Definir el estándar de contratos para IP Assets en Solana (basado en Metaplex Core o estándares de licencia on-chain).
