from flask import Flask, request, jsonify
import os, json, urllib.request, urllib.error

app = Flask(__name__)
BASE_URL = os.environ.get('PROFESSOR_AI_BASE_URL', 'https://9router-nbob.srv1266039.hstgr.cloud/v1').rstrip('/')
API_KEY = os.environ.get('PROFESSOR_AI_API_KEY', '')
MODEL = os.environ.get('PROFESSOR_AI_MODEL', 'FIGUEIRA-DEV-AUTO')

def ai_call(messages):
    payload = json.dumps({'model': MODEL, 'messages': messages, 'temperature': 0.1}).encode('utf-8')
    headers = {'Content-Type':'application/json'}
    if API_KEY:
        headers['Authorization'] = 'Bearer ' + API_KEY
    req = urllib.request.Request(BASE_URL + '/chat/completions', data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode('utf-8'))
        return data['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        body=e.read().decode('utf-8',errors='ignore')[:800]
        raise RuntimeError(f'IA respondeu HTTP {e.code}: {body}')
    except Exception as e:
        raise RuntimeError(str(e))

def parse_json(text):
    t=(text or '').strip()
    if t.startswith('```'):
        t=t.strip('`').strip()
        if t.lower().startswith('json'):
            t=t[4:].strip()
    try:
        return json.loads(t)
    except Exception:
        return {'score':None,'feedback':t or 'Correção concluída.'}

@app.route('/api/correct-block', methods=['POST','OPTIONS'])
def correct_block():
    if request.method=='OPTIONS':
        return ('',204)
    data=request.get_json(silent=True) or {}
    block=data.get('block')
    student=data.get('student') or 'estudante'
    answers=data.get('answers') or {}
    lesson=data.get('lesson') or {}
    if not answers:
        return jsonify({'error':'Nenhuma resposta deste bloco foi encontrada.'}),400
    prompt=f'''Você é professor avaliador de Matemática do 6º ano.
Corrija o BLOCO {block} da estudante {student} usando APENAS as respostas digitadas no aplicativo e o contexto pedagógico do próprio bloco abaixo.
Não peça foto. Não peça enunciado adicional. Não invente resposta que não esteja no material recebido.
Considere compreensão, resposta final e coerência com a atividade. Dê nota de 0 a 10.
Se alguma questão exigir desenvolvimento que não esteja digitado, não zere automaticamente: avalie o que for possível pela resposta final.
Escreva feedback curto, específico e pedagógico.
Retorne SOMENTE JSON válido com:
{{"score":0.0,"feedback":"...","strengths":["..."],"needs_review":["..."],"per_question":[{{"questao":1,"correta":true,"observacao":"..."}}]}}

CONTEXTO DO BLOCO:
{json.dumps(lesson,ensure_ascii=False)[:14000]}

RESPOSTAS SALVAS:
{json.dumps(answers,ensure_ascii=False)[:12000]}
'''
    try:
        out=parse_json(ai_call([
            {'role':'system','content':'Aja como professor avaliador. Seja objetivo, justo e pedagógico. Responda somente JSON válido.'},
            {'role':'user','content':prompt}
        ]))
        return jsonify(out)
    except Exception as e:
        return jsonify({'error':str(e)}),502
