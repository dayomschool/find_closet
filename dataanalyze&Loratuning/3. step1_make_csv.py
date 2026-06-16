import os
import pandas as pd

crop_root = "./Crop_Data_Detailed"
categories = ["top", "bottom", "dress"]
data_list = []

print("📊 크롭된 이미지와 텍스트를 하나의 교과서(CSV)로 통합하는 중...")

for cat in categories:
    cat_dir = os.path.join(crop_root, cat)
    if not os.path.exists(cat_dir): continue
    
    # 이미지 파일만 골라내기
    img_files = [f for f in os.listdir(cat_dir) if f.lower().endswith('.jpg')]
    
    for img_name in img_files:
        pure_name = os.path.splitext(img_name)[0]
        txt_name = f"{pure_name}.txt"
        
        img_path = os.path.join(cat_dir, img_name)
        txt_path = os.path.join(cat_dir, txt_name)
        
        # 짝이 맞는 텍스트 파일이 있을 때만 가로 한 줄로 기록
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                caption = f.read().strip()
            
            data_list.append({
                "image_path": img_path,
                "caption": caption
            })

# CSV 파일로 단정하게 저장
df = pd.DataFrame(data_list)
df.to_csv("./train_dataset.csv", index=False, encoding="utf-8-sig")
print(f"🚀 통합 완료! 총 {len(df)}개의 완벽한 훈련 가이드가 'train_dataset.csv'로 저장되었습니다.")