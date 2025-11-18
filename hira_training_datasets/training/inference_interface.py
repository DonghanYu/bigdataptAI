#!/usr/bin/env python3
"""
HIRA SOLAR-10.7B 추론 인터페이스
- 학습된 LoRA 모델 로드
- Gradio 웹 UI 제공
- HIRA 관련 질문에 답변
"""

import argparse
import sys
from pathlib import Path
import json

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    import gradio as gr
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False
    print("⚠️  필요한 라이브러리가 설치되지 않았습니다.")
    print("   pip install torch transformers peft gradio")


class HIRAInference:
    """HIRA 추론 클래스"""

    def __init__(self, base_model_path: str, lora_adapter_path: str = None):
        """
        Args:
            base_model_path: SOLAR 기본 모델 경로
            lora_adapter_path: LoRA 어댑터 경로 (선택)
        """
        self.base_model_path = Path(base_model_path)
        self.lora_adapter_path = Path(lora_adapter_path) if lora_adapter_path else None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = None
        self.model = None

        print("="*80)
        print("HIRA SOLAR-10.7B 추론 인터페이스")
        print("="*80 + "\n")

        self._print_environment()
        self._load_model()

    def _print_environment(self):
        """환경 정보 출력"""
        print("📊 환경:")
        print(f"  Device: {self.device}")
        print(f"  PyTorch: {torch.__version__}")

        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  VRAM: {vram:.1f} GB")

    def _load_model(self):
        """모델 로드"""
        print(f"\n모델 로드 중...")
        print(f"  기본 모델: {self.base_model_path}")

        # 토크나이저
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path,
            trust_remote_code=True
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print(f"  ✓ 토크나이저 로드 완료")

        # 기본 모델
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )

        print(f"  ✓ 기본 모델 로드 완료")

        # LoRA 어댑터
        if self.lora_adapter_path and self.lora_adapter_path.exists():
            print(f"  LoRA 어댑터: {self.lora_adapter_path}")
            self.model = PeftModel.from_pretrained(
                self.model,
                self.lora_adapter_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            print(f"  ✓ LoRA 어댑터 로드 완료")
        else:
            print(f"  ⚠️  LoRA 어댑터 없음 (기본 모델만 사용)")

        self.model.eval()

    def generate(
        self,
        instruction: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50
    ) -> str:
        """
        답변 생성

        Args:
            instruction: 질문/명령
            max_length: 최대 생성 길이
            temperature: 온도 (높을수록 다양성 증가)
            top_p: Nucleus sampling
            top_k: Top-K sampling

        Returns:
            생성된 답변
        """
        # 프롬프트 구성
        prompt = f"### Instruction:\n{instruction.strip()}\n\n### Response:\n"

        # 토크나이징
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=max_length,
            truncation=True
        ).to(self.device)

        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # 디코딩
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Response 부분만 추출
        if "### Response:" in generated_text:
            response = generated_text.split("### Response:")[-1].strip()
        else:
            response = generated_text.strip()

        return response

    def batch_generate(self, questions: list) -> list:
        """
        배치 생성

        Args:
            questions: 질문 리스트

        Returns:
            답변 리스트
        """
        answers = []
        for question in questions:
            answer = self.generate(question)
            answers.append(answer)

        return answers


def create_gradio_interface(inference: HIRAInference):
    """Gradio 인터페이스 생성"""

    def predict(instruction, temperature, top_p, top_k, max_length):
        """예측 함수"""
        try:
            response = inference.generate(
                instruction=instruction,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_length=max_length
            )
            return response
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}"

    # 예시 질문
    examples = [
        ["상병코드는 어떻게 조회하나요?"],
        ["환자표본 데이터 신청 방법은?"],
        ["HIRA 데이터 규모는 얼마나 되나요?"],
        ["맞춤형 데이터와 환자표본의 차이는?"],
        ["API 키는 어떻게 발급받나요?"],
        ["SAS Studio 신청 방법"],
        ["진료비 통계는 어디서 확인하나요?"],
        ["빅데이터분석센터는 어디에 있나요?"],
    ]

    # Gradio 인터페이스
    with gr.Blocks(title="HIRA SOLAR-10.7B", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🏥 HIRA 보건의료빅데이터 질의응답 시스템")
        gr.Markdown("SOLAR-10.7B 기반 LoRA 파인튜닝 모델")

        with gr.Row():
            with gr.Column(scale=2):
                instruction_input = gr.Textbox(
                    label="질문",
                    placeholder="HIRA 관련 질문을 입력하세요...",
                    lines=3
                )

                with gr.Accordion("고급 설정", open=False):
                    temperature_slider = gr.Slider(
                        minimum=0.1,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="Temperature (창의성)",
                        info="낮을수록 보수적, 높을수록 창의적"
                    )

                    top_p_slider = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.9,
                        step=0.05,
                        label="Top-p (다양성)",
                        info="Nucleus sampling"
                    )

                    top_k_slider = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=50,
                        step=1,
                        label="Top-k",
                        info="상위 k개 토큰만 고려"
                    )

                    max_length_slider = gr.Slider(
                        minimum=128,
                        maximum=1024,
                        value=512,
                        step=64,
                        label="Max Length",
                        info="최대 시퀀스 길이"
                    )

                submit_btn = gr.Button("답변 생성", variant="primary")
                clear_btn = gr.ClearButton()

            with gr.Column(scale=2):
                output = gr.Textbox(
                    label="답변",
                    lines=10,
                    show_copy_button=True
                )

        gr.Markdown("### 💡 예시 질문")
        gr.Examples(
            examples=examples,
            inputs=[instruction_input],
            label="클릭하여 질문 입력"
        )

        gr.Markdown("""
        ### 📊 모델 정보
        - **기본 모델**: SOLAR-10.7B (Upstage)
        - **파인튜닝**: LoRA (Low-Rank Adaptation)
        - **데이터셋**: HIRA 1,423개 Q&A
        - **학습 메뉴**: 서비스 소개, 보건의료빅데이터, 의료통계정보, 공공데이터, 고객지원
        """)

        # 이벤트 핸들러
        submit_btn.click(
            fn=predict,
            inputs=[
                instruction_input,
                temperature_slider,
                top_p_slider,
                top_k_slider,
                max_length_slider
            ],
            outputs=output
        )

        clear_btn.add([instruction_input, output])

    return demo


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="HIRA SOLAR-10.7B 추론 인터페이스")

    parser.add_argument("--base-model-path", type=str,
                       default="/home/work/LLM_Meditron/bigdataAI/solar_10.7b_package/model",
                       help="SOLAR 기본 모델 경로")
    parser.add_argument("--lora-adapter-path", type=str,
                       default=None,
                       help="LoRA 어댑터 경로 (학습된 모델)")
    parser.add_argument("--share", action="store_true",
                       help="공개 링크 생성")
    parser.add_argument("--server-name", type=str,
                       default="0.0.0.0",
                       help="서버 주소")
    parser.add_argument("--server-port", type=int,
                       default=7860,
                       help="서버 포트")

    args = parser.parse_args()

    # 환경 체크
    if not LIBS_AVAILABLE:
        print("\n❌ 필요한 라이브러리가 설치되지 않았습니다.")
        print("   pip install torch transformers peft gradio")
        sys.exit(1)

    # 모델 로드
    inference = HIRAInference(
        base_model_path=args.base_model_path,
        lora_adapter_path=args.lora_adapter_path
    )

    # Gradio 인터페이스 실행
    print(f"\n🚀 Gradio 인터페이스 시작...")
    print(f"   URL: http://{args.server_name}:{args.server_port}")

    if args.share:
        print(f"   공개 링크 생성 중...")

    demo = create_gradio_interface(inference)
    demo.launch(
        server_name=args.server_name,
        server_port=args.server_port,
        share=args.share
    )


if __name__ == "__main__":
    main()
