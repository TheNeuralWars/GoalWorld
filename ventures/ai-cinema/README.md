# Vertical: AI Cinema & Media Engine

Esta vertical se enfoca en la producción audiovisual y cinematográfica automatizada a partir de las sagas literarias y lore generados en el ecosistema GoalWorld.

## 🎯 Misión
Automatizar el pipeline de creación de trailers, cortometrajes y campañas de marketing visual utilizando modelos de difusión de imagen y video (Grok, ComfyUI, Luma, Runway) coordinados por agentes autónomos.

## 🛠️ Componentes y Flujo de Datos
1. **Screenplay Parser:** Toma las sagas literarias de la vertical de Lore y las convierte en guiones cinematográficos y descripciones de tomas (prompts visuales).
2. **Asset Generator:** Utiliza la OAuth de Grok y servidores de ComfyUI locales/remotos para generar imágenes consistentes de personajes y escenarios.
3. **Video Automation Daemon:** Daemon en PM2 (`hermes-video-daemon`) que compila las imágenes generadas, añade transiciones, música/efectos de sonido y genera el archivo MP4 final.
4. **Buffer Scheduler:** Publica automáticamente los videos generados en TikTok, Instagram Reels y YouTube Shorts optimizando los horarios de LATAM.

## 📋 Backlog Inmediato
- [ ] Integrar el generador de guiones en `scripts/video_automation/screenplay_generator.py`.
- [ ] Refinar el daemon de video para soportar transiciones dinámicas basadas en audio.
- [ ] Configurar el panel de control React en `play.goalworld.fun/marketing-control` para visualizar la cola de renders.
