from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta
import sqlite3
import os
import csv
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)


# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to expenses.db in the same directory
DB_FILE = os.path.join(BASE_DIR, "expenses.db")
# DB_FILE = "expenses.db"


# Ensure the database and tables exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            month TEXT,
            description TEXT,
            amount REAL,
            category TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            month TEXT PRIMARY KEY,
            amount REAL
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET"])
def home():
    return "Hi, Welcome to Expense Tracker!"


@app.route("/add-expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    required_fields = ["description", "amount", "category"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    expense_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    expense_month = (datetime.today() - timedelta(days=1)).strftime("%b%y")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO expenses (date, month, description, amount, category)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            expense_date,
            expense_month,
            data["description"],
            float(data["amount"]),
            data["category"],
        ),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()

    expense = {
        "id": expense_id,
        "date": expense_date,
        "month": expense_month,
        "description": data["description"],
        "amount": float(data["amount"]),
        "category": data["category"],
    }

    return jsonify({"message": "Expense added successfully", "expense": expense})


@app.route("/set-budget", methods=["POST"])
def set_budget():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    required_fields = ["month", "amount"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    month = data["month"]
    amount = float(data["amount"])

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO budgets (month, amount)
        VALUES (?, ?)
        ON CONFLICT(month) DO UPDATE SET amount=excluded.amount
    """,
        (month, amount),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Budget of ₹{amount:.2f} set for {month}."})


@app.route("/summary/<month>", methods=["GET"])
def summary(month):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, amount, category FROM expenses WHERE month = ?", (month,)
    )
    expenses = cursor.fetchall()
    cursor.execute("SELECT amount FROM budgets WHERE month = ?", (month,))
    budget_row = cursor.fetchone()
    conn.close()

    total = sum(exp[1] for exp in expenses)
    budget = float(budget_row[0]) if budget_row else 0.0
    remaining = budget - total

    # Budget vs Expense Chart
    plt.figure(figsize=(6, 4))
    plt.bar(["Budget", "Total Expense"], [budget, total], color=["blue", "red"])
    plt.title(f"Budget vs Expense for {month}")
    plt.ylabel("Amount (₹)")
    plt.tight_layout()
    buf1 = io.BytesIO()
    plt.savefig(buf1, format="png")
    plt.close()
    buf1.seek(0)
    budget_chart_base64 = base64.b64encode(buf1.read()).decode("utf-8")

    # Category-wise Chart
    category_totals = {}
    for exp in expenses:
        category = exp[2] if exp[2] else "Uncategorized"
        category_totals[category] = category_totals.get(category, 0) + exp[1]

    plt.figure(figsize=(6, 4))
    plt.bar(list(category_totals.keys()), list(category_totals.values()), color="green")
    plt.title(f"Category-wise Expenses for {month}")
    plt.ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png")
    plt.close()
    buf2.seek(0)
    category_chart_base64 = base64.b64encode(buf2.read()).decode("utf-8")

    return jsonify(
        {
            "month": month,
            "total_expense": total,
            "budget": budget,
            "remaining": remaining,
            "budget_chart_base64": budget_chart_base64,
            "category_chart_base64": category_chart_base64,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
