import os
import json
import random
import shutil
from collections import defaultdict

# ==========================================
# 1. 원본 데이터 및 결과 저장 경로 설정
# ==========================================
base_dir = "./Training"

src_base_paths = [
    os.path.join(base_dir, "원천데이터_1"),
    os.path.join(base_dir, "원천데이터_2"),
    os.path.join(base_dir, "원천데이터_3")
]
label_base_path = os.path.join(base_dir, "라벨링데이터")

# 완전히 새로 시작할 깨끗한 바구니 폴더 정의
sampled_output_img = "./샘플링데이터/원천"
sampled_output_json = "./샘플링데이터/라벨"

os.makedirs(sampled_output_img, exist_ok=True)
os.makedirs(sampled_output_json, exist_ok=True)

# ==========================================
# 2. 전수 스캔 및 라벨링 알맹이 기반 필터링
# ==========================================
print("🔄 [1단계] 원본 데이터 전수조사 및 라벨링 속성 검증 시작...")
style_to_files = defaultdict(list)

# 카테고리 매핑 규칙
category_mapping = {"상의": "top", "하의": "bottom", "원피스": "dress", "아우터": "top"}
total_scanned = 0

for src_path in src_base_paths:
    if not os.path.exists(src_path): continue
    
    for style_folder in os.listdir(src_path):
        style_dir = os.path.join(src_path, style_folder)
        if os.path.isdir(style_dir):
            
            # 한 스타일 폴더 내에서 연사(쌍둥이)를 묶기 위한 임시 딕셔너리
            sequence_dict = defaultdict(list)
            print(f"📂 [{style_folder}] 스타일 폴더 검사 중...")
            
            for img_name in os.listdir(style_dir):
                if img_name.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                    pure_name = os.path.splitext(img_name)[0]
                    
                    # 💡 뒤에 두세 자리만 다른 연사 사진을 한 묶음(Prefix)으로 잡기
                    if "-(" in pure_name:
                        prefix = pure_name.split("-(")[0]
                    elif "_" in pure_name:
                        prefix = pure_name.split("_")[0]
                    else:
                        prefix = pure_name[:-2] # 뒤의 두 자리 숫자를 날려서 묶음 키로 사용
                        
                    json_name = f"{pure_name}.json"
                    img_full_path = os.path.join(style_dir, img_name)
                    json_full_path = os.path.join(label_base_path, style_folder, json_name)
                    
                    if os.path.exists(json_full_path):
                        try:
                            with open(json_full_path, "r", encoding="utf-8") as f:
                                json_data = json.load(f)
                            
                            clothing_labels = json_data["데이터셋 정보"]["데이터셋 상세설명"]["라벨링"]
                            
                            has_valid_label = False
                            # 💡 렉트좌표는 안 보고, 라벨링 칸에 진짜 알맹이(색상, 기장 등)가 들어있는지 검사 ⭐
                            for kor_cat in category_mapping.keys():
                                label_list = clothing_labels.get(kor_cat, [{}])
                                if label_list and isinstance(label_list[0], dict) and len(label_list[0]) > 0:
                                    # 비어있는 {} 가 아니고 속성값이 채워져 있다면 유효 데이터로 인정!
                                    if any(k in label_list[0] for k in ["색상", "카테고리", "기장", "소재"]):
                                        has_valid_label = True
                                        break
                            
                            # 알맹이가 제대로 있는 진짜 정답지만 연사 바구니에 추가
                            if has_valid_label:
                                sequence_dict[prefix].append((img_full_path, json_full_path))
                        except:
                            continue
                    
                    total_scanned += 1
                    if total_scanned % 3000 == 0:
                        print(f"   ↳ ⏳ 현재까지 총 {total_scanned}장의 원본 이미지 라벨 검증 완료...")
            
            # 💡 [연사 차단 룰] 한 묶음(쌍둥이 세트)당 최대 3장만 무작위로 살리기 ⭐
            for prefix, model_pairs in sequence_dict.items():
                keep_count = min(len(model_pairs), 3)
                chosen_pairs = random.sample(model_pairs, keep_count)
                style_to_files[style_folder].extend(chosen_pairs)

# ==========================================
# 3. 스타일별 최종 3000장 샘플링 및 고속 복사
# ==========================================
print("\n📦 [2단계] 필터링 완료된 클린 데이터셋에서 스타일별 최종 3000장 추출 및 복사 시작...")
total_copied = 0

for style_name, pairs in style_to_files.items():
    style_img_out = os.path.join(sampled_output_img, style_name)
    style_json_out = os.path.join(sampled_output_json, style_name)
    os.makedirs(style_img_out, exist_ok=True)
    os.makedirs(style_json_out, exist_ok=True)
    
    # 완벽하게 필터링된 후보군 중 최종 3000장 랜덤 선택
    sampled_count = min(len(pairs), 3000)
    sampled_pairs = random.sample(pairs, sampled_count)
    
    print(f"  ▶ [{style_name}] 최종 선별된 {len(pairs)}장 중 {sampled_count}장 복사 중...")
    
    for img_path, json_path in sampled_pairs:
        try:
            img_name = os.path.basename(img_path)
            json_name = os.path.basename(json_path)
            
            shutil.copy(img_path, os.path.join(style_img_out, img_name))
            shutil.copy(json_path, os.path.join(style_json_out, json_name))
            total_copied += 1
        except:
            continue

print(f"\n🚀 [클린 샘플링 재구축 완료] 총 {total_copied}쌍의 완벽한 정제 데이터셋이 새로 복사되었습니다!")