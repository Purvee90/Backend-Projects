from datetime import datetime, timedelta
import json
import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt

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


def show_menu():
    print("\n=== Expense Tracker CLI ===")
    print("1. Add expense")
    print("2. View current expenses")
    print("3. Delete expense")
    print("4. View summary of expenses")
    print("5. Export to CSV")
    print("6. Set Budget monthwise")
    print("7. Exit")


def main():
    expense_dict = {}
    budget_dict = {}
    while True:
        show_menu()
        choice = input("Enter your choice: ")

        if choice == "1":
            description = input("Enter expense description: ")
            amount = input("Amount: ")
            category_expense = input("Category: ")
            try:
                amount = float(amount)
                expense_id = len(expense_dict) + 1
                expense_date = (datetime.today() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                )
                expense_month = (datetime.today() - timedelta(days=1)).strftime("%b%y")
                expense = {
                    "id": expense_id,
                    "date": expense_date,
                    "month": expense_month,
                    "description": description,
                    "amount": amount,
                    "category": category_expense,
                }
                expense_dict[expense_id] = expense
                print(f"Expense added successfully with ID {expense_id}.")
                save_expenses(expense_dict)
            except ValueError:
                print("Invalid amount. Please enter a numeric value.")

        elif choice == "2":
            if not expense_dict:
                print("Expense list is empty.")
            else:
                print("Your expense list:")
                for id, expense in expense_dict.items():
                    print(
                        f"ID: {id} | Date: {expense['date']} | Title: {expense['description']} | Amount: ₹{expense['amount']} | Category: {expense['category']}"
                    )

        elif choice == "3":
            if not expense_dict:
                print("No expenses to delete.")
            else:
                try:
                    expense_id = int(
                        input("Enter the ID of the expense you want to delete: ")
                    )
                    if expense_id in expense_dict:
                        del expense_dict[expense_id]
                        print(f"Expense with ID {expense_id} has been removed.")
                        save_expenses(expense_dict)
                    else:
                        print("Expense ID not found.")
                except ValueError:
                    print("Invalid input. Please enter a numeric ID.")

        elif choice == "4":
            month = input(
                "Enter the month to summarize in format (e.g., Jul25). Leave blank to include all: "
            ).strip()
            category_filter = (
                input("Enter category to filter by (leave blank to include all): ")
                .strip()
                .lower()
            )
            # Apply both filters together
            filtered_expenses = {
                id: exp
                for id, exp in expense_dict.items()
                if (
                    not month
                    or datetime.strptime(exp["date"], "%Y-%m-%d")
                    .strftime("%b%y")
                    .lower()
                    == month.lower()
                )
                and (
                    not category_filter
                    or exp.get("category", "").lower() == category_filter
                )
            }
            if not filtered_expenses:
                print("No expenses found for the given filters.")
            else:
                total = sum(exp["amount"] for exp in filtered_expenses.values())
                print(
                    f"\nTotal Expense{' for ' + month if month else ''} in category '{category_filter if category_filter else 'All'}': ₹{total:.2f}"
                )
                # Budget comparison
                if month and month in budget_dict:
                    budget = budget_dict[month]
                    remaining = float(budget) - total
                    print(f"Budget for {month}: ₹{budget:.2f}")
                    print(f"Remaining Budget: ₹{remaining:.2f}")
                    if remaining < 0:
                        print("⚠️ You have exceeded your budget!")
                    elif remaining < budget * 0.2:
                        print("🔔 Warning: You're close to reaching your budget limit.")

                # Budget vs Expense Chart
                budget = budget_dict.get(month, 0)
                plt.figure(figsize=(6, 4))
                plt.bar(
                    ["Budget", "Total Expense"], [budget, total], color=["blue", "red"]
                )
                plt.title(f"Budget vs Expense for {month}")
                plt.ylabel("Amount (₹)")
                plt.tight_layout()
                plt.savefig("budget_vs_expense_chart.png")
                plt.close()

                # Category-wise Chart
                print("\nFiltered Expenses:")
                for id, exp in filtered_expenses.items():
                    print(
                        f"ID: {id}, Date: {exp['date']}, Category: {exp.get('category', 'N/A')}, Amount: ₹{exp['amount']:.2f}, Description: {exp.get('description', '')}"
                    )

        elif choice == "5":
            month = input("Enter month to export (e.g., Jul25): ")
            month_expense = {
                id: exp
                for id, exp in expense_dict.items()
                if datetime.strptime(exp["date"], "%Y-%m-%d").strftime("%b%y") == month
            }
            if not expense_dict:
                print(f"No expenses found for {month}")
            else:
                try:
                    export_expenses_by_month(month)
                except ValueError:
                    print("Invalid input. Please enter a numeric ID")

        elif choice == "6":
            try:
                month = input("Enter Budget month to add (e.g., Jul25): ")
                budget_amount = input(f"Enter Budget for {month} : ")
                budget_dict[month] = budget_amount
                print(f"Budget of ₹{budget_amount:.2f} added for {month}.")
            except ValueError:
                print("Invalid input. Please enter a numeric ID")

        elif choice == "7":
            print("Exiting Expense Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
