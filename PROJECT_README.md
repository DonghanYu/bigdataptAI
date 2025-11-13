# HIRA 빅데이터 상담 챗봇 모델 구축 프로젝트

**프로젝트명**: HIRA 빅데이터 상담 챗봇
**버전**: 1.0.0
**날짜**: 2025-11-13
**모델**: SOLAR-10.7B-v1.0 + LoRA

---

## 📋 프로젝트 개요

건강보험심사평가원(HIRA) 빅데이터개방시스템의 데이터를 기반으로 건강보험 관련 질의응답을 수행하는 챗봇 모델을 구축하는 프로젝트입니다.

### 주요 목표

1. **학습 데이터**: 심평원 빅데이터개방시스템 기반 데이터 마련
2. **모델 학습**: 폐쇄망 환경에서 SOLAR-10.7B LoRA 미세조정
3. **모델 실증**: 인터페이스를 통한 사람 평가

### 기술 스택

- **모델**: SOLAR-10.7B-v1.0
- **미세조정**: LoRA (Low-Rank Adaptation)
- **프레임워크**: PyTorch 2.1, Transformers, PEFT
- **환경**: A100 80G x2, CPU 32 Core, Mem 800G
- **인터페이스**: JupyterLab, Flask, Gradio (선택)

---

## 🗂️ 프로젝트 구조

```
bigdataptAI/
├── README.md                          # 기본 README
├── PROJECT_README.md                  # 프로젝트 상세 문서 (본 문서)
├── config/
│   └── config.yaml                    # 설정 파일
├── docs/
│   └── 01_HIRA_DATA_PREPARATION_GUIDE.md  # 데이터 준비 가이드
├── notebooks/
│   ├── HIRA_Training_SOLAR_LoRA.ipynb     # 학습 노트북
│   └── HIRA_Interface.ipynb               # 인터페이스 노트북
├── workspace/
│   ├── data/
│   │   └── hira/
│   │       ├── raw/                   # 원본 데이터
│   │       ├── processed/             # 가공 데이터
│   │       └── cleaned/               # 정제 데이터
│   │           ├── train.jsonl
│   │           ├── val.jsonl
│   │           └── test.jsonl
│   ├── models/
│   │   └── solar_hira_lora/
│   │       ├── best_model/            # Best 체크포인트
│   │       ├── final_model/           # 최종 모델
│   │       └── training_history.json  # 학습 히스토리
│   └── logs/                          # 로그 파일
├── solar_10.7b_package/
│   └── model/                         # SOLAR-10.7B 모델
├── scripts/ (기존 Python 스크립트)
│   ├── 01_data_cleaning.py
│   ├── 02_train_with_validation.py
│   ├── 03_improved_interface.py
│   ├── 04_evaluate_model.py
│   └── 05_data_augmentation.py
└── train_solar                        # 기본 학습 스크립트
```

---

## 🚀 빠른 시작

### 전제 조건

```bash
# 필수 라이브러리 (폐쇄망에서 미리 설치 필요)
torch==2.1.0
transformers>=4.36.0
peft>=0.7.0
accelerate>=0.25.0
datasets>=2.15.0
tqdm
matplotlib
ipywidgets  # JupyterLab 인터페이스용
```

### 1단계: 환경 설정

```bash
# 1. 프로젝트 디렉토리 이동
cd /path/to/bigdataptAI

# 2. 설정 파일 확인 및 수정
vi config/config.yaml
# - model_path: SOLAR 모델 경로 설정
# - data paths: 데이터 경로 설정
# - 하이퍼파라미터 조정 (필요시)

# 3. 디렉토리 생성
mkdir -p workspace/{data/hira/{raw,processed,cleaned},models,logs}
```

### 2단계: 데이터 준비

**옵션 A: 실제 HIRA 데이터 사용**

`docs/01_HIRA_DATA_PREPARATION_GUIDE.md` 문서를 참조하여 다음을 수행:

1. HIRA 빅데이터개방시스템(https://opendata.hira.or.kr/) 접속
2. 필요한 통계 데이터 다운로드
3. QA 형식으로 변환
4. 데이터 정제 및 분할

```bash
# 데이터 정제 스크립트 실행
python 01_data_cleaning.py
```

**옵션 B: 테스트 데이터 사용**

학습 노트북 실행 시 자동으로 테스트 데이터가 생성됩니다.

### 3단계: 모델 학습

**방법 1: JupyterLab 노트북 사용 (권장)**

```bash
# JupyterLab 실행
jupyter lab

# 브라우저에서 다음 노트북 열기:
# notebooks/HIRA_Training_SOLAR_LoRA.ipynb

# 셀을 순차적으로 실행
```

**방법 2: Python 스크립트 사용**

```bash
# 검증 포함 학습 스크립트
python 02_train_with_validation.py

# 또는 기본 스크립트
python train_solar
```

### 4단계: 모델 평가 및 테스트

**JupyterLab 인터페이스:**

```bash
# notebooks/HIRA_Interface.ipynb 열기
# 인터랙티브 질의응답 테스트
```

**Flask 웹 인터페이스:**

```bash
# Flask 서버 실행
python 03_improved_interface.py

# 브라우저에서 접속
# http://localhost:8888
```

---

## 📚 상세 가이드

### 1. 데이터 준비

**문서**: `docs/01_HIRA_DATA_PREPARATION_GUIDE.md`

주요 내용:
- 심평원 빅데이터개방시스템 소개
- 데이터 수집 전략
- QA 데이터 구조 설계
- 데이터 생성 방법론
- 품질 관리 기준

**데이터 형식**:

```json
{
  "instruction": "건강보험 빅데이터 전문가로서 정확하게 답변하세요.",
  "input": "2023년 MRI 검사 건수는 얼마나 되나요?",
  "output": "2023년 건강보험 적용 MRI 검사는 총 4,251,032건이 시행되었습니다.",
  "metadata": {
    "category": "진료통계",
    "source": "HIRA",
    "year": 2023
  }
}
```

### 2. 모델 학습

**노트북**: `notebooks/HIRA_Training_SOLAR_LoRA.ipynb`

주요 단계:
1. 환경 설정 및 GPU 확인
2. 데이터 로드 및 전처리
3. SOLAR-10.7B 모델 로드
4. LoRA 설정 및 적용
5. 학습 실행
6. 모델 저장 및 평가

**주요 파라미터**:

```yaml
LoRA:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05

Training:
  batch_size: 2
  gradient_accumulation_steps: 4
  learning_rate: 2e-4
  num_epochs: 10
  max_length: 512
```

**학습 시간**:
- A100 80G x2 기준
- 3,000개 샘플: 약 2-3시간
- 10,000개 샘플: 약 6-8시간

### 3. 모델 평가

**노트북**: `notebooks/HIRA_Interface.ipynb`

평가 방법:
1. **인터랙티브 테스트**: 실시간 질의응답
2. **배치 평가**: 미리 정의된 테스트 세트
3. **파라미터 비교**: Temperature 등 실험
4. **성능 분석**: 생성 시간, 토큰 수 등

**평가 지표**:
- 생성 시간 (초)
- 생성 토큰 수
- 답변 품질 (1-5점)
- 사실 정확성
- Hallucination 발생률

---

## ⚙️ 설정 파일

**파일**: `config/config.yaml`

주요 섹션:

```yaml
paths:
  model_path: "solar_10.7b_package/model"
  data: {...}
  output: {...}

lora:
  r: 16
  lora_alpha: 32
  target_modules: [...]

training:
  batch_size: 2
  learning_rate: 2e-4
  num_epochs: 10

inference:
  temperature: 0.3
  max_new_tokens: 256
```

### 경로 수정 방법

1. `config/config.yaml` 열기
2. `paths` 섹션에서 환경에 맞는 절대/상대 경로 설정
3. 저장 후 노트북/스크립트 실행

---

## 🔧 트러블슈팅

### GPU 메모리 부족

```python
# config.yaml에서 배치 크기 줄이기
training:
  batch_size: 1  # 2에서 1로 변경
  gradient_accumulation_steps: 8  # 4에서 8로 증가
```

### 모델 로드 오류

```bash
# 경로 확인
ls solar_10.7b_package/model/

# 필수 파일:
# - config.json
# - pytorch_model.bin (또는 .safetensors)
# - tokenizer.json
# - tokenizer_config.json
```

### bitsandbytes 오류

```python
# 노트북/스크립트 첫 부분에 추가
import sys
import os
os.environ['BITSANDBYTES_NOWELCOME'] = '1'
sys.modules['bitsandbytes'] = None
```

### 폐쇄망 환경 설정

```python
# 모델 로드 시 local_files_only=True 사용
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    local_files_only=True,  # 필수
    trust_remote_code=True
)
```

---

## 📊 성능 벤치마크

### 학습 성능 (예상)

| 에폭 | Train Loss | Val Loss | 시간 (A100x2) |
|------|-----------|----------|---------------|
| 1    | 1.245     | 1.182    | 15분          |
| 5    | 0.421     | 0.398    | 1시간 15분    |
| 10   | 0.287     | 0.302    | 2시간 30분    |

### 추론 성능

| 메트릭            | 값           |
|------------------|--------------|
| 평균 생성 시간    | 1.2초        |
| 토큰/초          | 45 tokens/s  |
| 평균 답변 길이    | 120 토큰     |
| GPU 메모리 사용   | ~25GB        |

---

## 🎯 다음 단계

### 단기 (1-2주)

- [ ] 실제 HIRA 데이터 수집 및 정제
- [ ] 최소 3,000개 QA 쌍 생성
- [ ] 모델 재학습 및 평가
- [ ] 베이스라인 성능 측정

### 중기 (1개월)

- [ ] 데이터 증강 (5,000-10,000개)
- [ ] 하이퍼파라미터 튜닝
- [ ] A/B 테스팅
- [ ] 전문가 평가 수행

### 장기 (2-3개월)

- [ ] RAG 시스템 통합
- [ ] 실시간 데이터 업데이트 파이프라인
- [ ] Production 배포
- [ ] 모니터링 시스템 구축

---

## 📖 참고 자료

### 공식 문서

- **HIRA 빅데이터개방시스템**: https://opendata.hira.or.kr/
- **SOLAR 모델**: https://huggingface.co/upstage/SOLAR-10.7B-v1.0
- **LoRA 논문**: https://arxiv.org/abs/2106.09685
- **PEFT 라이브러리**: https://github.com/huggingface/peft

### 프로젝트 문서

1. `docs/01_HIRA_DATA_PREPARATION_GUIDE.md` - 데이터 준비 가이드
2. `config/config.yaml` - 설정 파일
3. `SUMMARY.md` - 프로젝트 요약 (기존)
4. `improvement_plan.md` - 개선 계획 (기존)

### 관련 코드

- **Transformers**: https://github.com/huggingface/transformers
- **PyTorch**: https://pytorch.org/docs/
- **Flask**: https://flask.palletsprojects.com/

---

## 👥 기여자

- **프로젝트 리드**: [이름]
- **ML 엔지니어**: [이름]
- **데이터 전문가**: [이름]
- **도메인 전문가**: [이름]

---

## 📝 라이선스

이 프로젝트는 [라이선스 유형]에 따라 배포됩니다.

**주의사항**:
- HIRA 데이터는 공공데이터로, 이용약관을 준수해야 합니다.
- SOLAR 모델은 Apache 2.0 라이선스입니다.
- 상업적 이용 시 별도 확인이 필요할 수 있습니다.

---

## 📞 문의

- **이슈 보고**: GitHub Issues
- **기술 문의**: [이메일]
- **협업 제안**: [이메일]

---

**마지막 업데이트**: 2025-11-13
**버전**: 1.0.0
