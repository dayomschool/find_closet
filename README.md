# Find Closet

LoRA로 파인튜닝한 CLIP 임베딩과 FAISS 유사도 검색, Groq LLM 기반 키워드 추출을 결합한 개인 옷장 코디 추천 시스템입니다. 자연어로 원하는 스타일을 입력하면 내 옷장(상의/하의/원피스) 사진들 중에서 가장 잘 맞는 아이템과 코디 조합을 추천해줍니다.

## 실행 화면

**홈 화면** — 카테고리 선택 및 스타일 검색

![홈 화면](docs/screenshots/01_home.png)

**스타일 추천 결과** — 카테고리별(상의/하의/원피스) 추천 및 유사도 점수

| 상의 | 하의 | 원피스 |
|---|---|---|
| ![상의 결과](docs/screenshots/02_result_top.png) | ![하의 결과](docs/screenshots/03_result_bottom.png) | ![원피스 결과](docs/screenshots/04_result_dress.png) |

**최적 코디 조합 Top 3**

![코디 조합](docs/screenshots/05_outfit_combination.png)

**내 옷장 관리** — 등록된 아이템 목록

![옷장 관리](docs/screenshots/06_closet_manage.png)

**아이템 상세보기** — AI 속성 분석 (스타일/부위/종류/핏/기장/색상/소재)

![상세보기](docs/screenshots/07_item_detail.png)

**옷 추가하기** — 이미지 업로드 후 자동 분류

![옷 추가](docs/screenshots/08_item_upload.png)

## 개발 환경 및 의존성

- Python 3.10+
- 주요 라이브러리
  - `torch`, `transformers` — CLIP 모델 (openai/clip-vit-base-patch32) 추론
  - `peft` — LoRA 어댑터 로드
  - `faiss-cpu` — 임베딩 유사도 검색(인덱싱)
  - `groq` — LLM 기반 자연어 쿼리 → 패션 키워드 추출
  - `streamlit` — 웹 UI
  - 전체 의존성 및 검증된 버전은 [`requirements.txt`](requirements.txt) 참고

## 설치 및 실행 방법

### 1. 가상환경 생성 및 활성화

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 Groq API 키를 입력합니다.

```
GROQ_API_KEY=your_groq_api_key_here
```

### 4. LoRA 가중치 다운로드

LoRA 가중치 파일(`adapter_model.safetensors`)은 용량 문제로 Git 저장소에 포함되어 있지 않습니다. 아래 링크에서 다운로드해 `models/lora/` 폴더에 넣어주세요.

- 다운로드 링크: [Google Drive](https://drive.google.com/drive/folders/1EPzjlv0yKN5mgs0-Z1YqYp4KWHCA0KGZ)

`models/lora/` 폴더 구성:
```
models/lora/
├── adapter_config.json          (저장소에 포함됨)
└── adapter_model.safetensors    (다운로드 필요)
```

> LoRA 가중치가 없어도 앱은 동작합니다 — `models/lora/adapter_config.json`이 없으면 기본 CLIP 모델로 자동 폴백됩니다.

### 5. FAISS 인덱스 빌드

`data/images/{상의,하의,원피스}` 폴더에 옷 사진을 넣은 뒤 인덱스를 빌드합니다.

```bash
python build_index.py
```

`data/faiss/`에 카테고리별 인덱스(`*_db.index`)와 경로 목록(`*_paths.json`)이 생성됩니다.

### 6. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## 데이터 파이프라인

```
이미지 등록 (data/images/{상의,하의,원피스})
    ↓
LoRA-CLIP 이미지 임베딩 추출 (build_index.py / backend.add_to_closet)
    ↓
FAISS 인덱싱 (카테고리별 IndexFlatIP, data/faiss/)
    ↓
사용자 자연어 쿼리 입력 ("결혼식 하객룩 추천해줘" 등)
    ↓
Groq LLM 키워드 추출 (FASHION_ATTRIBUTES 딕셔너리 어휘로 제한)
    ↓
LoRA-CLIP 텍스트 임베딩 변환 후 FAISS 유사도 검색
    ↓
카테고리별 Top-K 추천 + 상의/하의 코디 조합 Top-3 생성
```

## 팀원 역할 분담

| 학번 | 이름 | 역할 |
|---|---|---|
| 20221012 | 정다영 | • 전체 코드 구현 (`app.py`, `backend.py`, `build_index.py`)<br>• Streamlit 프론트엔드 구성 (홈/검색 결과/옷장 관리 페이지)<br>• FAISS 인덱싱 파이프라인 구축<br>• Groq 기반 자연어 키워드 추출 로직 설계 (FASHION_ATTRIBUTES 어휘 제한)<br>• 로컬 개발 환경 구성 및 GitHub 저장소 관리·배포 |
| 20230745 | 유혜빈 | • 학습/검색용 의류 이미지 데이터 수집 및 전처리<br>• LoRA 기반 CLIP 파인튜닝 (모델 학습) |
