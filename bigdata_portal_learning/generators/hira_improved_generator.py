#!/usr/bin/env python3
"""
HIRA 개선된 학습 데이터 생성기
- 중복 접두사/접미사 제거
- 자연스러운 변형만 생성
- 목표: 3,000-5,000건
"""

import yaml
import json
import random
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter

class HIRAImprovedGenerator:
    def __init__(self, core_qa_path: str):
        """초기화"""
        with open(core_qa_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.core_qa = data['core_qa']
        self.training_data = []

        # 동의어 사전 (확장)
        self.synonyms = {
            '신청': ['요청', '등록', '접수'],
            '방법': ['절차', '과정', '프로세스'],
            '확인': ['조회', '검색', '찾기', '보기'],
            '가능': ['되나요', '할 수 있나요'],
            '어디서': ['어느 곳에서', '어느 메뉴에서', '어디에서'],
            '어떻게': ['어떤 방법으로', '어떤 식으로', '어떻게'],
            '무엇': ['뭐', '어떤 것'],
            '데이터': ['자료', '정보'],
            '분석': ['연구', '분석'],
            '통계': ['수치', '통계'],
            '제공': ['제공', '지원', '제시'],
            '사용': ['이용', '활용'],
            '다운로드': ['내려받기', '받기'],
            '업로드': ['올리기', '업로드'],
            '변경': ['수정', '변경', '편집'],
            '삭제': ['제거', '삭제'],
            '비용': ['금액', '요금', '비용'],
            '무료': ['공짜', '무료'],
            '포함': ['포함', '담기'],
        }

    def generate(self, target_count: int = 8000):
        """학습 데이터 생성"""

        print("="*80)
        print("HIRA 개선된 학습 데이터 생성")
        print("="*80)
        print(f"목표: {target_count:,}건\n")

        # 1. 핵심 Q&A 카운트
        core_count = sum(len(items) for items in self.core_qa.values())
        print(f"핵심 Q&A: {core_count}개")

        # 2. 각 Q&A당 생성할 변형 수
        variants_per_qa = (target_count - core_count) // core_count
        print(f"각 Q&A당 약 {variants_per_qa}개 변형 생성\n")

        # 3. 원본 추가
        for menu, items in self.core_qa.items():
            for item in items:
                question = item['q']
                answer = item['a']
                self.training_data.append({
                    "instruction": question,
                    "input": "",
                    "output": answer
                })

        # 4. 변형 생성
        for menu, items in self.core_qa.items():
            for item in items:
                original_q = item['q']
                answer = item['a']

                # 각 Q&A에 대해 variants_per_qa개 변형 생성
                generated = 0
                attempts = 0
                max_attempts = variants_per_qa * 5  # 시도 횟수 증가

                while generated < variants_per_qa and attempts < max_attempts:
                    variant = self._generate_natural_variant(original_q)

                    if variant and variant != original_q:
                        # 오타/맞춤법 검증
                        variant = self._fix_typos(variant)

                        # 중복 체크
                        if not any(item['instruction'] == variant for item in self.training_data):
                            self.training_data.append({
                                "instruction": variant,
                                "input": "",
                                "output": answer
                            })
                            generated += 1

                    attempts += 1

        print(f"{'='*80}")
        print(f"✅ 생성 완료: {len(self.training_data):,}건")
        print(f"{'='*80}\n")

        return self.training_data

    def _generate_natural_variant(self, original_q: str) -> str:
        """자연스러운 변형 생성 (품질 우선)"""

        variants = []

        # 1. 어미 변형 (8회)
        for _ in range(8):
            variants.extend(self._변형_어미(original_q))

        # 2. 질문 형식 변형 (8회)
        for _ in range(8):
            variants.extend(self._변형_질문형식(original_q))

        # 3. 동의어 치환 (8회)
        for _ in range(8):
            variants.extend(self._변형_동의어(original_q))

        # 4. 조사 변형 (8회)
        for _ in range(8):
            variants.extend(self._변형_조사(original_q))

        # 5. 축약/확장 (8회)
        for _ in range(8):
            variants.extend(self._변형_축약확장(original_q))

        # 6. 의문사 변형 (8회)
        for _ in range(8):
            variants.extend(self._변형_의문사(original_q))

        # 중복 제거
        unique_variants = list(set(variants))

        # 원본 제외
        valid_variants = [v for v in unique_variants if v != original_q and len(v) >= 5 and len(v) <= 100]

        if valid_variants:
            return random.choice(valid_variants)
        else:
            return None

    def _변형_어미(self, question: str) -> List[str]:
        """어미 변형 (존댓말/반말) - 랜덤화"""
        variants = []

        patterns = [
            (r'(.+)하나요\?', [r'\1해요?', r'\1할까요?', r'\1하죠?', r'\1합니까?']),
            (r'(.+)인가요\?', [r'\1이에요?', r'\1일까요?', r'\1이죠?', r'\1입니까?']),
            (r'(.+)있나요\?', [r'\1있어요?', r'\1있을까요?', r'\1있죠?', r'\1있습니까?']),
            (r'(.+)되나요\?', [r'\1돼요?', r'\1될까요?', r'\1되죠?', r'\1됩니까?']),
            (r'(.+)가능한가요\?', [r'\1가능해요?', r'\1가능할까요?', r'\1할 수 있나요?', r'\1가능합니까?']),
            (r'(.+)뭔가요\?', [r'\1뭐예요?', r'\1무엇인가요?', r'\1뭐죠?', r'\1무엇입니까?']),
            (r'(.+)어떻게\?', [r'\1어떤 방법으로?', r'\1어떤 식으로?', r'\1어떻게 해요?']),
            (r'(.+)어디서\?', [r'\1어느 곳에서?', r'\1어디에서?', r'\1어느 메뉴에서?']),
            (r'(.+)왜\?', [r'\1왜요?', r'\1이유가 뭐예요?', r'\1왜 그런가요?']),
            (r'(.+)언제\?', [r'\1언제요?', r'\1언제인가요?', r'\1시기는?']),
            (r'(.+)얼마\?', [r'\1얼마예요?', r'\1얼마인가요?', r'\1비용은?']),
        ]

        for pattern, replacements in patterns:
            if re.search(pattern, question):
                # 랜덤하게 1-2개만 선택
                selected = random.sample(replacements, k=min(2, len(replacements)))
                for repl in selected:
                    variant = re.sub(pattern, repl, question)
                    if variant != question:
                        variants.append(variant)

        return variants

    def _변형_질문형식(self, question: str) -> List[str]:
        """질문 형식 변형"""
        variants = []

        patterns = [
            (r'(.+) 어떻게 하나요\?', [r'\1 방법은?', r'\1 방법이 어떻게 되나요?', r'\1 어떤 식으로 하나요?']),
            (r'(.+) 뭔가요\?', [r'\1이 무엇인가요?', r'\1에 대해 알려주세요', r'\1 설명해주세요', r'\1은 뭔가요?']),
            (r'(.+) 어디서 (.+)\?', [r'\2 어디에서 하나요?', r'\2 어느 곳에서 하나요?', r'\1 어디서 \2?']),
            (r'(.+) 가능한가요\?', [r'\1 수 있나요?', r'\1 되나요?', r'\1 할 수 있나요?']),
            (r'(.+)은 무엇인가요\?', [r'\1이 뭔가요?', r'\1에 대해 설명해주세요', r'\1을 알려주세요']),
            (r'(.+)를 어떻게\?', [r'\1 어떻게 하나요?', r'\1 방법은?', r'\1 어떤 식으로 하나요?']),
            (r'(.+)이 있나요\?', [r'\1 있어요?', r'\1이 제공되나요?', r'\1 확인할 수 있나요?']),
        ]

        for pattern, replacements in patterns:
            if re.search(pattern, question):
                for repl in replacements:
                    variant = re.sub(pattern, repl, question)
                    if variant != question:
                        variants.append(variant)

        return variants

    def _변형_동의어(self, question: str) -> List[str]:
        """동의어 치환 - 랜덤화"""
        variants = []

        # 질문에 있는 단어 찾기
        matching_words = [word for word in self.synonyms.keys() if word in question]

        # 랜덤하게 1-2개 단어만 선택
        if matching_words:
            selected_words = random.sample(matching_words, k=min(2, len(matching_words)))

            for word in selected_words:
                synonyms = self.synonyms[word]
                # 각 단어당 랜덤하게 1개 동의어만 선택
                synonym = random.choice(synonyms)
                variant = question.replace(word, synonym)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_조사(self, question: str) -> List[str]:
        """조사 변형"""
        variants = []

        replacements = [
            ('은', '는'),
            ('이', '가'),
            ('을', '를'),
            ('과', '와'),
        ]

        for old, new in replacements:
            if old in question:
                variant = question.replace(old, new, 1)
                variants.append(variant)

        return variants

    def _변형_축약확장(self, question: str) -> List[str]:
        """축약 또는 확장"""
        variants = []

        # 축약
        abbr_patterns = [
            (r'(.+) 어떻게 (.+)\?', r'\1 \2?'),
            (r'(.+) 어떤 (.+)\?', r'\1 \2?'),
        ]

        for pattern, replacement in abbr_patterns:
            if re.match(pattern, question):
                variant = re.sub(pattern, replacement, question)
                if variant != question:
                    variants.append(variant)

        # 확장
        if not question.endswith('?'):
            variants.append(question + '?')

        return variants

    def _변형_단어순서(self, question: str) -> List[str]:
        """단어 순서 변경"""
        variants = []

        # 간단한 순서 변경 패턴
        patterns = [
            (r'(.+) 어디서 (.+)', r'\2 어디서 하나요?'),
            (r'(.+)은 (.+)', r'\2 \1은?'),
            (r'(.+)와 (.+) 차이', r'\2와 \1 차이'),
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, question):
                variant = re.sub(pattern, replacement, question)
                if variant != question:
                    variants.append(variant)

        return variants

    def _변형_의문사(self, question: str) -> List[str]:
        """의문사 변형"""
        variants = []

        replacements = [
            ('뭔가요', '무엇인가요'),
            ('무엇인가요', '뭔가요'),
            ('어떻게', '어떤 방법으로'),
            ('어떤 방법으로', '어떻게'),
            ('어디서', '어느 곳에서'),
            ('어느 곳에서', '어디서'),
            ('언제', '몇 시에'),
            ('왜', '어떤 이유로'),
        ]

        for old, new in replacements:
            if old in question:
                variant = question.replace(old, new)
                if variant != question:
                    variants.append(variant)

        return variants

    def _is_valid_variant(self, text: str) -> bool:
        """변형 품질 검증"""

        # 최소 길이
        if len(text) < 5:
            return False

        # 최대 길이 (너무 긴 것 제외)
        if len(text) > 100:
            return False

        # 중복 조사 패턴 체크
        invalid_patterns = [
            r'([가-힣])(는|은|을|를|이|가)(는|은|을|를|이|가)',  # 중복 조사
            r'([가-힣]) (는|은|을|를|이|가)',  # 조사 앞 공백
            r'(수|할|될|받|볼) (수|할|될|받|볼)',  # 중복 동사
            r'어떻게 어떻게',  # 중복 의문사
            r'뭔가요 뭔가요',
            r'있나요 있나요',
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, text):
                return False

        # 필수 종결어미 체크 (질문이므로) - 확장
        valid_endings = [
            '?', '요?', '죠?', '나요?', '까요?', '해요?', '가요?',
            '요', '죠', '나요', '까요', '해요', '가요', '예요', '세요',
            '는요', '에요', '어요', '여요', '래요', '대요',
            '인가요', '인가요?', '습니까', '습니까?', '입니까', '입니까?',
            '될까요', '될까요?', '할까요', '할까요?',
            '조회', '신청', '방법', '절차', '확인', '검색',
            '있나요', '있나요?', '있어요', '있어요?',
            '되나요', '되나요?', '돼요', '돼요?',
            '뭐죠', '뭐죠?', '뭔가요', '뭔가요?', '무엇인가요', '무엇인가요?',
        ]
        if not any(text.endswith(e) for e in valid_endings):
            return False

        return True

    def _fix_typos(self, text: str) -> str:
        """오타/맞춤법 수정 (강화 버전)"""

        # 자주 발생하는 오타 패턴
        typo_fixes = [
            # 데이터 관련
            ('데가터', '데이터'),
            ('데이가', '데이터'),
            ('자료', '자료'),  # 패턴 유지

            # 조사 오류 - 받침 있는 단어
            ('기간는', '기간은'),
            ('방법는', '방법은'),
            ('목록는', '목록은'),
            ('통계는', '통계는'),
            ('정보는', '정보는'),
            ('공지사항는', '공지사항은'),
            ('데이터셋는', '데이터셋은'),
            ('코드는', '코드는'),  # 패턴 유지
            ('제한는', '제한은'),
            ('용량는', '용량은'),
            ('파일는', '파일은'),
            ('약관는', '약관은'),
            ('질문는', '질문은'),
            ('이용는', '이용은'),
            ('사용는', '사용은'),

            # 동사 오류
            ('받를', '받을'),
            ('사용를', '사용을'),
            ('이용를', '이용을'),
            ('확인를', '확인을'),
            ('할를', '할'),
            ('될를', '될'),
            ('수 있를', '수 있을'),
            ('와제', '과제'),
            ('가용', '이용'),
            ('수 있를까요', '수 있을까요'),

            # 공백 오류
            (' 는', '는'),
            (' 은', '은'),
            (' 을', '을'),
            (' 를', '를'),
            (' 이', '이'),
            (' 가', '가'),
            ('  ', ' '),  # 중복 공백

            # 의문사 오류
            ('누가이용', '누가 이용'),
            ('어디서검색', '어디서 검색'),
            ('어떻게해요', '어떻게 해요'),
        ]

        for wrong, correct in typo_fixes:
            text = text.replace(wrong, correct)

        # 정규식 기반 조사 오류 수정
        text = re.sub(r'([가-힣])는는', r'\1는', text)
        text = re.sub(r'([가-힣])은은', r'\1은', text)
        text = re.sub(r'([가-힣])을을', r'\1을', text)
        text = re.sub(r'([가-힣])를를', r'\1를', text)
        text = re.sub(r'([가-힣])이이', r'\1이', text)
        text = re.sub(r'([가-힣])가가', r'\1가', text)

        # 동사 중복 수정
        text = re.sub(r'(할|될|받|볼) (할|될|받|볼)', r'\1', text)
        text = re.sub(r'수 있를', '수 있을', text)
        text = re.sub(r'수 있을를', '수 있을', text)

        # 명사+조사 붙어쓰기 수정 (은/는)
        text = re.sub(r'([가-힣]{2,})은([가-힣])', lambda m: m.group(1) + '은 ' + m.group(2) if m.group(2) in '가나다라마바사아자차카타파하' else m.group(0), text)
        text = re.sub(r'([가-힣]{2,})는([가-힣])', lambda m: m.group(1) + '는 ' + m.group(2) if m.group(2) in '가나다라마바사아자차카타파하' else m.group(0), text)

        # 흔한 붙어쓰기 오류
        text = re.sub(r'매칭은가능', '매칭은 가능', text)
        text = re.sub(r'사용은수', '사용은 수', text)
        text = re.sub(r'이용은가능', '이용은 가능', text)
        text = re.sub(r'신청은어떻게', '신청은 어떻게', text)

        return text

    def get_statistics(self) -> Dict:
        """통계 정보"""
        questions = [item['instruction'] for item in self.training_data]
        answers = [item['output'] for item in self.training_data]

        q_lengths = [len(q) for q in questions]
        a_lengths = [len(a) for a in answers]

        # 질문 시작 패턴
        start_patterns = Counter()
        for q in questions:
            words = q.split()[:2]
            pattern = ' '.join(words) if len(words) >= 2 else q[:10]
            start_patterns[pattern] += 1

        return {
            "total": len(self.training_data),
            "q_length_avg": sum(q_lengths) / len(q_lengths),
            "q_length_min": min(q_lengths),
            "q_length_max": max(q_lengths),
            "a_length_avg": sum(a_lengths) / len(a_lengths),
            "a_length_min": min(a_lengths),
            "a_length_max": max(a_lengths),
            "start_patterns": start_patterns.most_common(10),
        }

    def save_jsonl(self, output_path: str):
        """JSONL 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"✅ JSONL 저장 완료: {output_path}")
        print(f"   총 {len(self.training_data):,}건\n")

    def save_json(self, output_path: str):
        """JSON 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.training_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON 저장 완료: {output_path}\n")

    def print_samples(self, count: int = 10):
        """샘플 출력"""
        print(f"{'='*80}")
        print(f"📝 무작위 샘플 {count}개")
        print(f"{'='*80}\n")

        samples = random.sample(self.training_data, min(count, len(self.training_data)))

        for i, sample in enumerate(samples, 1):
            print(f"[샘플 {i}]")
            print(f"Q: {sample['instruction']}")
            print(f"A: {sample['output'][:80]}...\n")

    def print_statistics(self):
        """통계 출력"""
        stats = self.get_statistics()

        print(f"{'='*80}")
        print(f"📊 데이터 통계")
        print(f"{'='*80}\n")

        print(f"[질문 길이]")
        print(f"  평균: {stats['q_length_avg']:.1f}자")
        print(f"  최소: {stats['q_length_min']}자")
        print(f"  최대: {stats['q_length_max']}자\n")

        print(f"[답변 길이]")
        print(f"  평균: {stats['a_length_avg']:.1f}자")
        print(f"  최소: {stats['a_length_min']}자")
        print(f"  최대: {stats['a_length_max']}자\n")

        print(f"[질문 시작 패턴 TOP 10]")
        for i, (pattern, count) in enumerate(stats['start_patterns'], 1):
            pct = (count / stats['total']) * 100
            print(f"  {i:2d}. {pattern:30s}: {count:4,}건 ({pct:4.1f}%)")


def main():
    # 경로 설정
    core_qa_path = "/home/user/bigdataptAI/bigdata_portal_learning/config/hira_core_qa_expanded.yaml"
    output_jsonl = "/home/user/bigdataptAI/bigdata_portal_learning/output/hira_train_final.jsonl"
    output_json = "/home/user/bigdataptAI/bigdata_portal_learning/output/hira_train_final.json"

    # 생성기 초기화
    generator = HIRAImprovedGenerator(core_qa_path)

    # 데이터 생성 (목표: 3,000건 - 현실적 목표)
    generator.generate(target_count=3000)

    # 통계 출력
    generator.print_statistics()

    # 샘플 출력
    generator.print_samples(10)

    # 저장
    generator.save_jsonl(output_jsonl)
    generator.save_json(output_json)

    print(f"{'='*80}")
    print(f"✅ 개선된 데이터 생성 완료!")
    print(f"{'='*80}\n")

    print(f"📁 생성 파일:")
    print(f"  1. {output_jsonl} (학습용)")
    print(f"  2. {output_json} (검토용)\n")


if __name__ == "__main__":
    main()
