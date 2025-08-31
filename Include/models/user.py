from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

class User(db.Model):
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  rank_id = db.Column(
    db.Integer,
    db.ForeignKey("ranks.id", ondelete="RESTRICT"),
    nullable=False,
    index=True,
  )
  email = db.Column(db.String(255), unique=True, nullable=False, index=True)
  username = db.Column(db.String(80), unique=True, nullable=False, index=True)

  _password_hash = db.Column("password", db.String(255), nullable=False)

  rank = db.relationship("Rank", back_populates="users")
  books = db.relationship("Book", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True)
  comments = db.relationship("Comment", back_populates="commentator", cascade="all, delete-orphan", passive_deletes=True)

  def __repr__(self):
    return f"<User {self.username}>"

  @property
  def password(self):
    raise AttributeError("password is write-only")

  @password.setter
  def password(self, plain_text: str):
    if not plain_text:
      raise ValueError("Password no puede ser vacío")
    peppered = plain_text + current_app.config["SECRET_KEY"]
    self._password_hash = generate_password_hash(
      peppered, method="pbkdf2:sha256", salt_length=16
    )

  def check_password(self, plain_text: str) -> bool:
    peppered = plain_text + current_app.config["SECRET_KEY"]

    if check_password_hash(self._password_hash, peppered):
      return True

    if check_password_hash(self._password_hash, plain_text):
      self._password_hash = generate_password_hash(
        peppered, method="pbkdf2:sha256", salt_length=16
      )
      try:
        db.session.commit()
      except Exception:
        db.session.rollback()
      return True
      
    return False
