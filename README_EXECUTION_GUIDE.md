# 🚀 SOLAR HIRA 모델 개선 실행 가이드

**목적**: Hallucination 문제 해결 및 모델 성능 향상

---

## 📋 전체 프로세스

```
1. 데이터 클리닝
   ↓
2. Train/Val/Test 분할
   ↓
3. 모델 재학습 (Validation 포함)
   ↓
4. 모델 평가
   ↓
5. Inference 파라미터 최적화
   ↓
6. [선택] 데이터 증강
   ↓
7. [선택] 재학습 및 평가
```

---

## ✅ Phase 1: 즉시 실행 (1-2일)

### Step 1: 데이터 클리닝 및 분할

**스크립트**: `01_data_cleaning.py`

**실행 전 준비**:
```bash
# 작업 디렉토리로 이동
cd /home/work/LLM_Meditron/bigdataAI

# 원본 데이터 위치 확인
ls workspace/data/hira/all_data_expanded.jsonl
```

**실행**:
```bash
# Python 스크립트 실행
python3 01_data_cleaning.py

# 예상 소요 시간: 1-2분
```

**예상 결과**:
```
cleaned_data/
├── train.jsonl      # 약 1,400개
├── val.jsonl        # 약 200개
└── test.jsonl       # 약 200개
```

**검증**:
```bash
# 파일 개수 확인
wc -l cleaned_data/*.jsonl

# 샘플 확인
head -n 3 cleaned_data/train.jsonl
```

✅ **체크포인트**: 
- [ ] 중복 제거 완료
- [ ] Train/Val/Test 분할 완료
- [ ] 파일 생성 확인

---

### Step 2: 모델 재학습 (Validation 포함)

**스크립트**: `02_train_with_validation.py`

**실행 전 준비**:
```bash
# GPU 메모리 확인
nvidia-smi

# 이전 모델 백업 (선택)
mv workspace/models/solar_hira_v2 workspace/models/solar_hira_v2_backup
```

**실행**:
```bash
# 학습 시작
python3 02_train_with_validation.py

# 예상 소요 시간: 2-3시간 (A100 기준)
```

**모니터링**:
```python
# 별도 터미널에서 로그 모니터링
tail -f workspace/models/solar_hira_v3/training_log.txt

# Tensorboard (선택)
tensorboard --logdir workspace/models/solar_hira_v3/logs
```

**예상 결과**:
```
workspace/models/solar_hira_v3/
├── best_model/              # Validation loss 최저 모델
├── final_model/             # 최종 epoch 모델
├── training_history.json    # Loss 히스토리
└── training_log.txt         # 학습 로그
```

✅ **체크포인트**:
- [ ] 학습 완료 (early stopping 작동)
- [ ] Best validation loss < 0.3
- [ ] 모델 파일 생성 확인

---

### Step 3: 모델 평가

**스크립트**: `04_evaluate_model.py`

**실행**:
```bash
# 평가 실행
python3 04_evaluate_model.py

# 예상 소요 시간: 10-15분
```

**예상 결과**:
```
workspace/evaluation/
├── evaluation_results.json     # 정량 지표
└── evaluation_report.txt       # 상세 리포트
```

**목표 지표**:
- BLEU > 0.60
- ROUGE-L > 0.65
- Hallucination Rate < 15%

✅ **체크포인트**:
- [ ] 평가 완료
- [ ] 지표 확인
- [ ] 목표 달성 여부 확인

---

### Step 4: 개선된 Inference 배포

**스크립트**: `03_improved_interface.py`

**실행**:
```bash
# Interface 시작
python3 03_improved_interface.py

# 브라우저에서 접속
# http://10.1.2.9:10359/proxy/8888/opnAI
```

**테스트**:
```
테스트 질문 예시:
1. "1인당 평균 진료비는?"
2. "DRG가 뭐야?"
3. "당뇨병 관리 현황 알려줘"
4. "내일 날씨는?" (부정 샘플 - 거절 확인)
```

✅ **체크포인트**:
- [ ] Interface 정상 작동
- [ ] Conservative generation 적용 (temp=0.3)
- [ ] Confidence scoring 표시
- [ ] 범위 외 질문 거절 확인

---

## 🔧 Phase 2: 추가 개선 (선택, 1주)

### Step 5: 데이터 증강

**스크립트**: `05_data_augmentation.py`

**실행**:
```bash
# 규칙 기반 증강 (무료)
python3 05_data_augmentation.py

# GPT-4 기반 증강 (유료, 고품질)
# API 키 설정 필요
```

**예상 결과**:
```
augmented_data/
└── train_augmented.jsonl    # 약 3,000-4,000개
```

✅ **체크포인트**:
- [ ] 증강 데이터 생성
- [ ] 샘플 품질 확인
- [ ] 부정 샘플 포함 확인

---

### Step 6: 증강 데이터로 재학습

**수정 필요**:
`02_train_with_validation.py`에서 데이터 경로 변경:

```python
# Before
train_file = DATA_PATH / "train.jsonl"

# After
train_file = DATA_PATH / "train_augmented.jsonl"
```

**실행**:
```bash
# 재학습
python3 02_train_with_validation.py

# 모델 v4로 저장하도록 수정
```

✅ **체크포인트**:
- [ ] 재학습 완료
- [ ] 성능 비교 (v3 vs v4)

---

## 📊 성공 기준

### 단기 (1-2주)
- [x] **Phase 1 완료**
- [ ] Validation Loss < 0.25
- [ ] Test BLEU > 0.60
- [ ] Hallucination Rate < 15%
- [ ] 사용자 테스트 5회 이상

### 중기 (1개월)
- [ ] 데이터 증강 완료
- [ ] 최종 모델 성능:
  - BLEU > 0.70
  - ROUGE-L > 0.70
  - Hallucination Rate < 10%
- [ ] Production 배포 준비

---

## 🐛 트러블슈팅

### 문제 1: GPU Out of Memory

**해결책**:
```python
# batch_size 감소
config['batch_size'] = 1
config['gradient_accumulation_steps'] = 8
```

### 문제 2: Early Stopping이 너무 빨리 작동

**해결책**:
```python
# Patience 증가
config['patience'] = 7
```

### 문제 3: Validation Loss가 감소하지 않음

**원인**: Overfitting 또는 Learning Rate 문제

**해결책**:
```python
# Learning rate 감소
config['learning_rate'] = 3e-5

# Dropout 증가
lora_config.lora_dropout = 0.1
```

### 문제 4: Hallucination 여전히 발생

**해결책**:
1. Temperature 더 낮추기 (0.2)
2. Repetition penalty 증가 (1.2)
3. Top-k 감소 (30)
4. RAG 시스템 도입 검토

---

## 📞 문의 및 지원

### 긴급 이슈
- GPU 오류: Backend.AI 관리자
- 데이터 문제: 도메인 전문가
- 코드 버그: ML 엔지니어

### 정기 리뷰
- 주간 회의: 매주 금요일
- 진행 상황 보고: Slack #ml-project

---

## 📝 체크리스트

### Day 1 (오늘)
- [ ] 01_data_cleaning.py 실행
- [ ] 데이터 분할 확인
- [ ] 02_train_with_validation.py 실행 시작

### Day 2
- [ ] 학습 완료 확인
- [ ] 04_evaluate_model.py 실행
- [ ] 평가 결과 분석

### Day 3
- [ ] 03_improved_interface.py 배포
- [ ] 사용자 테스트 5회
- [ ] 피드백 수집

### Week 2 (선택)
- [ ] 05_data_augmentation.py 실행
- [ ] 재학습
- [ ] 최종 평가

---

## 🎯 최종 목표

**현재 상태**:
- ❌ Hallucination 과다
- ❌ Validation 없음
- ❌ Overfitting 확인

**목표 상태**:
- ✅ Hallucination < 10%
- ✅ Validation-based training
- ✅ 안정적인 성능
- ✅ Production-ready

---

**작성일**: 2025-11-12  
**버전**: 1.0  
**담당**: ML Team
