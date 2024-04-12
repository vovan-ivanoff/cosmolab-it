from flask import Flask
from flask import render_template
from flask import request, redirect
from flask import session
import json
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '21d6t3yfuyhrewoi1en3kqw'


@app.route('/theme', methods=['GET', 'POST'])
def theme_selector():
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    if request.method == 'POST':
        session['questions_list'] = [random.choice(questions[
                                     request.form.to_dict()['themes']])
                                     for _ in range(20)]
        session['right_count'] = 0
        return redirect(f'/quiz/{request.form.to_dict()['themes']}/0')
    elif request.method == 'GET':
        return render_template("quiz.html",
                               title='Home',
                               themes=questions)


@app.route('/quiz/<theme>/<q_number>', methods=['GET', 'POST'])
def question_prompt(theme, q_number):
    if int(q_number) == 20:
        return f'правильных {session['right_count']}'
    vopros = session['questions_list'][int(q_number)]
    if request.method == 'POST':
        if int(request.form.to_dict()['answers']) == vopros['correct']:
            session['right_count'] += 1
            return redirect(f'/quiz/{theme}/{int(q_number) + 1}')
        else:
            return redirect(f'/quiz/{theme}/{int(q_number) + 1}')
    elif request.method == 'GET':
        return render_template("question.html",
                               question=vopros['question'],
                               variants=enumerate(vopros['answers']))


if __name__ == '__main__':
    app.run(debug=True)
