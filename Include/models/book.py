from . import db  # IMPORTA la instancia ÚNICA
from sqlalchemy.sql import func


class Book(db.Model):
  __tablename__ = "books"

  id = db.Column(db.Integer, primary_key=True)
  creator_user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  title = db.Column(db.String(200), nullable=False)
  subtitle = db.Column(db.String(200))
  description = db.Column(db.Text)
  creation_date = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  last_update_date = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

  # FK relations
  creator = db.relationship("User", back_populates="books")

  # Book -> Chapters
  chapters = db.relationship(
    "Chapter",
    back_populates="book",
    cascade="all, delete-orphan",
    passive_deletes=True,
    order_by="Chapter.id",
  )

  # Book -> Comments
  comments = db.relationship(
    "Comment",
    back_populates="book",
    cascade="all, delete-orphan",
    passive_deletes=True,
    order_by="Comment.id",
  )

  def __repr__(self):
    return f"<Book {self.title}>"