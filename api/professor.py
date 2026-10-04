from flask import Flask, request, jsonify
import os, json, urllib.request, urllib.error

app = Flask(__name__)

BASE_URL = os.environ.get('PROFESSOR_AI_BASE_URL', 'https://9router-nbob.srv1266039.hstgr.cloud/v1').rstrip('/')
API_KEY = os.environ.get('PROFESSOR_AI_API_KEY', '')
TEXT_MODEL = os.environ.get('PROFESSOR_AI_MODEL', 'llama3.2:latest')
VISION_MODEL = os.environ.get('PROFESSOR_AI_VISION_MODEL', TEXT_MODEL)

SYSTEM_PROMPT = '''Você é um professor de Matemática do 6º ano, em português do Brasil. Ensine uma ideia por vez, com frases curtas, linguagem clara e exemplos concretos. A estudante pode ter dificuldade de atenção e interpretação. Nunca entregue imediatamente a resposta de um exercício: primeiro identifique o que ela já sabe, dê uma pista curta e peça uma tentativa. Em correções, avalie resposta e raciocínio, destaque acertos, identifique o ponto exato do erro e sugira o próximo passo. Use terminologia escolar compatível com o material Bernoulli, sem copiar páginas ou ilustrações protegidas. Para correções, responda SOMENTE em JSON válido com as chaves score (0 a 10), feedback (texto curto), strengths (lista curta) e needs_review (lista curta).'''

def ai_call(model, messages, temperature=0.2):
    payload = json.dumps({'model': model, 'messages': messages, 'temperature': temperature}).encode('utf-8')
    headers = {'Content-Type':'application/json'}
    if API_KEY:
        headers['Authorization'] = 'Bearer ' + API_KEY
    req = urllib.request.Request(BASE_URL + '/chat/completions', data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')[:1000]
        raise RuntimeError(f'IA respondeu HTTP {e.code}: {body}')
    except Exception as e:
        raise RuntimeError(str(e))
    try:
        return data['choices'][0]['message']['content']
    except Exception:
        raise RuntimeError('Resposta inesperada do provedor de IA')

def parse_json_content(text):
    t = text.strip()
    if t.startswith('```'):
        t = t.strip('`')
        if t.lower().startswith('json'):
            t = t[4:].strip()
    try:
        return json.loads(t)
    except Exception:
        return {'feedback': t}

@app.route('/api/professor', methods=['POST','OPTIONS'])
def professor():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json(silent=True) or {}
    mode = data.get('mode','chat')
    student = data.get('student') or 'estudante'
    try:
        if mode == 'chat':
            q = (data.get('question') or '').strip()
            if not q:
                return jsonify({'error':'Digite uma pergunta.'}), 400
            ctx = data.get('context') or {}
            prompt = f'Estudante: {student}. Contexto atual: {json.dumps(ctx, ensure_ascii=False)}. Dúvida: {q}'
            content = ai_call(TEXT_MODEL,[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':prompt}],0.35)
            return jsonify({'message':content,'provider':'router','model':TEXT_MODEL})

        if mode == 'correct_block':
            image = data.get('image')
            if not image:
                return jsonify({'error':'Foto do bloco não recebida.'}), 400
            block = data.get('block')
            answers = data.get('answers') or {}
            text = f'Corrija o bloco {block} da estudante {student}. Considere as respostas digitadas: {json.dumps(answers, ensure_ascii=False)}. Analise também a foto do caderno. Dê nota de 0 a 10 considerando resultado, procedimento e compreensão.'
            msg = [{'type':'text','text':text},{'type':'image_url','image_url':{'url':image}}]
            content = ai_call(VISION_MODEL,[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':msg}],0.1)
            out = parse_json_content(content); out['provider']='router'; out['model']=VISION_MODEL
            return jsonify(out)

        if mode == 'correct_exam':
            images = data.get('images') or []
            if not images:
                return jsonify({'error':'Fotos da avaliação não recebidas.'}), 400
            answers = data.get('answers') or {}
            parts = [{'type':'text','text':f'Corrija a Avaliação Final da estudante {student}. São 20 questões, nota total 10. Considere as respostas digitadas: {json.dumps(answers, ensure_ascii=False)}. Use as fotos para conferir cálculos e raciocínio. Responda com nota de 0 a 10 e feedback pedagógico curto.'}]
            for im in images[:4]:
                parts.append({'type':'image_url','image_url':{'url':im}})
            content = ai_call(VISION_MODEL,[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':parts}],0.1)
            out = parse_json_content(content); out['provider']='router'; out['model']=VISION_MODEL
            return jsonify(out)

        return jsonify({'error':'Modo inválido.'}), 400
    except Exception as e:
        msg = str(e)
        if 'image' in msg.lower() or 'vision' in msg.lower() or 'multimodal' in msg.lower():
            msg += ' O modelo configurado parece não aceitar imagens. Configure PROFESSOR_AI_VISION_MODEL com um modelo multimodal.'
        return jsonify({'error':msg}), 502
