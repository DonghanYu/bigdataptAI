#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLAR HIRA Flask Interface - 개선 버전
- Conservative generation parameters
- Hallucination 방지 최적화
- Confidence scoring
"""

import sys
import os

os.environ['BITSANDBYTES_NOWELCOME'] = '1'
sys.modules['bitsandbytes'] = None

import torch
from flask import Flask, request, jsonify
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import traceback

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

os.chdir("/home/work/LLM_Meditron/bigdataAI")
WORK_DIR = Path(os.getcwd())
BASE_MODEL_PATH = str(WORK_DIR / "solar_10.7b_package" / "model")
LORA_MODEL_PATH = str(WORK_DIR / "workspace" / "models" / "solar_hira_v3" / "best_model")

model = None
tokenizer = None
device = None

# ============================================
# HTML 인터페이스
# ============================================
HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HIRA Assistant v2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
.container{width:100%;max-width:1200px;height:90vh;background:white;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);display:flex;flex-direction:column}
.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:25px 30px;border-radius:20px 20px 0 0}
.header h1{font-size:24px;font-weight:600}
.header .version{font-size:12px;opacity:0.8;margin-top:5px}
.chat{flex:1;overflow-y:auto;padding:30px;background:#f8fafc}
.msg{margin-bottom:20px;display:flex;gap:15px;animation:slideIn 0.3s}
@keyframes slideIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.avatar{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;flex-shrink:0}
.msg.user .avatar{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white}
.msg.assistant .avatar{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white}
.content{max-width:70%;padding:15px 20px;border-radius:15px;line-height:1.6;word-wrap:break-word}
.msg.user .content{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white}
.msg.assistant .content{background:white;color:#1e293b;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
.confidence{font-size:11px;color:#64748b;margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0}
.confidence.high{color:#10b981}
.confidence.medium{color:#f59e0b}
.confidence.low{color:#ef4444}
.input-box{padding:25px 30px;background:white;border-top:1px solid #e2e8f0;display:flex;gap:15px}
#input{flex:1;padding:15px 20px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;resize:none;font-family:inherit;min-height:50px}
#input:focus{outline:none;border-color:#667eea}
#btn{padding:15px 30px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:transform 0.2s}
#btn:hover{transform:translateY(-2px)}
#btn:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.welcome{text-align:center;color:#64748b;margin-top:50px}
.welcome h2{font-size:28px;margin-bottom:10px}
.settings{margin-top:20px;padding:15px;background:#f8fafc;border-radius:10px;font-size:13px}
.settings label{display:block;margin-bottom:8px;color:#475569}
.settings input{width:80px;padding:5px;margin-left:10px;border:1px solid #e2e8f0;border-radius:5px}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🏥 SOLAR HIRA Assistant</h1>
<div class="version">v2.0 - Improved with Validation & Anti-Hallucination</div>
</div>
<div class="chat" id="chat">
<div class="welcome">
<h2>환영합니다</h2>
<p>건강보험심사평가원(HIRA) 데이터에 대해 무엇이든 물어보세요</p>
<div class="settings">
<label>
Temperature: <input type="number" id="temp" value="0.3" step="0.1" min="0.1" max="1.0">
</label>
<label>
Max Tokens: <input type="number" id="maxlen" value="256" step="32" min="128" max="512">
</label>
</div>
</div>
</div>
<div class="input-box">
<textarea id="input" placeholder="질문을 입력하세요..."></textarea>
<button id="btn" onclick="send()">전송</button>
</div>
</div>
<script>
function add(text, type, confidence=null) {
var w=document.querySelector('.welcome');
if(w)w.style.display='none';
var c=document.getElementById('chat');
var d=document.createElement('div');
d.className='msg '+type;

var content = '<div class="content">'+text;
if(confidence !== null && type === 'assistant') {
    var confClass = confidence >= 0.7 ? 'high' : (confidence >= 0.4 ? 'medium' : 'low');
    var confText = confidence >= 0.7 ? '신뢰도 높음' : (confidence >= 0.4 ? '신뢰도 보통' : '신뢰도 낮음');
    content += '<div class="confidence '+confClass+'">'+confText+' ('+Math.round(confidence*100)+'%)</div>';
}
content += '</div>';

d.innerHTML='<div class="avatar">'+(type=='user'?'👤':'🤖')+'</div>'+content;
c.appendChild(d);
c.scrollTop=c.scrollHeight;
return d;
}

async function send() {
var i=document.getElementById('input');
var b=document.getElementById('btn');
var temp=parseFloat(document.getElementById('temp').value);
var maxlen=parseInt(document.getElementById('maxlen').value);
var q=i.value.trim();

if(!q){alert('질문을 입력해주세요');return;}

add(q,'user');
i.value='';
b.disabled=true;
var l=add('생성 중...','assistant');

try{
const currentPath = window.location.pathname.replace(/\\/$/, '');
const apiPath = currentPath + '/api/chat';

var r=await fetch(apiPath,{
method:'POST',
headers:{'Content-Type':'application/json','Accept':'application/json'},
body:JSON.stringify({
    question:q,
    temperature:temp,
    max_length:maxlen
})
});

if(!r.ok) throw new Error('HTTP '+r.status);

var d=await r.json();
l.remove();

if(d.status=='success') {
    add(d.response,'assistant', d.confidence);
} else {
    add('오류: '+d.message,'assistant');
}

}catch(e){
console.error('Fetch error:', e);
l.remove();
add('오류: '+e.message,'assistant');
}finally{
b.disabled=false;
i.focus();
}
}

document.getElementById('input').onkeydown=function(e){
if(e.key=='Enter'&&!e.shiftKey){e.preventDefault();send();}
};
</script>
</body>
</html>"""

def load_model():
    """모델 로드"""
    global model, tokenizer, device
    print("\n" + "="*70)
    print("모델 로딩...")
    print("="*70)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_PATH,
        local_files_only=True,
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        local_files_only=True,
        trust_remote_code=True
    )
    
    model = PeftModel.from_pretrained(base, LORA_MODEL_PATH)
    model.eval()
    
    print("="*70)
    print("✅ 모델 준비 완료")
    print("="*70 + "\n")

def generate(question, max_length=256, temperature=0.3):
    """
    개선된 생성 함수
    - Conservative parameters
    - Repetition penalty
    - Length penalty
    """
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
            temperature=temperature,      # 더 보수적
            top_p=0.85,                    # 상위 85%만
            top_k=40,                      # 상위 40개 토큰만
            repetition_penalty=1.15,       # 반복 억제
            no_repeat_ngram_size=3,        # 3-gram 반복 금지
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            length_penalty=1.0,            # 길이 페널티
            early_stopping=True
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Response 부분만 추출
    if "### Response:" in response:
        response = response.split("### Response:")[-1].strip()
    
    # Confidence 계산 (간단한 휴리스틱)
    confidence = calculate_confidence(response, question)
    
    return response, confidence

def calculate_confidence(response, question):
    """
    신뢰도 점수 계산 (0-1)
    간단한 휴리스틱 기반
    """
    confidence = 1.0
    
    # 너무 짧은 답변
    if len(response) < 20:
        confidence *= 0.6
    
    # 반복 패턴 탐지
    words = response.split()
    if len(words) > len(set(words)) * 1.5:  # 중복 단어 많음
        confidence *= 0.7
    
    # 불확실성 표현
    uncertain_words = ['아마', '가능성', '추측', '확실하지', '모르겠']
    for word in uncertain_words:
        if word in response:
            confidence *= 0.8
            break
    
    # 답변이 질문과 관련없음 (간단 체크)
    question_words = set(question.split())
    response_words = set(response.split())
    overlap = len(question_words & response_words)
    if overlap == 0 and len(question_words) > 3:
        confidence *= 0.5
    
    return max(0.1, min(1.0, confidence))

# ============================================
# Routes
# ============================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if '/api/chat' not in request.path:
        return HTML
    return "Use POST for /api/chat", 405

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@app.route('/opnAI/api/chat', methods=['POST', 'OPTIONS'])
@app.route('/proxy/<int:port>/opnAI/api/chat', methods=['POST', 'OPTIONS'])
def chat_all(port=None):
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status':'error','message':'No JSON'}), 400
        
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'status':'error','message':'Empty question'}), 400
        
        max_length = data.get('max_length', 256)
        temperature = data.get('temperature', 0.3)
        
        # Validation
        temperature = max(0.1, min(1.0, temperature))
        max_length = max(64, min(512, max_length))
        
        print(f"\n[Q] {question[:80]}")
        print(f"[Params] temp={temperature}, max_len={max_length}")
        
        response, confidence = generate(question, max_length, temperature)
        
        print(f"[A] {len(response)} chars, confidence={confidence:.2f}")
        
        return jsonify({
            'status': 'success',
            'response': response,
            'confidence': round(confidence, 2)
        })
    
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return jsonify({'status':'error','message':str(e)}), 500

if __name__ == '__main__':
    load_model()
    
    print("\n" + "="*70)
    print("Flask 시작")
    print("="*70)
    print(f"\nLocal: http://localhost:8888")
    print(f"Proxy: http://10.1.2.9:10359/proxy/8888/opnAI")
    print("\n개선사항:")
    print("  ✅ Conservative generation (temp=0.3)")
    print("  ✅ Repetition penalty (1.15)")
    print("  ✅ No repeat n-gram (3)")
    print("  ✅ Confidence scoring")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False, threaded=True)
