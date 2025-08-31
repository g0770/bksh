from . import db
from sqlalchemy.sql import func


class Comment(db.Model):
  __tablename__ = "comments"

  id = db.Column(db.Integer, primary_key=True)
  commentator_user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  book_id = db.Column(
    db.Integer,
    db.ForeignKey("books.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  content = db.Column(db.Text, nullable=False)
  creation_date = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  last_update_date = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

  # FK relations
  commentator = db.relationship("User", back_populates="comments")
  book = db.relationship("Book", back_populates="comments")