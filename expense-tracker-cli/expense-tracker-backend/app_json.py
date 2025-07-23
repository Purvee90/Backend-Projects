from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta
import json
import os
import csv
import matplotlib.pyplot as plt

app = Flask(__name__)
EXPENSE_FILE = "Expense Sheet.json"
budget_dict = {}


def load_expense():
    if not os.path.exists(EXPENSE_FILE):
        return []
    with open(EXPENSE_FILE, "r") as file:
        return json.load(file)


def save_expenses(expenses):
    with open(EXPENSE_FILE, "w") as file:
        json.dump(expenses, file, indent=2)


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

    expenses = load_expense()
    expense_id = len(expenses) + 1
    expense_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    expense_month = (datetime.today() - timedelta(days=1)).strftime("%b%y")

    expense = {
        "id": expense_id,
        "date": expense_date,
        "month": expense_month,
        "description": data["description"],
        "amount": float(data["amount"]),
        "category": data["category"],
    }

    expenses.append(expense)
    save_expenses(expenses)
    return jsonify({"message": "Expense added successfully", "expense": expense})


@app.route("/delete-expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expenses = load_expense()
    updated_expenses = [exp for exp in expenses if exp["id"] != expense_id]
    if len(updated_expenses) == len(expenses):
        return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404
    save_expenses(updated_expenses)
    return jsonify({"message": f"Expense with ID {expense_id} deleted successfully"})


@app.route("/update-expense/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    expenses = load_expense()
    for exp in expenses:
        if exp["id"] == expense_id:
            exp["description"] = data.get("description", exp["description"])
            exp["amount"] = float(data.get("amount", exp["amount"]))
            exp["category"] = data.get("category", exp["category"])
            save_expenses(expenses)
            return jsonify(
                {
                    "message": f"Expense with ID {expense_id} updated successfully",
                    "expense": exp,
                }
            )
    return jsonify({"error": f"Expense with ID {expense_id} not found"}), 404


@app.route("/set-budget", methods=["POST"])
def set_budget():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    required_fields = ["month", "amount"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    month = data["month"]
    amount = float(data["amount"])
    budget_dict[month] = amount
    return jsonify({"message": f"Budget of ₹{amount:.2f} set for {month}."})


@app.route("/summary/<month>", methods=["GET"])
def summary(month):
    expenses = load_expense()
    filtered = [
        exp
        for exp in expenses
        if datetime.strptime(exp["date"], "%Y-%m-%d").strftime("%b%y") == month
    ]
    total = sum(exp["amount"] for exp in filtered)
    budget = float(budget_dict.get(month, 0))
    remaining = budget - total

    # Budget vs Expense Chart
    plt.figure(figsize=(6, 4))
    plt.bar(["Budget", "Total Expense"], [budget, total], color=["blue", "red"])
    plt.title(f"Budget vs Expense for {month}")
    plt.ylabel("Amount (₹)")
    plt.tight_layout()
    budget_chart_path = f"budget_vs_expense_{month}.png"
    plt.savefig(budget_chart_path)
    plt.close()

    # Category-wise Chart
    category_totals = {}
    for exp in filtered:
        category = exp.get("category", "Uncategorized")
        category_totals[category] = category_totals.get(category, 0) + exp["amount"]

    plt.figure(figsize=(6, 4))
    plt.bar(list(category_totals.keys()), list(category_totals.values()), color="green")
    plt.title(f"Category-wise Expenses for {month}")
    plt.ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    category_chart_path = f"category_wise_expense_{month}.png"
    plt.savefig(category_chart_path)
    plt.close()

    return jsonify(
        {
            "month": month,
            "total_expense": total,
            "budget": budget,
            "remaining": remaining,
            "budget_chart": budget_chart_path,
            "category_chart": category_chart_path,
        }
    )


@app.route("/export/<month>", methods=["GET"])
def export_csv(month):
    expenses = load_expense()
    filtered = [
        exp
        for exp in expenses
        if datetime.strptime(exp["date"], "%Y-%m-%d").strftime("%b%y") == month
    ]
    if not filtered:
        return jsonify({"message": f"No expenses found for {month}."}), 404

    # filename = f"expenses_{month}.csv"
    filename = os.path.join(os.getcwd(), f"expenses_{month}.csv")
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Amount", "Category"])
        for exp in filtered:
            writer.writerow(
                [exp["date"], exp["description"], exp["amount"], exp["category"]]
            )

    return send_file(filename, as_attachment=True)
    # The line `# return send_file(filename, as_attachment=True, mimetype="text/csv")` in the Flask
    # route `/export/<month>` is responsible for sending the CSV file as an attachment in the HTTP
    # response.
    # return send_file(filename, as_attachment=True, mimetype="text/csv")


if __name__ == "__main__":
    app.run(debug=True)
