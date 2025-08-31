from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import inspect
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, Rank, User, Book, Chapter, Comment

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_ECHO"] = False

db.init_app(app)

def require_login():
    if "user_id" not in session:
        return False
    return True

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
@app.route("/home")
def home():
  if not require_login():
    return redirect(url_for("login"))

  user_id = session["user_id"]

  q = request.args.get("q", "", type=str).strip()
  scope = request.args.get("scope", "all")
  sort = request.args.get("sort", "updated_desc")

  books_query = Book.query
  if scope == "mine":
    books_query = books_query.filter(Book.creator_user_id == user_id)

  if q:
    like = f"%{q}%"
    books_query = books_query.filter(
      db.or_(
        Book.title.ilike(like),
        Book.subtitle.ilike(like),
        Book.description.ilike(like),
      )
    )

  if sort == "created_desc":
    books_query = books_query.order_by(Book.creation_date.desc())
  else:
    books_query = books_query.order_by(Book.last_update_date.desc())

  search_results = books_query.limit(20).all() 

  last_5_mine = (
    Book.query.filter_by(creator_user_id=user_id)
    .order_by(Book.creation_date.desc())
    .limit(5)
    .all()
  )

  last_10_updated = (
    Book.query.order_by(Book.last_update_date.desc())
    .limit(10)
    .all()
  )

  return render_template(
    "home.html",
    q=q,
    scope=scope,
    sort=sort,
    search_results=search_results,
    last_5_mine=last_5_mine,
    last_10_updated=last_10_updated,
  )


@app.route("/my-books")
def my_books():
  if "user_id" not in session:
    return redirect(url_for("login"))
  user_id = session["user_id"]
  books = (
    Book.query.filter_by(creator_user_id=user_id)
    .order_by(Book.creation_date.desc())
    .all()
  )
  return render_template("my_books.html", books=books)


@app.route("/books/<int:book_id>")
def book_detail(book_id):
  if "user_id" not in session:
    return redirect(url_for("login"))

  book = Book.query.get_or_404(book_id)

  page = request.args.get("page", 1, type=int)
  per_page = 10
  pagination = (
    Chapter.query.filter_by(book_id=book.id)
    .order_by(Chapter.id.asc())
    .paginate(page=page, per_page=per_page, error_out=False)
  )
  chapters = pagination.items

  return render_template(
    "book_detail.html",
    book=book,
    chapters=chapters,
    pagination=pagination,
  )

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
