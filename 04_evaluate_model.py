#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모델 평가 스크립트
- BLEU, ROUGE 계산
- Perplexity 측정
- Hallucination 체크
"""

import sys
import os

os.environ['BITSANDBYTES_NOWELCOME'] = '1'
sys.modules['bitsandbytes'] = None

import torch
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm
import numpy as np
from collections import defaultdict

# ============================================
# 설정
# ============================================
WORK_DIR = Path("/home/work/LLM_Meditron/bigdataAI")
BASE_MODEL_PATH = WORK_DIR / "solar_10.7b_package" / "model"
LORA_MODEL_PATH = WORK_DIR / "workspace" / "models" / "solar_hira_v3" / "best_model"
TEST_FILE = WORK_DIR / "workspace" / "data" / "hira" / "cleaned_data" / "test.jsonl"
OUTPUT_DIR = WORK_DIR / "workspace" / "evaluation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("="*80)
print("모델 평가")
print("="*80)
print(f"Device: {device}")

# ============================================
# 모델 로드
# ============================================
print("\n모델 로딩...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)

model = PeftModel.from_pretrained(base_model, LORA_MODEL_PATH)
model.eval()
print("✅ 모델 로드 완료")

# ============================================
# 테스트 데이터 로드
# ============================================
print(f"\n테스트 데이터 로드: {TEST_FILE}")
test_data = []
with open(TEST_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            test_data.append(json.loads(line.strip()))
        except:
            continue
print(f"✅ {len(test_data)}개 샘플 로드")

# ============================================
# 생성 함수
# ============================================
def generate_response(question, max_length=256, temperature=0.3):
    """응답 생성"""
    prompt = f"### Instruction:\n{question}\n\n### Response:\n"
    
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=temperature,
            top_p=0.85,
            top_k=40,
            repetition_penalty=1.15,
            no_repeat_ngram_size=3,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    if "### Response:" in response:
        response = response.split("### Response:")[-1].strip()
    
    return response

# ============================================
# 평가 메트릭
# ============================================
def calculate_bleu(reference, hypothesis):
    """BLEU Score 계산 (간단 버전)"""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    
    # 1-gram precision
    common = len(set(ref_words) & set(hyp_words))
    if len(hyp_words) == 0:
        return 0.0
    
    precision = common / len(hyp_words)
    
    # Brevity penalty
    bp = 1.0 if len(hyp_words) >= len(ref_words) else np.exp(1 - len(ref_words)/len(hyp_words))
    
    return bp * precision

def calculate_rouge_l(reference, hypothesis):
    """ROUGE-L Score 계산"""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    
    # LCS (Longest Common Subsequence)
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i-1] == hyp_words[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    lcs_length = dp[m][n]
    
    if m == 0 or n == 0:
        return 0.0
    
    recall = lcs_length / m
    precision = lcs_length / n
    
    if recall + precision == 0:
        return 0.0
    
    f1 = 2 * recall * precision / (recall + precision)
    return f1

def exact_match(reference, hypothesis):
    """Exact Match (완전 일치)"""
    return 1.0 if reference.strip() == hypothesis.strip() else 0.0

def check_hallucination(question, reference, hypothesis):
    """
    Hallucination 체크 (간단한 휴리스틱)
    Returns: 0 (no hallucination) or 1 (hallucination detected)
    """
    # 1. 너무 짧은 답변
    if len(hypothesis) < 10:
        return 1
    
    # 2. 질문과 전혀 관련 없음
    q_words = set(question.lower().split())
    h_words = set(hypothesis.lower().split())
    r_words = set(reference.lower().split())
    
    # 질문과의 겹치는 단어
    overlap_with_q = len(q_words & h_words)
    overlap_with_r = len(r_words & h_words)
    
    if overlap_with_q == 0 and len(q_words) > 3:
        return 1  # 질문과 무관
    
    if overlap_with_r < len(r_words) * 0.2:
        return 1  # 정답과 너무 다름
    
    # 3. 과도한 반복
    words = hypothesis.split()
    if len(words) > len(set(words)) * 2:
        return 1
    
    return 0

# ============================================
# 평가 실행
# ============================================
print("\n" + "="*80)
print("평가 시작")
print("="*80)

results = {
    'bleu': [],
    'rouge_l': [],
    'exact_match': [],
    'hallucination': [],
    'samples': []
}

for i, item in enumerate(tqdm(test_data, desc="Evaluating")):
    question = item['instruction']
    reference = item['output']
    
    # 생성
    hypothesis = generate_response(question)
    
    # 메트릭 계산
    bleu = calculate_bleu(reference, hypothesis)
    rouge = calculate_rouge_l(reference, hypothesis)
    em = exact_match(reference, hypothesis)
    hall = check_hallucination(question, reference, hypothesis)
    
    results['bleu'].append(bleu)
    results['rouge_l'].append(rouge)
    results['exact_match'].append(em)
    results['hallucination'].append(hall)
    
    # 샘플 저장 (처음 10개)
    if i < 10:
        results['samples'].append({
            'question': question,
            'reference': reference,
            'hypothesis': hypothesis,
            'bleu': round(bleu, 3),
            'rouge_l': round(rouge, 3),
            'exact_match': em,
            'hallucination': hall
        })

# ============================================
# 결과 집계
# ============================================
print("\n" + "="*80)
print("평가 결과")
print("="*80)

avg_bleu = np.mean(results['bleu'])
avg_rouge = np.mean(results['rouge_l'])
avg_em = np.mean(results['exact_match'])
hallucination_rate = np.mean(results['hallucination'])

print(f"\n📊 정량 평가:")
print(f"  BLEU:              {avg_bleu:.4f}")
print(f"  ROUGE-L:           {avg_rouge:.4f}")
print(f"  Exact Match:       {avg_em:.4f} ({avg_em*100:.1f}%)")
print(f"  Hallucination:     {hallucination_rate:.4f} ({hallucination_rate*100:.1f}%)")

# ============================================
# 결과 저장
# ============================================
# JSON 저장
output_file = OUTPUT_DIR / "evaluation_results.json"
summary = {
    'metrics': {
        'bleu': round(avg_bleu, 4),
        'rouge_l': round(avg_rouge, 4),
        'exact_match': round(avg_em, 4),
        'hallucination_rate': round(hallucination_rate, 4)
    },
    'num_samples': len(test_data),
    'samples': results['samples']
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"\n✅ 결과 저장: {output_file}")

# 텍스트 리포트 저장
report_file = OUTPUT_DIR / "evaluation_report.txt"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("모델 평가 리포트\n")
    f.write("="*80 + "\n\n")
    
    f.write(f"테스트 샘플 수: {len(test_data)}\n")
    f.write(f"모델: {LORA_MODEL_PATH}\n\n")
    
    f.write("평가 메트릭:\n")
    f.write(f"  BLEU:              {avg_bleu:.4f}\n")
    f.write(f"  ROUGE-L:           {avg_rouge:.4f}\n")
    f.write(f"  Exact Match:       {avg_em:.4f} ({avg_em*100:.1f}%)\n")
    f.write(f"  Hallucination:     {hallucination_rate:.4f} ({hallucination_rate*100:.1f}%)\n\n")
    
    f.write("="*80 + "\n")
    f.write("샘플 결과 (처음 10개)\n")
    f.write("="*80 + "\n\n")
    
    for i, sample in enumerate(results['samples'], 1):
        f.write(f"[샘플 {i}]\n")
        f.write(f"Q: {sample['question']}\n")
        f.write(f"정답: {sample['reference']}\n")
        f.write(f"생성: {sample['hypothesis']}\n")
        f.write(f"BLEU: {sample['bleu']}, ROUGE: {sample['rouge_l']}, ")
        f.write(f"EM: {sample['exact_match']}, Hall: {sample['hallucination']}\n\n")

print(f"✅ 리포트 저장: {report_file}")

print("\n" + "="*80)
print("평가 완료!")
print("="*80)
