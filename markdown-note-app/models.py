from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    markdown_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    # Future enhancement for user authentication
    # user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("notes", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "markdown_text": self.markdown_text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "username": self.user.username,
        }

    def __repr__(self):
        return f"<Note {self.id} - {self.title}>"

    # def __init__(self, id, title, markdown_text):
    #     self.id = id
    #     self.title = title
    #     self.markdown_text = markdown_text


class User(db.Model):
    __tablename__ = "users"

    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

    # def __init__(self, id, username, email, password_hash):
    #     self.id = id
    #     self.username = username
    #     self.email = email
    #     self.password_hash = password_hash
