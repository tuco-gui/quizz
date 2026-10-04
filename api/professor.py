from flask import Flask, request, jsonify
import os, json, urllib.request, urllib.error

app = Flask(__name__)

BASE_URL = os.environ.get('PROFESSOR_AI_BASE_URL', 'https://9router-nbob.srv1266039.hstgr.cloud/v1').rstrip('/')
API_KEY = os.environ.get('PROFESSOR_AI_API_KEY', '')
TEXT_MODEL = os.environ.get('PROFESSOR_AI_MODEL', 'llama3.2:latest')
VISION_MODEL = os.environ.get('PROFESSOR_AI_VISION_MODEL', TEXT_MODEL)

SYSTEM_PROMPT = '''Você é um professor avaliador de Matemática do 6º ano, em português do Brasil. Ensine uma ideia por vez, com frases curtas, linguagem clara e exemplos concretos. A estudante pode ter dificuldade de atenção e interpretação. Em dúvidas, não entregue imediatamente a resposta: primeiro identifique o que ela já sabe, dê uma pista curta e peça uma tentativa. Em avaliações, aja como professor: corrija questão por questão, atribua pontos conforme os pesos, mostre o que foi acertado e errado, explique de forma curta o ponto do erro e indique exatamente o que precisa ser revisado. Depois da correção, crie poucos exercícios novos e direcionados apenas aos conteúdos em que houve dificuldade, usando números e situações diferentes dos da prova. Use terminologia escolar compatível com o material Bernoulli, sem copiar páginas ou ilustrações protegidas. Em correções, responda SOMENTE em JSON válido.'''

EXAM_SPEC = [
  {'n':1,'weight':0.30,'question':'Na fração 5/8, identifique numerador e denominador.','expected':'numerador 5; denominador 8','needs_work':False},
  {'n':2,'weight':0.30,'question':'Uma barra de chocolate foi dividida em 6 partes iguais e 4 foram comidas. Que fração representa a parte comida?','expected':'4/6; aceitar 2/3 como equivalente simplificada','needs_work':False},
  {'n':3,'weight':0.30,'question':'Calcule 3/7 + 2/7.','expected':'5/7','needs_work':False},
  {'n':4,'weight':0.30,'question':'Calcule 7/10 - 3/10.','expected':'4/10; aceitar 2/5','needs_work':False},
  {'n':5,'weight':0.50,'question':'Complete a fração equivalente: 2/3 = __/12.','expected':'8/12, portanto o número é 8','needs_work':False},
  {'n':6,'weight':0.50,'question':'Calcule 1/2 + 1/4.','expected':'3/4','needs_work':True},
  {'n':7,'weight':0.50,'question':'Calcule 5/6 - 1/3.','expected':'1/2; aceitar 3/6 antes da simplificação','needs_work':True},
  {'n':8,'weight':0.50,'question':'Calcule 3/5 × 10/9.','expected':'2/3','needs_work':True},
  {'n':9,'weight':0.90,'question':'Há 2 litros de líquido. Cada copo comporta 1/4 de litro. Quantos copos completos podem ser servidos? Organize DADOS, PERGUNTA e OPERAÇÃO.','expected':'8 copos; operação 2 ÷ 1/4 = 8','needs_work':True},
  {'n':10,'weight':0.90,'question':'Um caminho foi percorrido 2/5 pela manhã e 1/3 à tarde. Qual fração foi percorrida no total e qual fração restou?','expected':'total 11/15; restante 4/15','needs_work':True},
  {'n':11,'weight':0.30,'question':'Escreva 7/10 na forma decimal.','expected':'0,7; aceitar 0.7','needs_work':False},
  {'n':12,'weight':0.30,'question':'Escreva 0,35 como fração decimal.','expected':'35/100; aceitar 7/20 se a resposta estiver simplificada','needs_work':False},
  {'n':13,'weight':0.30,'question':'Compare 3,5 e 3,50.','expected':'são iguais','needs_work':False},
  {'n':14,'weight':0.30,'question':'Calcule 2,58 + 3,20.','expected':'5,78','needs_work':False},
  {'n':15,'weight':0.50,'question':'Calcule 10,01 - 9,70.','expected':'0,31','needs_work':True},
  {'n':16,'weight':0.50,'question':'Coloque em ordem crescente: 1,9; 1,09; 1,99; 1,909.','expected':'1,09; 1,9; 1,909; 1,99','needs_work':False},
  {'n':17,'weight':0.50,'question':'Calcule 2,5 × 3,2.','expected':'8','needs_work':True},
  {'n':18,'weight':0.50,'question':'Calcule 84,6 ÷ 3.','expected':'28,2','needs_work':True},
  {'n':19,'weight':0.90,'question':'Há 3,25 litros de bebida. Cada copo comporta 0,25 litro. Quantos copos completos podem ser servidos?','expected':'13 copos','needs_work':True},
  {'n':20,'weight':0.90,'question':'Um produto custa R$ 32,90 por kg. Foram comprados 2,7 kg. Qual é o valor total e qual é o troco de R$ 100,00?','expected':'total R$ 88,83; troco R$ 11,17','needs_work':True}
]

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

def build_exam_report(out, student):
    score = out.get('score')
    pq = out.get('per_question') or []
    correct = [str(x.get('numero')) for x in pq if x.get('correta') is True]
    wrong = [str(x.get('numero')) for x in pq if x.get('correta') is False]
    lines = []
    lines.append(f'Resultado da avaliação de {student}')
    if score is not None:
        try: lines.append(f'Nota: {float(score):.1f}/10,0'.replace('.', ','))
        except: lines.append(f'Nota: {score}/10,0')
    if correct: lines.append('Questões acertadas: ' + ', '.join(correct) + '.')
    if wrong: lines.append('Questões que precisam de correção: ' + ', '.join(wrong) + '.')
    details=[]
    for x in pq:
        if x.get('correta') is False:
            obs=(x.get('observacao') or '').strip()
            pts=x.get('pontos_obtidos'); mx=x.get('pontos_maximos')
            prefix=f'Q{x.get("numero")}'
            if pts is not None and mx is not None: prefix += f' ({pts}/{mx})'
            details.append(prefix + (': '+obs if obs else ''))
    if details:
        lines.append('O que corrigir:')
        lines.extend('• '+d for d in details)
    needs=out.get('needs_review') or []
    if needs:
        lines.append('Revisar antes da prova: ' + '; '.join(str(x) for x in needs) + '.')
    strengths=out.get('strengths') or []
    if strengths:
        lines.append('Pontos fortes: ' + '; '.join(str(x) for x in strengths) + '.')
    exercises=out.get('remedial_exercises') or []
    if exercises:
        lines.append('Treino recomendado:')
        for i,ex in enumerate(exercises[:6],1):
            if isinstance(ex,dict):
                topic=ex.get('topico') or ex.get('topic') or ''
                prompt=ex.get('exercicio') or ex.get('prompt') or ''
                reason=ex.get('objetivo') or ex.get('why') or ''
                txt=f'{i}. {prompt}'
                if topic: txt += f' [{topic}]'
                if reason: txt += f' — {reason}'
                lines.append(txt)
            else:
                lines.append(f'{i}. {ex}')
    if out.get('feedback'):
        lines.append('Resumo do professor: ' + str(out.get('feedback')).strip())
    return '\n'.join(lines)

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
            text = f'''Corrija o bloco {block} da estudante {student}. Considere as respostas digitadas: {json.dumps(answers, ensure_ascii=False)}. A foto contém principalmente cálculos do caderno e NÃO precisa repetir os enunciados. Analise a foto como evidência do raciocínio. Não peça novamente enunciados que já fazem parte do aplicativo. Dê nota de 0 a 10 considerando resultado, procedimento e compreensão. Retorne JSON com score, feedback, strengths, needs_review e remedial_exercises. Em remedial_exercises crie de 2 a 4 exercícios novos, apenas sobre os erros encontrados, sem fornecer as respostas.'''
            msg = [{'type':'text','text':text},{'type':'image_url','image_url':{'url':image}}]
            content = ai_call(VISION_MODEL,[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':msg}],0.1)
            out = parse_json_content(content); out['provider']='router'; out['model']=VISION_MODEL
            return jsonify(out)

        if mode == 'correct_exam':
            images = data.get('images') or []
            if not images:
                return jsonify({'error':'Fotos da avaliação não recebidas.'}), 400
            answers = data.get('answers') or {}
            instructions = f'''Você é o PROFESSOR AVALIADOR desta prova. Corrija a Avaliação Final da estudante {student}.

REGRA ESSENCIAL:
- Os enunciados, pesos e o gabarito estão fornecidos abaixo pelo SISTEMA. NUNCA peça ao aluno para enviar enunciados, prova completa ou gabarito.
- As fotos são apenas das contas/cálculos do caderno. É normal que não mostrem os enunciados.
- Use PRIMEIRO a resposta digitada no aplicativo para cada questão.
- Use as fotos para confirmar procedimento, cálculo e raciocínio nas questões que exigem conta.
- Se uma questão não exige desenvolvimento escrito, corrija pela resposta digitada; NÃO penalize por não haver cálculo na foto.
- Se a resposta digitada estiver correta e o cálculo não for necessário, dê a pontuação integral.
- Nas questões marcadas needs_work=true, considere o raciocínio visível nas fotos quando for possível associá-lo ao número da questão.
- Se a foto estiver parcialmente ilegível, não invente erro: use o que estiver legível e a resposta digitada.
- Some EXATAMENTE os pesos. A prova vale 10,00 pontos.
- Não solicite material adicional. Faça a melhor correção possível com o que o sistema já forneceu.

O RELATÓRIO TEM DE FUNCIONAR COMO DEVOLUTIVA DE PROFESSOR:
1. dizer a nota final;
2. indicar claramente quais questões foram acertadas;
3. indicar quais questões foram erradas;
4. em cada questão errada, explicar em uma frase qual foi o erro ou qual conceito precisa ser corrigido;
5. listar os conteúdos prioritários para revisão;
6. destacar também os pontos fortes;
7. criar de 3 a 6 exercícios NOVOS, sem respostas, direcionados SOMENTE aos conteúdos que ela errou, com dificuldade semelhante à prova e números diferentes. Não copie nenhuma questão da avaliação.

BANCO OFICIAL DA AVALIAÇÃO E GABARITO INTERNO:
{json.dumps(EXAM_SPEC, ensure_ascii=False)}

RESPOSTAS DIGITADAS NO APLICATIVO:
{json.dumps(answers, ensure_ascii=False)}

Retorne SOMENTE JSON válido com esta estrutura:
{{
  "score": 0.0,
  "feedback": "resumo geral curto e pedagógico",
  "strengths": ["ponto forte 1"],
  "needs_review": ["conteúdo 1"],
  "per_question": [
    {{"numero":1,"correta":true,"pontos_obtidos":0.30,"pontos_maximos":0.30,"observacao":"resposta correta"}}
  ],
  "remedial_exercises": [
    {{"topico":"frações","exercicio":"enunciado do novo exercício","objetivo":"o que este exercício treina"}}
  ]
}}
Inclua as 20 questões em per_question.'''
            parts = [{'type':'text','text':instructions}]
            for im in images[:4]:
                parts.append({'type':'image_url','image_url':{'url':im}})
            content = ai_call(VISION_MODEL,[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':parts}],0.05)
            out = parse_json_content(content)
            out['provider']='router'; out['model']=VISION_MODEL
            out['raw_summary']=out.get('feedback','')
            out['feedback']=build_exam_report(out, student)
            return jsonify(out)

        return jsonify({'error':'Modo inválido.'}), 400
    except Exception as e:
        msg = str(e)
        if 'image' in msg.lower() or 'vision' in msg.lower() or 'multimodal' in msg.lower():
            msg += ' O modelo configurado parece não aceitar imagens. Configure PROFESSOR_AI_VISION_MODEL com um modelo multimodal.'
        return jsonify({'error':msg}), 502
