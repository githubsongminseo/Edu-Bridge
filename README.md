# 시스템 안내 가이드 
# EDU-bridge 🌏

> **유아교육 현장 교사를 위한 AI 기반 지도안 자동 생성 플랫폼**
>
> 10개국 유아교육과정 데이터를 RAG로 검색해 수업 주제에 맞는 지도안 카드를 제안하고,
> 우리 유치원 양식(.docx)에 자동으로 채워주는 서비스입니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🎯 **Play-Scanner** | 키워드/사진 입력 → 10개국 교육과정 RAG 검색 → 지도안 카드 3장 제안 → 지도안 자동 생성 |
| 📋 **내 양식 자동 채우기** | .docx 양식 업로드 → AI 셀 의미 분석 → 지도안 내용 자동 채우기 → 수정 채팅 → .docx 다운로드 |
| 💌 **AI 알림장** | 활동 사진 + 메모 → 학부모 알림장 자동 생성 (톤 선택 가능) |
| 💬 **교사 커뮤니티** | 글쓰기·댓글·좋아요·수정·신고 |
| 🔐 **회원 시스템** | 로그인·마이페이지·구독 플랜·무료체험 14일 |
| 📁 **파일 보관함** | 양식 적용된 지도안 저장 및 이력 관리 |

---

## 🏗️ 시스템 구조

```
User input (키워드 / 사진)
    ↓
Frontend (HTML / CSS / Vanilla JS)
    ↓
Backend + FastAPI
    ├── POST /api/extract     키워드 추출 (Gemini Flash-Lite)
    ├── POST /api/cards       카드 생성 (RAG + Gemini Flash-Lite)
    └── POST /api/lesson      지도안 생성 (Gemini Flash)
         ↓
AI / RAG Pipeline
    Stage A : 키워드 추출       → Gemini Flash-Lite
    Stage B-D: RAG 검색         → ChromaDB (bge-m3) · 3-weight scoring
    Stage E : 카드 생성          → Gemini Flash-Lite
    Stage F : 지도안 생성        → Gemini Flash
         ↓
내 양식 파이프라인
    .docx 업로드 → 양식 분석 → 셀 매핑 → AI 채우기 → 미리보기/수정 → .docx 출력
```

**RAG 검색 가중치 수식**
```
S = a·max(C) + b·avg(C) + g·sim(q, P)
```
- `C` : 청크 코사인 유사도
- `q` : 쿼리 벡터
- `P` : 국가 철학 요약 벡터

---

## 🗂️ 폴더 구조

```
backend/
├── main.py                        # FastAPI 진입점 (전체 API 라우터)
├── database.py                    # SQLAlchemy 모델 (User, SavedLesson, ...)
├── auth.py                        # JWT 인증
├── requirements.txt
│
├── services/
│   ├── retriever.py               # 3-weight RAG 검색
│   ├── keyword_extractor.py       # Gemini 키워드 추출
│   ├── card_generator.py          # 지도안 카드 3장 생성
│   ├── lesson_planner.py          # 지도안 전문 생성
│   ├── template_analyzer.py       # .docx 양식 구조 분석 + AI 셀 채우기
│   ├── template_filler.py         # 셀 내용 채우기 (Gemini)
│   ├── template_parser.py         # .docx 파싱
│   ├── docx_writer.py             # .docx 출력
│   └── applied_template_service.py
│
├── static/
│   └── edu-bridge-full.html       # 단일 HTML 프론트엔드 (SPA)
│
├── data/
│   ├── all_chunks.json            # ChromaDB 적재용 (163개 청크, 10개국)
│   └── all_countries.json         # 국가별 철학 요약 + 메타데이터
│
├── data_level0.bin                # ChromaDB 벡터 인덱스
├── header.bin
├── length.bin
└── link_lists.bin
```

---

## ⚙️ 기술 스택

| 분류 | 기술 |
|------|------|
| Backend | FastAPI · Uvicorn · SQLite · SQLAlchemy |
| Frontend | Vanilla JS · HTML · CSS (Single HTML SPA) |
| AI | Gemini Flash · Gemini Flash-Lite (Google GenAI) |
| Vector DB | ChromaDB · bge-m3 (On-device 임베딩) |
| 문서 처리 | python-docx |
| 인증 | JWT (python-jose) |
| 외부 접속 | ngrok (베타) |

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
cd ~/Desktop/AI_system/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일 생성:

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_jwt_secret_key
```

### 3. 서버 실행

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 외부 접속 (ngrok)

```bash
ngrok http 8000 --request-header-add "ngrok-skip-browser-warning: true"
```

브라우저에서 `http://localhost:8000` 접속

---

## 📡 주요 API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/extract` | 키워드 추출 |
| POST | `/api/cards` | 지도안 카드 생성 |
| POST | `/api/lesson` | 지도안 생성 |
| POST | `/api/lessons/save` | 지도안 저장 |
| GET | `/api/lessons/my` | 내 지도안 목록 |
| POST | `/api/templates/upload` | 양식 업로드 |
| POST | `/api/lesson/preview-fills` | 양식 미리보기 |
| POST | `/api/applied-templates/save` | 양식 적용 파일 저장 |
| GET | `/api/applied-templates/all` | 파일 보관함 목록 |
| POST | `/api/community/posts` | 커뮤니티 글 작성 |
| GET | `/api/me` | 내 정보 |
| GET | `/api/me/subscription` | 구독 정보 |

전체 API 문서: `http://localhost:8000/docs`

---

## 🗄️ 데이터베이스

SQLite (`edubridge.db`) — 서버 첫 실행 시 자동 생성

| 테이블 | 설명 |
|--------|------|
| `users` | 회원 정보 · 구독 상태 |
| `saved_lessons` | 저장된 지도안 |
| `user_templates` | 업로드된 양식 |
| `applied_templates` | 양식 적용 이력 (파일 보관함) |
| `community_posts` | 커뮤니티 게시글 |
| `community_comments` | 댓글 |
| `community_likes` | 좋아요 |
| `notices` | 공지사항 |

---

## ⚠️ 현재 한계 및 향후 개선

| 한계 | 개선 방향 |
|------|-----------|
| ngrok 로컬 서버 → 서버 종료 시 중단 | AWS / Railway 클라우드 배포 전환 |
| hwp 양식 미지원 | LibreOffice 변환 파이프라인 도입 |
| Gemini JSON 파싱 오류 간헐 발생 | 자동 복구 로직 적용 완료 · 프롬프트 고도화 |
| 도메인 특화 어휘 불일치 (미술성 등) | LOV 기반 교육 온톨로지 어휘 확장 레이어 도입 |
| 10개국 163청크 | 국가 수 확장 · 최신 교육과정 주기적 업데이트 |

---

## 👥 팀

EDU-bridge 개발팀

---

*베타 버전 · 2026년 6월 기준*








# 초코소라빵 RAG 백엔드

10개국 유아교육과정 RAG 시스템의 백엔드.

## 폴더 구조

```
backend/
├── requirements.txt           # Python 패키지 목록
├── README.md                   # 이 파일
├── data/
│   ├── all_chunks.json        # ChromaDB 적재용 (163개 청크)
│   ├── all_countries.json     # 1차 가중치용 (10개국 메타+철학)
│   └── countries/             # 나라별 원본 JSON (참고용)
├── db/
│   ├── load_data.py           # ✅ 1단계: ChromaDB 적재
│   ├── quick_search_test.py   # ✅ 2단계: 적재 검증 (sanity check)
│   └── chroma_db/             # (자동 생성) 영속 벡터 DB
├── services/                  # (다음 단계)
│   ├── retriever.py           # 가중치 적용 검색 로직
│   ├── reranker.py            # LLM 재선별
│   ├── card_generator.py      # 카드 3장 생성
│   └── lesson_planner.py      # 지도안 생성
├── prompts/                   # (다음 단계) LLM 프롬프트 템플릿
└── main.py                    # (다음 단계) FastAPI 진입점
```

## 셋업 (최초 1회)

### 1. 가상환경 생성 + 패키지 설치

```bash
cd backend
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> ⚠ **주의**: `torch` 설치에 5분 정도 걸릴 수 있어요. CPU만 쓸 거라
> 굳이 CUDA 버전 받지 않아도 됩니다.

### 2. 데이터 파일 배치

`data/` 폴더에 다음 두 파일을 넣으세요:
- `all_chunks.json` (163개 청크)
- `all_countries.json` (10개국 메타+철학)

### 3. ChromaDB 적재

```bash
cd db
python load_data.py
```

**예상 소요 시간:**
- 첫 실행: 5~10분 (bge-m3 모델 약 2.3GB 다운로드 + 임베딩)
- 두 번째 실행부터: 1분 이내 (모델 캐싱됨)

성공하면 `db/chroma_db/` 폴더에 벡터 DB가 생성돼요.

### 4. 검색 sanity check

```bash
python quick_search_test.py
```

5개 테스트 쿼리에 대해 top-5 결과가 출력돼요. 다음과 같은 결과가 정상이에요:

- "원주민 문화와 자연을 연결한 야외 활동" → AUS(호주)가 상위
- "교육과 돌봄을 통합한 일상 속 학습" → FIN(핀란드)가 상위
- "100가지 언어로 자신의 생각을 표현하는 미술 활동" → ITA(이탈리아)가 상위

만약 **모든 쿼리에서 한 나라만 1등**이면 `weight_boost`나 청크 분포에 문제가 있는 거예요.
이때는 `merge_summary.md`의 "모니터링 포인트" 섹션 참고.

## 다음 단계

**[A] 적재 + 검증 ← 여기까지 완료하면 ✅ 데이터 준비 끝**

[B] 검색 함수 (`services/retriever.py`)
- 키워드 임베딩 → top-30 청크 검색
- `philosophy_weight` 적용해서 국가별 점수 집계
- `all_countries.json`의 `philosophy_summary`로 1차 가중치 검색
- 상위 5개국 후보 반환

[C] 보편적 지도안 양식 (`data/lesson_plan_template.md`)

[D] LLM 프롬프트 작성 (키워드 추출, 카드 생성, 지도안 생성)

[E] FastAPI 백엔드 (`main.py` + 3개 엔드포인트)

[F] Streamlit 프론트엔드

## 문제 해결

**Q: `load_data.py` 실행 시 메모리 부족 오류**
- bge-m3 모델은 약 2GB RAM을 사용해요. 다른 무거운 프로그램을 끄세요.
- 그래도 안 되면 `model_name="BAAI/bge-small-en-v1.5"` 같은 작은 모델로 변경 (한국어 성능은 다소 떨어짐).

**Q: 다운로드가 너무 느려요**
- 한국에서 HuggingFace 다운로드가 느릴 때가 있어요. 첫 실행 시 30분까지 걸릴 수 있으니 인내심을 가지고 기다리세요.
- 한 번 받으면 `~/.cache/huggingface/` 에 캐시되어 재사용돼요.

**Q: 적재된 DB를 다시 만들고 싶어요**
- `db/chroma_db/` 폴더를 통째로 지우고 `load_data.py`를 재실행하세요.
- (스크립트가 기존 컬렉션을 자동으로 덮어쓰지만, 완전 초기화하려면 폴더 삭제가 안전.)
