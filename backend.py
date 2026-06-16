import os
import torch
import faiss
import json
import shutil
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGE_DIR = os.path.join(DATA_DIR, "images")
FAISS_DIR = os.path.join(DATA_DIR, "faiss")
LORA_DIR = os.path.join(BASE_DIR, "models", "lora")

base_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

if os.path.exists(os.path.join(LORA_DIR, "adapter_config.json")):
    from peft import PeftModel
    model = PeftModel.from_pretrained(base_model, LORA_DIR).to(device)
    print("LoRA 모델 로드 완료!")
else:
    model = base_model.to(device)
    print("기본 CLIP 모델 로드 완료! (LoRA 없음)")

model.eval()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FASHION_ATTRIBUTES = {
    "스타일": ["retro", "romantic", "modern", "street", "sporty", "classic", "feminine", "tomboy", "sexy"],
    "부위": ["top", "bottom", "dress"],
    "종류": ["cardigan", "knit", "dress", "blouse", "shirt", "skirt", "jacket", "jeans", "coat", "top", "t-shirt"],
    "핏": ["normal fit", "loose fit", "skinny fit", "oversized", "wide fit", "tight fit"],
    "기장": ["crop", "normal length", "half length", "midi length", "mini length", "long length", "maxi length"],
    "색상": ["gray", "green", "navy", "red", "beige", "brown", "black", "blue", "yellow", "white", "pink"],
    "소재": ["cotton", "denim", "knit", "wool", "leather", "linen", "polyester", "silk", "fleece", "corduroy"],
}

KEYWORD_PICK_COUNTS = {
    "스타일": "1~2개",
    "부위": "0~1개",
    "종류": "1~2개",
    "핏": "0~1개",
    "기장": "0~1개",
    "색상": "0~2개",
    "소재": "0~1개",
}

ALL_ATTRIBUTE_WORDS = {word.lower() for words in FASHION_ATTRIBUTES.values() for word in words}


def _load_index(cat_name):
    index_path = os.path.join(FAISS_DIR, f"{cat_name}_db.index")
    paths_path = os.path.join(FAISS_DIR, f"{cat_name}_paths.json")
    if os.path.exists(index_path) and os.path.exists(paths_path):
        index = faiss.read_index(index_path)
        with open(paths_path, encoding="utf-8") as f:
            paths = json.load(f)
        return index, paths
    return faiss.IndexFlatIP(512), []


index_top, top_paths = _load_index("top")
index_bottom, bottom_paths = _load_index("bottom")
index_dress, dress_paths = _load_index("dress")


def extract_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.get_image_features(**inputs)
    embedding = output.pooler_output if hasattr(output, "pooler_output") else output
    embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding.cpu().numpy()[0]


def get_text_embedding(query_text):
    inputs = processor(text=[query_text], return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        output = model.get_text_features(**inputs)
    embedding = output.pooler_output if hasattr(output, "pooler_output") else output
    embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding.cpu().numpy()


def classify_category(image_path):
    labels = ["a top or shirt or blouse", "pants or skirt or jeans", "a dress or one-piece"]
    cat_map = {0: "상의", 1: "하의", 2: "원피스"}
    image = Image.open(image_path).convert("RGB")
    inputs = processor(text=labels, images=image, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        cat = cat_map[probs.argmax().item()]
    return cat


def add_to_closet(image_path, filename):
    global index_top, index_bottom, index_dress
    global top_paths, bottom_paths, dress_paths

    category = classify_category(image_path)
    cat_eng = {"상의": "top", "하의": "bottom", "원피스": "dress"}[category]

    save_folder = os.path.join(IMAGE_DIR, category)
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, filename)
    shutil.copy(image_path, save_path)

    vec = extract_image_embedding(save_path)

    if cat_eng == "top":
        index_top.add(np.array([vec]).astype("float32"))
        top_paths.append(save_path)
        faiss.write_index(index_top, os.path.join(FAISS_DIR, "top_db.index"))
        with open(os.path.join(FAISS_DIR, "top_paths.json"), "w", encoding="utf-8") as f:
            json.dump(top_paths, f, ensure_ascii=False)
    elif cat_eng == "bottom":
        index_bottom.add(np.array([vec]).astype("float32"))
        bottom_paths.append(save_path)
        faiss.write_index(index_bottom, os.path.join(FAISS_DIR, "bottom_db.index"))
        with open(os.path.join(FAISS_DIR, "bottom_paths.json"), "w", encoding="utf-8") as f:
            json.dump(bottom_paths, f, ensure_ascii=False)
    else:
        index_dress.add(np.array([vec]).astype("float32"))
        dress_paths.append(save_path)
        faiss.write_index(index_dress, os.path.join(FAISS_DIR, "dress_db.index"))
        with open(os.path.join(FAISS_DIR, "dress_paths.json"), "w", encoding="utf-8") as f:
            json.dump(dress_paths, f, ensure_ascii=False)

    return category


def extract_fashion_keywords(query):
    categories_desc = "\n".join(
        f"- {name} ({KEYWORD_PICK_COUNTS[name]}): {', '.join(words)}"
        for name, words in FASHION_ATTRIBUTES.items()
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""너는 패션 키워드 추출기야. 아래 카테고리별 단어 목록에 있는 단어 중에서만 골라서 사용자 요청에 맞는 키워드를 추출해.
목록에 없는 단어나 새로운 표현은 절대 만들지 마. 카테고리별로 표시된 개수만큼만 골라.

{categories_desc}

사용자 요청: "{query}"

출력 형식: 선택한 단어만 콤마(,)로 구분한 한 줄로 출력해. 카테고리 이름, 설명, 다른 말은 절대 쓰지 마.""",
        }],
    )
    raw_keywords = [k.strip() for k in response.choices[0].message.content.strip().split(",")]
    keywords = [k for k in raw_keywords if k.lower() in ALL_ATTRIBUTE_WORDS]
    return keywords or raw_keywords


def search_category(query_text, index, paths, top_k=5):
    if index.ntotal == 0:
        return []
    top_k = min(top_k, index.ntotal)
    text_vec = get_text_embedding(query_text)
    scores, indices = index.search(text_vec, top_k)
    return [{"path": paths[idx], "score": float(score)} for score, idx in zip(scores[0], indices[0])]


def get_outfit_combinations(query, sel_top, sel_bottom, sel_dress):
    keywords = extract_fashion_keywords(query)
    text_query = ", ".join(keywords)
    result = {"keywords": keywords, "tops": [], "bottoms": [], "dresses": [], "combinations": []}

    if sel_top:
        result["tops"] = search_category(text_query, index_top, top_paths)
    if sel_bottom:
        result["bottoms"] = search_category(text_query, index_bottom, bottom_paths)
    if sel_dress:
        result["dresses"] = search_category(text_query, index_dress, dress_paths)

    for top in result["tops"]:
        for bottom in result["bottoms"]:
            result["combinations"].append({
                "top": top["path"],
                "bottom": bottom["path"],
                "score": (top["score"] + bottom["score"]) / 2,
            })

    result["combinations"].sort(key=lambda x: -x["score"])
    result["combinations"] = result["combinations"][:3]
    return result


def extract_clothing_attributes(image_path):
    result = {}
    image = Image.open(image_path).convert("RGB")
    for attr_name, labels in FASHION_ATTRIBUTES.items():
        inputs = processor(text=labels, images=image, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)
            best_idx = probs.argmax().item()
            result[attr_name] = labels[best_idx]
    return result
