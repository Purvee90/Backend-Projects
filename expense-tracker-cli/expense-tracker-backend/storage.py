import json
import os
import csv
from datetime import datetime

EXPENSE_FILE = "Expense Sheet.json"


def load_expense():
    """Load expenses from the JSON file."""
    if not os.path.exists(EXPENSE_FILE):
        return []
    with open(EXPENSE_FILE, "r") as file:
        return json.load(file)


def save_expenses(expense):
    """Save expenses to the JSON file."""
    with open(EXPENSE_FILE, "w") as file:
        json.dump(expense, file, indent=2)


def export_expenses_by_month(month_input):
    """Export expenses for a given month to a CSV file."""
    all_expenses = load_expense()
    filtered_expenses = [
        exp
        for exp in all_expenses
        if datetime.strptime(exp["date"], "%Y-%m-%d").strftime("%b%y") == month_input
    ]

    if not filtered_expenses:
        print(f"No expenses found for {month_input}.")
        return

    filename = f"expenses_{month_input}.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Amount"])
        for exp in filtered_expenses:
            writer.writerow([exp["date"], exp["description"], exp["amount"]])
    print(f"Expenses for {month_input} exported to {filename}.")

    return filename
