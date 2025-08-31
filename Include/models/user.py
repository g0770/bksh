from . import db
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

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
  password = db.Column(db.String(255), nullable=False)
  username = db.Column(db.String(80), unique=True, nullable=False, index=True)

  # FK relations
  rank = db.relationship("Rank", back_populates="users")

  # User (creator) -> Books
  books = db.relationship(
    "Book",
    back_populates="creator",
    cascade="all, delete-orphan",
    passive_deletes=True,
  )

  # User (commentator) -> Comments
  comments = db.relationship(
    "Comment",
    back_populates="commentator",
    cascade="all, delete-orphan",
    passive_deletes=True,
  )

  def __repr__(self):
    return f"<User {self.username}>"
    
  def hashPassword(self , password):
    self.password = generate_password_hash(password)
    
  def comparaPassword(self ,password):
    return check_password_hash(self.password  , password)

