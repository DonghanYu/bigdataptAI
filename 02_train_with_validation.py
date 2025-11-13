#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLAR-10.7B LoRA 학습 - Validation 포함 개선 버전
- Train/Val 분리
- Validation loss 기반 Early Stopping
- 상세 메트릭 로깅
"""

import sys
import os

# bitsandbytes 차단
os.environ['BITSANDBYTES_NOWELCOME'] = '1'
sys.modules['bitsandbytes'] = None

import torch
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from datetime import datetime
import numpy as np

print("="*80)
print("SOLAR-10.7B LoRA 학습 - Validation 개선 버전")
print("="*80)

# ============================================
# 설정
# ============================================
WORK_DIR = Path("/home/work/LLM_Meditron/bigdataAI")
MODEL_PATH = WORK_DIR / "solar_10.7b_package" / "model"
DATA_PATH = WORK_DIR / "workspace" / "data" / "hira" / "cleaned_data"
OUTPUT_PATH = WORK_DIR / "workspace" / "models" / "solar_hira_v3"
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n📊 환경:")
print(f"  Device: {device}")
print(f"  PyTorch: {torch.__version__}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# ============================================
# 학습 설정 - 개선된 파라미터
# ============================================
config = {
    "batch_size": 2,
    "gradient_accumulation_steps": 4,
    "learning_rate": 5e-5,
    "num_epochs": 15,  # 증가
    "max_length": 512,
    "warmup_steps": 100,
    "logging_steps": 10,
    "eval_steps": 50,  # Validation 주기
    "patience": 5,     # Early stopping patience 증가
}

print(f"\n⚙️  학습 설정:")
for k, v in config.items():
    print(f"  {k}: {v}")

# ============================================
# Dataset 클래스
# ============================================
class HIRADataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=512):
        self.data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    self.data.append(json.loads(line.strip()))
                except:
                    continue
        
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        print(f"📂 Loaded {len(self.data)} examples from {file_path.name}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        instruction = item['instruction'].strip()
        output = item['output'].strip()
        
        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
        
        encoding = self.tokenizer(
            prompt,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze()
        }

# ============================================
# Evaluation 함수
# ============================================
def evaluate(model, val_loader, device):
    """Validation 평가"""
    model.eval()
    total_loss = 0
    num_batches = 0
    
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validating", leave=False):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            total_loss += outputs.loss.item()
            num_batches += 1
    
    model.train()
    return total_loss / num_batches

# ============================================
# 모델 로드
# ============================================
print(f"\n🔄 모델 로딩...")
print(f"  Path: {MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)

print(f"✅ Model loaded")
print(f"  Parameters: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")

# ============================================
# LoRA 설정
# ============================================
print(f"\n🔧 LoRA 설정...")

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    bias="none"
)

model = get_peft_model(model, lora_config)
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
all_params = sum(p.numel() for p in model.parameters())

print(f"✅ LoRA 적용 완료")
print(f"  Trainable: {trainable_params / 1e6:.2f}M ({100 * trainable_params / all_params:.2f}%)")

# ============================================
# 데이터 로드
# ============================================
print(f"\n📂 데이터 로드...")

train_file = DATA_PATH / "train.jsonl"
val_file = DATA_PATH / "val.jsonl"

train_dataset = HIRADataset(train_file, tokenizer, config['max_length'])
val_dataset = HIRADataset(val_file, tokenizer, config['max_length'])

train_loader = DataLoader(
    train_dataset,
    batch_size=config['batch_size'],
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=config['batch_size'],
    shuffle=False,
    num_workers=0
)

# ============================================
# Optimizer & Scheduler
# ============================================
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=config['learning_rate'],
    weight_decay=0.01
)

total_steps = len(train_loader) * config['num_epochs'] // config['gradient_accumulation_steps']
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=total_steps,
    eta_min=config['learning_rate'] * 0.1
)

# ============================================
# 학습 루프
# ============================================
print(f"\n🚀 학습 시작...\n")

model.train()
global_step = 0
best_val_loss = float('inf')
patience_counter = 0

history = {
    'train_loss': [],
    'val_loss': [],
    'learning_rate': [],
    'best_epoch': 0
}

for epoch in range(config['num_epochs']):
    epoch_loss = 0
    progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{config['num_epochs']}")
    
    for step, batch in enumerate(progress_bar):
        # Forward
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        loss = outputs.loss / config['gradient_accumulation_steps']
        loss.backward()
        
        # Gradient accumulation
        if (step + 1) % config['gradient_accumulation_steps'] == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            global_step += 1
            
            # Logging
            if global_step % config['logging_steps'] == 0:
                current_lr = scheduler.get_last_lr()[0]
                current_loss = loss.item() * config['gradient_accumulation_steps']
                
                history['train_loss'].append(current_loss)
                history['learning_rate'].append(current_lr)
                
                progress_bar.set_postfix({
                    'loss': f"{current_loss:.4f}",
                    'lr': f"{current_lr:.2e}"
                })
        
        epoch_loss += loss.item()
    
    # Epoch 종료 - Training Loss
    avg_train_loss = epoch_loss / len(train_loader) * config['gradient_accumulation_steps']
    
    # Validation
    print(f"\n📊 Epoch {epoch+1} 평가 중...")
    val_loss = evaluate(model, val_loader, device)
    history['val_loss'].append(val_loss)
    
    print(f"  Train Loss: {avg_train_loss:.4f}")
    print(f"  Val Loss:   {val_loss:.4f}")
    
    # Best model 저장
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        history['best_epoch'] = epoch + 1
        
        checkpoint_path = OUTPUT_PATH / "best_model"
        model.save_pretrained(checkpoint_path)
        tokenizer.save_pretrained(checkpoint_path)
        
        print(f"  ✅ Best model saved (Val Loss: {val_loss:.4f})")
    else:
        patience_counter += 1
        print(f"  ⚠️  No improvement. Patience: {patience_counter}/{config['patience']}")
        
        if patience_counter >= config['patience']:
            print(f"\n🛑 Early stopping triggered at epoch {epoch+1}")
            print(f"   Best Val Loss: {best_val_loss:.4f} at epoch {history['best_epoch']}")
            break
    
    print()

# ============================================
# 최종 저장
# ============================================
final_path = OUTPUT_PATH / "final_model"
model.save_pretrained(final_path)
tokenizer.save_pretrained(final_path)

# 히스토리 저장
history_file = OUTPUT_PATH / "training_history.json"
with open(history_file, 'w') as f:
    json.dump(history, f, indent=2)

# 로그 저장
log_file = OUTPUT_PATH / "training_log.txt"
with open(log_file, 'w') as f:
    f.write("="*80 + "\n")
    f.write("Training Summary\n")
    f.write("="*80 + "\n\n")
    f.write(f"Best Epoch: {history['best_epoch']}\n")
    f.write(f"Best Val Loss: {best_val_loss:.4f}\n")
    f.write(f"Final Train Loss: {avg_train_loss:.4f}\n")
    f.write(f"\nConfig:\n")
    for k, v in config.items():
        f.write(f"  {k}: {v}\n")

print("="*80)
print("✅ 학습 완료!")
print(f"  Best Val Loss: {best_val_loss:.4f}")
print(f"  Best Epoch: {history['best_epoch']}")
print(f"  Model: {final_path}")
print(f"  History: {history_file}")
print(f"  Log: {log_file}")
print("="*80)
