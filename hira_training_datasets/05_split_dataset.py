#!/usr/bin/env python3
"""
HIRA 데이터셋 분할
- Train/Val/Test 분할
- 메뉴별 분할
- JSONL 형식 저장
- 통계 생성
"""

import json
import random
from pathlib import Path
from typing import List, Dict
from collections import defaultdict, Counter
import argparse
from datetime import datetime


class DatasetSplitter:
    """데이터셋 분할기"""

    def __init__(self, input_path: str):
        """초기화"""
        with open(input_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # 랜덤 시드 고정 (재현성)
        random.seed(42)

        self.splits = {
            "train": [],
            "val": [],
            "test": []
        }

        self.by_menu = defaultdict(lambda: {"train": [], "val": [], "test": []})

        self.stats = {
            "total": len(self.data),
            "by_split": {},
            "by_menu": {},
            "by_generation_method": {}
        }

    def split(self, train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1):
        """데이터 분할"""
        print("="*80)
        print("데이터셋 분할")
        print("="*80 + "\n")

        print(f"총 데이터: {len(self.data)}개")
        print(f"분할 비율: Train {train_ratio*100:.0f}% / Val {val_ratio*100:.0f}% / Test {test_ratio*100:.0f}%\n")

        # 메뉴별로 그룹화
        by_menu = defaultdict(list)
        for qa in self.data:
            menu = qa["metadata"]["menu"]
            by_menu[menu].append(qa)

        # 각 메뉴별로 분할 (계층적 샘플링)
        for menu, qa_list in by_menu.items():
            random.shuffle(qa_list)

            total = len(qa_list)
            train_end = int(total * train_ratio)
            val_end = train_end + int(total * val_ratio)

            train = qa_list[:train_end]
            val = qa_list[train_end:val_end]
            test = qa_list[val_end:]

            self.splits["train"].extend(train)
            self.splits["val"].extend(val)
            self.splits["test"].extend(test)

            self.by_menu[menu]["train"] = train
            self.by_menu[menu]["val"] = val
            self.by_menu[menu]["test"] = test

        # 섞기
        random.shuffle(self.splits["train"])
        random.shuffle(self.splits["val"])
        random.shuffle(self.splits["test"])

        print(f"분할 결과:")
        print(f"  Train: {len(self.splits['train'])}개 ({len(self.splits['train'])/len(self.data)*100:.1f}%)")
        print(f"  Val:   {len(self.splits['val'])}개 ({len(self.splits['val'])/len(self.data)*100:.1f}%)")
        print(f"  Test:  {len(self.splits['test'])}개 ({len(self.splits['test'])/len(self.data)*100:.1f}%)")

        # 통계 수집
        self._collect_statistics()

        return self.splits

    def _collect_statistics(self):
        """통계 수집"""
        # 분할별 통계
        for split_name, split_data in self.splits.items():
            self.stats["by_split"][split_name] = {
                "count": len(split_data),
                "avg_q_length": sum(qa["metadata"]["question_length"] for qa in split_data) / len(split_data) if split_data else 0,
                "avg_a_length": sum(qa["metadata"]["answer_length"] for qa in split_data) / len(split_data) if split_data else 0,
            }

        # 메뉴별 통계
        for menu, splits in self.by_menu.items():
            self.stats["by_menu"][menu] = {
                "train": len(splits["train"]),
                "val": len(splits["val"]),
                "test": len(splits["test"]),
                "total": len(splits["train"]) + len(splits["val"]) + len(splits["test"])
            }

        # 생성 방법별 통계
        gen_methods = Counter()
        for qa in self.data:
            method = qa["metadata"]["generation_method"]
            gen_methods[method] += 1

        self.stats["by_generation_method"] = dict(gen_methods)

    def save_all(self, output_dir: str):
        """모든 형식으로 저장"""
        output_dir = Path(output_dir)

        # 1. Train/Val/Test JSON
        self._save_split_json(output_dir / "full")

        # 2. Train JSONL (LoRA 학습용)
        self._save_train_jsonl(output_dir / "full" / "train.jsonl")

        # 3. 메뉴별 JSON
        self._save_by_menu_json(output_dir / "by_menu")

        # 4. 통계
        self._save_statistics(output_dir / "metadata" / "dataset_statistics.json")

        print(f"\n✅ 모든 파일 저장 완료: {output_dir}")

    def _save_split_json(self, output_dir: Path):
        """Train/Val/Test JSON 저장"""
        output_dir.mkdir(parents=True, exist_ok=True)

        for split_name, split_data in self.splits.items():
            output_path = output_dir / f"{split_name}.json"

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(split_data, f, ensure_ascii=False, indent=2)

            print(f"  {split_name}.json: {len(split_data)}개 "
                  f"({output_path.stat().st_size/1024:.1f} KB)")

    def _save_train_jsonl(self, output_path: Path):
        """Train JSONL 저장 (LoRA 학습용)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in self.splits["train"]:
                # 메타데이터 제거 (학습에 불필요)
                train_item = {
                    "instruction": qa["instruction"],
                    "input": qa["input"],
                    "output": qa["output"]
                }
                f.write(json.dumps(train_item, ensure_ascii=False) + '\n')

        print(f"  train.jsonl: {len(self.splits['train'])}개 "
              f"({output_path.stat().st_size/1024:.1f} KB)")

    def _save_by_menu_json(self, output_dir: Path):
        """메뉴별 JSON 저장"""
        output_dir.mkdir(parents=True, exist_ok=True)

        for menu, splits in self.by_menu.items():
            menu_dir = output_dir / menu
            menu_dir.mkdir(parents=True, exist_ok=True)

            for split_name, split_data in splits.items():
                output_path = menu_dir / f"{split_name}.json"

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(split_data, f, ensure_ascii=False, indent=2)

        print(f"  by_menu/: {len(self.by_menu)}개 메뉴")

    def _save_statistics(self, output_path: Path):
        """통계 저장"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stats_report = {
            "summary": {
                "total_data": self.stats["total"],
                "train_count": len(self.splits["train"]),
                "val_count": len(self.splits["val"]),
                "test_count": len(self.splits["test"]),
                "train_ratio": len(self.splits["train"]) / self.stats["total"],
                "val_ratio": len(self.splits["val"]) / self.stats["total"],
                "test_ratio": len(self.splits["test"]) / self.stats["total"],
            },
            "by_split": self.stats["by_split"],
            "by_menu": self.stats["by_menu"],
            "by_generation_method": self.stats["by_generation_method"],
            "timestamp": datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats_report, f, ensure_ascii=False, indent=2)

        print(f"  statistics.json: 통계 리포트")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "="*80)
        print("📊 데이터셋 통계")
        print("="*80)

        print(f"\n전체:")
        print(f"  총 데이터: {self.stats['total']}개")
        for split_name, split_stats in self.stats["by_split"].items():
            ratio = split_stats["count"] / self.stats["total"] * 100
            print(f"  {split_name.capitalize():5s}: {split_stats['count']:4d}개 ({ratio:5.1f}%) "
                  f"[Q:{split_stats['avg_q_length']:.1f}자, A:{split_stats['avg_a_length']:.1f}자]")

        print(f"\n메뉴별:")
        print(f"  {'메뉴':<20} {'Train':>7} {'Val':>7} {'Test':>7} {'Total':>7}")
        print("  " + "-"*54)

        for menu, menu_stats in sorted(self.stats["by_menu"].items()):
            print(f"  {menu:<20} {menu_stats['train']:7d} {menu_stats['val']:7d} "
                  f"{menu_stats['test']:7d} {menu_stats['total']:7d}")

        print(f"\n생성 방법별:")
        sorted_methods = sorted(
            self.stats["by_generation_method"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for method, count in sorted_methods[:10]:
            pct = (count / self.stats['total']) * 100
            print(f"  {method:25s}: {count:4d}개 ({pct:5.1f}%)")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="HIRA 데이터셋 분할")
    parser.add_argument("--input", type=str,
                       default="output/temp/quality_filtered.json",
                       help="입력 파일 (품질 검증 완료)")
    parser.add_argument("--output", type=str,
                       default="output/v1.0",
                       help="출력 디렉토리")
    parser.add_argument("--train", type=float, default=0.8,
                       help="Train 비율 (default: 0.8)")
    parser.add_argument("--val", type=float, default=0.1,
                       help="Validation 비율 (default: 0.1)")
    parser.add_argument("--test", type=float, default=0.1,
                       help="Test 비율 (default: 0.1)")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("HIRA 데이터셋 분할기 v1.0")
    print("="*80 + "\n")

    # 경로 설정
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input
    output_dir = base_dir / args.output

    # 분할기 초기화
    splitter = DatasetSplitter(input_path)

    # 분할 실행
    splits = splitter.split(
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test
    )

    # 저장
    splitter.save_all(output_dir)

    # 통계
    splitter.print_statistics()

    print("\n" + "="*80)
    print("🎉 데이터셋 분할 완료!")
    print("="*80)

    print(f"\n📁 생성된 파일:")
    print(f"  {output_dir}/full/train.json")
    print(f"  {output_dir}/full/train.jsonl  ← LoRA 학습용")
    print(f"  {output_dir}/full/val.json")
    print(f"  {output_dir}/full/test.json")
    print(f"  {output_dir}/by_menu/...")
    print(f"  {output_dir}/metadata/dataset_statistics.json")

    print(f"\n🚀 LoRA 학습 시작:")
    print(f"  python3 train_lora.py --data {output_dir}/full/train.jsonl")


if __name__ == "__main__":
    main()
