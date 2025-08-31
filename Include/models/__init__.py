from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .rank import Rank
from .user import User
from .book import Book
from .chapter import Chapter
from .comment import Comment
