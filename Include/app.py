from flask import Flask
from sqlalchemy import inspect
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, Rank, User, Book, Chapter, Comment

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_ECHO"] = False

db.init_app(app)

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
