import sqlalchemy
from sqlalchemy import Enum
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"  # Optional: custom table name

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationship: One user can have many expenses
    expenses = db.relationship("Expense", backref="expense_user", lazy=True)
    budgets = db.relationship("Budget", backref="budget_user", lazy=True)
    # backref='user': Allows access to the user from the expense side.
    # lazy=True: Loads related data only when accessed.

    # Method to set password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=False)
    # category = db.Column(db.String(50), nullable=False)

    category = db.Column(
        Enum(
            "Groceries",
            "Leisure",
            "Electronics",
            "Utilities",
            "Clothing",
            "Health",
            "Others",
            name="expense_category",
        ),
        nullable=False,
    )

    expense_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    month = db.Column(db.String(10), nullable=False)
    # created_at = db.Column(db.DateTime, default=datetime.now)
    # updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    # notes = db.Column(db.String(255))
    # is_deleted = db.Column(db.Boolean, default=False)

    # user = db.relationship("User", backref="expense_user")
    # In both Expense and Budget models, you're defining a relationship to User again, even though it's already defined in the User model using db.relationship.
    # This causes SQLAlchemy to get confused and not register the models properly, which is why db.create_all() doesn't create the tables.

    def __init__(self, amount, description, category, expense_date, user_id, month):
        self.amount = amount
        self.description = description
        self.category = category
        self.expense_date = expense_date
        self.user_id = user_id
        self.month = month
        # self.created_at = created_at
        # self.updated_at = updated_at
        # self.notes = notes
        # self.is_deleted = is_delted


class Budget(db.Model):
    __tablename__ = "budget"

    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(10), nullable=False)
    budget_amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def __init__(self, budget_amount, category, user_id, month, start_date, end_date):
        self.budget_amount = budget_amount
        self.category = category
        self.user_id = user_id
        self.month = month
        self.start_date = start_date
        self.end_date = end_date

    # Relationship to User
    # user = db.relationship("User", backref="budget_user")
