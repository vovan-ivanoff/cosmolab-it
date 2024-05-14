from string import ascii_uppercase
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
rooms = {}
cur_que = {}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code


def generate_qs(theme):
    tmp = []
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    for _ in range(20):
        while (i := random.choice(
                questions[theme])) in tmp:
            pass
        tmp.append(i)
    return tmp.copy()


def get_themes():
    with open("questions.json", 'r', encoding='UTF-8') as f:
        questions: dict = json.load(f)['questions']
    return list(questions.keys())


def add_rating_db(rating: dict):
    connection = sqlite3.connect('users_data.db')
    cursor = connection.cursor()
    sel_query = "SELECT rating FROM users WHERE name = ?"
    upd_query = 'UPDATE users SET rating = ? WHERE name = ?'
    for user in rating:
        cursor.execute(sel_query, (user))
        usr_psw = cursor.fetchall()
        cursor.execute(upd_query, (rating[user] + usr_psw[0][0],
                                   user))
    connection.commit()
    connection.close()


@socketio.on('connect', namespace='/room')
def handle_connect(_):
    name = session['username']
    room = session.get('room')
    if name is None or room is None:
        return
    if room not in rooms:
        leave_room(room)
    join_room(room)
    send(f"{name} заходит в чат", to=room)
    session['coop_progress'] = 0
    rooms[room]["members"] += 1
    rooms[room]["result"][name] = 0
    rooms[room]["ready"][name] = False
    emit("pcount", rooms[room]['members'], to=room)
    emit("themes", rooms[room]["themes"])


@socketio.on('start', namespace='/room')
def handle_start(theme):
    room = session["room"]
    questions = generate_qs(theme)
    rooms[room]['questions'] = questions
    emit("question", rooms[room]['questions'][0], to=room)


@socketio.on('answer', namespace='/room')
def handle_answer(answer):
    room = rooms[session["room"]]
    name = session["username"]
    if answer == 'corr':
        room['result'][name] += 1
    session['coop_progress'] += 1
    if session['coop_progress'] >= len(room['questions']):
        room['ready'][name] = True
        emit('wait')
        flag = True
        for n in room['ready']:
            flag = flag and room['ready'][n]
        if flag:
            emit("end", room["result"], to=session['room'])
            add_rating_db(room["result"])
    else:
        emit("question", room['questions'][session['coop_progress']])


@socketio.on('message', namespace='/room')
def handle_chat_message(message):
    result = session['username'] + " : " + message
    print("Received message: " + result)
    send(result, to=session["room"])


@socketio.on('disconnect', namespace='/room')
def handle_disconnect():
    room = session.get("room")
    name = session.get("username")
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        rooms[room]['ready'].pop(name)
        emit("pcount", rooms[room]['members'], to=room)
        if rooms[room]["members"] <= 0:
            del rooms[room]
        send(f"{name} покинул(а) чат", to=room)


@socketio.on('connect', namespace='/single')
def handle_single_connect(_):
    session['progress'] = 0
    session['correct'] = 0
    emit("themes", get_themes())


@socketio.on('start', namespace='/single')
def handle_single_start(theme):
    questions = generate_qs(theme)
    session['questions'] = questions
    emit("question", session['questions'][0])


@socketio.on('answer', namespace='/single')
def handle_single_answer(answer):
    name = session["username"]
    if answer == 'corr':
        session['correct'] += 1
    session['progress'] += 1
    if session['progress'] >= len(session['questions']):
        emit("end", {name: session['correct']})
        add_rating_db({name: session['correct']})
    else:
        emit("question", session['questions'][session['progress']])


@app.route("/single")
def single():
    return render_template('single.html', name=session.get('username'))


@app.route('/coop', methods=['POST', 'GET'])
def createroom():
    if request.method == "POST":
        # session['name'] = request.form.get("name_room")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if join is not False and not code:
            return render_template("joinroom.html",
                                   error="Please enter a room code.",
                                   code=code)
        room = code
        if create is not False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0,
                           'result': {},
                           'themes': get_themes(),
                           'ready': {}}
        elif code not in rooms:
            return render_template("joinroom.html",
                                   error="Room does not exist.",
                                   code=code)
        session["room"] = room
        return redirect("/room")
    return render_template("joinroom.html", rooms=rooms)


@app.route("/room")
def show_room():
    return render_template('room.html', code=session.get('room'))


@app.route('/rating')
def show_rating():
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
        p_and_u = password + username
        crypto_password = sha256(p_and_u.encode('utf-8')).hexdigest()
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

        # mail + test of loyalty
        mail = request.form['mail']
        if '@' not in mail:
            correct_mail = False
        rating = 0
        p_and_u = password + username
        crypto_password = sha256(p_and_u.encode('utf-8')).hexdigest()
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


@app.route('/create_quiz', methods=['POST', 'GET'])
def create_quiz():
    return render_template('create_quiz.html')


@app.route('/make_quiz', methods=['POST', 'GET'])
def make_quiz():
    if request.method == 'POST':
        cur_que['name'] = request.form['name_quiz']
        cur_que['amount'] = int(request.form['amount'])
    return render_template('make_quiz.html', cur_que=cur_que)

@app.route('/get_zip', methods=['POST', 'GET'])
def get_zip():
    if request.method == 'POST':
        print(request.form)
        json_data = {cur_que['name']: []}
        for i in range(int(len(request.form) / 5)):
            json_data[cur_que['name']].append({"question": request.form['ans' + str(i)]})
            json_data[cur_que['name']][i]["answers"] = [request.form['cor' + str(i)]]
            for j in range(3):
                json_data[cur_que['name']][i]["answers"].append(request.form[str(i) + '/' + str(j)])
            json_data[cur_que['name']][i]['correct'] = 1
            json_data[cur_que['name']][i]['time'] = 30

        print(json_data)
        json_loaded = json.dumps(json_data, ensure_ascii=False, indent=2)
        with open('example.json', 'w', encoding="UTF-8") as f:
            f.write(json_loaded)
    return render_template('get_zip.html')

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host="localhost", allow_unsafe_werkzeug=True, debug=True)
