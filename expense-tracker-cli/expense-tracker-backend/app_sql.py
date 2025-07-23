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


# To allow users to optionally provide a custom date when adding an expense, here's the corrected and complete version of your add_expense() function:
@app.route("/add-expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    required_fields = ["description", "amount", "category"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Use provided date or default to yesterday
    if "date" in data and data["date"]:
        try:
            expense_date = datetime.strptime(data["date"], "%Y-%m-%d").strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    else:
        # expense_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d") Set to yesterday date
        expense_date = datetime.today().strftime("%Y-%m-%d")  # Set to current date

    expense_month = datetime.strptime(expense_date, "%Y-%m-%d").strftime("%b%y")

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


@app.route("/delete-expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()

    if rows_deleted == 0:
        return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404
    return jsonify({"message": f"Expense with ID {expense_id} deleted successfully"})


@app.route("/update-expense/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch existing expense
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404

    # Prepare updated values
    updated_description = data.get("description", existing[3])
    updated_amount = float(data.get("amount", existing[4]))
    updated_category = data.get("category", existing[5])

    cursor.execute(
        """
        UPDATE expenses
        SET description = ?, amount = ?, category = ?
        WHERE id = ?
        """,
        (updated_description, updated_amount, updated_category, expense_id),
    )
    conn.commit()
    conn.close()

    updated_expense = {
        "id": expense_id,
        "date": existing[1],
        "month": existing[2],
        "description": updated_description,
        "amount": updated_amount,
        "category": updated_category,
    }

    return jsonify(
        {
            "message": f"Expense with ID {expense_id} updated successfully",
            "expense": updated_expense,
        }
    )


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
    # Generate warning if budget exceeded
    warning = ""
    if total > budget:
        warning = f"⚠️ Warning: Total expenses ₹{total:.2f} exceed the budget ₹{budget:.2f} for {month}."

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
            "warning": warning,
            "budget_chart_base64": budget_chart_base64,
            "category_chart_base64": category_chart_base64,
        }
    )


@app.route("/view-expenses/<month>", methods=["GET"])
def view_expenses(month):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, description, amount, category FROM expenses WHERE month = ? ORDER BY date",
        (month,),
    )
    rows = cursor.fetchall()
    conn.close()

    expenses = [
        {
            "id": row[0],
            "date": row[1],
            "description": row[2],
            "amount": row[3],
            "category": row[4],
        }
        for row in rows
    ]

    return jsonify({"month": month, "expenses": expenses})


if __name__ == "__main__":
    app.run(debug=True)
