from flask import Flask, request, render_template, redirect, session
from models import db, User, Message
from utils import generate_substitution_key, encrypt, decrypt
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ctf_chat.db'  # SQLite для простоты
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey_for_demo_ctf_only'

db.init_app(app)

# Создаем таблицы при первом запуске
with app.app_context():
    db.create_all()

# Регистрация пользователя
def register_user(login, password):
    if not User.query.filter_by(login=login.upper()).first():
        new_user = User(login=login.upper(), password=password)
        db.session.add(new_user)
        db.session.commit()
        return True
    return False

# Аутентификация пользователя
def authenticate_user(login, password):
    user = User.query.filter_by(login=login.upper(), password=password).first()
    return user is not None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and not request.args.get("send"):
        login = request.form.get("username", "").strip().upper()
        pw = request.form.get("password", "").strip()

        if request.form.get("action") == "Register":
            if register_user(login, pw):
                session["username"] = login
                return redirect("/")
            else:
                return "User already exists.", 403

        if authenticate_user(login, pw):
            session["username"] = login
            return redirect("/")
        else:
            return "Invalid login or password", 403

    user = session.get("username", "")
    if not user:
        return render_template("index.html", login=True)

    # Выход
    if request.args.get("logout") == "1":
        session.pop("username", None)
        return redirect("/")

    # Отправка сообщения
    if request.args.get("send") == "1":
        to = request.form.get("to", "").strip().upper()
        text = request.form.get("text", "")
        if to and text:
            sender = User.query.filter_by(login=user).first()
            receiver = User.query.filter_by(login=to).first()
            if sender and receiver:
                key = generate_substitution_key()  # Новый ключ для каждого сообщения
                ct = encrypt(text.upper(), key)
                print(ct)
                new_message = Message(sender_id=sender.id, receiver_id=receiver.id, ciphertext=ct, key=key)
                db.session.add(new_message)
                db.session.commit()
                return redirect("/")

    # Получаем текущего пользователя
    current_user = User.query.filter_by(login=user).first()

    # Последние 100 сообщений, связанных с текущим пользователем
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.id.desc()).limit(100).all()

    visible = []
    for msg in messages:
        sender = User.query.get(msg.sender_id).login
        receiver = User.query.get(msg.receiver_id).login
        key = msg.key
        pt = decrypt(msg.ciphertext, key)
        direction = "←" if receiver == user else "→"
        other = sender if receiver == user else receiver
        visible.append((direction, other, pt))

    # Последние 100 зашифрованных сообщений, не связанных с пользователем
    hidden = Message.query.filter(
        (Message.sender_id != current_user.id) & (Message.receiver_id != current_user.id)
    ).order_by(Message.id.desc()).limit(100).all()
    hidden = [(User.query.get(msg.sender_id).login, User.query.get(msg.receiver_id).login, msg.ciphertext) for msg in hidden]

    return render_template("index.html", login=False, username=user,
                           users=[u.login for u in User.query.all() if u.login != user],
                           visible=visible, hidden=hidden)

if __name__ == "__main__":
    app.run(debug=True, port=7777)