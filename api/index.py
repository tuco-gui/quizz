from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Dados simulados para ambiente Vercel (sem banco de dados)
USERS = []
RESPONSES = []
SCORES = []

# Carregar as perguntas do quiz
QUIZ_DATA = {
    "1": [
        {
            "id": 1,
            "question": "Qual o propósito bíblico de Jesus ter levado sobre si nossas dores e enfermidades, segundo Isaías 53:4-5?",
            "options": [
                "Prover cura e paz por meio do seu sofrimento",
                "Demonstrar sua humanidade",
                "Nos ensinar a suportar o sofrimento com fé",
                "Mostrar que Ele também sofria como nós"
            ],
            "correct": 0
        },
        {
            "id": 2,
            "question": "De acordo com Romanos 3:23-25, como a justificação é oferecida aos pecadores?",
            "options": [
                "Por meio das boas obras e da obediência à Lei",
                "Como recompensa por esforço pessoal",
                "Gratuitamente, pela graça, mediante a fé em Jesus Cristo",
                "Pela intercessão dos santos"
            ],
            "correct": 2
        },
        {
            "id": 3,
            "question": "Segundo 2 Coríntios 5:21, o que significa dizer que Jesus 'se fez pecado' por nós?",
            "options": [
                "Que Ele foi acusado injustamente de um crime",
                "Que Ele pecou como ser humano",
                "Que assumiu nossa condição pecaminosa para nos justificar diante de Deus",
                "Que Ele foi rejeitado pelos líderes religiosos"
            ],
            "correct": 2
        },
        {
            "id": 4,
            "question": "O que simboliza o rasgar do véu do templo após a morte de Jesus, conforme Mateus 27:51?",
            "options": [
                "O fim das tradições judaicas",
                "Um aviso de destruição de Jerusalém",
                "A abertura do acesso direto à presença de Deus",
                "A libertação dos condenados no Hades"
            ],
            "correct": 2
        },
        {
            "id": 5,
            "question": "Em Colossenses 3:3-5, o apóstolo Paulo afirma que o 'velho homem' deve morrer para que a nova vida surja. O que isso representa no contexto da cruz, segundo o ensino da aula?",
            "options": [
                "Que devemos abandonar nossas tradições religiosas",
                "Que devemos ignorar os desejos do corpo físico",
                "Que a vida cristã é uma prática diária de renúncia ao pecado",
                "Que devemos alcançar a perfeição para sermos salvos"
            ],
            "correct": 2
        }
    ],
    "2": [
        {
            "id": 6,
            "question": "O que o sangue de Cristo simboliza?",
            "options": [
                "Um ritual religioso",
                "Sacrifício e redenção",
                "Uma tradição antiga",
                "Um símbolo de medo"
            ],
            "correct": 1
        },
        {
            "id": 7,
            "question": "Qual destas afirmações sobre o nome de Jesus está correta?",
            "options": [
                "É apenas um nome comum",
                "Tem poder para curar e libertar",
                "Deve ser usado com cautela",
                "Não tem importância espiritual"
            ],
            "correct": 1
        },
        {
            "id": 8,
            "question": "O que significa 'andar na luz' segundo os ensinamentos?",
            "options": [
                "Viver em pecado oculto",
                "Ter uma vida cheia de boas obras visíveis",
                "Manter uma relação íntima com Deus e outros crentes",
                "Evitar conflitos sociais"
            ],
            "correct": 2
        },
        {
            "id": 9,
            "question": "Qual é um dos resultados de reconhecer o poder do sangue de Cristo?",
            "options": [
                "Medo constante do julgamento divino",
                "Liberdade e paz interior",
                "Aumento da culpa e vergonha",
                "Isolamento social"
            ],
            "correct": 1
        },
        {
            "id": 10,
            "question": "Como devemos usar o nome de Jesus, segundo os ensinamentos?",
            "options": [
                "Com fé e autoridade em todas as situações",
                "Apenas em momentos de necessidade",
                "Como um último recurso",
                "Para se vangloriar diante dos outros"
            ],
            "correct": 0
        }
    ],
    "3": [
        {
            "id": 11,
            "question": "O que significa ser filho(a) de Deus para um cristão?",
            "options": [
                "Ter privilégios especiais na sociedade",
                "Viver em conformidade com os padrões divinos",
                "Ter acesso a riqueza material",
                "Ser aceito por todos"
            ],
            "correct": 1
        },
        {
            "id": 12,
            "question": "Uma das práticas que os cristãos devem evitar é:",
            "options": [
                "Oração",
                "Jejum",
                "Inveja",
                "Comunhão"
            ],
            "correct": 2
        },
        {
            "id": 13,
            "question": "Qual é um dos principais objetivos da vida cristã, segundo os ensinamentos?",
            "options": [
                "Agradar aos homens",
                "Buscar reconhecimento social",
                "Viver para agradar a Deus",
                "Acumular bens materiais"
            ],
            "correct": 2
        },
        {
            "id": 14,
            "question": "O perdão deve ser:",
            "options": [
                "Condicional e limitado",
                "Incondicional e contínuo",
                "Apenas quando conveniente",
                "Algo raro e especial"
            ],
            "correct": 1
        },
        {
            "id": 15,
            "question": "Como devemos lidar com as tentações do mundo, segundo os ensinamentos?",
            "options": [
                "Ignorá-las completamente",
                "Enfrentá-las com fé e oração",
                "Ceder ocasionalmente",
                "Focar apenas nas coisas boas"
            ],
            "correct": 1
        }
    ],
    "4": [
        {
            "id": 16,
            "question": "Por que a participação na igreja é importante para o cristão?",
            "options": [
                "Para ganhar prestígio social",
                "Para crescimento espiritual e comunhão",
                "Para evitar solidão",
                "Para seguir tradições familiares"
            ],
            "correct": 1
        },
        {
            "id": 17,
            "question": "Qual é uma prática essencial na vida de oração?",
            "options": [
                "Orar apenas quando necessário",
                "Usar palavras eloquentes",
                "Orar com fé e sinceridade",
                "Evitar orações longas"
            ],
            "correct": 2
        },
        {
            "id": 18,
            "question": "Os benefícios da oração incluem:",
            "options": [
                "Acalmar ansiedades e fortalecer relacionamentos com Deus",
                "Ganhar sempre o que se pede",
                "Ser ouvido por todos",
                "Obter reconhecimento público"
            ],
            "correct": 0
        },
        {
            "id": 19,
            "question": "Como podemos demonstrar nossa fé através da oração?",
            "options": [
                "Apenas orando em silêncio",
                "Compartilhando nossas orações com outras pessoas",
                "Orando sem esperar respostas",
                "Orando conforme as instruções bíblicas"
            ],
            "correct": 3
        },
        {
            "id": 20,
            "question": "Quais são algumas maneiras de incentivar outros à oração?",
            "options": [
                "Impor regras rígidas",
                "Compartilhar experiências pessoais",
                "Criticar quem não ora",
                "Evitar discutir sobre oração"
            ],
            "correct": 1
        }
    ],
    "5": [
        {
            "id": 21,
            "question": "O perdão é considerado:",
            "options": [
                "Uma sugestão opcional",
                "Uma ordem divina necessária",
                "Algo que deve ser evitado",
                "Apenas para ocasiões especiais"
            ],
            "correct": 1
        },
        {
            "id": 22,
            "question": "O batismo simboliza:",
            "options": [
                "A aceitação social",
                "Purificação e identificação com Cristo",
                "Um ritual sem importância",
                "Uma tradição cultural"
            ],
            "correct": 1
        },
        {
            "id": 23,
            "question": "Quais são os efeitos negativos da falta de perdão na vida do cristão?",
            "options": [
                "Amargura e ressentimento",
                "Crescimento espiritual",
                "Paz interior",
                "Comunhão saudável"
            ],
            "correct": 0
        },
        {
            "id": 24,
            "question": "Como devemos usar o poder do nome de Jesus?",
            "options": [
                "Para manipulação pessoal",
                "Apenas em situações extremas",
                "Com fé em todas as circunstâncias",
                "Para impressionar os outros"
            ],
            "correct": 2
        },
        {
            "id": 25,
            "question": "Quais são passos práticos para crescer espiritualmente após o batismo?",
            "options": [
                "Ignorar ensinamentos bíblicos",
                "Focar apenas em coisas naturais",
                "Viver isoladamente",
                "Participar ativamente da comunidade cristã"
            ],
            "correct": 3
        }
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        # Validar dados
        if not name or not phone:
            return render_template('register.html', error="Nome e telefone são obrigatórios")
        
        # Criar novo usuário
        user_id = len(USERS) + 1
        user = {
            'id': user_id,
            'name': name,
            'phone': phone,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        USERS.append(user)
        
        # Salvar ID do usuário na sessão
        session['user_id'] = user_id
        session['name'] = name
        
        # Iniciar o quiz
        return redirect(url_for('start_quiz'))
    
    return render_template('register.html')

@app.route('/start-quiz')
def start_quiz():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    # Inicializar o quiz na aula 1, pergunta 1
    session['current_aula'] = 1
    session['current_question'] = 0
    session['score'] = 0
    session['aula_scores'] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    return render_template('start_quiz.html')

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    current_aula = session.get('current_aula', 1)
    current_question = session.get('current_question', 0)
    
    # Verificar se ainda há perguntas na aula atual
    if current_aula <= 5:
        if current_question < len(QUIZ_DATA[str(current_aula)]):
            question_data = QUIZ_DATA[str(current_aula)][current_question]
            return render_template('quiz.html', 
                                  question=question_data,
                                  aula=current_aula,
                                  question_number=current_question + 1,
                                  total_questions=len(QUIZ_DATA[str(current_aula)]))
        else:
            # Avançar para a próxima aula
            session['current_aula'] = current_aula + 1
            session['current_question'] = 0
            
            # Se ainda houver aulas, mostrar mensagem de transição
            if session['current_aula'] <= 5:
                return render_template('next_aula.html', next_aula=session['current_aula'])
            else:
                # Finalizar o quiz
                return redirect(url_for('finish'))
    else:
        # Finalizar o quiz
        return redirect(url_for('finish'))

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    current_aula = session.get('current_aula', 1)
    current_question = session.get('current_question', 0)
    
    # Obter a resposta do usuário
    selected_option = int(request.form.get('option', -1))
    
    if selected_option == -1:
        return redirect(url_for('quiz'))
    
    # Verificar se a resposta está correta
    question_data = QUIZ_DATA[str(current_aula)][current_question]
    is_correct = (selected_option == question_data['correct'])
    
    # Salvar a resposta
    response = {
        'user_id': session['user_id'],
        'question_id': question_data['id'],
        'aula_number': current_aula,
        'selected_option': selected_option,
        'is_correct': is_correct,
        'created_at': datetime.now().isoformat()
    }
    RESPONSES.append(response)
    
    # Atualizar a pontuação
    if is_correct:
        session['score'] = session.get('score', 0) + 1
        session['aula_scores'][str(current_aula)] = session['aula_scores'].get(str(current_aula), 0) + 1
    
    # Avançar para a próxima pergunta
    session['current_question'] = current_question + 1
    
    # Verificar se é a última pergunta da aula
    if session['current_question'] >= len(QUIZ_DATA[str(current_aula)]):
        # Salvar a pontuação da aula
        score = {
            'user_id': session['user_id'],
            'aula_number': current_aula,
            'correct_answers': session['aula_scores'].get(str(current_aula), 0),
            'total_questions': len(QUIZ_DATA[str(current_aula)]),
            'created_at': datetime.now().isoformat()
        }
        SCORES.append(score)
    
    # Mostrar feedback
    return render_template('feedback.html', 
                          is_correct=is_correct,
                          correct_answer=question_data['options'][question_data['correct']],
                          selected_answer=question_data['options'][selected_option])

@app.route('/next-question')
def next_question():
    return redirect(url_for('quiz'))

@app.route('/finish')
def finish():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    user_id = session['user_id']
    
    # Obter as pontuações do usuário
    user_scores = [score for score in SCORES if score['user_id'] == user_id]
    total_score = sum(score['correct_answers'] for score in user_scores)
    total_questions = sum(score['total_questions'] for score in user_scores)
    
    # Obter o ranking
    ranking = get_ranking()
    
    return render_template('finish.html', 
                          scores=user_scores,
                          total_score=total_score,
                          total_questions=total_questions,
                          ranking=ranking[:10])  # Top 10

@app.route('/ranking')
def ranking():
    ranking_data = get_ranking()
    return render_template('ranking.html', ranking=ranking_data)

def get_ranking():
    # Calcular pontuação total por usuário
    user_totals = {}
    for score in SCORES:
        user_id = score['user_id']
        if user_id not in user_totals:
            user_totals[user_id] = {
                'total_correct': 0,
                'total_questions': 0,
                'aula_scores': {}
            }
        user_totals[user_id]['total_correct'] += score['correct_answers']
        user_totals[user_id]['total_questions'] += score['total_questions']
        user_totals[user_id]['aula_scores'][score['aula_number']] = score['correct_answers']
    
    # Formatar os resultados
    ranking = []
    for user in USERS:
        user_id = user['id']
        if user_id in user_totals:
            total_correct = user_totals[user_id]['total_correct']
            total_questions = user_totals[user_id]['total_questions']
            ranking.append({
                'user_id': user_id,
                'name': user['name'],
                'phone': user['phone'],
                'aula_scores': user_totals[user_id]['aula_scores'],
                'total_correct': total_correct,
                'total_questions': total_questions,
                'percentage': (total_correct / total_questions * 100) if total_questions > 0 else 0
            })
    
    # Ordenar por pontuação
    ranking.sort(key=lambda x: x['total_correct'], reverse=True)
    
    # Adicionar posição no ranking
    for i, item in enumerate(ranking):
        item['rank'] = i + 1
    
    return ranking

@app.route('/api/ranking')
def api_ranking():
    ranking_data = get_ranking()
    return jsonify(ranking_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
