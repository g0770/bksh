from . import db
from sqlalchemy.sql import func


class Chapter(db.Model):
  __tablename__ = "chapters"

  id = db.Column(db.Integer, primary_key=True)
  book_id = db.Column(
    db.Integer,
    db.ForeignKey("books.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  title = db.Column(db.String(200), nullable=False)
  content_url = db.Column(db.String(500), nullable=False)

  # FK relation
  book = db.relationship("Book", back_populates="chapters")

  def __repr__(self):
    return f"<Chapter {self.title} of Book#{self.book_id}>"