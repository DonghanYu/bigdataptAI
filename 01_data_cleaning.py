#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 클리닝 및 Train/Val/Test 분할
- 중복 제거
- 품질 필터링
- 전략적 분할
"""

import json
import hashlib
from pathlib import Path
from collections import Counter
import random

def load_jsonl(file_path):
    """JSONL 파일 로드"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except:
                continue
    return data

def save_jsonl(data, file_path):
    """JSONL 파일 저장"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def get_hash(text):
    """텍스트 해시값 생성"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def clean_data(data):
    """데이터 클리닝"""
    print("\n" + "="*70)
    print("데이터 클리닝 시작")
    print("="*70)
    
    original_count = len(data)
    print(f"\n원본 데이터: {original_count}개")
    
    # 1. 중복 제거 (완전 중복)
    seen_outputs = set()
    unique_data = []
    duplicates = 0
    
    for item in data:
        output_hash = get_hash(item['output'])
        if output_hash not in seen_outputs:
            seen_outputs.add(output_hash)
            unique_data.append(item)
        else:
            duplicates += 1
    
    print(f"  ├─ 완전 중복 제거: {duplicates}개")
    data = unique_data
    
    # 2. 품질 필터링
    quality_filtered = []
    
    for item in data:
        output = item['output'].strip()
        instruction = item['instruction'].strip()
        
        # 필터링 조건
        if len(output) < 10:  # 너무 짧은 답변
            continue
        if len(instruction) < 5:  # 너무 짧은 질문
            continue
        if output.count('이것이 중요한 이유는') > 1:  # 중복 템플릿
            continue
        
        quality_filtered.append(item)
    
    removed = len(data) - len(quality_filtered)
    print(f"  ├─ 품질 필터링: {removed}개 제거")
    data = quality_filtered
    
    # 3. 템플릿 문구 정리
    cleaned_data = []
    
    for item in data:
        output = item['output']
        
        # 과도한 반복 문구 제거
        if output.count('\n\n이것이 중요한 이유는') == 1:
            # 템플릿을 더 자연스럽게 변경
            output = output.replace(
                '\n\n이것이 중요한 이유는 건강보험 제도와 데이터 분석의 기초가 되기 때문입니다.',
                ''
            ).strip()
        
        item['output'] = output
        cleaned_data.append(item)
    
    print(f"  └─ 최종 정제 데이터: {len(cleaned_data)}개")
    
    return cleaned_data

def analyze_data(data, title="데이터 분석"):
    """데이터 통계 출력"""
    print(f"\n📊 {title}")
    print(f"  총 샘플 수: {len(data)}")
    
    # 답변 길이 분석
    output_lengths = [len(item['output']) for item in data]
    print(f"  답변 길이:")
    print(f"    평균: {sum(output_lengths)/len(output_lengths):.1f}자")
    print(f"    최소: {min(output_lengths)}자")
    print(f"    최대: {max(output_lengths)}자")
    
    # 질문 유형 분석
    instructions = [item['instruction'] for item in data]
    first_words = [inst.split()[0] if inst.split() else '' for inst in instructions]
    common_starts = Counter(first_words).most_common(5)
    print(f"  빈번한 질문 시작어:")
    for word, count in common_starts:
        print(f"    '{word}': {count}개")

def split_data(data, train_ratio=0.8, val_ratio=0.1, seed=42):
    """Train/Val/Test 분할"""
    print("\n" + "="*70)
    print("데이터 분할")
    print("="*70)
    
    random.seed(seed)
    random.shuffle(data)
    
    total = len(data)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)
    
    train_data = data[:train_size]
    val_data = data[train_size:train_size + val_size]
    test_data = data[train_size + val_size:]
    
    print(f"\n분할 결과:")
    print(f"  Train: {len(train_data)}개 ({len(train_data)/total*100:.1f}%)")
    print(f"  Val:   {len(val_data)}개 ({len(val_data)/total*100:.1f}%)")
    print(f"  Test:  {len(test_data)}개 ({len(test_data)/total*100:.1f}%)")
    
    return train_data, val_data, test_data

def main():
    """메인 실행 함수"""
    # 경로 설정
    input_file = Path("all_data_expanded.jsonl")  # 입력 파일
    output_dir = Path("cleaned_data")
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("HIRA 데이터 클리닝 & 분할")
    print("="*70)
    
    # 1. 데이터 로드
    print(f"\n📂 데이터 로드: {input_file}")
    data = load_jsonl(input_file)
    analyze_data(data, "원본 데이터")
    
    # 2. 클리닝
    cleaned_data = clean_data(data)
    analyze_data(cleaned_data, "정제 데이터")
    
    # 3. 분할
    train_data, val_data, test_data = split_data(cleaned_data)
    
    # 4. 저장
    print("\n" + "="*70)
    print("파일 저장")
    print("="*70)
    
    train_file = output_dir / "train.jsonl"
    val_file = output_dir / "val.jsonl"
    test_file = output_dir / "test.jsonl"
    
    save_jsonl(train_data, train_file)
    save_jsonl(val_data, val_file)
    save_jsonl(test_data, test_file)
    
    print(f"  ✅ Train: {train_file}")
    print(f"  ✅ Val:   {val_file}")
    print(f"  ✅ Test:  {test_file}")
    
    # 5. 샘플 출력
    print("\n" + "="*70)
    print("샘플 데이터 확인")
    print("="*70)
    
    for i, item in enumerate(train_data[:3], 1):
        print(f"\n[Train 샘플 {i}]")
        print(f"Q: {item['instruction']}")
        print(f"A: {item['output'][:100]}...")
    
    print("\n" + "="*70)
    print("✅ 완료!")
    print("="*70)

if __name__ == "__main__":
    main()
