import os
import requests

def test_infrastructure():
    print("Verificando infraestructura...")
    
    # 1. Test de Paquetes (E2B)
    try:
        import e2b
        import e2b_code_interpreter
        print("✅ Paquetes E2B instalados.")
    except ImportError as e:
        print(f"❌ Fallo paquete E2B: {e}")

    # 2. Test de Conectividad con el "Músculo" (Modal)
    print("Iniciando Modal Factory (Asset Gen)...")
    MODAL_ENDPOINT = "https://nico--gw-video-factory.modal.run"
    try:
        response = requests.post(f"{MODAL_ENDPOINT}/generate_video", json={"prompt": "test", "seed": 1})
        if response.status_code == 200 or response.status_code == 405:
            print("✅ Modal Factory operativo.")
        else:
            print(f"⚠️ Modal Factory respondió con error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando a Modal: {str(e)}")

if __name__ == "__main__":
    test_infrastructure()
