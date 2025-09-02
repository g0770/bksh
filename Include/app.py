import os
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, func
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, Rank, User, Book, Chapter, Comment

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".md"}

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_ECHO"] = False # para debug
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 mb

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db.init_app(app)

#--------------------
#Funciones utilizadas

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def require_login():
    if "user_id" not in session:
        return False
    return True
  
#--------------------
#Login
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
      session["user_id"] = user.id
      session["user_username"] = user.username
      flash("Login exitoso", "success")
      return redirect(url_for("home"))
    else:
      flash("Usuario o contraseña incorrectos", "danger")

  return render_template("login.html")

#Register
@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if User.query.filter((User.username == username) | (User.email == email)).first():
      flash("Usuario o email ya registrados", "danger")
    else:
      new_user = User(username=username, email=email, rank_id=1) #rank_id 1 = rank "User"
      new_user.password = password #esta en otra linea para q se combine con secret key y se hashee
      db.session.add(new_user)
      db.session.commit()
      flash("Cuenta creada con éxito, ahora podés iniciar sesión", "success")
      return redirect(url_for("login"))

  return render_template("register.html")

#Logout
@app.route("/logout")
def logout():
  session.clear()
  flash("Sesión cerrada correctamente", "info")
  return redirect(url_for("login"))

#--------------------
#Home
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

#Libros del usuario logeado
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

#Pagina principal de un libro
@app.route("/books/<int:book_id>", methods=["GET", "POST"])
def book_detail(book_id):
  if "user_id" not in session:
    return redirect(url_for("login"))

  book = Book.query.get_or_404(book_id)

  if request.method == "POST":
    action = request.form.get("action")

    # para volver a la misma página de capítulos después de la acción
    current_page = request.args.get("page", 1, type=int)

    if action == "create_comment":
      content = request.form.get("content", "").strip()
      if not content:
        flash("El comentario no puede estar vacío", "danger")
        return redirect(url_for("book_detail", book_id=book.id, page=current_page))

      cm = Comment(
        commentator_user_id=session["user_id"],
        book_id=book.id,
        content=content,
      )
      db.session.add(cm)
      # book.last_update_date = func.now()
      db.session.commit()
      flash("Comentario publicado", "success")
      return redirect(url_for("book_detail", book_id=book.id, page=current_page))

    elif action == "edit_comment":
      comment_id = request.form.get("comment_id", type=int)
      content = request.form.get("content", "").strip()
      cm = Comment.query.get_or_404(comment_id)

      if cm.commentator_user_id != session["user_id"]:
        abort(403)
      if not content:
        flash("El comentario no puede quedar vacío", "danger")
        return redirect(url_for("book_detail", book_id=book.id, page=current_page))

      cm.content = content
      db.session.commit()
      flash("Comentario actualizado", "success")
      return redirect(url_for("book_detail", book_id=book.id, page=current_page))

    elif action == "delete_comment":
      comment_id = request.form.get("comment_id", type=int)
      cm = Comment.query.get_or_404(comment_id)

      if cm.commentator_user_id != session["user_id"]:
          abort(403)

      db.session.delete(cm)
      db.session.commit()
      flash("Comentario eliminado", "info")
      return redirect(url_for("book_detail", book_id=book.id, page=current_page))

    else:
      flash("Acción no válida", "danger")
      return redirect(url_for("book_detail", book_id=book.id, page=current_page))

  page = request.args.get("page", 1, type=int)
  per_page = 10
  pagination = (
    Chapter.query.filter_by(book_id=book.id)
    .order_by(Chapter.id.asc())
    .paginate(page=page, per_page=per_page, error_out=False)
  )
  chapters = pagination.items

  comments = (
    Comment.query.filter_by(book_id=book.id)
    .order_by(Comment.creation_date.desc())
    .all()
  )

  return render_template(
    "book_detail.html",
    book=book,
    chapters=chapters,
    pagination=pagination,
    comments=comments,
  )

#Edicion de libro
@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
  if "user_id" not in session:
    return redirect(url_for("login"))
  book = Book.query.get_or_404(book_id)
  if book.creator_user_id != session["user_id"]:
    abort(403)

  if request.method == "POST":
    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip() or None
    description = request.form.get("description", "").strip() or None

    if not title:
      flash("El título es obligatorio", "danger")
      return redirect(url_for("edit_book", book_id=book.id))

    book.title = title
    book.subtitle = subtitle
    book.description = description
    book.last_update_date = func.now()
    db.session.commit()
    flash("Libro actualizado", "success")
    return redirect(url_for("book_detail", book_id=book.id))

  return render_template("edit_book.html", book=book)

#Borrar libro
@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
  if "user_id" not in session:
    return redirect(url_for("login"))
  book = Book.query.get_or_404(book_id)
  if book.creator_user_id != session["user_id"]:
    abort(403)

  for ch in Chapter.query.filter_by(book_id=book.id).all():
    # content_url -> /uploads/<filename>
    filename = None
    if ch.content_url:
      # maneja URL generada por url_for (path local)
      try:
        # puede venir como /uploads/abc.pdf o http://host/uploads/abc.pdf
        path = urlparse(ch.content_url).path
        if path.startswith("/uploads/"):
            filename = path.split("/uploads/", 1)[1]
      except Exception:
        filename = None

    if filename:
      fpath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      try:
        if os.path.exists(fpath):
          os.remove(fpath)
      except Exception:
        pass

  db.session.delete(book)  # comments y chapters caen por cascade
  db.session.commit()
  flash("Libro eliminado (incluyendo capítulos y archivos).", "info")
  return redirect(url_for("my_books"))


#Busqueda avanzada
@app.route("/search")
def search():
  if "user_id" not in session:
    return redirect(url_for("login"))

  q = request.args.get("q", "", type=str).strip()
  sort = request.args.get("sort", "updated_desc")
  page = request.args.get("page", 1, type=int)
  per_page = 18

  base = db.session.query(
    Book,
    func.count(Chapter.id).label("chapters_count")
  ).outerjoin(Chapter, Chapter.book_id == Book.id)

  if q:
    like = f"%{q}%"
    base = base.filter(
      db.or_(
        Book.title.ilike(like),
        Book.subtitle.ilike(like),
        Book.description.ilike(like),
      )
    )
    
  base = base.group_by(Book.id)

  if sort == "creator_az":
    base = base.join(User, User.id == Book.creator_user_id).order_by(User.username.asc())
  elif sort == "created_desc":
    base = base.order_by(Book.creation_date.desc())
  elif sort == "chapters_desc":
    base = base.order_by(func.count(Chapter.id).desc(), Book.title.asc())
  else:  # "updated_desc" default
    base = base.order_by(Book.last_update_date.desc())

  pagination = base.paginate(page=page, per_page=per_page, error_out=False)
  results = pagination.items

  return render_template(
    "advanced_search.html",
    q=q,
    sort=sort,
    results=results,
    pagination=pagination,
  )

#archivos
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
  if "user_id" not in session:
    return redirect(url_for("login"))
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

#Crear libro
@app.route("/books/new", methods=["GET", "POST"])
def new_book():
  if "user_id" not in session:
    return redirect(url_for("login"))

  if request.method == "POST":
    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip() or None
    description = request.form.get("description", "").strip() or None

    if not title:
      flash("El título es obligatorio", "danger")
      return redirect(url_for("new_book"))

    b = Book(
      title=title,
      subtitle=subtitle,
      description=description,
      creator_user_id=session["user_id"],
    )
    db.session.add(b)
    db.session.commit()
    flash("Libro creado", "success")
    return redirect(url_for("book_detail", book_id=b.id))

  return render_template("new_book.html")

#Crear capitulo nuevo de un libro
@app.route("/books/<int:book_id>/chapters/new", methods=["GET", "POST"])
def new_chapter(book_id):
  if "user_id" not in session:
    return redirect(url_for("login"))

  book = Book.query.get_or_404(book_id)
  # solo el dueño puede agregar capítulos
  if book.creator_user_id != session["user_id"]:
    abort(403)

  if request.method == "POST":
    title = request.form.get("title", "").strip()
    file = request.files.get("file")

    if not title:
      flash("El título del capítulo es obligatorio", "danger")
      return redirect(url_for("new_chapter", book_id=book.id))

    if not file or file.filename == "":
      flash("Subí un archivo .pdf o .md", "danger")
      return redirect(url_for("new_chapter", book_id=book.id))

    if not allowed_file(file.filename):
      flash("Formato inválido. Solo .pdf o .md", "danger")
      return redirect(url_for("new_chapter", book_id=book.id))

    filename = secure_filename(file.filename)
    final_name = f"{book.id}_{session['user_id']}_{filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
    file.save(save_path)

    content_url = url_for("uploaded_file", filename=final_name)

    c = Chapter(book_id=book.id, title=title, content_url=content_url)
    db.session.add(c)
    
    book.last_update_date = func.now()
    db.session.commit()

    flash("Capítulo agregado", "success")
    return redirect(url_for("book_detail", book_id=book.id))

  return render_template("new_chapter.html", book=book)

#Pagina principal de un capitulo (lector de capitulo)
@app.route("/chapters/<int:chapter_id>")
def chapter_reader(chapter_id):
  if "user_id" not in session:
    return redirect(url_for("login"))

  chapter = Chapter.query.get_or_404(chapter_id)
  # content_url es /uploads/<filename>
  try:
    filename = chapter.content_url.split("/uploads/", 1)[1]
  except Exception:
    abort(404)

  _, ext = os.path.splitext(filename.lower())
  is_md = ext == ".md"
  is_pdf = ext == ".pdf"
  
  md_html = None
  if is_md:
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
      abort(404)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
      text = f.read()
    try:
      import markdown as md
      md_html = md.markdown(text, output_format="html5", extensions=["extra", "tables", "fenced_code"])
    except Exception:
      md_html = f"<pre class='text'>{text}</pre>"

  return render_template(
    "chapter_reader.html",
    chapter=chapter,
    filename=filename,
    is_md=is_md,
    is_pdf=is_pdf,
    md_html=md_html,
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
