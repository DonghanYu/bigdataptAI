#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIRA 보건의료빅데이터개방시스템 샘플 데이터 생성기
각 메뉴별 10개씩 총 50개 샘플 생성
"""

import json
import random
import yaml
from pathlib import Path
from typing import List, Dict

class HIRASampleGenerator:
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.menu_structure = self._load_yaml('hira_menu_structure.yaml')
        self.question_templates = self._load_yaml('hira_question_templates.yaml')
        self.generated_data = []
        self.question_set = set()

    def _load_yaml(self, filename: str) -> dict:
        """YAML 파일 로드"""
        with open(self.config_dir / filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_samples(self, samples_per_menu: int = 10) -> List[Dict]:
        """각 메뉴별로 샘플 생성"""
        print("="*80)
        print("HIRA 보건의료빅데이터개방시스템 샘플 생성")
        print("="*80)
        print(f"메뉴당 {samples_per_menu}개씩 생성\n")

        for menu_key, menu_info in self.menu_structure['menus'].items():
            menu_name = menu_info['name']
            topics = menu_info['topics']

            print(f"📂 {menu_name}")
            print("-" * 60)

            # 각 메뉴에서 samples_per_menu개 생성
            menu_samples = []
            for i in range(samples_per_menu):
                # 랜덤하게 주제 선택
                topic = random.choice(topics)

                # Q&A 생성
                qa = self._generate_qa(menu_key, topic)

                if qa and qa['instruction'] not in self.question_set:
                    self.question_set.add(qa['instruction'])
                    menu_samples.append(qa)

            print(f"   ✅ 생성: {len(menu_samples)}개\n")
            self.generated_data.extend(menu_samples)

        print("="*80)
        print(f"✅ 총 {len(self.generated_data)}개 샘플 생성 완료")
        print("="*80)

        return self.generated_data

    def _generate_qa(self, menu_key: str, topic: dict) -> Dict:
        """Q&A 쌍 생성"""
        topic_id = topic['id']
        topic_name = topic['name']
        keywords = topic.get('keywords', [])

        # 질문 생성
        question = self._generate_question(menu_key, topic_id, topic_name, keywords)

        # 답변 생성
        answer = self._generate_answer(menu_key, topic_id, topic_name, keywords)

        return {
            "instruction": question,
            "input": "",
            "output": answer
        }

    def _generate_question(self, menu_key: str, topic_id: str, topic_name: str, keywords: List[str]) -> str:
        """질문 생성 (장식 제거 버전)"""

        templates = self.question_templates['question_patterns']

        # 메뉴/주제별 특화 질문 패턴 선택
        if 'patient_sample' in topic_id or 'customized' in topic_id or 'data_request' in topic_id:
            patterns = templates.get('data_request', templates['basic'])

        elif 'sas' in topic_id or 'remote' in topic_id or 'onsite' in topic_id:
            patterns = templates.get('analysis_tool', templates['basic'])

        elif 'code' in topic_id or 'term' in topic_id:
            patterns = templates.get('code_lookup', templates['basic'])

        elif 'stats' in topic_id or 'cost' in topic_id or 'olap' in topic_id:
            patterns = templates.get('statistics', templates['basic'])

        elif 'api' in topic_id or 'open' in topic_id:
            patterns = templates.get('open_api', templates['basic'])

        elif 'structure' in topic_id or 'table' in topic_id:
            patterns = templates.get('data_structure', templates['basic'])

        elif 'support' in menu_key or 'inquiry' in topic_id or 'contact' in topic_id:
            patterns = templates.get('support', templates['basic'])

        elif 'error' in topic_id or 'issue' in topic_id or 'problem' in topic_id:
            patterns = templates.get('troubleshooting', templates['basic'])

        else:
            patterns = templates['basic']

        # 패턴 선택 및 변수 치환
        if isinstance(patterns, list):
            question = random.choice(patterns)

            # {topic} 치환
            if '{topic}' in question:
                question = question.replace('{topic}', topic_name)
        else:
            # 딕셔너리인 경우 기본 패턴 사용
            question = f"{topic_name} 어떻게 하나요?"

        return question

    def _generate_answer(self, menu_key: str, topic_id: str, topic_name: str, keywords: List[str]) -> str:
        """답변 생성"""

        templates = self.question_templates['answer_templates']

        # 주제별 답변 템플릿 매칭
        if 'patient_sample' in topic_id:
            answer_list = templates.get('patient_sample', [])

        elif 'customized' in topic_id:
            answer_list = templates.get('customized_analysis', [])

        elif 'sas' in topic_id:
            answer_list = templates.get('sas_studio', [])

        elif 'code' in topic_id or 'term' in topic_id:
            answer_list = templates.get('code_lookup', [])

        elif 'stats' in topic_id or 'cost' in topic_id or 'olap' in topic_id:
            answer_list = templates.get('statistics_info', [])

        elif 'api' in topic_id or 'open' in topic_id:
            answer_list = templates.get('open_api', [])

        elif 'structure' in topic_id or 'table' in topic_id:
            answer_list = templates.get('data_structure', [])

        elif 'remote' in topic_id or 'onsite' in topic_id:
            answer_list = templates.get('analysis_method', [])

        elif 'education' in topic_id or 'brief' in topic_id:
            answer_list = templates.get('education', [])

        elif 'support' in menu_key or 'inquiry' in topic_id:
            answer_list = templates.get('customer_support', [])

        elif 'approval' in topic_id:
            answer_list = templates.get('approval', [])

        elif 'cost' in keywords or '비용' in topic_name:
            answer_list = templates.get('cost', [])

        elif 'period' in topic_id or '기간' in topic_name:
            answer_list = templates.get('data_period', [])

        elif 'error' in topic_id or 'issue' in topic_id:
            answer_list = templates.get('system_error', [])

        else:
            # 기본 답변
            answer_list = []

        if answer_list:
            return random.choice(answer_list)
        else:
            # 매칭 실패 시 기본 답변
            return f"{topic_name}은(는) HIRA 보건의료빅데이터개방시스템(opendata.hira.or.kr)의 해당 메뉴에서 확인할 수 있습니다. 자세한 내용은 고객센터(033-739-1018)로 문의하시기 바랍니다."

    def save_jsonl(self, output_path: str):
        """JSONL 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.generated_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"\n✅ 저장 완료: {output_path}")

    def print_samples(self):
        """샘플 출력"""
        print("\n" + "="*80)
        print("📝 생성된 샘플 미리보기")
        print("="*80)

        for i, item in enumerate(self.generated_data, 1):
            print(f"\n[샘플 {i}]")
            print(f"Q: {item['instruction']}")
            print(f"A: {item['output'][:200]}{'...' if len(item['output']) > 200 else ''}")


def main():
    """메인 함수"""
    config_dir = Path(__file__).parent.parent / 'config'
    output_dir = Path(__file__).parent.parent / 'output'

    # 샘플 생성기 초기화
    generator = HIRASampleGenerator(config_dir)

    # 각 메뉴별 10개씩 생성
    generator.generate_samples(samples_per_menu=10)

    # 샘플 출력
    generator.print_samples()

    # 저장
    generator.save_jsonl(output_dir / 'hira_samples_50.jsonl')

    print("\n" + "="*80)
    print("✅ 샘플 생성 완료!")
    print("="*80)
    print(f"\n다음 단계:")
    print(f"  1. 샘플 품질 확인")
    print(f"  2. 승인 후 전체 데이터 생성 (1,500-2,500건)")


if __name__ == "__main__":
    main()
