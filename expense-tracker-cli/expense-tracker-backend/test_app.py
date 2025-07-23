import unittest
import json
from app_json import app, save_expenses
from datetime import datetime, timedelta


class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        save_expenses([])  # Clear existing data before each test

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hi, Welcome to Expense Tracker!", response.data)

    def test_add_expense(self):
        data = {"description": "Lunch", "amount": 150, "category": "Food"}
        response = self.client.post("/add-expense", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expense added successfully", response.data)

    def test_delete_expense(self):
        self.client.post(
            "/add-expense",
            json={"description": "Coffee", "amount": 50, "category": "Beverage"},
        )
        response = self.client.delete("/delete-expense/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"deleted successfully", response.data)

    def test_update_expense(self):
        self.client.post(
            "/add-expense",
            json={"description": "Snacks", "amount": 100, "category": "Food"},
        )
        update_data = {
            "description": "Evening Snacks",
            "amount": 120,
            "category": "Food",
        }
        response = self.client.put("/update-expense/1", json=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"updated successfully", response.data)

    def test_set_budget(self):
        data = {"month": "Jul25", "amount": 5000}
        response = self.client.post("/set-budget", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Budget of", response.data)

    def test_summary(self):
        month = (datetime.today() - timedelta(days=1)).strftime("%b%y")
        self.client.post(
            "/add-expense",
            json={"description": "Groceries", "amount": 300, "category": "Shopping"},
        )
        self.client.post("/set-budget", json={"month": month, "amount": 1000})
        response = self.client.get(f"/summary/{month}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"total_expense", response.data)

    def test_export_csv(self):
        month = (datetime.today() - timedelta(days=1)).strftime("%b%y")
        self.client.post(
            "/add-expense",
            json={"description": "Transport", "amount": 200, "category": "Travel"},
        )
        response = self.client.get(f"/export/{month}")
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.mimetype, "text/csv") because .csv files are often associated with Excel on Windows systems, and Flask/send_file uses OS-level MIME type detection
        self.assertIn(response.mimetype, ["text/csv", "application/vnd.ms-excel"])


if __name__ == "__main__":
    unittest.main()
