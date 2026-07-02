#!/usr/bin/env python3
"""
brand_safety.py — Brand-safety vision check (face similarity).

Deploys InsightFace to detect faces in generated images and flags high-risk
similarities vs known professional footballers to protect social channels (TikTok, IG).
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Optional

SIMILARITY_THRESHOLD = float(os.getenv("BRAND_SAFETY_THRESHOLD", "0.55"))
KNOWN_PLAYERS = [
    "Lionel Messi", "Kylian Mbappé", "Cristiano Ronaldo",
    "Erling Haaland", "Vinícius Jr.", "Jude Bellingham",
    "Lamine Yamal", "Pedri", "Julián Álvarez",
]

EMBEDDINGS_FILE = Path("/home/ubuntu/hermes/brand_safety/players_embeddings.json")

def load_reference_embeddings() -> dict:
    """Load reference vectors for registered professional player faces."""
    if EMBEDDINGS_FILE.exists():
        try:
            with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Decode lists back to numpy arrays
                return {k: [np.array(v) for v in vs] for k, vs in data.items()}
        except Exception as e:
            print(f"[BrandSafety] Error reading reference embeddings catalog: {e}")
    return {}

def save_reference_embeddings(embeddings: dict):
    """Save reference vectors catalog."""
    EMBEDDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    serializable = {k: [v.tolist() for v in vs] for k, vs in embeddings.items()}
    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)

def register_player_face(player_name: str, image_path: str) -> bool:
    """Register a new player reference face vector into the catalog."""
    try:
        from insightface.app import FaceAnalysis
        import cv2
    except ImportError:
        print("[BrandSafety] InsightFace / OpenCV not installed. Cannot retrieve embedding.")
        return False

    img = cv2.imread(image_path)
    if img is None:
        print(f"[BrandSafety] Image path not found: {image_path}")
        return False

    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    faces = app.get(img)

    if not faces:
        print("[BrandSafety] No faces detected in reference image.")
        return False

    # Extract the largest face embedding
    face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    embedding = face.normed_embedding

    catalog = load_reference_embeddings()
    catalog.setdefault(player_name, []).append(embedding)
    save_reference_embeddings(catalog)
    print(f"[BrandSafety] Registered face embedding for {player_name} successfully.")
    return True

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot_prod = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_prod / (norm_v1 * norm_v2))

def check_image(image_path: Optional[Path]) -> dict:
    """Return brand-safety similarity verdict for a generated image.

    Checks detected faces mapping against known professional footballer faces embeddings.
    """
    if os.getenv("BRAND_SAFETY_ENABLED", "false").lower() != "true":
        return {"status": "skip", "reason": "BRAND_SAFETY_ENABLED=false"}

    if not image_path or not Path(image_path).exists():
        return {"status": "error", "reason": f"Image path '{image_path}' not found."}

    try:
        from insightface.app import FaceAnalysis
        import cv2
    except ImportError:
        return {"status": "skip", "reason": "deps not installed"}

    catalog = load_reference_embeddings()
    if not catalog:
        return {"status": "ok", "max_similarity": 0.0, "matched_player": None, "note": "No reference embeddings catalog found"}

    try:
        # Avoid downloading model inside loop by using pre-cached model dir if needed
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        
        img = cv2.imread(str(image_path))
        if img is None:
            return {"status": "error", "reason": "CV2 failed to decode image file"}
            
        faces = app.get(img)
        if not faces:
            return {"status": "ok", "max_similarity": 0.0, "matched_player": None, "note": "No face detected"}

        max_sim = 0.0
        best_match = None

        for face in faces:
            emb = face.normed_embedding
            for player, refs in catalog.items():
                for ref_emb in refs:
                    sim = cosine_similarity(emb, ref_emb)
                    if sim > max_sim:
                        max_sim = sim
                        best_match = player

        if max_sim >= SIMILARITY_THRESHOLD:
            return {
                "status": "blocked",
                "max_similarity": round(max_sim, 4),
                "matched_player": best_match,
                "reason": f"Likeness resemblance vs {best_match} ({max_sim:.2f}) exceeds safety limit ({SIMILARITY_THRESHOLD:.2f})."
            }

        return {
            "status": "ok",
            "max_similarity": round(max_sim, 4),
            "matched_player": best_match
        }

    except Exception as e:
        return {"status": "error", "reason": f"InsightFace engine check failed: {e}"}

if __name__ == "__main__":
    print(check_image(None))
