from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import inspect
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, Rank, User, Book, Chapter, Comment

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_ECHO"] = False

db.init_app(app)

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
      session["user_id"] = user.id
      session["user_username"] = user.username
      flash("Login exitoso", "success")
      return redirect(url_for("home"))
    else:
      flash("Usuario o contraseña incorrectos", "danger")

  return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if User.query.filter((User.username == username) | (User.email == email)).first():
      flash("Usuario o email ya registrados", "danger")
    else:
      new_user = User(username=username, email=email, password=password, rank_id=1) #rank_id = rank "User"
      db.session.add(new_user)
      db.session.commit()
      flash("Cuenta creada con éxito, ahora podés iniciar sesión", "success")
      return redirect(url_for("login"))

  return render_template("register.html")


@app.route("/")
def home():
  if "user_id" not in session:
    return redirect(url_for("login"))
  return f"Bienvenido, usuario {session['user_username']}!"

if __name__ == "__main__":
  with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if not tables: 
        print("creating tables...")
        db.create_all()
    else:
        print(f"all tables done")
  app.run(debug=True)
