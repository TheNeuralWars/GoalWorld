import os
import requests
import json
import urllib.parse
import base64
from e2b import Sandbox

# API Keys e infraestructuras registradas en OmniRoute
E2B_API_KEY = "e2b_d0d079401ffcfe6a65f600dcf7137fef463cec30"
MODAL_GEN_ENDPOINT = "https://glimoorglandor--gw-video-factory-videofactory-generate-video.modal.run"
POLLINATIONS_URL = "https://image.pollinations.ai/p/"

def run_hybrid_pipeline():
    print("🚀 Iniciando Pipeline Híbrido Optimizado para Costo-Cero...")
    
    # 1. Prompt de imagen base (Pollinations)
    prompt = "Detailed horizontal shot of a futuristic soccer stadium at night, stadium lights, neon green pitch, cyberpunk sports arena, hyper-detailed, 8k resolution"
    print(f"Prompt base: '{prompt}'")
    
    # FASE 1: Generación de la imagen base de alta fidelidad en Pollinations
    print("🎨 [Fase 1] Generando imagen de partida nítida en Pollinations...")
    encoded_prompt = urllib.parse.quote(prompt)
    draft_url = f"{POLLINATIONS_URL}{encoded_prompt}?width=1024&height=576&seed=1337&nologo=true"
    
    try:
        response = requests.get(draft_url, timeout=30)
        if response.status_code == 200:
            image_data = response.content
            print("✅ Imagen base de alta fidelidad generada y descargada.")
            local_draft_path = "/data/apps/GoalWorld/scripts/video_automation/output/pollinations_high_res.jpg"
            os.makedirs(os.path.dirname(local_draft_path), exist_ok=True)
            with open(local_draft_path, "wb") as f:
                f.write(image_data)
        else:
            print(f"❌ Error en Pollinations ({response.status_code}).")
            return
    except Exception as e:
        print(f"❌ Error conectando a Pollinations: {str(e)}")
        return

    # Convertimos la imagen recibida a Base64 para mandársela a Modal
    image_b64 = base64.b64encode(image_data).decode("utf-8")

    # FASE 2: Animación en Modal (Vídeo real con GPU A10G usando la imagen base)
    print("\n🎥 [Fase 2] Enviando imagen base en Base64 a Modal para animación SVD...")
    try:
        # Enviamos la imagen para animar vía payload JSON
        response = requests.post(
            MODAL_GEN_ENDPOINT, 
            json={"image_b64": image_b64, "seed": 42}, 
            timeout=600
        )
        if response.status_code == 200:
            video_content = response.content
            print("✅ Inferencia de SVD en Modal completada desde la imagen de Pollinations.")
        else:
            print(f"❌ Fallo en Modal: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error conectando a Modal: {str(e)}")
        return

    # FASE 3: Composición final en Sandbox seguro de E2B
    print("\n🧠 [Fase 3] Inicializando Sandbox seguro de E2B...")
    try:
        with Sandbox.create(api_key=E2B_API_KEY) as sandbox:
            print("  - Sandbox de E2B levantada con éxito.")
            
            # Instalar FFmpeg en la sandbox
            print("  - Instalando FFmpeg en la sandbox...")
            sandbox.commands.run("sudo apt-get update && sudo apt-get install -y ffmpeg")
            
            # Subir el video de Modal a la sandbox
            print("  - Subiendo video de Modal a la sandbox...")
            sandbox.files.write(path="/home/user/input.mp4", data=video_content)
            
            # Codificación Final Optimizado
            print("  - Ejecutando composición de FFmpeg en la sandbox...")
            ffmpeg_cmd = "ffmpeg -y -i /home/user/input.mp4 -vcodec libx264 -crf 23 -pix_fmt yuv420p /home/user/output.mp4"
            
            render_res = sandbox.commands.run(ffmpeg_cmd)
            if render_res.exit_code != 0:
                print(f"❌ Error en composición de FFmpeg: {render_res.stderr}")
                return
                
            print("  - Composición optimizada de FFmpeg finalizada con éxito.")
            
            # Descargamos
            final_video_bytes = sandbox.files.read("/home/user/output.mp4", format="bytes")
            
            output_vps_path = "/data/apps/GoalWorld/scripts/video_automation/output/gw_hybrid_production.mp4"
            with open(output_vps_path, "wb") as f:
                f.write(final_video_bytes)
                
            print(f"\n🎉 ¡INFRAESTRUCTURA HÍBRIDA VERIFICADA DE PUNTA A PUNTA!")
            print(f"Video generado y guardado en: {output_vps_path}")
            
    except Exception as e:
        print(f"❌ Error en fase de composición E2B: {str(e)}")

if __name__ == "__main__":
    run_hybrid_pipeline()
