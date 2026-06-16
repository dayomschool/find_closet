"""
기존 이미지 폴더에서 FAISS 인덱스를 새로 빌드하는 스크립트.
구글 드라이브에서 이미지를 data/images/ 아래에 복사한 뒤 실행하세요.
"""
import os
import json
import numpy as np
import faiss
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")
FAISS_DIR = os.path.join(BASE_DIR, "data", "faiss")
LORA_DIR = os.path.join(BASE_DIR, "models", "lora")

os.makedirs(FAISS_DIR, exist_ok=True)
device = "cuda" if torch.cuda.is_available() else "cpu"

base_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

if os.path.exists(os.path.join(LORA_DIR, "adapter_config.json")) and os.path.exists(os.path.join(LORA_DIR, "adapter_model.safetensors")):
    from peft import PeftModel
    model = PeftModel.from_pretrained(base_model, LORA_DIR).to(device)
    print("LoRA 모델 사용")
else:
    model = base_model.to(device)
    print("기본 CLIP 모델 사용")

model.eval()

CATEGORIES = {"top": "상의", "bottom": "하의", "dress": "원피스"}

for cat_eng, cat_kor in CATEGORIES.items():
    folder = os.path.join(IMAGE_DIR, cat_kor)
    if not os.path.exists(folder):
        print(f"{cat_kor} 폴더 없음, 건너뜀")
        continue

    vectors, paths = [], []
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))]
    print(f"\n{cat_kor}: {len(files)}장 처리 중...")

    for filename in files:
        full_path = os.path.join(folder, filename)
        try:
            image = Image.open(full_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                output = model.get_image_features(**inputs)
            emb = output.pooler_output if hasattr(output, "pooler_output") else output
            emb = emb / emb.norm(dim=-1, keepdim=True)
            vectors.append(emb.cpu().numpy()[0])
            paths.append(full_path)
            print(f"  OK {filename}")
        except Exception as e:
            print(f"  FAIL {filename}: {e}")

    if vectors:
        index = faiss.IndexFlatIP(512)
        index.add(np.array(vectors).astype("float32"))
        faiss.write_index(index, os.path.join(FAISS_DIR, f"{cat_eng}_db.index"))
        with open(os.path.join(FAISS_DIR, f"{cat_eng}_paths.json"), "w", encoding="utf-8") as f:
            json.dump(paths, f, ensure_ascii=False, indent=2)
        print(f"  {cat_eng} 저장 완료 ({len(paths)}벌)")

print("\n완료!")
