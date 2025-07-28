import jwt
import os
from flask import Flask, request, jsonify, send_file
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from functools import wraps
from models import db, Expense, User, Budget
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from sqlalchemy import or_
from sqlalchemy.orm import aliased
import csv
import io
from io import BytesIO
from flask import Response


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex(32)  # Replace with a secure key

db.init_app(app)


# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return jsonify({"error": f"Token is invalid: {str(e)}"}), 401
        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/", methods=["GET"])
def home():
    return "Hi, Welcome to Expense Tracker!"


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter(
        or_(getattr(User, "username") == username, getattr(User, "email") == email)
    ).first():
        return jsonify({"error": "Username or email already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(
        id=None, username=username, email=email, password_hash=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    username = data.get("username")
    password = data.get("password")

    if not all([username, password]):
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = jwt.encode(
        {"user_id": user.id}, app.config["SECRET_KEY"], algorithm="HS256"
    )
    return jsonify({"message": "Login successful", "token": token}), 200


@app.route("/add-expense", methods=["POST"])
@token_required
def add_expense(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    required_fields = ["description", "amount", "category"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

        try:
            expense_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    else:
        expense_date = date.today()

    expense_month = expense_date.strftime("%b%y")

    expense = Expense(
        expense_date=expense_date,
        month=expense_month,
        description=data["description"],
        amount=float(data["amount"]),
        category=data["category"],
        user_id=current_user.id,
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify({"message": "Expense added successfully"}), 201


@app.route("/update-expense/<int:expense_id>", methods=["PUT"])
@token_required
def update_expense(current_user, expense_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if not expense:
        return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404

    expense.description = data.get("description", expense.description)
    expense.amount = float(data.get("amount", expense.amount))
    expense.category = data.get("category", expense.category)

    db.session.commit()

    return (
        jsonify({"message": f"Expense with ID {expense_id} updated successfully"}),
        200,
    )


@app.route("/delete-expense/<int:expense_id>", methods=["DELETE"])
@token_required
def delete_expense(current_user, expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if not expense:
        return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return (
        jsonify({"message": f"Expense with ID {expense_id} deleted successfully"}),
        200,
    )


@app.route("/expenses", methods=["GET"])
@token_required
def list_expenses(current_user):
    filter_type = request.args.get("filter", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    today = date.today()
    start, end = None, None

    if filter_type == "week":
        start = today - timedelta(days=7)
        end = today
    elif filter_type == "month":
        start = today - timedelta(days=30)
        end = today
    elif filter_type == "3months":
        start = today - timedelta(days=90)
        end = today
    elif filter_type == "custom" and start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # ExpenseModel = aliased(Expense)
    # query = ExpenseModel.query.filter_by(user_id=current_user.id)
    query = Expense.query.filter_by(user_id=current_user.id)
    query = query.filter(Expense.expense_date.between(start, end))  # type: ignore

    if start and end:
        # query = query.filter(ExpenseModel.expense_date.between(start, end))
        query = query.filter(getattr(Expense, "expense_date").between(start, end))
    elif start:
        # query = query.filter(ExpenseModel.expense_date >= start)
        query = query.filter(getattr(Expense, "expense_date") >= start)

    # expenses = query.order_by(ExpenseModel.expense_date.desc()).all()
    expenses = query.order_by(getattr(Expense, "expense_date").desc()).all()
    result = [
        {
            "id": e.id,
            "amount": e.amount,
            "description": e.description,
            "category": e.category,
            "date": e.expense_date.strftime("%Y-%m-%d"),
            "month": e.month,
        }
        for e in expenses
    ]
    return jsonify({"expenses": result})


@app.route("/set-budget", methods=["POST"])
@token_required
def set_budget(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    required_fields = ["amount", "start_date", "end_date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date"}), 400

    month = start_date.strftime("%b%y")
    category = data.get("category")  # Optional

    budget = Budget(
        budget_amount=float(data["amount"]),
        category=category,
        user_id=current_user.id,
        month=month,
        start_date=start_date,
        end_date=end_date,
    )

    db.session.add(budget)
    db.session.commit()

    return jsonify({"message": "Budget set successfully"}), 201


@app.route("/export-expenses", methods=["GET"])
@token_required
def export_expenses(current_user):
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "Missing 'month' query parameter"}), 400

    expenses = Expense.query.filter_by(user_id=current_user.id, month=month).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Amount", "Description", "Category", "Date", "Month"])

    for e in expenses:
        writer.writerow(
            [
                e.id,
                e.amount,
                e.description,
                e.category,
                e.expense_date.strftime("%Y-%m-%d"),
                e.month,
            ]
        )

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=expenses_{month}.csv"},
    )


@app.route("/budget-vs-expense-chart", methods=["GET"])
@token_required
def budget_vs_expense_chart(current_user):
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "Missing 'month' query parameter"}), 400

    total_budget = (
        db.session.query(db.func.sum(getattr(Budget, "budget_amount")))
        .filter_by(user_id=current_user.id, month=month)
        .scalar()
        or 0
    )

    total_expense = (
        db.session.query(db.func.sum(getattr(Expense, "amount")))
        .filter_by(user_id=current_user.id, month=month)
        .scalar()
        or 0
    )

    fig, ax = plt.subplots()
    ax.bar(["Budget", "Expense"], [total_budget, total_expense], color=["green", "red"])
    ax.set_title(f"Budget vs Expense for {month}")
    ax.set_ylabel("Amount")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    return send_file(
        img,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"budget_vs_expense_{month}.png",
    )


@app.route("/category-expense-chart", methods=["GET"])
@token_required
def category_expense_chart(current_user):
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "Missing 'month' query parameter"}), 400

    category_totals = (
        db.session.query(
            getattr(Expense, "category"), db.func.sum(getattr(Expense, "amount"))
        )
        .filter_by(user_id=current_user.id, month=month)
        .group_by(getattr(Expense, "category"))
        .all()
    )

    categories = [c[0] for c in category_totals]
    amounts = [c[1] for c in category_totals]

    fig, ax = plt.subplots()
    ax.bar(categories, amounts, color="skyblue")
    ax.set_title(f"Category-wise Expenses for {month}")
    ax.set_ylabel("Amount")
    ax.set_xlabel("Category")
    plt.xticks(rotation=45)

    img = BytesIO()
    plt.tight_layout()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    return send_file(
        img,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"category_expense_{month}.png",
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
