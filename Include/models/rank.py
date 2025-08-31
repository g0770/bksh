from . import db
from sqlalchemy.sql import func


class Rank(db.Model):
  __tablename__ = "ranks"

  id = db.Column(db.Integer, primary_key=True)
  rank = db.Column(db.String(50), unique=True, nullable=False)

  # Rank -> Users
  users = db.relationship(
    "User",
    back_populates="rank",
    cascade="all, delete",
    passive_deletes=True,
  )

  def __repr__(self):
    return f"<Rank {self.rank}>"


