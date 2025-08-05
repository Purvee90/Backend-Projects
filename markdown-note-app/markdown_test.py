import unittest
import json
from models import db, Note, User
from markdown_app import (
    app,
    db,
    create_snippet,
    calculate_note_stats,
    remove_markdown_formatting,
)  # Update this if your filename is different


class MarkdownAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        # print(db.inspect(db.engine).get_table_names())

    # def tearDown(self):
    #     with app.app_context():
    #         db.session.remove()
    #         db.drop_all()

    def test_register_user(self):
        # with app.app_context():
        existing_user = User.query.filter_by(username="testuser").first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()

        response = self.client.post(
            "/register",
            json={
                "username": "testuser1",
                "email": "test1@example.com",
                "password": "securepassword1",
            },
        )
        print(response.status_code)
        print(response.get_json())

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("user_id", data)

    def test_login_user(self):
        self.client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "securepassword",
            },
        )
        response = self.client.post(
            "/login",
            json={"username_or_email": "testuser", "password": "securepassword"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("user_id", data)

    def test_save_note(self):
        response = self.client.post(
            "/save-note",
            json={
                "title": "Test Note",
                "markdown_text": "# Heading\nThis is a test note.",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("note_id", data)

    def test_list_notes(self):
        self.client.post(
            "/save-note",
            json={"title": "Test Note", "markdown_text": "This is a test note."},
        )
        response = self.client.get("/list-notes")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertIn("title", data[0])

    def test_search_notes(self):
        self.client.post(
            "/save-note",
            json={
                "title": "Searchable Note",
                "markdown_text": "This note contains the keyword: flask.",
            },
        )
        response = self.client.get("/search-notes?q=flask")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["query"], "flask")
        self.assertTrue(data["total_results"] > 0)

    def test_create_snippet_found(self):
        text = "This is a long markdown note about Flask and Python development."
        query = "Flask"
        snippet = create_snippet(text, query)
        self.assertIn("Flask", snippet)
        self.assertTrue(len(snippet) <= 150)

    def test_create_snippet_not_found(self):
        text = "This is a long markdown note about Django and web development."
        query = "Flask"
        snippet = create_snippet(text, query)
        self.assertTrue(snippet.startswith("This is a long"))
        self.assertTrue(len(snippet) <= 150)

    def test_remove_markdown_formatting(self):
        markdown_text = """
        # Header
        **Bold Text** and *Italic Text*
        Link
        !Image
        ```python
        print("Hello")
        ```
        - List item
        """
        plain_text = remove_markdown_formatting(markdown_text)
        self.assertNotIn("**", plain_text)
        self.assertNotIn("*", plain_text)
        self.assertNotIn("[", plain_text)
        self.assertNotIn("!", plain_text)
        self.assertNotIn("```", plain_text)
        self.assertNotIn("-", plain_text)
        self.assertIn("Bold Text", plain_text)
        self.assertIn("Italic Text", plain_text)

    def test_calculate_note_stats(self):
        markdown_text = """
        # Title
        This is a **bold* note with a [link.
        - Item 1
        - Item 2
        ```python
        print("Hello")
        ```
        """
        stats = calculate_note_stats(markdown_text)
        self.assertEqual(stats["word_count"], 14)
        self.assertEqual(stats["markdown_elements"]["headers"], 1)
        self.assertEqual(stats["markdown_elements"]["links"], 1)
        self.assertEqual(stats["markdown_elements"]["images"], 0)
        self.assertEqual(stats["markdown_elements"]["code_blocks"], 1)
        self.assertEqual(stats["markdown_elements"]["list_items"], 2)


if __name__ == "__main__":
    unittest.main()
