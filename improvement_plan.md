# SOLAR-10.7B HIRA 모델 개선 실행 계획서

**작성일**: 2025-11-12  
**현황**: 훈련 지표는 양호하나 추론 시 Hallucination 발생

---

## 🔍 문제 진단 요약

### 1. Overfitting 확인
- **증거**: Epoch 1 (Loss: 0.2371) → Epoch 3 (Loss: 0.6694) 지속적 악화
- **원인**: 소규모 데이터셋(1976개), 검증 데이터 부재, 데이터 중복

### 2. 데이터 품질 이슈
- 완전 중복 답변 다수 존재 (샘플 100개 중 13개)
- 템플릿 기반 반복 문구 과다
- 답변 길이 편차 큼 (20자~585자)

### 3. 훈련 설정 문제
- Train/Validation split 없음
- Early stopping이 Training loss 기준 (잘못된 지표)
- Patience가 너무 짧음 (2 epochs)

---

## ✅ Phase 1: 긴급 대응 (1-2일)

### Task 1.1: 데이터 클리닝 & 분할
**Priority**: 🔴 Critical

**작업 내용**:
```python
1. 중복 제거
   - 완전 중복 답변 삭제
   - 유사도 90% 이상 샘플 통합
   
2. Train/Val/Test 분할
   - Train: 80% (약 1,400개)
   - Validation: 10% (약 200개)
   - Test: 10% (약 200개)
   
3. 품질 필터링
   - 답변 길이 < 15자 제거
   - 의미없는 반복 문구 제거
   - 템플릿 다양화
```

**예상 결과**: 고품질 데이터 1,500-1,600개 확보

**코드 위치**: `scripts/01_data_cleaning.py`

---

### Task 1.2: 훈련 파라미터 수정
**Priority**: 🔴 Critical

**변경 사항**:
```yaml
Before:
  - num_epochs: 5
  - early_stopping_patience: 2
  - early_stopping_metric: train_loss ❌
  - validation_split: None ❌

After:
  - num_epochs: 10-15
  - early_stopping_patience: 5
  - early_stopping_metric: val_loss ✅
  - validation_split: 10% ✅
  - save_total_limit: 3 (최고 성능 3개만 보관)
```

**추가 기능**:
- Validation loss 모니터링
- 각 epoch마다 validation 평가
- Tensorboard 로깅

**코드 위치**: `scripts/02_train_with_validation.py`

---

### Task 1.3: Inference 파라미터 최적화
**Priority**: 🟡 High

**현재 설정**:
```python
temperature=0.7
top_p=0.9
```

**개선 설정**:
```python
# Conservative Generation
temperature=0.3          # 더 결정론적
top_p=0.85              # 상위 토큰 제한
repetition_penalty=1.15  # 반복 억제
max_new_tokens=256      # 과도한 생성 방지
no_repeat_ngram_size=3  # 3-gram 반복 금지

# Hallucination 탐지
do_sample=True
length_penalty=1.0
early_stopping=True
```

**코드 위치**: `step7_interface.ipynb` 수정

---

## 🔧 Phase 2: 중기 개선 (1주)

### Task 2.1: 데이터 증강
**Priority**: 🟡 High

**방법론**:

1. **Paraphrasing (의역)**
```python
# GPT-4 활용
Instruction: "1인당 평균 진료비는 얼마인가요?"
→ 변형: "평균 진료비용이 궁금합니다"
→ 변형: "개인당 의료비 지출 평균은?"
```

2. **Negative Sampling (부정 샘플)**
```python
# 범위 외 질문 대응
Q: "내일 날씨는?"
A: "죄송합니다. 건강보험 관련 질문에만 답변 가능합니다."

Q: "주식 투자 방법은?"
A: "HIRA 데이터와 관련된 의료 정보만 제공합니다."
```

3. **Contextual Variation (맥락 변형)**
```python
# 동일 정보, 다른 맥락
원본: "DRG는 진단명 기준 환자군 분류입니다."
변형1: "연구자입니다. DRG 시스템에 대해 설명해주세요."
변형2: "환자 입장에서 DRG가 뭔지 쉽게 알려주세요."
```

**목표**: 데이터셋 3,000-4,000개로 확장

**도구**: 
- OpenAI GPT-4 API
- 자체 Paraphrasing 스크립트

---

### Task 2.2: 평가 시스템 구축
**Priority**: 🟡 High

**정량 평가 지표**:
```python
1. BLEU Score (번역 품질)
2. ROUGE-L (요약 품질)
3. Perplexity (언어 모델 성능)
4. Exact Match (정확한 답변 비율)
```

**정성 평가 체크리스트**:
```
✓ Factual Accuracy (사실 정확성)
✓ Relevance (질문 관련성)
✓ Completeness (답변 완전성)
✓ Clarity (명확성)
✗ Hallucination (거짓 정보)
✗ Contradiction (모순)
```

**도구**:
- `evaluate` library (Hugging Face)
- Custom evaluation scripts
- 전문가 리뷰 템플릿

---

### Task 2.3: 하이퍼파라미터 튜닝
**Priority**: 🟢 Medium

**실험 매트릭스**:
| LoRA Rank (r) | Alpha | Dropout | Learning Rate |
|---------------|-------|---------|---------------|
| 8             | 16    | 0.05    | 5e-5          |
| 16            | 32    | 0.05    | 5e-5          | ← 현재
| 32            | 64    | 0.05    | 3e-5          |
| 16            | 32    | 0.1     | 5e-5          |

**평가 방법**:
- 각 설정별 3회 반복 실험
- Validation loss 기준 선택
- Test set으로 최종 검증

---

## 🚀 Phase 3: 장기 전략 (2-4주)

### Task 3.1: RAG 시스템 도입
**Priority**: 🟢 Medium-Low

**아키텍처**:
```
User Query
    ↓
[Vector DB 검색]
    ↓
Top-K 관련 문서 추출
    ↓
[Prompt Construction]
    ↓
LLM Generation (Context-aware)
    ↓
Response + Citations
```

**장점**:
- ✅ Hallucination 대폭 감소
- ✅ 최신 정보 실시간 반영
- ✅ 출처 명시 가능
- ✅ 데이터 업데이트 용이

**기술 스택**:
- Vector DB: FAISS / Chroma
- Embedding: sentence-transformers
- Reranker: cross-encoder

---

### Task 3.2: RLHF/DPO 적용
**Priority**: 🔵 Low (선택적)

**방법**:
1. Human Feedback 수집
   - 전문가 5-10명
   - 답변 쌍 비교 (A vs B)
   - 선호도 점수 수집

2. DPO (Direct Preference Optimization)
   - 선호 데이터로 추가 학습
   - 정책 모델 업데이트

**예상 효과**:
- 답변 품질 10-20% 향상
- 사용자 만족도 증가

---

### Task 3.3: 모니터링 시스템
**Priority**: 🟢 Medium

**구성 요소**:
```python
1. Logging Dashboard
   - 실시간 쿼리 모니터링
   - 응답 시간 추적
   - 에러율 체크

2. Confidence Scoring
   - 각 답변의 신뢰도 점수
   - 낮은 신뢰도 → 경고 표시

3. Fallback Mechanism
   - Confidence < 0.5 → "확실하지 않습니다"
   - RAG 검색으로 보완
```

**도구**:
- Prometheus + Grafana
- Custom logging system

---

## 📊 성공 지표 (KPI)

### 단기 (1-2주)
- [ ] Validation Loss < 0.15
- [ ] Test Set BLEU > 0.7
- [ ] Hallucination Rate < 10%

### 중기 (1개월)
- [ ] 사용자 만족도 > 4.0/5.0
- [ ] 정확도 > 85%
- [ ] 응답 시간 < 2초

### 장기 (2-3개월)
- [ ] RAG 시스템 통합 완료
- [ ] Production 배포
- [ ] 일일 활성 사용자 100명+

---

## 💰 리소스 요구사항

### 인력
- ML 엔지니어: 1명 (풀타임)
- 도메인 전문가: 1명 (파트타임, 평가용)
- 데이터 라벨러: 2명 (파트타임, 증강용)

### 컴퓨팅
- GPU: A100 80GB x 1 (계속 사용)
- 추가 스토리지: 100GB (증강 데이터)
- API 비용: GPT-4 (데이터 증강) ~ $200

### 시간
- Phase 1: 1-2일
- Phase 2: 1주
- Phase 3: 2-4주 (선택적)

**총 예상 기간**: 4-6주 (전체 완료 시)

---

## 🔄 다음 단계

### 즉시 시작
1. ✅ 데이터 클리닝 스크립트 작성
2. ✅ Train/Val split 구현
3. ✅ 재훈련 스크립트 준비

### 이번 주 내
4. 재훈련 실행 및 모니터링
5. Inference 파라미터 튜닝
6. 초기 평가 수행

### 다음 주
7. 데이터 증강 시작
8. 평가 시스템 구축
9. A/B 테스팅 설계

---

## 📞 연락처 및 지원

**문의사항**: 
- 기술 이슈: ML팀 Slack 채널
- 데이터 관련: 도메인 전문가와 협의
- 긴급 사항: 프로젝트 매니저 직접 연락

**문서 위치**:
- 코드 저장소: `/workspace/solar_hira_v2/`
- 실험 로그: `/workspace/logs/`
- 평가 결과: `/workspace/evaluation/`

---

**승인자**: _____________  
**날짜**: 2025-11-12
