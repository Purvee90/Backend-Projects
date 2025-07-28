from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from models import db, User, Budget, Expense
from app import app

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses_tracker.db"

with app.app_context():
    # Clear existing tables
    db.drop_all()
    db.create_all()

    categories = [
        "Groceries",
        "Leisure",
        "Electronics",
        "Utilities",
        "Clothing",
        "Health",
        "Others",
    ]

    # Create 5 users
    users = []
    for i in range(1, 6):
        user = User(
            id=None,
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=generate_password_hash(f"password{i}"),
        )
        db.session.add(user)
        users.append(user)
    db.session.commit()

    # Add 10 budgets and 10 expenses per user
    for user in users:
        for j in range(10):
            entry_date = date(2025, 7, 1) + timedelta(days=j * 30)
            month_str = entry_date.strftime("%b%y")
            category = categories[j % len(categories)]

            budget = Budget(
                budget_amount=1000 + j * 50,
                category=category,
                user_id=user.id,
                month=month_str,
                start_date=entry_date,
                end_date=entry_date + timedelta(days=29),
            )
            db.session.add(budget)

            expense = Expense(
                amount=100 + j * 20,
                description=f"{category} expense {j+1}",
                category=category,
                expense_date=entry_date + timedelta(days=5),
                user_id=user.id,
                month=month_str,
            )
            db.session.add(expense)

    db.session.commit()

print(
    "✅ Database reset and seeded with 5 users, each having 10 budgets and 10 expenses."
)
