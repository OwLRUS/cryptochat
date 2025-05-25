from flask import Flask, request, render_template, redirect, session
from utils import generate_substitution_key, encrypt, decrypt
import string
import os

app = Flask(__name__)
app.secret_key = 'secretkey_for_demo_ctf_only'

USERFILE = 'users.txt'

# Загружаем пользователей
def load_users():
    users = {}
    if os.path.exists(USERFILE):
        with open(USERFILE, 'r') as f:
            for line in f:
                if ':' in line:
                    login, pw = line.strip().split(':', 1)
                    users[login.upper()] = pw
    return users

# Добавляем нового пользователя
def register_user(login, password):
    with open(USERFILE, 'a') as f:
        f.write(f"{login}:{password}\n")

USERS = load_users()
KEYS = {}  # (sender, receiver) → key
MESSAGES = []  # (sender, receiver, ciphertext)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and not request.args.get("send"):
        login = request.form.get("username", "").strip().upper()
        pw = request.form.get("password", "").strip()

        if request.form.get("action") == "Register":
            if login not in USERS:
                register_user(login, pw)
                USERS[login] = pw
                session["username"] = login
                return redirect("/")
            else:
                return "User already exists.", 403

        if USERS.get(login) == pw:
            session["username"] = login
            return redirect("/")
        else:
            return "Invalid login or password", 403

    user = session.get("username", "")
    if not user:
        return render_template("index.html", login=True)

    # Logout
    if request.args.get("logout") == "1":
        session.pop("username", None)
        return redirect("/")

    # Отправка сообщения
    if request.args.get("send") == "1":
        to = request.form.get("to", "").strip().upper()
        text = request.form.get("text", "")
        if to and text:
            key = KEYS.get((user, to))
            if not key:
                key = generate_substitution_key()
                KEYS[(user, to)] = key
            ct = encrypt(text.upper(), key)
            MESSAGES.append((user, to, ct))

    # Видимые сообщения = все входящие и исходящие
    visible = []
    hidden = []
    for sender, receiver, ct in MESSAGES:
        if receiver == user or sender == user:
            key = KEYS.get((sender, receiver))
            pt = decrypt(ct, key) if key else "<ERROR>"
            direction = "←" if receiver == user else "→"
            other = sender if receiver == user else receiver
            visible.append((direction, other, pt))
        else:
            hidden.append((sender, receiver, ct))

    return render_template("index.html", login=False, username=user,
                           users=sorted(USERS.keys() - {user}),
                           visible=visible, hidden=hidden)

if __name__ == "__main__":
    app.run(debug=True, port=7777)
