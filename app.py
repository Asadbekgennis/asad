from flask import Flask, render_template, g, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db

app = Flask(__name__)
app.config['SECRET_KEY'] = "asjdgaiwuyed78tg7tsa87d872ed"


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'questions_db'):
        g.sqlite_db.close()


def current_user():
    user_now = None
    if 'name' in session:
        db = get_db()
        user_get = db.execute('select id, name, password, expert, admin from users where name=?', [session['name']])
        user_now = user_get.fetchone()
    return user_now


@app.route('/')
def main_menu():
    user = current_user()
    db = get_db()
    if not user:
        questions = db.execute(
            'select questions.questions_text, questions.answer_text, askers.name as askers_name, expert.name as expert_name from questions join users as askers on askers.id == questions.asked_by_id join users as expert on expert.id == questions.expert_id where questions.answer_text is not null')
        questions = questions.fetchall()
        return render_template('home.html', user=user, questions=questions)
    elif user and not user['expert'] and not user['admin']:
        questions = db.execute(
            'select questions.questions_text, questions.answer_text, askers.name as askers_name, expert.name as expert_name from questions join users as askers on askers.id == questions.asked_by_id join users as expert on expert.id == questions.expert_id where askers.id =? and  questions.answer_text is not null ',
            [user['id']])
        questions = questions.fetchall()
        return render_template('home.html', user=user, questions=questions)
    elif user['expert']:
        questions = db.execute(
            'select questions.questions_text, questions.answer_text, askers.name as askers_name, expert.name as expert_name from questions join users as askers on askers.id == questions.asked_by_id join users as expert on expert.id == questions.expert_id where expert.id =? and  questions.answer_text is not null ',
            [user['id']])
        questions = questions.fetchall()
        return render_template('home.html', user=user, questions=questions)
    else:
        questions = db.execute(
            'select questions.questions_text, questions.answer_text, askers.name as askers_name, expert.name as expert_name from questions join users as askers on askers.id == questions.asked_by_id join users as expert on expert.id == questions.expert_id where questions.answer_text is not null')
        questions = questions.fetchall()
        return render_template('home.html', user=user, questions=questions)


@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    if request.method == "POST":
        name = request.form.get('name')
        password = request.form.get('password')
        hashed = generate_password_hash(password, method='sha256')
        check_user = db.execute('select name, password from users where name = ?', [name])
        user_result = check_user.fetchone()
        print(type(name))
        print(type(hashed))
        if not user_result:
            db.execute("insert into users (name, password,expert, admin) values (?,?,?,?)",
                       [name, hashed, False, False])
            db.commit()
            return redirect(url_for('main_menu'))
        else:
            error = 'username bor'
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # check_user1()
    user = current_user()
    db = get_db()

    error = 'Users or password incorrect'
    if request.method == "POST":
        name = request.form.get('name')
        password = request.form.get('password')
        check_user = db.execute('select name, password from users where name = ?', [name])
        user_result = check_user.fetchone()
        db.commit()

        if user_result:
            if check_password_hash(user_result['password'], password):
                session['name'] = user_result['name']
                return redirect(url_for('main_menu'))
            else:
                return render_template('login.html', error=error)
        else:
            return render_template('login.html', error=error)
    return render_template('login.html', user=user)


@app.route('/ask_questions', methods=['GET', 'POST'])
def ask_question():
    user = current_user()
    try:
        if not user['admin'] and not user['expect']:
            return redirect(url_for('main_menu'))
    except TypeError:
        return redirect(url_for('main_menu'))
    db = get_db()
    if request.method == "POST":
        question_text = request.form.get('question_text')
        expert_id = int(request.form.get('expert_id'))
        db.execute('insert into questions (questions_text, expert_id, asked_by_id) values (?,?,?)',
                   [question_text, expert_id, user['id']])
        db.commit()

        return redirect(url_for('ask_question'))
    elif request.method == "GET":
        get_users = db.execute('select id, name, expert, admin from users where expert=?', [True])
        get_users = get_users.fetchall()
        return render_template('ask_questions.html', get_users=get_users, user=user)


@app.route('/answer_questions')
def answer_questions():
    user = current_user()
    try:
        if not user['admin'] and not user:
            return redirect(url_for('main_menu'))
    except TypeError:
        return redirect(url_for('main_menu'))
    db = get_db()
    questions = db.execute(
        'select questions.id, questions.questions_text, users.name from questions join users on users.id = questions.asked_by_id where questions.answer_text is null and questions.expert_id = ?',
        [user['id']])
    questions = questions.fetchall()

    return render_template('answer_questions.html', user=user, questions=questions)


@app.route('/answer/<int:get_id>', methods=['POST', 'GET'])
def answer(get_id):
    user = current_user()
    try:
        if not user['admin'] and not user:
            return redirect(url_for('main_menu'))
    except TypeError:
        return redirect(url_for('main_menu'))
    db = get_db()
    get_ask = db.execute('select id, questions_text, asked_by_id from questions where id=?', [get_id])
    get_ask = get_ask.fetchone()

    if request.method == 'POST':
        answer_text = request.form.get('answer')
        db.execute('update questions set answer_text=? where id=?', [answer_text, get_id])
        db.commit()
        return redirect(url_for('answer_questions'))
    return render_template('answer.html', get_ask=get_ask, user=user)


@app.route('/unanswered')
def unanswered():
    user = current_user()
    db = get_db()
    try:
        if not user['expert']:
            return redirect(url_for('main_menu'))
    except TypeError:
        return redirect(url_for('main_menu'))
    if not user:
        get_questions = db.execute('select ')
    return render_template('unanswered.html')


@app.route('/user_setup')
def user_setup():
    user = current_user()
    db = get_db()
    user_list = db.execute('select id, name, expert, admin from users where admin=?', [False])
    try:
        if not user['admin']:
            return redirect(url_for('main_menu'))
    except TypeError:
        return redirect(url_for('main_menu'))
    user_list = user_list.fetchall()
    return render_template('users.html', user_list=user_list, user=user)


@app.route('/log_out')
def log_out():
    session['name'] = None
    return redirect(url_for('main_menu'))


if __name__ == '__main__':
    app.run()
