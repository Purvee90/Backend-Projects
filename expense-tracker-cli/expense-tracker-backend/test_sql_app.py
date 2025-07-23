import unittest
import json
import sqlite3
import os
from datetime import datetime
from app_sql import app, DB_FILE


class ExpenseTrackerSQLTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        # self.clear_expenses_table()

    # def clear_expenses_table(self):
    #     conn = sqlite3.connect(DB_FILE)
    #     cursor = conn.cursor()
    #     cursor.execute("DELETE FROM expenses")
    #     cursor.execute("DELETE FROM budgets")
    #     conn.commit()
    #     conn.close()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hi, Welcome to Expense Tracker!", response.data)

    def test_add_expense(self):
        data = {"description": "Lunch", "amount": 150, "category": "Food"}
        response = self.client.post("/add-expense", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expense added successfully", response.data)

    def test_update_expense(self):
        response = self.client.post(
            "/add-expense",
            json={"description": "Snacks", "amount": 100, "category": "Food"},
        )
        expense_id = json.loads(response.data)["expense"]["id"]

        update_data = {
            "description": "Evening Snacks",
            "amount": 120,
            "category": "Food",
        }
        response = self.client.put(f"/update-expense/{expense_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"updated successfully", response.data)

    def test_delete_expense(self):
        response = self.client.post(
            "/add-expense",
            json={"description": "Coffee", "amount": 50, "category": "Beverage"},
        )
        expense_id = json.loads(response.data)["expense"]["id"]

        response = self.client.delete(f"/delete-expense/{expense_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"deleted successfully", response.data)

    def test_set_budget(self):
        month = datetime.today().strftime("%b%y")
        data = {"month": month, "amount": 5000}
        response = self.client.post("/set-budget", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Budget of", response.data)

    def test_summary(self):
        month = datetime.today().strftime("%b%y")
        self.client.post(
            "/add-expense",
            json={"description": "Groceries", "amount": 300, "category": "Shopping"},
        )
        self.client.post("/set-budget", json={"month": month, "amount": 1000})
        response = self.client.get(f"/summary/{month}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"total_expense", response.data)


if __name__ == "__main__":
    unittest.main()
