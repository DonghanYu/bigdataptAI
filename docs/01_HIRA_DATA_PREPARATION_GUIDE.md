# HIRA 빅데이터 학습 데이터 준비 가이드

**프로젝트**: HIRA 빅데이터 상담 챗봇 모델
**버전**: 1.0
**작성일**: 2025-11-13

---

## 📋 목차

1. [개요](#1-개요)
2. [심평원 빅데이터개방시스템 소개](#2-심평원-빅데이터개방시스템-소개)
3. [데이터 수집 전략](#3-데이터-수집-전략)
4. [데이터 구조 설계](#4-데이터-구조-설계)
5. [데이터 생성 방법론](#5-데이터-생성-방법론)
6. [품질 관리](#6-품질-관리)
7. [실행 절차](#7-실행-절차)

---

## 1. 개요

### 1.1 목적
건강보험심사평가원(HIRA) 빅데이터개방시스템의 공개 데이터를 기반으로 SOLAR-10.7B 모델을 미세조정하여 건강보험 관련 질의응답 챗봇을 구축합니다.

### 1.2 데이터 요구사항
- **규모**: 최소 3,000개 이상의 고품질 QA 쌍
- **형식**: JSONL (JSON Lines)
- **구조**: Instruction-Input-Output 형식
- **품질**: 전문가 검증 또는 공식 데이터 기반

---

## 2. 심평원 빅데이터개방시스템 소개

### 2.1 시스템 정보
- **URL**: https://opendata.hira.or.kr/
- **운영기관**: 건강보험심사평가원
- **목적**: 건강보험 관련 공공데이터 개방 및 활용 지원

### 2.2 주요 데이터 카테고리

#### 2.2.1 진료 통계 데이터
```
- 연도별/지역별 진료 현황
- 상병별 진료 통계
- 연령별/성별 진료비 분석
- 의료기관 종별 진료 현황
```

#### 2.2.2 약제 정보
```
- 약제 급여 목록
- 약가 정보
- 약제 사용량 통계
- 고가 약제 현황
```

#### 2.2.3 의료 행위 정보
```
- 행위 급여 목록
- 비급여 행위 정보
- 신의료기술 현황
```

#### 2.2.4 건강보험 제도
```
- DRG 수가 정보
- 본인부담금 정보
- 요양급여기준
```

### 2.3 데이터 접근 방법

#### 방법 1: 웹 포털 직접 다운로드
```bash
1. https://opendata.hira.or.kr/ 접속
2. 회원가입 및 로그인
3. 데이터 카테고리 선택
4. 원하는 데이터셋 검색 및 다운로드
   - CSV, XLSX, JSON 등 다양한 형식 제공
```

#### 방법 2: 공공데이터포털 API 활용
```bash
1. https://www.data.go.kr/ 접속
2. HIRA 관련 API 신청
3. 인증키 발급
4. API를 통한 자동 수집
```

#### 방법 3: 웹 스크래핑 (공개 정보)
```python
# 예시: 통계 페이지 크롤링 (허용된 범위 내)
import requests
from bs4 import BeautifulSoup

# 주의: robots.txt 확인 및 이용약관 준수 필수
```

---

## 3. 데이터 수집 전략

### 3.1 데이터 소스 우선순위

| 우선순위 | 데이터 유형 | 수집 목표 | 비고 |
|---------|------------|----------|------|
| 1 | 진료 통계 | 1,000개 | 기본 통계 질문 |
| 2 | 약제 정보 | 800개 | 약제 관련 질의 |
| 3 | 건강보험 제도 | 700개 | 제도 설명 |
| 4 | 의료 행위 | 500개 | 전문 용어 설명 |
| 총계 | - | 3,000개 | - |

### 3.2 데이터 수집 체크리스트

```
□ HIRA 빅데이터개방시스템 계정 생성
□ 주요 데이터셋 목록 작성
□ 데이터 다운로드 권한 확인
□ 데이터 이용약관 검토
□ 수집 스크립트 준비
□ 저장 경로 설정 (workspace/data/hira/raw/)
□ 백업 계획 수립
```

---

## 4. 데이터 구조 설계

### 4.1 표준 JSONL 형식

```json
{
  "instruction": "건강보험 빅데이터 전문가로서 정확하게 답변하세요.",
  "input": "2023년 전체 진료비는 얼마인가요?",
  "output": "2023년 건강보험 총 진료비는 약 125조 2,450억원으로 집계되었습니다. 이는 전년 대비 약 8.2% 증가한 수치입니다.",
  "metadata": {
    "category": "진료통계",
    "source": "HIRA 연간 통계",
    "year": 2023,
    "confidence": "high"
  }
}
```

### 4.2 Instruction 템플릿

| 카테고리 | Instruction 예시 |
|---------|-----------------|
| 통계 질의 | "건강보험 빅데이터 전문가로서 정확한 통계를 제공하세요." |
| 제도 설명 | "건강보험 제도를 일반인이 이해하기 쉽게 설명하세요." |
| 약제 정보 | "약제 정보를 전문적이면서도 명확하게 답변하세요." |
| 용어 설명 | "의료 전문 용어를 쉬운 말로 풀어서 설명하세요." |

### 4.3 디렉토리 구조

```
workspace/data/hira/
├── raw/                          # 원본 데이터
│   ├── treatment_stats/          # 진료 통계
│   ├── medicine/                 # 약제 정보
│   ├── insurance_system/         # 제도 정보
│   └── medical_procedures/       # 의료 행위
├── processed/                    # 가공 데이터
│   ├── qa_pairs.jsonl           # 생성된 QA 쌍
│   └── metadata.json            # 메타데이터
└── cleaned/                      # 정제 데이터
    ├── train.jsonl              # 학습 데이터 (80%)
    ├── val.jsonl                # 검증 데이터 (10%)
    └── test.jsonl               # 테스트 데이터 (10%)
```

---

## 5. 데이터 생성 방법론

### 5.1 자동 생성 방법

#### 방법 A: 규칙 기반 생성
```python
# 예시: CSV 통계를 QA로 변환
def generate_qa_from_stats(csv_file):
    """
    통계 데이터를 QA 형식으로 변환
    """
    df = pd.read_csv(csv_file)

    qa_pairs = []
    for _, row in df.iterrows():
        # 질문 생성 템플릿
        questions = [
            f"{row['year']}년 {row['disease']} 환자는 몇 명인가요?",
            f"{row['disease']}의 {row['year']}년 진료 인원을 알려주세요."
        ]

        # 답변 생성
        answer = f"{row['year']}년 {row['disease']} 환자는 총 {row['patient_count']:,}명이며, 진료비는 {row['cost']:,}원입니다."

        for q in questions:
            qa_pairs.append({
                "instruction": "건강보험 빅데이터 전문가로서 정확하게 답변하세요.",
                "input": q,
                "output": answer
            })

    return qa_pairs
```

#### 방법 B: LLM 기반 증강 (추천)
```python
# GPT-4 또는 Claude를 활용한 QA 생성
def augment_with_llm(raw_data, llm_client):
    """
    원본 데이터를 LLM으로 다양한 QA로 확장
    """
    prompt = f"""
다음 건강보험 통계 데이터를 바탕으로 5개의 질문-답변 쌍을 생성하세요.

데이터:
{raw_data}

요구사항:
1. 질문은 자연스러운 일상 언어로
2. 답변은 정확하고 구체적으로
3. 다양한 질문 유형 (통계, 비교, 추세 등)

출력 형식: JSON
"""

    response = llm_client.generate(prompt)
    return parse_json(response)
```

### 5.2 수동 생성 가이드

#### 전문가 작성 템플릿
```markdown
### QA 작성 가이드

#### 좋은 예시
Q: 2023년 MRI 검사 건수는 얼마나 되나요?
A: 2023년 MRI 검사는 총 4,251,032건이 시행되었습니다. 이는 전년 대비 약 3.2% 증가한 수치입니다.

#### 나쁜 예시
Q: MRI는?
A: 많습니다.

#### 체크리스트
- [ ] 질문이 명확한가?
- [ ] 답변에 구체적인 수치가 포함되었는가?
- [ ] 출처가 명확한가?
- [ ] 오타가 없는가?
```

---

## 6. 품질 관리

### 6.1 데이터 검증 기준

```python
# 품질 검증 스크립트
def validate_qa_quality(qa_item):
    """QA 품질 검증"""
    checks = {
        "has_instruction": len(qa_item.get("instruction", "")) > 10,
        "has_input": len(qa_item.get("input", "")) > 5,
        "has_output": len(qa_item.get("output", "")) > 20,
        "no_placeholder": "TODO" not in qa_item.get("output", ""),
        "no_excessive_length": len(qa_item.get("output", "")) < 1000
    }

    return all(checks.values()), checks
```

### 6.2 중복 제거

```python
def remove_duplicates(qa_list):
    """중복 QA 제거"""
    seen = set()
    unique = []

    for qa in qa_list:
        # 출력 기준 해시
        output_hash = hashlib.md5(qa["output"].encode()).hexdigest()

        if output_hash not in seen:
            seen.add(output_hash)
            unique.append(qa)

    return unique
```

### 6.3 품질 점검표

```
□ 중복 데이터 제거 완료
□ 답변 길이 적정 (20자 ~ 500자)
□ 질문 다양성 확보
□ 사실 정확성 검증
□ 오타/맞춤법 검사
□ 메타데이터 완성도
□ 출처 표기 명확성
```

---

## 7. 실행 절차

### 7.1 Phase 1: 데이터 수집 (1-2주)

```bash
# Step 1: 환경 설정
mkdir -p workspace/data/hira/{raw,processed,cleaned}

# Step 2: HIRA 웹사이트에서 데이터 다운로드
# - 진료 통계 CSV/Excel 파일
# - 약제 정보 데이터
# - 제도 관련 문서

# Step 3: 수집 로그 작성
echo "$(date): 진료통계 2020-2023 다운로드 완료" >> data_collection.log
```

### 7.2 Phase 2: 데이터 변환 (3-5일)

```bash
# QA 생성 스크립트 실행
python scripts/convert_hira_to_qa.py \
    --input workspace/data/hira/raw/ \
    --output workspace/data/hira/processed/qa_pairs.jsonl \
    --min-qa-per-source 3 \
    --use-llm-augmentation
```

### 7.3 Phase 3: 품질 검증 (2-3일)

```bash
# 품질 검증
python scripts/validate_qa_data.py \
    --input workspace/data/hira/processed/qa_pairs.jsonl \
    --output-report quality_report.html

# 중복 제거 및 정제
python 01_data_cleaning.py
```

### 7.4 Phase 4: 데이터 분할

```bash
# Train/Val/Test 분할
python scripts/split_dataset.py \
    --input workspace/data/hira/processed/qa_pairs.jsonl \
    --output workspace/data/hira/cleaned/ \
    --train-ratio 0.8 \
    --val-ratio 0.1 \
    --test-ratio 0.1
```

---

## 8. 예시 데이터셋

### 8.1 진료 통계 예시

```json
{
  "instruction": "건강보험 빅데이터 전문가로서 정확하게 답변하세요.",
  "input": "2023년 고혈압 환자 수는?",
  "output": "2023년 건강보험 진료를 받은 고혈압 환자는 약 1,342만 명으로 집계되었습니다. 이는 전체 인구의 약 26%에 해당하며, 연간 진료비는 약 3조 2,450억원입니다.",
  "metadata": {
    "category": "진료통계",
    "disease": "고혈압",
    "year": 2023,
    "source": "HIRA 질병통계"
  }
}
```

### 8.2 제도 설명 예시

```json
{
  "instruction": "건강보험 제도를 일반인이 이해하기 쉽게 설명하세요.",
  "input": "DRG가 무엇인가요?",
  "output": "DRG(Diagnosis Related Group)는 '진단명 기준 환자군 분류'를 의미합니다. 같은 질병으로 입원한 환자들을 그룹으로 묶어 미리 정해진 금액을 지불하는 제도입니다. 예를 들어 맹장 수술을 받으면 입원 기간이나 사용한 약에 관계없이 일정 금액만 내게 됩니다.",
  "metadata": {
    "category": "제도설명",
    "keyword": "DRG",
    "difficulty": "medium"
  }
}
```

---

## 9. 참고 자료

### 9.1 공식 문서
- HIRA 빅데이터개방시스템: https://opendata.hira.or.kr/
- 공공데이터포털: https://www.data.go.kr/
- HIRA 통계: https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA020041000100

### 9.2 관련 도구
- 데이터 변환: `pandas`, `openpyxl`
- QA 생성: `openai`, `anthropic`
- 품질 검증: `jsonschema`, `hashlib`

### 9.3 법적 고려사항
```
⚠️ 주의사항
- HIRA 데이터 이용약관 준수
- 개인정보 포함 데이터 사용 금지
- 상업적 이용 시 별도 승인 필요
- 데이터 출처 명시 의무
```

---

## 10. FAQ

**Q1: 실제 HIRA 데이터가 없으면 어떻게 하나요?**
A: 공개된 통계 보고서와 백서를 활용하여 QA를 수동 생성하거나, GPT-4를 이용해 합성 데이터를 생성할 수 있습니다.

**Q2: 데이터 수집에 얼마나 걸리나요?**
A: 자동화 정도에 따라 다르지만, 수동 수집 시 2-3주, 반자동 시 1주일 정도 소요됩니다.

**Q3: 최소 몇 개의 QA가 필요한가요?**
A: LoRA 미세조정에는 최소 1,000개 이상을 권장하며, 3,000개 이상이면 좋은 성능을 기대할 수 있습니다.

**Q4: 데이터 품질이 가장 중요한가요?**
A: 네. 품질 낮은 10,000개보다 고품질 3,000개가 훨씬 효과적입니다.

---

**작성자**: AI Assistant
**검토자**: (추후 전문가 검토 필요)
**승인일**: 2025-11-13
