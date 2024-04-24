import json
import random
import sqlite3
from hashlib import sha256
from flask import Flask, render_template, url_for
from flask import request, flash, redirect, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = '21d6t3yfuyhrewoi1en3kqw'
socketio = SocketIO(app, cors_allowed_origins='*')


@socketio.on('message')
def handle_message(message):
    print("Received message: " + message)
    send(message, broadcast=True)


@app.route('/single', methods=['GET', 'POST'])
def theme_selector():
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    if request.method == 'POST':
        tmp = []
        for _ in range(20):
            while (i := random.choice(
                       questions[request.form.to_dict()['themes']])) in tmp:
                pass
            tmp.append(i)
        session['questions_list'] = tmp.copy()
        session['right_count'] = 0
        return redirect(f"/victorina/{request.form.to_dict()['themes']}/0")
    elif request.method == 'GET':
        return render_template("quiz.html",
                               title='Home',
                               themes=questions)


@app.route('/victorina/<theme>/<q_number>', methods=['GET', 'POST'])
def question_prompt(theme, q_number):
    if int(q_number) == 20:
        return f"правильных {session['right_count']}"
    vopros = session['questions_list'][int(q_number)]
    if request.method == 'POST':
        if int(request.form.to_dict()['answers']) == vopros['correct']:
            session['right_count'] += 1
            return redirect(f'/victorina/{theme}/{int(q_number) + 1}')
        else:
            return redirect(f'/victorina/{theme}/{int(q_number) + 1}')
    elif request.method == 'GET':
        return render_template("question.html",
                               question=vopros['question'],
                               variants=enumerate(vopros['answers']))


@app.route('/coop')
def coop():
    return render_template('coop.html', title="Командная игра")


@app.route('/mode')
def quiz():
    return render_template('mode.html',
                           title="Выбор режима",
                           name=session['username'])


@app.route('/')
@app.route('/authorization', methods=['POST', 'GET'])
def authorize():
    if 'username' in session.keys() and not session['username'] is None:
        redirect(url_for('quiz'))
    if request.method == 'POST':
        db = sqlite3.connect('users_data.db')
        c = db.cursor()
        # c.execute("""CREATE TABLE users (
        # name text,
        # password text
        # )""")
        username = request.form['username']
        password = request.form['password']
        crypto_password = sha256(password.encode('utf-8')).hexdigest()
        query = "SELECT * FROM users WHERE name = ?"
        c.execute(query, (username,))
        usr_psw = c.fetchall()
        if len(usr_psw) != 0:
            usr_psw = usr_psw[0]
            if usr_psw[0] == username and usr_psw[1] == crypto_password:
                flash('вы вошли в аккаунт')
                session['username'] = username
                render_template('authorize.html', title="Вход")
                return redirect(url_for('quiz'))
            else:
                flash('ошибка')
        else:
            flash('такого аккаунта нет')
        # query = "SELECT * FROM users"
        # c.execute(query)
        # print(c.fetchall())
        db.commit()
        db.close()
    return render_template('authorize.html', title="Вход")


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        db = sqlite3.connect('users_data.db')
        c = db.cursor()
        # c.execute("""CREATE TABLE users (
        # name text,
        # password text
        # )""")
        username = request.form['username']
        password = request.form['password']
        crypto_password = sha256(password.encode('utf-8')).hexdigest()
        query = "SELECT * FROM users WHERE name = ?"
        c.execute(query, (username,))
        finded = c.fetchall()
        print(finded)
        if len(finded) == 0:
            query = "INSERT INTO users VALUES (?, ?)"
            c.execute(query, (username, crypto_password))
            c.execute("SELECT * FROM users")

            flash('аккаунт создан')
            db.commit()
        if len(finded) == 1:
            flash('такой аккаунт уже существует')
        db.close()
    return render_template('registration.html', title="Регистрация")


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host="127.0.0.1", allow_unsafe_werkzeug=True)