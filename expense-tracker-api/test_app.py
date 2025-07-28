import unittest
import json
from app import app, db, User, Expense


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        self.test_user = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpass",
        }
        self.app.post("/signup", json=self.test_user)

        # Login and store token
        login_response = self.app.post(
            "/login",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"],
            },
        )
        login_data = json.loads(login_response.data)
        self.token = login_data.get("token")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_expense_with_token(self):
        response = self.app.post(
            "/add-expense",
            headers={"Authorization": self.token},
            json={
                "description": "Test Expense",
                "amount": 100,
                "category": "Test",
                "date": "2025-07-28",
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_update_expense_with_token(self):
        # First add an expense
        add_response = self.app.post(
            "/add-expense",
            headers={"Authorization": self.token},
            json={
                "description": "Test Expense",
                "amount": 100,
                "category": "Test",
                "date": "2025-07-28",
            },
        )
        expense_id = Expense.query.first().id

        # Update the expense
        update_response = self.app.put(
            f"/update-expense/{expense_id}",
            headers={"Authorization": self.token},
            json={
                "description": "Updated Expense",
                "amount": 150,
                "category": "Updated",
            },
        )
        self.assertEqual(update_response.status_code, 200)

    def test_delete_expense_with_token(self):
        # Add an expense
        self.app.post(
            "/add-expense",
            headers={"Authorization": self.token},
            json={
                "description": "Test Expense",
                "amount": 100,
                "category": "Test",
                "date": "2025-07-28",
            },
        )
        expense_id = Expense.query.first().id

        # Delete the expense
        delete_response = self.app.delete(
            f"/delete-expense/{expense_id}", headers={"Authorization": self.token}
        )
        self.assertEqual(delete_response.status_code, 200)

    def test_signup_with_missing_fields(self):
        response = self.app.post("/signup", json={"username": "user2"})
        self.assertEqual(response.status_code, 400)

    def test_login_with_invalid_credentials(self):
        response = self.app.post(
            "/login", json={"username": "wronguser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
