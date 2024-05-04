import json
import random
import sqlite3
from hashlib import sha256
from flask import Flask, render_template, url_for
from flask import request, flash, redirect, session
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = '21d6t3yfuyhrewoi1en3kqw'


@app.route('/single', methods=['GET', 'POST'])
def theme_selector():
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    if request.method == 'POST':
        tmp = []
        for _ in range(20):
            print(request.form.to_dict())
            while (i := random.choice(
                       questions[request.form.to_dict()['themes']])) in tmp:
                pass
            tmp.append(i)
        session['questions_list'] = tmp.copy()
        session['right_count'] = 0
        return redirect(f'/victorina/{request.form.to_dict()["themes"]}/0')
    elif request.method == 'GET':
        return render_template("quiz.html",
                               title='Home',
                               themes=questions)





@app.route('/victorina/<theme>/<q_number>', methods=['GET', 'POST'])
def question_prompt(theme, q_number):
    
    if int(q_number) == 20:
        #update rating in users_data.db
        rating = session["right_count"]
        connection = sqlite3.connect('users_data.db')
        cursor = connection.cursor()
        query = "SELECT rating FROM users WHERE name = ?"
        cursor.execute(query, (session['username'],))
        usr_psw = cursor.fetchall()

        cursor.execute('UPDATE users SET rating = ? WHERE name = ?', (rating + usr_psw[0][0], session['username']))
        connection.commit()
        connection.close()

        return f'правильных ответов {rating}'
    vopros = session['questions_list'][int(q_number)]
 
    if request.method == 'POST':
        
    
        if int(request.form.to_dict()['answers']) == vopros['correct']:
            session['right_count'] += 1
            return redirect(f'/victorina/{theme}/{int(q_number) + 1}')
        else:
            return redirect(f'/victorina/{theme}/{int(q_number) + 1}')
    elif request.method == 'GET':
        return render_template("question.html",
                                theme=theme,
                                q_number=int(q_number)+1,
                                question=vopros['question'],
                                variants=enumerate(vopros['answers']))


@app.route('/coop')
def coop():
    return render_template('coop.html', title="Командная игра")

@app.route('/rating')
def rating():
    connection = sqlite3.connect('users_data.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    ids = [(row[0], row[2]) for row in cursor]
    
    ids = sorted(ids, reverse=True, key=lambda x: x[1])
    session['users_rating'] = ids.copy()
    return render_template("rating.html", rows=ids)


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
        password_and_username = password + username
        crypto_password = sha256(password_and_username.encode('utf-8')).hexdigest()
        
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
        correct_mail = True
        error = False
        username = request.form['username']
        if username == "":
            error = True
            flash('введите никнейм')
        password = request.form['password']
        if password == "":
            error = True
            flash('введите пароль')

        #mail + test of loyalty
        mail = request.form['mail']
        
        if '@' not in mail:
            correct_mail = False
        rating = 0
        password_and_username = password + username
        crypto_password = sha256(password_and_username.encode('utf-8')).hexdigest()
        
        query = "SELECT * FROM users WHERE name = ?"
        c.execute(query, (username,))
        finded = c.fetchall()
        print(finded)
        if len(finded) == 0 and correct_mail is True and error is False:
            query = "INSERT INTO users VALUES (?, ?, ?, ?)"
            c.execute(query, (username, crypto_password, rating, mail))
            c.execute("SELECT * FROM users")

            flash('аккаунт создан')
            db.commit()
        elif correct_mail is False and len(finded) == 0:
            flash('неверно указан адрес электронной почты')
        if len(finded) == 1 and error is False:
            flash('такой аккаунт уже существует')
        db.close()
    return render_template('registration.html', title="Регистрация")


if __name__ == '__main__':
    app.run(debug=True)
