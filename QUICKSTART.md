# HIRA 빅데이터 챗봇 - 빠른 시작 가이드

**5분 안에 시작하기**

---

## 🚀 3단계로 시작하기

### Step 1: 환경 확인 (1분)

```bash
# GPU 확인
nvidia-smi

# Python 버전 확인 (3.8 이상)
python --version

# 필수 라이브러리 확인
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import peft; print(f'PEFT: {peft.__version__}')"
```

**문제가 있다면?**
```bash
# 라이브러리 설치 (폐쇄망에서는 미리 준비 필요)
pip install torch==2.1.0 transformers peft accelerate datasets tqdm
```

### Step 2: 설정 파일 수정 (2분)

```bash
# 설정 파일 열기
vi config/config.yaml

# 또는
nano config/config.yaml
```

**필수 수정 사항:**

```yaml
paths:
  # SOLAR 모델 경로 (본인 환경에 맞게 수정)
  model_path: "/실제/경로/solar_10.7b_package/model"

  # 데이터 경로 (상대 경로 사용 가능)
  data:
    cleaned: "workspace/data/hira/cleaned"
```

**경로 예시:**

| 환경 | 경로 예시 |
|------|-----------|
| Backend.AI | `/home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model` |
| 로컬 | `/Users/name/projects/solar_10.7b_package/model` |
| 상대 경로 | `solar_10.7b_package/model` |

### Step 3: JupyterLab 실행 (2분)

```bash
# JupyterLab 시작
jupyter lab

# 터미널에서 표시된 URL 복사
# 예: http://localhost:8888/?token=xxxxx
```

**브라우저에서:**

1. `notebooks/HIRA_Training_SOLAR_LoRA.ipynb` 열기
2. 첫 셀부터 순차 실행 (Shift + Enter)
3. GPU 및 경로 확인
4. 학습 시작!

---

## 📝 체크리스트

시작 전에 다음을 확인하세요:

```
✅ GPU 사용 가능 (nvidia-smi 확인)
✅ SOLAR-10.7B 모델 다운로드 완료
✅ config.yaml에서 model_path 수정
✅ JupyterLab 실행 가능
✅ 디스크 여유 공간 100GB 이상
```

---

## 🎯 첫 실행 플로우

### 옵션 A: 테스트 데이터로 빠른 실험

```python
# 노트북 실행 시 자동으로 테스트 데이터 생성
# 300개 샘플, 학습 시간 약 15-20분
```

**장점**: 즉시 시작 가능
**단점**: 실제 성능 측정 불가

### 옵션 B: HIRA 실제 데이터 사용

1. **데이터 준비** (1-2주)
   - `docs/01_HIRA_DATA_PREPARATION_GUIDE.md` 참조
   - HIRA 웹사이트에서 데이터 다운로드
   - QA 형식으로 변환

2. **데이터 정제**
   ```bash
   python 01_data_cleaning.py
   ```

3. **학습 시작**
   - 노트북 실행 또는 스크립트 사용

---

## 🖥️ 실행 방법 비교

| 방법 | 난이도 | 장점 | 단점 |
|------|--------|------|------|
| **JupyterLab** (권장) | ⭐ 쉬움 | - 단계별 실행<br>- 시각화 지원<br>- 디버깅 용이 | - 서버 필요 |
| **Python 스크립트** | ⭐⭐ 보통 | - 자동 실행<br>- 백그라운드 가능 | - 중간 확인 어려움 |
| **Flask 웹** | ⭐⭐⭐ 어려움 | - 웹 UI<br>- 다중 사용자 | - 설정 복잡 |

### JupyterLab (권장)

```bash
# 1. 실행
jupyter lab

# 2. 노트북 열기
notebooks/HIRA_Training_SOLAR_LoRA.ipynb

# 3. 셀 실행
Shift + Enter
```

### Python 스크립트

```bash
# 백그라운드 실행
nohup python 02_train_with_validation.py > training.log 2>&1 &

# 로그 확인
tail -f training.log
```

### Flask 웹 인터페이스 (학습 후)

```bash
# 서버 시작
python 03_improved_interface.py

# 브라우저 접속
http://localhost:8888
```

---

## ⏱️ 예상 소요 시간

| 단계 | 테스트 데이터 | 실제 데이터 |
|------|--------------|------------|
| 환경 설정 | 5분 | 5분 |
| 데이터 준비 | 자동 (1분) | 1-2주 |
| 모델 학습 | 15-20분 | 2-3시간 |
| 평가 테스트 | 5분 | 30분 |
| **총 시간** | **~30분** | **2주 + 4시간** |

*A100 80G x2 기준*

---

## 🔍 실행 중 확인사항

### 1. GPU 메모리 모니터링

```bash
# 별도 터미널에서 실행
watch -n 1 nvidia-smi
```

**정상 범위:**
- 학습 중: 25-35GB per GPU
- 추론 중: 20-25GB per GPU

### 2. 학습 진행 확인

노트북에서 Progress Bar 확인:
```
Epoch 1/10: 100%|██████████| 135/135 [15:23<00:00, 6.84s/it]
Train Loss: 1.245, Val Loss: 1.182
```

### 3. 체크포인트 확인

```bash
# 저장된 모델 확인
ls -lh workspace/models/solar_hira_lora/

# 출력 예시:
# best_model/
# checkpoint-epoch-2/
# checkpoint-epoch-4/
# training_history.json
```

---

## ❓ 자주 묻는 질문 (FAQ)

### Q1: "CUDA out of memory" 오류가 발생해요

```yaml
# config.yaml 수정
training:
  batch_size: 1  # 2에서 1로 줄이기
  gradient_accumulation_steps: 8  # 4에서 8로 늘리기
```

### Q2: 모델 파일을 찾을 수 없다고 나와요

```bash
# 경로 확인
ls solar_10.7b_package/model/config.json

# 없으면 절대 경로 사용
# config.yaml:
# model_path: "/전체/경로/solar_10.7b_package/model"
```

### Q3: 학습이 너무 느려요

**확인사항:**
1. GPU 사용 중인지 확인: `torch.cuda.is_available()`
2. bfloat16 사용 중인지 확인 (A100 최적화)
3. Gradient checkpointing 활성화

### Q4: 테스트 데이터는 어디서 받나요?

노트북 실행 시 자동 생성됩니다.
또는:
```bash
# docs/01_HIRA_DATA_PREPARATION_GUIDE.md 참조
# HIRA 웹사이트에서 실제 데이터 다운로드
```

---

## 📞 도움이 필요하면

1. **문서 확인**
   - `PROJECT_README.md` - 전체 가이드
   - `docs/01_HIRA_DATA_PREPARATION_GUIDE.md` - 데이터 가이드

2. **로그 확인**
   - 노트북: 셀 출력 확인
   - 스크립트: `training.log` 파일 확인

3. **이슈 보고**
   - GitHub Issues
   - 또는 프로젝트 담당자에게 문의

---

## 🎉 성공적으로 시작했다면

다음 단계:

1. ✅ `notebooks/HIRA_Interface.ipynb`로 모델 테스트
2. ✅ 실제 HIRA 데이터 준비 시작
3. ✅ 하이퍼파라미터 튜닝 실험
4. ✅ 팀원과 결과 공유

**Happy Training! 🚀**
