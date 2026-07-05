import os
import requests
import json
import urllib.parse
import sys
from e2b import Sandbox

# API Keys y Endpoints
E2B_API_KEY = os.environ.get("E2B_API_KEY")
if not E2B_API_KEY:
    print("❌ ERROR: E2B_API_KEY no configurado en el entorno.")
    sys.exit(1)

POLLINATIONS_URL = "https://image.pollinations.ai/p/"

def produce_video_e2e():
    print("🎨 1. Generando imagen base en Pollinations...")
    prompt_img = "Futuristic soccer player kicking a Solana-glowing digital football in a crowded virtual world cup stadium, highly detailed, neon sports cyberpunk, 9:16 vertical ratio"
    encoded_prompt = urllib.parse.quote(prompt_img)
    img_url = f"{POLLINATIONS_URL}{encoded_prompt}?width=1080&height=1920&seed=42&nologo=true"
    
    print(f"Descargando imagen desde: {img_url}")
    img_data = requests.get(img_url).content
    local_img_path = "/data/apps/GoalWorld/scripts/video_automation/output/test_pollinations_base.jpg"
    os.makedirs(os.path.dirname(local_img_path), exist_ok=True)
    with open(local_img_path, "wb") as f:
        f.write(img_data)
    print("✅ Imagen base guardada localmente.")

    print("\n🚀 2. Creando Sandbox de E2B...")
    sandbox = Sandbox.create(api_key=E2B_API_KEY)
    
    try:
        print("✅ Sandbox de E2B creado con éxito.")
        
        # 2.1 Instalar FFmpeg en la sandbox
        print("Instalando FFmpeg dentro de la sandbox...")
        sandbox.commands.run("sudo apt-get update && sudo apt-get install -y ffmpeg")
        print("✅ FFmpeg instalado en la sandbox.")
        
        # Subimos la imagen generada al sandbox
        print("Subiendo imagen base a la sandbox...")
        sandbox.files.write(path="/home/user/base.jpg", data=img_data)
        
        # Generamos un archivo de audio vacío en el sandbox
        print("Generando audio de prueba de 5 segundos...")
        sandbox.commands.run("ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 5 -q:a 9 /home/user/silence.mp3")
        
        # Generamos el video de forma ultra rápida (composición estática)
        print("🎥 3. Ejecutando composición de video con FFmpeg en la sandbox...")
        ffmpeg_cmd = (
            "ffmpeg -y -loop 1 -i /home/user/base.jpg -i /home/user/silence.mp3 "
            "-c:v libx264 -t 5 -pix_fmt yuv420p -c:a aac -shortest /home/user/output_composed.mp4"
        )
        
        render_res = sandbox.commands.run(ffmpeg_cmd)
        if render_res.exit_code != 0:
            print(f"❌ Error en Render de FFmpeg: {render_res.stderr}")
            return
            
        print("✅ Video renderizado con éxito dentro de la sandbox.")
        
        # Descargamos el video terminado de la sandbox al VPS (en formato bytes!)
        print("Descargando video final al VPS...")
        video_bytes = sandbox.files.read("/home/user/output_composed.mp4", format="bytes")
        
        output_path = "/data/apps/GoalWorld/scripts/video_automation/output/gw_e2e_video_composition.mp4"
        with open(output_path, "wb") as f:
            f.write(video_bytes)
            
        print(f"\n🎉 ¡PROCESO COMPLETADO! Video guardado en: {output_path}")
        
    finally:
        # Cerramos la sandbox
        sandbox.kill()
        print("Sandbox de E2B liberada.")

if __name__ == "__main__":
    produce_video_e2e()
