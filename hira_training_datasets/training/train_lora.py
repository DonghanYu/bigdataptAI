#!/usr/bin/env python3
"""
HIRA SOLAR-10.7B LoRA 학습 스크립트
- HIRA 데이터셋으로 SOLAR-10.7B 모델 학습
- LoRA (Low-Rank Adaptation) 사용
- Train/Val/Test 분할 지원
- Gradio 인터페이스 제공
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import json

# bitsandbytes 경고 차단
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    from tqdm import tqdm
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch/Transformers가 설치되지 않았습니다.")
    print("   GPU 환경에서 다음 명령으로 설치하세요:")
    print("   pip install torch transformers peft accelerate bitsandbytes")


class HIRADataset(Dataset):
    """HIRA 데이터셋 클래스"""

    def __init__(self, file_path: str, tokenizer, max_length: int = 512):
        """
        Args:
            file_path: JSONL 파일 경로
            tokenizer: Hugging Face tokenizer
            max_length: 최대 시퀀스 길이
        """
        self.data = []

        # JSONL 파일 로드
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if 'instruction' in item and 'output' in item:
                        self.data.append(item)
                except json.JSONDecodeError:
                    continue

        self.tokenizer = tokenizer
        self.max_length = max_length

        print(f"  📂 로드: {len(self.data):,}개 ({Path(file_path).name})")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # 프롬프트 형식
        instruction = item['instruction'].strip()
        response = item['output'].strip()

        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n{response}"

        # 토크나이징
        encoding = self.tokenizer(
            prompt,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }


class HIRATrainer:
    """HIRA LoRA 학습기"""

    def __init__(self, config: dict):
        """
        Args:
            config: 학습 설정 딕셔너리
        """
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 경로 설정
        self.model_path = Path(config['model_path'])
        self.data_path = Path(config['data_path'])
        self.output_path = Path(config['output_path'])
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 모델 & 토크나이저
        self.tokenizer = None
        self.model = None
        self.train_dataset = None
        self.val_dataset = None

        print("="*80)
        print("HIRA SOLAR-10.7B LoRA 학습")
        print("="*80 + "\n")

        self._print_environment()
        self._print_config()

    def _print_environment(self):
        """환경 정보 출력"""
        print("📊 환경:")
        print(f"  Device: {self.device}")
        print(f"  PyTorch: {torch.__version__}")

        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  VRAM: {vram:.1f} GB")
        else:
            print("  ⚠️  GPU 없음 (CPU 모드, 학습 매우 느림)")

    def _print_config(self):
        """설정 정보 출력"""
        print(f"\n⚙️  학습 설정:")
        for key, value in self.config.items():
            if key not in ['model_path', 'data_path', 'output_path']:
                print(f"  {key}: {value}")

    def load_model(self):
        """모델 및 토크나이저 로드"""
        print(f"\n[1/5] 모델 로드 중...")
        print(f"  경로: {self.model_path}")

        # 토크나이저
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print(f"  ✓ 토크나이저 로드 완료")

        # 모델
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )

        print(f"  ✓ 기본 모델 로드 완료")

        # LoRA 설정
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=self.config['lora_r'],
            lora_alpha=self.config['lora_alpha'],
            lora_dropout=self.config['lora_dropout'],
            target_modules=["q_proj", "v_proj"]  # SOLAR 모델용
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        print(f"  ✓ LoRA 적용 완료")

    def load_data(self):
        """데이터 로드"""
        print(f"\n[2/5] 데이터 로드 중...")

        train_path = self.data_path / "train.jsonl"
        val_path = self.data_path / "val.json"

        if not train_path.exists():
            raise FileNotFoundError(f"Train 파일 없음: {train_path}")

        # Train 데이터
        self.train_dataset = HIRADataset(
            train_path,
            self.tokenizer,
            max_length=self.config['max_length']
        )

        # Validation 데이터
        if val_path.exists():
            # JSON을 JSONL로 변환
            val_jsonl = self.data_path / "val.jsonl"
            if not val_jsonl.exists():
                with open(val_path, 'r', encoding='utf-8') as f:
                    val_data = json.load(f)
                with open(val_jsonl, 'w', encoding='utf-8') as f:
                    for item in val_data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')

            self.val_dataset = HIRADataset(
                val_jsonl,
                self.tokenizer,
                max_length=self.config['max_length']
            )
        else:
            print("  ⚠️  Validation 데이터 없음")
            self.val_dataset = None

    def train(self):
        """학습 실행"""
        print(f"\n[3/5] 학습 시작...")

        # Training Arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_path),
            num_train_epochs=self.config['num_epochs'],
            per_device_train_batch_size=self.config['batch_size'],
            per_device_eval_batch_size=self.config['batch_size'],
            gradient_accumulation_steps=self.config['gradient_accumulation_steps'],
            learning_rate=self.config['learning_rate'],
            warmup_steps=self.config['warmup_steps'],
            logging_steps=self.config['logging_steps'],
            eval_strategy="steps" if self.val_dataset else "no",
            eval_steps=self.config.get('eval_steps', 100),
            save_steps=self.config.get('save_steps', 500),
            save_total_limit=3,
            fp16=torch.cuda.is_available(),
            dataloader_pin_memory=False,
            report_to="none",
            load_best_model_at_end=True if self.val_dataset else False,
            metric_for_best_model="eval_loss" if self.val_dataset else None,
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            tokenizer=self.tokenizer,
        )

        # 학습 시작
        start_time = datetime.now()
        print(f"  시작 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        trainer.train()

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n  ✓ 학습 완료!")
        print(f"  종료 시각: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  소요 시간: {duration}")

    def save_model(self):
        """모델 저장"""
        print(f"\n[4/5] 모델 저장 중...")

        # LoRA 어댑터만 저장
        lora_path = self.output_path / "lora_adapter"
        self.model.save_pretrained(lora_path)
        self.tokenizer.save_pretrained(lora_path)

        print(f"  ✓ LoRA 어댑터 저장: {lora_path}")

        # 설정 저장
        config_path = self.output_path / "training_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 학습 설정 저장: {config_path}")

    def evaluate(self):
        """평가 실행"""
        print(f"\n[5/5] 평가 중...")

        if self.val_dataset is None:
            print("  ⚠️  Validation 데이터 없음")
            return

        self.model.eval()

        val_loader = DataLoader(
            self.val_dataset,
            batch_size=self.config['batch_size'],
            shuffle=False
        )

        total_loss = 0
        num_batches = 0

        with torch.no_grad():
            for batch in tqdm(val_loader, desc="  평가"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                total_loss += outputs.loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        perplexity = np.exp(avg_loss)

        print(f"\n  평가 결과:")
        print(f"    Loss: {avg_loss:.4f}")
        print(f"    Perplexity: {perplexity:.2f}")

        # 결과 저장
        results = {
            "val_loss": avg_loss,
            "perplexity": perplexity,
            "evaluated_at": datetime.now().isoformat()
        }

        with open(self.output_path / "eval_results.json", 'w') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="HIRA SOLAR-10.7B LoRA 학습")

    # 경로
    parser.add_argument("--model-path", type=str,
                       default="/home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model",
                       help="SOLAR 모델 경로")
    parser.add_argument("--data-path", type=str,
                       default="../output/v1.0/full",
                       help="데이터 경로 (train.jsonl 포함)")
    parser.add_argument("--output-path", type=str,
                       default="./trained_models/hira_solar_lora",
                       help="출력 경로")

    # 학습 파라미터
    parser.add_argument("--batch-size", type=int, default=2,
                       help="배치 크기")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4,
                       help="그래디언트 누적 스텝")
    parser.add_argument("--learning-rate", type=float, default=5e-5,
                       help="학습률")
    parser.add_argument("--num-epochs", type=int, default=3,
                       help="에폭 수")
    parser.add_argument("--max-length", type=int, default=512,
                       help="최대 시퀀스 길이")

    # LoRA 파라미터
    parser.add_argument("--lora-r", type=int, default=16,
                       help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32,
                       help="LoRA alpha")
    parser.add_argument("--lora-dropout", type=float, default=0.05,
                       help="LoRA dropout")

    args = parser.parse_args()

    # 환경 체크
    if not TORCH_AVAILABLE:
        print("\n❌ PyTorch가 설치되지 않아 학습을 실행할 수 없습니다.")
        print("   GPU 환경에서 다음 명령으로 설치 후 재실행하세요:")
        print("   pip install torch transformers peft accelerate bitsandbytes")
        sys.exit(1)

    # 설정
    config = {
        "model_path": args.model_path,
        "data_path": args.data_path,
        "output_path": args.output_path,
        "batch_size": args.batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "num_epochs": args.num_epochs,
        "max_length": args.max_length,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "warmup_steps": 100,
        "logging_steps": 10,
        "eval_steps": 100,
        "save_steps": 500,
    }

    # 학습 실행
    trainer = HIRATrainer(config)

    try:
        trainer.load_model()
        trainer.load_data()
        trainer.train()
        trainer.save_model()
        trainer.evaluate()

        print("\n" + "="*80)
        print("🎉 학습 완료!")
        print("="*80)
        print(f"\n모델 저장 위치: {trainer.output_path}")
        print(f"\n다음 단계:")
        print(f"  python3 inference_interface.py --model-path {trainer.output_path}/lora_adapter")

    except Exception as e:
        print(f"\n❌ 학습 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
