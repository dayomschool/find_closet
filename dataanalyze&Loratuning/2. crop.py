import os
import json
from PIL import Image

# ==========================================
# 1. 경로 설정
# ==========================================
base_dir = "./샘플링데이터"
img_input_root = os.path.join(base_dir, "원천")
json_input_root = os.path.join(base_dir, "라벨")

# 최종 결과물이 저장될 폴더
output_root = "./Crop_Data_Detailed"
categories = ["top", "bottom", "dress"]

for cat in categories:
    os.makedirs(os.path.join(output_root, cat), exist_ok=True)

# 아우터는 상의로 통합하는 매핑
category_mapping = {
    "상의": "top",
    "하의": "bottom",
    "원피스": "dress",
    "아우터": "top"
}

print("✂️ 세부 속성 추출 및 멀티 오브젝트 크롭을 시작합니다...")

total_cropped_count = 0
image_processed_count = 0

# ==========================================
# 2. 크롭 및 텍스트 라벨링 동시 진행
# ==========================================
for style_name in os.listdir(img_input_root):
    style_img_path = os.path.join(img_input_root, style_name)
    style_json_path = os.path.join(json_input_root, style_name)
    
    if not os.path.isdir(style_img_path): continue
    
    print(f"▶ 현재 스타일 분석 중: [{style_name}]")
    
    for img_name in os.listdir(style_img_path):
        if not img_name.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')): continue
        
        pure_name = os.path.splitext(img_name)[0]
        json_name = f"{pure_name}.json"
        
        img_full_path = os.path.join(style_img_path, img_name)
        json_full_path = os.path.join(style_json_path, json_name)
        
        if not os.path.exists(json_full_path): continue
        
        try:
            with Image.open(img_full_path) as img:
                img = img.convert("RGB")
                
                with open(json_full_path, "r", encoding="utf-8") as f:
                    label_data = json.load(f)
                
                # 렉트좌표와 라벨링 정보 가져오기
                rect_coords = label_data["데이터셋 정보"]["데이터셋 상세설명"]["렉트좌표"]
                clothing_labels = label_data["데이터셋 정보"]["데이터셋 상세설명"]["라벨링"]
                
                # 상의, 하의, 아우터, 원피스를 하나씩 검사
                for kor_cat, eng_cat in category_mapping.items():
                    coords = rect_coords.get(kor_cat, [{}])
                    details_list = clothing_labels.get(kor_cat, [{}]) # 색상, 기장, 소재 등이 들어있는 곳 ⭐
                    
                    for i, coord in enumerate(coords):
                        if isinstance(coord, dict) and "X좌표" in coord:
                            x, y = float(coord["X좌표"]), float(coord["Y좌표"])
                            w, h = float(coord["가로"]), float(coord["세로"])
                            
                            if w > 0 and h > 0:
                                # A. 이미지 크롭 및 저장
                                cropped_obj = img.crop((x, y, x + w, y + h))
                                
                                save_base_name = f"{style_name}_{pure_name}_{eng_cat}_{i}"
                                img_save_path = os.path.join(output_root, eng_cat, f"{save_base_name}.jpg")
                                txt_save_path = os.path.join(output_root, eng_cat, f"{save_base_name}.txt")
                                
                                cropped_obj.save(img_save_path, "JPEG", quality=95)
                                
                                # B. 💡 JSON에서 세부 속성 긁어와서 단정한 텍스트 문장 만들기
                                info_sentence = f"스타일: {style_name}, 부위: {kor_cat}"
                                
                                if i < len(details_list):
                                    det = details_list[i]
                                    # 색상, 기장, 카테고리, 소재 등 정보가 있으면 문장에 추가
                                    if "색상" in det and det["색상"]: info_sentence += f", 색상: {det['색상']}"
                                    if "기장" in det and det["기장"]: info_sentence += f", 기장: {det['기장']}"
                                    if "카테고리" in det and det["카테고리"]: info_sentence += f", 종류: {det['카테고리']}"
                                    if "핏" in det and det["핏"]: info_sentence += f", 핏: {det['핏']}"
                                    
                                    # 소재는 리스트 형태일 수 있으므로 처리
                                    if "소재" in det and det["소재"]:
                                        materials = ", ".join(det["소재"]) if isinstance(det["소재"], list) else det["소재"]
                                        info_sentence += f", 소재: {materials}"
                                
                                # C. 단정하게 정리된 한 줄 문장을 .txt 파일로 저장 ⭐
                                with open(txt_save_path, "w", encoding="utf-8") as txt_f:
                                    txt_f.write(info_sentence)
                                
                                total_cropped_count += 1
            
            image_processed_count += 1
            if image_processed_count % 1000 == 0:
                print(f"⏳ 진행 중: {image_processed_count}장 완료... (옷 조각 + 정답 텍스트 세트: {total_cropped_count}개)")

        except Exception as e:
            continue

print(f"\n🚀 세부 라벨링 텍스트 + 크롭 파이프라인 구축 완료!")
print(f"✅ 생성된 총 세트 수: {total_cropped_count}개 (이미지+텍스트 1:1 매칭)")
print(f"📁 저장 폴더: {os.path.abspath(output_root)}")