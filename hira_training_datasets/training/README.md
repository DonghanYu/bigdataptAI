# HIRA SOLAR-10.7B LoRA 학습 및 추론

HIRA 데이터셋으로 SOLAR-10.7B 모델을 LoRA로 파인튜닝하고 웹 인터페이스로 테스트

## 📋 목차

- [환경 요구사항](#환경-요구사항)
- [설치](#설치)
- [1단계: 학습](#1단계-학습)
- [2단계: 추론 인터페이스](#2단계-추론-인터페이스)
- [트러블슈팅](#트러블슈팅)

---

## 🖥️ 환경 요구사항

### 필수
- **GPU**: NVIDIA GPU 16GB+ VRAM 권장 (RTX 3090, A100, V100 등)
- **RAM**: 32GB+ 권장
- **Storage**: 50GB+ 여유 공간
- **OS**: Linux (Ubuntu 20.04+ 권장)

### 소프트웨어
- Python 3.8+
- CUDA 11.8+ 또는 12.1+
- PyTorch 2.0+

---

## 📦 설치

### 1. Python 환경 생성

```bash
# 가상환경 생성 (선택)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 2. 필수 패키지 설치

```bash
cd /home/user/bigdataptAI/hira_training_datasets/training

# PyTorch 설치 (CUDA 12.1 예시)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 나머지 패키지 설치
pip install -r requirements.txt
```

### 3. SOLAR 모델 다운로드

SOLAR-10.7B 모델을 다운로드하거나 경로를 확인하세요:

```bash
# 옵션 1: Hugging Face에서 다운로드
huggingface-cli download upstage/SOLAR-10.7B-v1.0 --local-dir ./models/solar-10.7b

# 옵션 2: 기존 모델 경로 확인
ls -la /home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model
```

---

## 🚀 1단계: 학습

### 기본 학습

```bash
python3 train_lora.py \
  --model-path /home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model \
  --data-path ../output/v1.0/full \
  --output-path ./trained_models/hira_solar_lora \
  --num-epochs 3 \
  --batch-size 2 \
  --learning-rate 5e-5
```

### 파라미터 설명

| 파라미터 | 설명 | 기본값 |
|----------|------|--------|
| `--model-path` | SOLAR 모델 경로 | (필수) |
| `--data-path` | 데이터 경로 (train.jsonl 포함) | `../output/v1.0/full` |
| `--output-path` | 학습 모델 저장 경로 | `./trained_models/hira_solar_lora` |
| `--num-epochs` | 학습 에폭 수 | 3 |
| `--batch-size` | 배치 크기 | 2 |
| `--gradient-accumulation-steps` | 그래디언트 누적 | 4 |
| `--learning-rate` | 학습률 | 5e-5 |
| `--max-length` | 최대 시퀀스 길이 | 512 |
| `--lora-r` | LoRA rank | 16 |
| `--lora-alpha` | LoRA alpha | 32 |
| `--lora-dropout` | LoRA dropout | 0.05 |

### 메모리 최적화 옵션

**VRAM 부족 시:**
```bash
python3 train_lora.py \
  --batch-size 1 \
  --gradient-accumulation-steps 8 \
  --max-length 256 \
  --lora-r 8
```

### 학습 모니터링

학습 중 다음 정보가 표시됩니다:
```
Step 100/1000 | Loss: 1.234 | LR: 5e-5
Eval Loss: 1.150 | Perplexity: 3.15
```

### 예상 소요 시간

| GPU | 배치 크기 | 1 에폭 시간 (1,136개) |
|-----|-----------|---------------------|
| RTX 3090 (24GB) | 2 | ~30분 |
| A100 (40GB) | 4 | ~20분 |
| V100 (16GB) | 1 | ~50분 |

---

## 🌐 2단계: 추론 인터페이스

### Gradio 웹 UI 실행

```bash
python3 inference_interface.py \
  --base-model-path /home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model \
  --lora-adapter-path ./trained_models/hira_solar_lora/lora_adapter \
  --server-port 7860
```

### 접속

브라우저에서 접속:
```
http://localhost:7860
```

### 공개 링크 생성 (외부 접속)

```bash
python3 inference_interface.py \
  --base-model-path /path/to/solar \
  --lora-adapter-path ./trained_models/hira_solar_lora/lora_adapter \
  --share
```

### 인터페이스 기능

1. **질문 입력**: HIRA 관련 질문 입력
2. **파라미터 조정**:
   - Temperature: 창의성 조절 (0.1-2.0)
   - Top-p: 다양성 조절 (0.1-1.0)
   - Top-k: 토큰 선택 범위 (1-100)
   - Max Length: 최대 시퀀스 길이
3. **예시 질문**: 8개 샘플 질문 제공

---

## 🧪 테스트

### 빠른 테스트 (Python)

```python
from inference_interface import HIRAInference

# 모델 로드
inference = HIRAInference(
    base_model_path="/path/to/solar",
    lora_adapter_path="./trained_models/hira_solar_lora/lora_adapter"
)

# 질문
question = "상병코드는 어떻게 조회하나요?"
answer = inference.generate(question)

print(f"Q: {question}")
print(f"A: {answer}")
```

### 배치 테스트

```python
questions = [
    "환자표본 데이터 신청 방법은?",
    "HIRA 데이터 규모는?",
    "API 키 발급 방법"
]

answers = inference.batch_generate(questions)

for q, a in zip(questions, answers):
    print(f"Q: {q}\nA: {a}\n")
```

---

## 📊 학습 결과 확인

### 저장된 파일 구조

```
trained_models/hira_solar_lora/
├── lora_adapter/              # LoRA 어댑터 (추론에 사용)
│   ├── adapter_config.json
│   ├── adapter_model.bin
│   └── ...
├── training_config.json       # 학습 설정
├── eval_results.json          # 평가 결과
└── checkpoint-*/              # 체크포인트 (선택)
```

### 평가 결과 확인

```bash
cat trained_models/hira_solar_lora/eval_results.json
```

```json
{
  "val_loss": 1.234,
  "perplexity": 3.45,
  "evaluated_at": "2025-11-18T12:00:00"
}
```

---

## ⚠️ 트러블슈팅

### 1. CUDA Out of Memory

**증상:**
```
RuntimeError: CUDA out of memory
```

**해결:**
```bash
# 배치 크기 줄이기
python3 train_lora.py --batch-size 1 --max-length 256

# LoRA rank 줄이기
python3 train_lora.py --lora-r 8 --lora-alpha 16
```

### 2. PyTorch CUDA 버전 불일치

**증상:**
```
RuntimeError: CUDA error: no kernel image is available for execution
```

**해결:**
```bash
# CUDA 버전 확인
nvidia-smi

# 맞는 PyTorch 설치
# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 3. 모델 로딩 실패

**증상:**
```
OSError: Model file not found
```

**해결:**
```bash
# 모델 경로 확인
ls -la /home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model

# 또는 Hugging Face에서 다운로드
huggingface-cli download upstage/SOLAR-10.7B-v1.0 --local-dir ./models/solar
```

### 4. Gradio 접속 안 됨

**증상:**
```
Connection refused
```

**해결:**
```bash
# 방화벽 확인
sudo ufw allow 7860

# 포트 변경
python3 inference_interface.py --server-port 8080

# 모든 IP 허용
python3 inference_interface.py --server-name 0.0.0.0
```

---

## 💡 성능 최적화 팁

### 학습 속도 향상

1. **Mixed Precision Training** (자동 적용)
   - FP16 사용으로 메모리 절약 & 속도 향상

2. **Gradient Checkpointing**
   ```python
   model.gradient_checkpointing_enable()
   ```

3. **데이터 병렬화** (Multi-GPU)
   ```bash
   torchrun --nproc_per_node=2 train_lora.py ...
   ```

### 추론 속도 향상

1. **배치 추론**
   ```python
   answers = inference.batch_generate(questions)
   ```

2. **KV Cache 활용** (자동)

3. **양자화** (INT8)
   ```python
   load_in_8bit=True  # 모델 로딩 시
   ```

---

## 📚 참고

### 관련 파일
- 학습 스크립트: `train_lora.py`
- 추론 스크립트: `inference_interface.py`
- 데이터셋: `../output/v1.0/full/train.jsonl`

### 외부 링크
- [SOLAR 모델](https://huggingface.co/upstage/SOLAR-10.7B-v1.0)
- [LoRA 논문](https://arxiv.org/abs/2106.09685)
- [Gradio 문서](https://gradio.app/docs/)

---

## 📞 문의

데이터셋 또는 학습 관련 문의:
- GitHub Issues: [링크]
- 이메일: [이메일]

---

**버전**: 1.0.0
**생성일**: 2025-11-18
**상태**: ✅ 학습 및 추론 준비 완료
