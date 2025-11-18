# HIRA 오픈데이터 포털 크롤링 프로젝트

건강보험심사평가원(HIRA) 보건의료빅데이터개방시스템의 정보를 수집하고 JSON 형식으로 규격화하는 프로젝트입니다.

## 🎯 프로젝트 개요

### 목표
HIRA 오픈데이터 포털(https://opendata.hira.or.kr)의 모든 정보를 **JSON 형식으로 규격화**하여 활용 가능한 데이터로 변환

### 결과
✅ **323개 Q&A 쌍** - 수동 큐레이션 + JSON 규격화 완료
✅ **5개 주요 메뉴** - 53개 주제 구조화
✅ **3개 출력 형식** - 전체 데이터, 요약, 학습용 JSON

## 📁 프로젝트 구조

```
hira_crawler/
├── hira_selenium_crawler.py      # Selenium 기반 크롤러 (브라우저 환경용)
├── hira_playwright_crawler.py    # Playwright 기반 크롤러 (자동 브라우저)
├── hira_requests_crawler.py      # Requests 기반 크롤러 (경량)
├── convert_yaml_to_json.py       # YAML → JSON 변환기 ✅ 실제 사용
├── README.md                      # 기본 문서
├── FINAL_README.md                # 최종 문서 (이 파일)
├── output/                        # 출력 파일들
│   ├── hira_data_from_yaml_*.json      # 전체 데이터 (126 KB)
│   ├── hira_summary_from_yaml_*.json   # 요약 + 전체 (140 KB)
│   └── hira_qa_training_*.json         # Q&A 학습용 (91 KB)
└── screenshots/                   # 스크린샷 (디버깅용)
```

## 🚀 실행 방법

### ✅ 실제 작동하는 방법 (YAML → JSON 변환)

```bash
cd /home/user/bigdataptAI/hira_crawler
python3 convert_yaml_to_json.py
```

**출력 파일:**
1. `hira_data_from_yaml_*.json` - 전체 데이터
2. `hira_summary_from_yaml_*.json` - 요약 + 전체
3. `hira_qa_training_*.json` - Q&A 학습용

### ⚠️ 크롤러 사용 (현재 403 차단됨)

HIRA 사이트가 강력한 봇 차단 시스템(WAF)을 사용하여 모든 자동화 접근이 차단됩니다.

```bash
# Selenium (브라우저 필요)
python3 hira_selenium_crawler.py  # ❌ Chrome 미설치

# Playwright (자동 브라우저)
python3 hira_playwright_crawler.py  # ❌ 403 Forbidden

# Requests (경량)
python3 hira_requests_crawler.py  # ❌ 403 Forbidden
```

**해결 방법:**
- 실제 브라우저 환경에서 수동 실행
- VPN 또는 프록시 사용
- 사이트 관리자에게 API 접근 요청

## 📊 생성된 JSON 규격

### 1. 전체 데이터 (`hira_data_from_yaml_*.json`)

```json
{
  "site_info": {
    "url": "https://opendata.hira.or.kr",
    "source": "Manual curation",
    "converted_at": "2025-11-18T05:21:20.800277",
    "version": "1.0.0"
  },
  "menu_structure": {
    "service_intro": {
      "id": "service_intro",
      "name": "서비스 소개",
      "weight": 300,
      "topics_count": 8,
      "topics": [...]
    }
  },
  "core_qa": {
    "service_intro": {
      "menu_id": "service_intro",
      "qa_count": 68,
      "qa_pairs": [
        {
          "question": "상병코드는 어떻게 조회하나요?",
          "answer": "상병코드(KCD 코드)는 '서비스 소개 > ...",
          "question_length": 16,
          "answer_length": 113
        }
      ]
    }
  },
  "statistics": {
    "total_menus": 5,
    "total_topics": 53,
    "total_qa_pairs": 323,
    "question_stats": {
      "avg_length": 15.4,
      "min_length": 7,
      "max_length": 29
    },
    "answer_stats": {
      "avg_length": 80.8,
      "min_length": 22,
      "max_length": 183
    }
  }
}
```

### 2. 요약 데이터 (`hira_summary_from_yaml_*.json`)

```json
{
  "summary": {
    "source": "HIRA manual curation",
    "converted_at": "2025-11-18T05:21:20.800277",
    "statistics": {...}
  },
  "menu_list": [
    {
      "id": "service_intro",
      "name": "서비스 소개",
      "topics": 8
    }
  ],
  "qa_list": [
    {
      "menu_id": "service_intro",
      "qa_count": 68,
      "sample_qa": [...]
    }
  ],
  "full_data": {...}
}
```

### 3. Q&A 학습용 (`hira_qa_training_*.json`)

```json
[
  {
    "instruction": "상병코드는 어떻게 조회하나요?",
    "input": "",
    "output": "상병코드(KCD 코드)는 '서비스 소개 > 용어설명 > ..."
  },
  {
    "instruction": "KCD 코드가 뭔가요?",
    "input": "",
    "output": "KCD(Korean Standard Classification of Diseases)는 ..."
  }
]
```

## 📈 데이터 통계

### 수집된 데이터

| 항목 | 수량 |
|------|------|
| 메뉴 | 5개 |
| 주제 | 53개 |
| Q&A 쌍 | 323개 |
| 질문 평균 길이 | 15.4자 |
| 답변 평균 길이 | 80.8자 |

### 메뉴별 분포

| 메뉴 | Q&A 수 |
|------|--------|
| 서비스 소개 | 68개 |
| 보건의료빅데이터 | 108개 |
| 의료통계정보 | 64개 |
| 공공데이터 | 40개 |
| 고객지원 | 43개 |

## 🔧 기술 스택

### 크롤링 엔진 (3가지 구현)
- **Selenium** - 브라우저 자동화 (Chrome 필요)
- **Playwright** - 자동 브라우저 (권장)
- **Requests + BeautifulSoup** - 경량 크롤러

### 데이터 처리
- **PyYAML** - YAML 파싱
- **BeautifulSoup4** - HTML 파싱
- **JSON** - 데이터 규격화

## ⚠️ 제약 사항 및 해결

### 1. 403 Forbidden 차단
**문제:** HIRA 사이트가 모든 자동화 요청 차단
**원인:** WAF (Web Application Firewall) 또는 봇 차단 시스템
**해결:** 수동 큐레이션 데이터를 JSON으로 변환

### 2. Chrome 브라우저 미설치
**문제:** Selenium이 Chrome을 찾을 수 없음
**원인:** 환경에 Chrome 미설치
**해결:** Playwright 사용 또는 Requests 사용

### 3. Playwright 페이지 크래시
**문제:** 페이지 로딩 중 크래시
**원인:** SSL 인증서 오류 + 메모리 부족
**해결:** Requests로 변경

## 💡 활용 방법

### 1. LLM 학습 데이터로 사용

```python
import json

# Q&A 학습용 JSON 로드
with open('output/hira_qa_training_*.json', 'r', encoding='utf-8') as f:
    training_data = json.load(f)

# LoRA 학습에 사용
# 기존 bigdata_portal_learning 프로젝트와 연동 가능
```

### 2. 챗봇 지식베이스로 사용

```python
import json

# 전체 데이터 로드
with open('output/hira_data_from_yaml_*.json', 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

# 질문 검색
for qa_group in hira_data['core_qa'].values():
    for qa in qa_group['qa_pairs']:
        if '상병코드' in qa['question']:
            print(f"Q: {qa['question']}")
            print(f"A: {qa['answer']}")
```

### 3. 데이터 분석

```python
import json

# 요약 데이터 로드
with open('output/hira_summary_from_yaml_*.json', 'r', encoding='utf-8') as f:
    summary = json.load(f)

# 통계 출력
stats = summary['summary']['statistics']
print(f"총 Q&A: {stats['total_qa_pairs']}쌍")
print(f"평균 질문 길이: {stats['question_stats']['avg_length']:.1f}자")
print(f"평균 답변 길이: {stats['answer_stats']['avg_length']:.1f}자")
```

## 📚 기존 프로젝트와의 관계

### bigdata_portal_learning/
기존 프로젝트에서 수동으로 작성한 YAML 데이터를 소스로 사용

```
bigdata_portal_learning/config/
├── hira_menu_structure.yaml      # 메뉴 구조 (소스)
└── hira_core_qa_expanded.yaml    # Q&A 데이터 (소스)
                 ↓
         hira_crawler/
         convert_yaml_to_json.py
                 ↓
         hira_crawler/output/
         ├── hira_data_from_yaml_*.json
         ├── hira_summary_from_yaml_*.json
         └── hira_qa_training_*.json
```

## 🎓 학습 및 활용

### 기존 LoRA 학습 파이프라인과 연동

```bash
# 1. Q&A JSON을 학습 데이터 폴더로 복사
cp output/hira_qa_training_*.json \
   ../bigdata_portal_learning/output/hira_final.json

# 2. 데이터 클리닝 (Train/Val/Test 분할)
cd ../bigdata_portal_learning
python3 01_data_cleaning.py

# 3. LoRA 학습
python3 02_train_with_validation.py

# 4. 모델 평가
python3 04_evaluate_model.py
```

## 🔍 향후 개선 방향

### Phase 2: 실제 크롤링 성공
1. VPN/프록시 사용
2. 브라우저 자동화 정교화
3. Rate limiting 준수
4. HIRA에 API 접근 요청

### Phase 3: 데이터 확장
1. 수동 큐레이션 Q&A 확장 (323 → 1,000개)
2. GPT 기반 변형 생성 (1,000 → 5,000개)
3. 실제 통계 데이터 크롤링
4. Open API 연동

## 📝 라이센스 및 저작권

### 크롤러 코드
본 프로젝트의 크롤러 코드는 MIT 라이센스

### 수집된 데이터
HIRA 오픈데이터 포털의 데이터 저작권은 **건강보험심사평가원**에 있음

### 사용 제한
- 연구 및 학습 목적으로만 사용
- 상업적 이용 시 HIRA에 문의
- 재배포 시 출처 명시 필수

## 🙏 감사

- **HIRA** - 보건의료빅데이터 개방
- **기존 프로젝트** - 수동 큐레이션 데이터 제공

---

## ✅ 체크리스트

- [x] Selenium 크롤러 작성
- [x] Playwright 크롤러 작성
- [x] Requests 크롤러 작성
- [x] YAML → JSON 변환기 작성
- [x] JSON 규격화 완료
- [x] 3가지 출력 형식 생성
- [x] README 문서화 완료
- [ ] 실제 크롤링 성공 (403 차단)
- [ ] 데이터 확장 (향후)

---

**프로젝트 생성일**: 2025-11-18
**버전**: 1.0.0
**상태**: ✅ JSON 규격화 완료, ⚠️ 실시간 크롤링 차단됨
**실제 사용 가능**: YAML → JSON 변환기
