from flask import Flask
from flask import render_template
from flask import request, redirect
import json

app = Flask(__name__)


@app.route('/theme', methods=['GET', 'POST'])
def theme_selector():
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)
    if request.method == 'POST':
        print(request.form)
        return redirect(f'/quiz/{request.form.to_dict()['themes']}/0')
    elif request.method == 'GET':
        return render_template("quiz.html",
                               title='Home',
                               themes=questions['questions'])


@app.route('/quiz/<theme>/<q_number>', methods=['GET', 'POST'])
def question_prompt(theme, q_number):
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    vopros = questions[theme][int(q_number)]
    if request.method == 'POST':
        if int(request.form.to_dict()['answers']) == vopros['correct']:
            return redirect(f'/quiz/{theme}/{int(q_number) + 1}')
        else:
            return "иди нахуй"
    elif request.method == 'GET':
        return render_template("question.html",
                               question=vopros['question'],
                               variants=enumerate(vopros['answers']))


if __name__ == '__main__':
    app.run(debug=True)