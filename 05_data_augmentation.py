#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 증강 스크립트
- GPT-4를 이용한 Paraphrasing
- 부정 샘플 생성
- 질문 변형
"""

import json
import time
from pathlib import Path
from tqdm import tqdm
import random

# OpenAI API 설정 (사용 시 API 키 필요)
# from openai import OpenAI
# client = OpenAI(api_key="YOUR_API_KEY")

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

# ============================================
# 방법 1: 규칙 기반 변형 (무료)
# ============================================
def paraphrase_rule_based(instruction):
    """
    규칙 기반 질문 변형
    API 없이도 사용 가능
    """
    variants = []
    
    # 패턴 1: 존댓말 <-> 반말
    if instruction.endswith('요') or instruction.endswith('까'):
        # 존댓말 버전
        variants.append(instruction)
        # 반말 버전
        plain = instruction.replace('인가요', '인가').replace('알려주세요', '알려줘')
        plain = plain.replace('설명해주세요', '설명해줘').replace('무엇입니까', '뭐야')
        if plain != instruction:
            variants.append(plain)
    
    # 패턴 2: 질문 형식 변형
    if '?' in instruction or '무엇' in instruction or '얼마' in instruction:
        # "X는 무엇인가요?" → "X에 대해 알려주세요"
        if '무엇' in instruction:
            topic = instruction.split('무엇')[0].strip()
            variants.append(f"{topic}에 대해 설명해주세요")
            variants.append(f"{topic}이 궁금합니다")
        
        # "X 알려주세요" → "X가 궁금해요"
        if '알려주세요' in instruction:
            topic = instruction.replace('알려주세요', '').strip()
            variants.append(f"{topic}가 궁금합니다")
            variants.append(f"{topic}는 뭔가요?")
    
    # 패턴 3: 안녕하세요 추가/제거
    if instruction.startswith('안녕하세요'):
        variants.append(instruction.replace('안녕하세요. ', ''))
    else:
        variants.append(f"안녕하세요. {instruction}")
    
    return list(set(variants))[:3]  # 최대 3개 변형

def generate_negative_samples():
    """
    부정 샘플 생성
    (범위 외 질문에 대한 거절 답변)
    """
    negative_samples = [
        {
            "instruction": "내일 날씨 어때?",
            "input": "",
            "output": "죄송합니다. 건강보험심사평가원(HIRA) 데이터와 관련된 질문에만 답변할 수 있습니다."
        },
        {
            "instruction": "주식 투자 방법 알려줘",
            "input": "",
            "output": "죄송합니다. 저는 의료 및 건강보험 데이터 전문 어시스턴트입니다. HIRA 데이터 관련 질문을 해주세요."
        },
        {
            "instruction": "맛집 추천해줘",
            "input": "",
            "output": "죄송합니다. 건강보험 및 의료 데이터에 관한 질문만 답변 가능합니다."
        },
        {
            "instruction": "영어 공부 방법은?",
            "input": "",
            "output": "죄송합니다. 저는 HIRA(건강보험심사평가원) 데이터 전문 AI입니다. 의료 통계나 건강보험 관련 질문을 해주세요."
        },
        {
            "instruction": "이 코드 오류 좀 봐줘",
            "input": "",
            "output": "죄송합니다. 프로그래밍 관련 질문은 답변할 수 없습니다. 건강보험 데이터 관련 질문을 해주세요."
        },
        {
            "instruction": "너는 누구야?",
            "input": "",
            "output": "저는 건강보험심사평가원(HIRA) 데이터를 기반으로 학습한 의료 정보 어시스턴트입니다. 의료 통계, 상병 코드, 약물 정보 등에 대해 답변할 수 있습니다."
        },
        {
            "instruction": "심심해",
            "input": "",
            "output": "건강보험이나 의료 데이터에 대해 궁금한 점이 있으시면 언제든 질문해주세요!"
        },
    ]
    return negative_samples

# ============================================
# 방법 2: GPT-4 기반 변형 (유료, 고품질)
# ============================================
def paraphrase_with_gpt4(instruction, api_key=None):
    """
    GPT-4를 이용한 고품질 Paraphrasing
    주의: API 키와 비용 필요
    """
    if api_key is None:
        print("⚠️  GPT-4 API 키가 없습니다. 규칙 기반 변형을 사용합니다.")
        return paraphrase_rule_based(instruction)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""다음 질문을 의미는 유지하면서 3가지 다른 방식으로 바꿔주세요.
원래 질문: {instruction}

요구사항:
1. 의미는 정확히 유지
2. 존댓말/반말 섞어서
3. 질문 형식 다양하게
4. 각 변형은 한 줄로

변형1: 
변형2: 
변형3:"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 한국어 paraphrasing 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        result = response.choices[0].message.content
        
        # 결과 파싱
        variants = []
        for line in result.split('\n'):
            if line.startswith('변형'):
                variant = line.split(':', 1)[1].strip()
                if variant:
                    variants.append(variant)
        
        return variants[:3]
    
    except Exception as e:
        print(f"⚠️  GPT-4 호출 실패: {e}")
        return paraphrase_rule_based(instruction)

# ============================================
# 메인 증강 함수
# ============================================
def augment_data(input_file, output_file, method='rule', api_key=None, augment_ratio=2.0):
    """
    데이터 증강
    
    Args:
        input_file: 입력 파일 경로
        output_file: 출력 파일 경로
        method: 'rule' (규칙 기반) 또는 'gpt4' (GPT-4 기반)
        api_key: OpenAI API 키 (method='gpt4'일 때 필요)
        augment_ratio: 증강 비율 (2.0 = 2배로 증가)
    """
    print("="*80)
    print("데이터 증강")
    print("="*80)
    print(f"방법: {method}")
    print(f"증강 비율: {augment_ratio}x")
    
    # 원본 데이터 로드
    original_data = load_jsonl(input_file)
    print(f"\n원본 데이터: {len(original_data)}개")
    
    # 증강된 데이터 저장소
    augmented_data = original_data.copy()
    
    # 부정 샘플 추가
    negative_samples = generate_negative_samples()
    augmented_data.extend(negative_samples)
    print(f"부정 샘플 추가: {len(negative_samples)}개")
    
    # 기존 데이터 변형
    target_count = int(len(original_data) * augment_ratio)
    samples_to_augment = target_count - len(augmented_data)
    
    if samples_to_augment > 0:
        print(f"\n변형 생성 중... (목표: {samples_to_augment}개)")
        
        # 샘플 선택 (균등하게)
        selected_indices = random.choices(
            range(len(original_data)),
            k=samples_to_augment
        )
        
        for idx in tqdm(selected_indices):
            item = original_data[idx]
            instruction = item['instruction']
            
            # 변형 생성
            if method == 'gpt4':
                variants = paraphrase_with_gpt4(instruction, api_key)
                time.sleep(0.5)  # API rate limit 고려
            else:
                variants = paraphrase_rule_based(instruction)
            
            # 변형 추가 (원본 답변 유지)
            for variant in variants:
                if variant and variant != instruction:
                    augmented_data.append({
                        "instruction": variant,
                        "input": item['input'],
                        "output": item['output']
                    })
                
                # 목표 도달 시 중단
                if len(augmented_data) >= target_count:
                    break
            
            if len(augmented_data) >= target_count:
                break
    
    # 저장
    save_jsonl(augmented_data, output_file)
    
    print(f"\n최종 데이터: {len(augmented_data)}개")
    print(f"증가율: {len(augmented_data) / len(original_data):.2f}x")
    print(f"\n✅ 저장 완료: {output_file}")
    
    # 샘플 출력
    print("\n" + "="*80)
    print("증강 샘플 예시")
    print("="*80)
    
    for i, item in enumerate(augmented_data[-5:], 1):
        print(f"\n[샘플 {i}]")
        print(f"Q: {item['instruction']}")
        print(f"A: {item['output'][:80]}...")

# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    # 경로 설정
    input_file = Path("cleaned_data/train.jsonl")
    output_file = Path("augmented_data/train_augmented.jsonl")
    output_file.parent.mkdir(exist_ok=True)
    
    # 방법 선택
    print("\n데이터 증강 방법을 선택하세요:")
    print("1. 규칙 기반 (무료, 즉시)")
    print("2. GPT-4 기반 (유료, 고품질)")
    
    # 규칙 기반 실행 (기본)
    print("\n규칙 기반 증강을 실행합니다...")
    augment_data(
        input_file=input_file,
        output_file=output_file,
        method='rule',
        augment_ratio=2.5  # 2.5배로 증가
    )
    
    # GPT-4 사용 시 (API 키 필요)
    # API_KEY = "your-api-key-here"
    # augment_data(
    #     input_file=input_file,
    #     output_file=output_file,
    #     method='gpt4',
    #     api_key=API_KEY,
    #     augment_ratio=3.0
    # )
    
    print("\n" + "="*80)
    print("✅ 완료!")
    print("="*80)
    print("\n다음 단계:")
    print("1. 증강된 데이터로 재학습")
    print("2. validation 성능 비교")
    print("3. test set 평가")
