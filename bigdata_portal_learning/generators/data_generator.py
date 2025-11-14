#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빅데이터개방포털 학습 데이터 생성기
템플릿 기반으로 7,000건의 학습 데이터 자동 생성
"""

import json
import random
import yaml
from pathlib import Path
from typing import List, Dict
from itertools import product
import re

class BigDataPortalDataGenerator:
    def __init__(self, config_dir: str):
        """
        데이터 생성기 초기화

        Args:
            config_dir: 설정 파일이 있는 디렉토리 경로
        """
        self.config_dir = Path(config_dir)
        self.menu_structure = self._load_yaml('menu_structure.yaml')
        self.question_templates = self._load_yaml('question_templates.yaml')
        self.generated_data = []
        self.question_set = set()  # 중복 체크용

    def _load_yaml(self, filename: str) -> dict:
        """YAML 파일 로드"""
        with open(self.config_dir / filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_all_data(self, target_count: int = 7000) -> List[Dict]:
        """
        전체 데이터 생성

        Args:
            target_count: 생성할 총 데이터 개수

        Returns:
            생성된 데이터 리스트
        """
        print("="*80)
        print("빅데이터개방포털 학습 데이터 생성 시작")
        print("="*80)
        print(f"목표: {target_count:,}건 생성\n")

        # 1. 메뉴별로 데이터 생성
        for menu_key, menu_info in self.menu_structure['menus'].items():
            menu_name = menu_info['name']
            weight = menu_info['weight']
            topics = menu_info['topics']

            print(f"\n📂 {menu_name} ({weight}건 목표)")
            print("-" * 60)

            menu_data = self._generate_menu_data(menu_key, menu_info)

            print(f"   ✅ 생성 완료: {len(menu_data)}건")

            self.generated_data.extend(menu_data)

        # 2. 목표 개수 맞추기 (부족하면 추가 생성)
        current_count = len(self.generated_data)
        if current_count < target_count:
            shortage = target_count - current_count
            print(f"\n⚠️  목표 개수 부족 ({current_count}/{target_count})")
            print(f"   추가 생성: {shortage}건")

            additional_data = self._generate_additional_data(shortage)
            self.generated_data.extend(additional_data)

        # 3. 데이터 섞기
        random.shuffle(self.generated_data)

        # 4. 최종 개수 조정
        self.generated_data = self.generated_data[:target_count]

        print("\n" + "="*80)
        print(f"✅ 생성 완료: 총 {len(self.generated_data):,}건")
        print("="*80)

        return self.generated_data

    def _generate_menu_data(self, menu_key: str, menu_info: dict) -> List[Dict]:
        """메뉴별 데이터 생성"""
        menu_data = []
        weight = menu_info['weight']
        topics = menu_info['topics']

        # 각 주제별 생성 개수 계산
        per_topic = weight // len(topics)

        for topic in topics:
            topic_data = self._generate_topic_data(menu_key, topic, per_topic)
            menu_data.extend(topic_data)

        return menu_data

    def _generate_topic_data(self, menu_key: str, topic: dict, count: int) -> List[Dict]:
        """주제별 데이터 생성"""
        topic_data = []
        topic_id = topic['id']
        topic_name = topic['name']
        keywords = topic.get('keywords', [])

        attempts = 0
        max_attempts = count * 5  # 중복 방지를 위한 최대 시도 횟수

        while len(topic_data) < count and attempts < max_attempts:
            attempts += 1

            # 질문-답변 쌍 생성
            qa_pair = self._generate_qa_pair(menu_key, topic_id, topic_name, keywords)

            if qa_pair and qa_pair['instruction'] not in self.question_set:
                self.question_set.add(qa_pair['instruction'])
                topic_data.append(qa_pair)

        return topic_data

    def _generate_qa_pair(self, menu_key: str, topic_id: str, topic_name: str, keywords: List[str]) -> Dict:
        """질문-답변 쌍 생성"""

        # 질문 생성
        question = self._generate_question(menu_key, topic_id, topic_name, keywords)

        # 답변 생성
        answer = self._generate_answer(menu_key, topic_id, question, keywords)

        return {
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "menu": menu_key,
                "topic": topic_id,
                "topic_name": topic_name
            }
        }

    def _generate_question(self, menu_key: str, topic_id: str, topic_name: str, keywords: List[str]) -> str:
        """질문 생성"""

        question = ""

        # 질문 패턴 선택 전략
        # 3. API 관련 (우선 처리)
        if 'api' in menu_key:
            patterns = self.question_templates['question_patterns']['api']
            question = random.choice(patterns)
            # 변수 치환 (안전하게 replace 사용)
            if "{code}" in question:
                question = question.replace("{code}", random.choice(["400", "401", "403", "404", "500"]))
            if "{data}" in question:
                question = question.replace("{data}", random.choice(keywords) if keywords else "데이터")
            if "{language}" in question:
                question = question.replace("{language}", random.choice(["Python", "Java", "JavaScript", "R"]))

        # 2. 검색 관련
        elif 'search' in menu_key and keywords and random.random() < 0.4:
            patterns = self.question_templates['question_patterns']['search']
            keyword = random.choice(keywords)
            question = random.choice(patterns).format(keyword=keyword)

        # 7. 계정 관련
        elif 'support' in menu_key and 'account' in topic_id:
            patterns = self.question_templates['question_patterns']['account']
            question = random.choice(patterns)

        # 6. 문제 해결
        elif 'support' in menu_key and random.random() < 0.3:
            patterns = self.question_templates['question_patterns']['troubleshooting']
            question = random.choice(patterns)

        # 5. 데이터 관련
        elif 'data' in menu_key or 'catalog' in menu_key:
            patterns = self.question_templates['question_patterns']['data']
            question = random.choice(patterns)

        # 8. 정책 관련
        elif random.random() < 0.2:
            patterns = self.question_templates['question_patterns']['policy']
            question = random.choice(patterns)

        # 4. 사용법 질문
        elif random.random() < 0.3:
            patterns = self.question_templates['question_patterns']['howto']
            actions = ["검색", "다운로드", "활용", "분석", "공유", "저장", "내보내기", "필터링", "정렬", "변환"]
            action = random.choice(actions)
            question = random.choice(patterns).format(action=action)

        # 1. 기본 패턴
        elif random.random() < 0.3:
            patterns = self.question_templates['question_patterns']['basic']
            question = random.choice(patterns).format(topic=topic_name)

        # 9. 기본값 (fallback)
        else:
            patterns = self.question_templates['question_patterns']['basic']
            question = random.choice(patterns).format(topic=topic_name)

        # 질문 다양화 (존댓말/반말 섞기)
        question = self._diversify_question(question)

        return question

    def _generate_answer(self, menu_key: str, topic_id: str, question: str, keywords: List[str]) -> str:
        """답변 생성"""

        answer_templates = self.question_templates['answer_templates']

        # 답변 템플릿 선택 전략
        answer = ""

        # 1. 검색 관련
        if 'search' in topic_id or 'search' in menu_key:
            if 'advanced' in topic_id or '고급' in question or '필터' in question:
                templates = answer_templates.get('search_advanced', [])
            else:
                templates = answer_templates.get('search_basic', [])

            if templates:
                answer = random.choice(templates)
                if keywords:
                    answer = answer.replace("{keyword}", random.choice(keywords))

        # 2. API 관련
        elif 'api' in menu_key or 'api' in topic_id.lower():
            if 'key' in topic_id or '키' in question or '발급' in question:
                templates = answer_templates.get('api_key', [])
            else:
                templates = answer_templates.get('api_usage', [])

            if templates:
                answer = random.choice(templates)
                answer = answer.replace("{language}", random.choice(["Python", "Java", "JavaScript"]))

        # 3. 다운로드 관련
        elif 'download' in topic_id or '다운로드' in question:
            if '대용량' in topic_id or '여러' in question or '일괄' in question:
                templates = answer_templates.get('download_bulk', [])
            else:
                templates = answer_templates.get('download_basic', [])

            if templates:
                answer = random.choice(templates)

        # 4. 메타데이터
        elif 'metadata' in topic_id or 'meta' in topic_id or '메타' in question:
            templates = answer_templates.get('metadata', [])
            if templates:
                answer = random.choice(templates)

        # 5. 라이센스 - 상업적 이용
        elif 'commercial' in topic_id or '상업' in question or '영리' in question:
            templates = answer_templates.get('license_commercial', [])
            if templates:
                answer = random.choice(templates)

        # 6. 라이센스 - 출처 표시
        elif 'attribution' in topic_id or '출처' in question:
            templates = answer_templates.get('license_attribution', [])
            if templates:
                answer = random.choice(templates)

        # 7. 갱신 주기
        elif 'update' in topic_id or '갱신' in question or '업데이트' in question:
            templates = answer_templates.get('update_cycle', [])
            if templates:
                answer = random.choice(templates)

        # 8. 품질
        elif 'quality' in topic_id or '품질' in question:
            templates = answer_templates.get('quality', [])
            if templates:
                answer = random.choice(templates)

        # 9. 파일 형식
        elif 'format' in topic_id or '형식' in question or '포맷' in question:
            templates = answer_templates.get('format', [])
            if templates:
                answer = random.choice(templates)

        # 10. 인코딩
        elif 'encoding' in topic_id or '인코딩' in question or '깨' in question:
            templates = answer_templates.get('encoding', [])
            if templates:
                answer = random.choice(templates)

        # 11. 시각화
        elif 'viz' in topic_id or 'visual' in topic_id or '시각화' in question or '차트' in question:
            templates = answer_templates.get('visualization', [])
            if templates:
                answer = random.choice(templates)

        # 12. 분석 도구
        elif 'tool' in topic_id or '도구' in question:
            templates = answer_templates.get('tools', [])
            if templates:
                answer = random.choice(templates)

        # 13. 활용 사례
        elif 'case' in topic_id or '사례' in question:
            templates = answer_templates.get('case', [])
            if templates:
                answer = random.choice(templates)

        # 14. 회원가입
        elif 'join' in topic_id or '가입' in question:
            templates = answer_templates.get('account_join', [])
            if templates:
                answer = random.choice(templates)

        # 15. 로그인
        elif 'login' in topic_id or '로그인' in question:
            templates = answer_templates.get('account_login', [])
            if templates:
                answer = random.choice(templates)

        # 16. 비밀번호
        elif 'password' in topic_id or '비밀번호' in question:
            templates = answer_templates.get('account_password', [])
            if templates:
                answer = random.choice(templates)

        # 17. 1:1 문의
        elif 'inquiry' in topic_id or '문의' in question:
            templates = answer_templates.get('support_inquiry', [])
            if templates:
                answer = random.choice(templates)

        # 18. FAQ
        elif 'faq' in topic_id or 'FAQ' in question or '자주' in question:
            templates = answer_templates.get('faq', [])
            if templates:
                answer = random.choice(templates)

        # 19. 공지사항
        elif 'notice' in topic_id or '공지' in question:
            templates = answer_templates.get('notice', [])
            if templates:
                answer = random.choice(templates)

        # 20. 오류
        elif 'error' in topic_id or '오류' in question or '에러' in question:
            templates = answer_templates.get('error', [])
            if templates:
                answer = random.choice(templates)

        # 21. 가이드/튜토리얼
        elif 'tutorial' in topic_id or 'guide' in topic_id or '가이드' in question or '매뉴얼' in question:
            templates = answer_templates.get('tutorial', [])
            if templates:
                answer = random.choice(templates)

        # 22. 모바일
        elif 'mobile' in topic_id or '모바일' in question or '스마트폰' in question:
            templates = answer_templates.get('mobile', [])
            if templates:
                answer = random.choice(templates)

        # 23. 뉴스레터
        elif 'newsletter' in topic_id or '뉴스레터' in question or '구독' in question:
            templates = answer_templates.get('newsletter', [])
            if templates:
                answer = random.choice(templates)

        # 기본 답변 (템플릿 매칭 실패 시)
        if not answer:
            answer = f"{question.replace('?', '').replace('어떻게 하나요', '')}은(는) 빅데이터개방포털의 해당 메뉴에서 이용하실 수 있습니다. 자세한 내용은 포털의 이용 가이드를 참조하시거나 고객센터(1234-5678)로 문의해주세요."

        return answer

    def _diversify_question(self, question: str) -> str:
        """질문 다양화 (존댓말/반말 변환, 표현 변경 등)"""

        # 30% 확률로 반말로 변환
        if random.random() < 0.3:
            question = question.replace('하나요', '해')
            question = question.replace('되나요', '돼')
            question = question.replace('알려주세요', '알려줘')
            question = question.replace('인가요', '인가')
            question = question.replace('무엇입니까', '뭐야')
            question = question.replace('설명해주세요', '설명해줘')

        # 20% 확률로 "안녕하세요" 추가
        if random.random() < 0.2 and not question.startswith('안녕'):
            question = f"안녕하세요. {question}"

        # 10% 확률로 구체적 상황 추가
        if random.random() < 0.1:
            situations = [
                "처음 사용하는데 ",
                "급한데 ",
                "궁금한게 있는데 ",
                "도움이 필요해요. "
            ]
            question = random.choice(situations) + question

        return question

    def _generate_additional_data(self, count: int) -> List[Dict]:
        """추가 데이터 생성 (목표 개수 부족 시)"""
        additional_data = []

        # 기존 데이터에서 무작위 선택하여 변형
        for _ in range(count):
            if self.generated_data:
                base_item = random.choice(self.generated_data)

                # 질문 변형
                new_question = self._diversify_question(base_item['instruction'])

                # 중복 체크
                if new_question not in self.question_set:
                    self.question_set.add(new_question)
                    additional_data.append({
                        "instruction": new_question,
                        "input": base_item['input'],
                        "output": base_item['output'],
                        "metadata": base_item['metadata']
                    })

        return additional_data

    def save_jsonl(self, output_path: str, include_metadata: bool = False):
        """JSONL 형식으로 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.generated_data:
                # metadata 포함 여부 선택
                if not include_metadata and 'metadata' in item:
                    output_item = {k: v for k, v in item.items() if k != 'metadata'}
                else:
                    output_item = item

                f.write(json.dumps(output_item, ensure_ascii=False) + '\n')

        print(f"\n✅ 저장 완료: {output_path}")
        print(f"   총 {len(self.generated_data):,}건")

    def save_json(self, output_path: str, include_metadata: bool = False):
        """JSON 형식으로 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = []
        for item in self.generated_data:
            if not include_metadata and 'metadata' in item:
                output_item = {k: v for k, v in item.items() if k != 'metadata'}
            else:
                output_item = item
            output_data.append(output_item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 저장 완료: {output_path}")
        print(f"   총 {len(output_data):,}건")

    def print_statistics(self):
        """데이터 통계 출력"""
        print("\n" + "="*80)
        print("📊 데이터 통계")
        print("="*80)

        # 메뉴별 분포
        menu_counts = {}
        for item in self.generated_data:
            menu = item.get('metadata', {}).get('menu', 'unknown')
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

        print("\n[메뉴별 분포]")
        for menu, count in sorted(menu_counts.items(), key=lambda x: x[1], reverse=True):
            menu_name = self.menu_structure['menus'].get(menu, {}).get('name', menu)
            percentage = (count / len(self.generated_data)) * 100
            print(f"  {menu_name:20s}: {count:5,}건 ({percentage:5.1f}%)")

        # 질문 길이 분포
        q_lengths = [len(item['instruction']) for item in self.generated_data]
        avg_q_len = sum(q_lengths) / len(q_lengths)

        print(f"\n[질문 길이]")
        print(f"  평균: {avg_q_len:.1f}자")
        print(f"  최소: {min(q_lengths)}자")
        print(f"  최대: {max(q_lengths)}자")

        # 답변 길이 분포
        a_lengths = [len(item['output']) for item in self.generated_data]
        avg_a_len = sum(a_lengths) / len(a_lengths)

        print(f"\n[답변 길이]")
        print(f"  평균: {avg_a_len:.1f}자")
        print(f"  최소: {min(a_lengths)}자")
        print(f"  최대: {max(a_lengths)}자")

        # 샘플 출력
        print("\n" + "="*80)
        print("📝 데이터 샘플 (무작위 5개)")
        print("="*80)

        samples = random.sample(self.generated_data, min(5, len(self.generated_data)))
        for i, sample in enumerate(samples, 1):
            print(f"\n[샘플 {i}]")
            print(f"Q: {sample['instruction']}")
            print(f"A: {sample['output'][:150]}{'...' if len(sample['output']) > 150 else ''}")


def main():
    """메인 실행 함수"""

    # 설정
    config_dir = Path(__file__).parent.parent / 'config'
    output_dir = Path(__file__).parent.parent / 'output'

    # 데이터 생성기 초기화
    generator = BigDataPortalDataGenerator(config_dir)

    # 데이터 생성
    target_count = 7000
    generator.generate_all_data(target_count)

    # 통계 출력
    generator.print_statistics()

    # JSONL 형식으로 저장 (학습용 - metadata 제외)
    generator.save_jsonl(output_dir / 'bigdata_portal_train.jsonl', include_metadata=False)

    # JSON 형식으로도 저장 (검토용 - metadata 포함)
    generator.save_json(output_dir / 'bigdata_portal_train_with_metadata.json', include_metadata=True)

    print("\n" + "="*80)
    print("✅ 모든 작업 완료!")
    print("="*80)
    print(f"\n생성 파일:")
    print(f"  1. {output_dir / 'bigdata_portal_train.jsonl'} (학습용)")
    print(f"  2. {output_dir / 'bigdata_portal_train_with_metadata.json'} (검토용)")
    print(f"\n다음 단계:")
    print(f"  1. 생성된 데이터 품질 검증")
    print(f"  2. LoRA 학습 파이프라인 실행")
    print(f"  3. 필요시 GPT 기반 증강 (10,000건으로 확장)")


if __name__ == "__main__":
    main()
