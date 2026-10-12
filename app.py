import modal
import os
from fastapi import FastAPI, Response

app = modal.App("gw-video-factory")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch", "diffusers", "accelerate", "xformers",
        "opencv-python-headless", "fastapi", "transformers", "safetensors"
    )
)

@app.cls(image=image, gpu="a10g", timeout=600)
class VideoFactory:
    @modal.enter()
    def load_pipelines(self):
        from diffusers import AutoPipelineForText2Image, StableVideoDiffusionPipeline
        import torch
        
        print("Cargando pipeline SDXL Turbo en GPU...")
        self.txt2img = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")
        
        print("Cargando pipeline SVD img2vid en GPU...")
        self.img2vid = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")
        self.img2vid.enable_model_cpu_offload()

    @modal.fastapi_endpoint(method="POST")
    def generate_video(self, data: dict):
        import torch
        import base64
        import io
        from PIL import Image
        from diffusers.utils import export_to_video
        import tempfile
        
        image_b64 = data.get("image_b64")
        seed = data.get("seed", 42)
        generator = torch.manual_seed(seed)
        
        if image_b64:
            print("Cargando imagen inicial provista en Base64...")
            image_data = base64.b64decode(image_b64)
            image_init = Image.open(io.BytesIO(image_data)).convert("RGB")
        else:
            prompt = data.get("prompt", "a futuristic soccer match in a cyberpunk stadium")
            print(f"Generando imagen inicial para: {prompt}")
            image_init = self.txt2img(
                prompt=prompt, 
                num_inference_steps=2, 
                guidance_scale=0.0,
                generator=generator
            ).images[0]
        
        # Redimensionado de precisión para SVD
        image_init = image_init.resize((1024, 576))
        
        # Ejecutar SVD con parámetros estables para evitar deformación
        print("Animando imagen inicial con SVD (Parámetros optimizados)...")
        frames = self.img2vid(
            image_init, 
            decode_chunk_size=8, 
            generator=generator,
            motion_bucket_id=80,      # Movimiento estable, menos distorsión
            noise_aug_strength=0.02,   # Conserva los límites nítidos de la imagen original
            num_inference_steps=25     # Pasos suficientes para estabilidad y nitidez
        ).frames[0]
        
        # Exportar a temporal
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            export_to_video(frames, tmp.name, fps=8)
            tmp.seek(0)
            video_bytes = tmp.read()
            
        os.remove(tmp.name)
        return Response(content=video_bytes, media_type="video/mp4")

    @modal.fastapi_endpoint(method="POST")
    def process_video(self, data: dict):
        return {"status": "processed", "result_url": "s3://goalworld-assets/final_video_xyz.mp4"}
