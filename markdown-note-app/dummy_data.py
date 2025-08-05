from markdown_app import app, db, User, Note
from datetime import datetime
import random


def create_dummy_users():
    users = [
        {"username": "alice", "email": "alice@example.com", "password": "alicepass"},
        {"username": "bob", "email": "bob@example.com", "password": "bobpass"},
        {
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "charliepass",
        },
        {"username": "diana", "email": "diana@example.com", "password": "dianapass"},
        {"username": "edward", "email": "edward@example.com", "password": "edwardpass"},
    ]
    for u in users:
        if not User.query.filter_by(username=u["username"]).first():
            user = User(username=u["username"], email=u["email"])
            user.set_password(u["password"])
            db.session.add(user)
    db.session.commit()


def create_dummy_notes():
    users = User.query.all()
    markdown_samples = [
        "# Introduction\nThis is a sample note with a header.",
        "**Bold Text** and *Italic Text* in markdown.",
        "Link to Flask",
        "![Image",
        "```python\nprint('Hello, world!')\n```",
        "- Item 1\n- Item 2\n- Item 3",
        "# Heading\nSome text with `inline code`.",
        "Markdown is **awesome** for writing notes.",
        "Use `re.findall()` to extract patterns.",
        "## Subheading\nMore structured content.",
    ]

    for i in range(20):
        user = users[i % len(users)]  # Distribute notes among users
        content = "\n".join(random.sample(markdown_samples, k=3))
        note = Note(title=f"Note {i+1}", markdown_text=content, user_id=user.id)
        db.session.add(note)
    db.session.commit()


with app.app_context():
    db.drop_all()
    db.create_all()
    create_dummy_users()
    create_dummy_notes()
    print("✅ 5 users and 20 notes created successfully.")
