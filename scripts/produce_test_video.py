import os
import requests
import sys

# Make sure e2b is installed and we have the api key
from e2b import Sandbox

def produce_video():
    print("🚀 Iniciando Pipeline de Video Autónomo...")
    
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        print("❌ ERROR: E2B_API_KEY no configurado en el entorno.")
        sys.exit(1)
        
    source_video_path = "/data/apps/GoalWorld/scripts/video_automation/output/grok_video_grok_img_1782370188_1_20260625_065249.mp4"
    if not os.path.exists(source_video_path):
        print(f"❌ ERROR: Video origen no encontrado en {source_video_path}")
        sys.exit(1)
        
    # 1. Generar activo visual rápido usando Pollinations AI
    print("🖼️ Generando overlay de marca usando Pollinations AI...")
    overlay_url = "https://image.pollinations.ai/p/text_goalworld_solana_neon_badge_cyberpunk_icon?width=300&height=100&nologo=true&seed=42"
    overlay_path = "/tmp/pollinations_overlay.png"
    
    try:
        response = requests.get(overlay_url)
        if response.status_code == 200:
            with open(overlay_path, "wb") as f:
                f.write(response.content)
            print("✅ Overlay generado y descargado en el VPS.")
        else:
            print(f"⚠️ Error descargando overlay de Pollinations: {response.status_code}. Usando fallback local...")
            # Fallback simple si falla la red
            overlay_path = None
    except Exception as e:
        print(f"❌ Error en Pollinations: {e}. Continuando sin overlay...")
        overlay_path = None

    # 2. Inicializar sandbox de E2B (El Cerebro de Edición)
    print("🧠 Inicializando sandbox de E2B...")
    try:
        with Sandbox(api_key=api_key) as sandbox:
            print("  - Sandbox inicializado con éxito.")
            
            # Subir video original al sandbox
            print("  - Subiendo video origen al sandbox E2B...")
            with open(source_video_path, "rb") as f:
                sandbox.files.write("input.mp4", f.read())
            print("  - Video subido.")
            
            # Subir overlay al sandbox si existe, y hacer el render.
            if overlay_path and os.path.exists(overlay_path):
                print("  - Subiendo overlay al sandbox E2B...")
                with open(overlay_path, "rb") as f:
                    sandbox.files.write("overlay.png", f.read())
                print("  - Overlay subido.")
                
                # Ejecutar composición con FFmpeg (overlay en la esquina superior izquierda [10:10])
                print("  - Ejecutando proceso de composición FFmpeg en el sandbox...")
                cmd = "ffmpeg -y -i input.mp4 -i overlay.png -filter_complex '[0:v][1:v] overlay=10:10' -codec:a copy output.mp4"
            else:
                # Composición simple (solo transcodificación/recorte para testing)
                print("  - Advertencia: Sin overlay. Ejecutando procesamiento directo en E2B...")
                cmd = "ffmpeg -y -i input.mp4 -t 5 -codec:v copy -codec:a copy output.mp4"
                
            # Ejecutar el comando
            process = sandbox.process.start(cmd)
            result = process.wait()
            
            if result.exit_code != 0:
                print(f"❌ ERROR: FFmpeg falló en E2B: {result.stderr}")
                sys.exit(1)
            print("✅ Composición FFmpeg finalizada con éxito.")
            
            # Descargar archivo resultante de la sandbox al destino del VPS
            output_destination = "/data/apps/GoalWorld/data/marketing_pipeline/gw_e2e_video_composition.mp4"
            print(f"📥 Descargando producto final del sandbox a {output_destination}...")
            video_bytes = sandbox.files.read("output.mp4")
            with open(output_destination, "wb") as f:
                f.write(video_bytes)
            print("🎉 Video finalizado y disponible localmente.")
            
    except Exception as e:
        print(f"❌ Fallo crítico en el pipeline E2B: {e}")
        sys.exit(1)

if __name__ == "__main__":
    produce_video()
