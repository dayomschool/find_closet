import os
import pandas as pd

base_training_path = "./Training"

if not os.path.exists(base_training_path):
    print(f"\n❌ [오류] '{base_training_path}' 폴더를 찾을 수 없습니다!")
else:
    print("\n📡 폴더 내부를 직접 순회하며 진짜 이미지 파일 전수조사를 시작합니다...")
    print("📂 대상 루트 폴더: ", os.path.abspath(base_training_path))
    
    style_file_counts = {}
    total_physical_images = 0
    valid_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
    
    for root, dirs, files in os.walk(base_training_path):
        image_files = [f for f in files if f.endswith(valid_extensions)]
        
        if len(image_files) > 0:
            style_name = os.path.basename(root)
            
            if style_name not in style_file_counts:
                style_file_counts[style_name] = 0
            style_file_counts[style_name] += len(image_files)
            total_physical_images += len(image_files)

    print("=" * 65)
    print(f"📊 [진짜 물리 원본 이미지 총합] 총 {total_physical_images:,} 장의 파일 존재")
    print("=" * 65)
    
    print("\n🔍 [폴더별 직접 카운트한 스타일별 실제 파일 수량]")
    print("-" * 65)
    print(f"{'스타일 폴더 명 (Style)':<25} | {'실제 파일 수량 (장)':<15} | {'비율 (%)':<10}")
    print("-" * 65)
    
    sorted_styles = sorted(style_file_counts.items(), key=lambda x: x[1], reverse=True)
    
    for style, count in sorted_styles:
        # 🔥 에러 패치 구간: 파이썬 순수 float 연산에 맞게 내장 함수 round()로 수정 완료!
        ratio = round((count / total_physical_images * 100), 2) if total_physical_images > 0 else 0
        print(f"{style:<25} | {count:<15,} | {ratio:<10}%")
        
    print("-" * 65)
    print(f"▶ 물리 파일 총합 검증 수량: {total_physical_images:,}장")
    print("=" * 65)
    
    summary_df = pd.DataFrame({
        'Style Folder Name': [x[0] for x in sorted_styles],
        'Physical File Count': [x[1] for x in sorted_styles],
        'Ratio (%)': [round((x[1] / total_physical_images * 100), 2) for x in sorted_styles]
    })
    summary_df.to_csv("./physical_files_summary.csv", index=False, encoding='utf-8-sig')
    print("\n💾 전수조사 성적표가 [physical_files_summary.csv] 파일로 자동 추출되었습니다!")