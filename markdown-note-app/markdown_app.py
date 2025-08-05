from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Note, User
import markdown
import re
from datetime import datetime
from sqlalchemy import or_
from collections import Counter
from werkzeug.security import check_password_hash
from utils import create_snippet, remove_markdown_formatting
from services.markdown_render import calculate_note_stats
from routes.notes import notes
# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()


app.register_blueprint(notes_bp)

# Health check
@app.route("/")
def home():
    return "Markdown Note-taking App is running!"


# Register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user_id": user.id})


# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username_or_email = data.get("username_or_email")
    password = data.get("password")

    if not username_or_email or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "user_id": user.id})


# # 1. Search notes
# @app.route("/search-notes", methods=["GET"])
# def search_notes():
#     query = request.args.get("q", "").strip()

#     if not query:
#         return jsonify({"error": "Search query is required"})

#     # Search in both title and markdown_text
#     notes = (
#         Note.query.filter(
#             or_(Note.title.contains(query), Note.markdown_text.contains(query))
#         )
#         .order_by(Note.created_at.desc())
#         .all()
#     )

#     # Format results with highlighted snippets
#     results = []
#     for note in notes:
#         # Create snippet with context around the match
#         snippet = create_snippet(note.markdown_text, query)
#         results.append(
#             {
#                 "id": note.id,
#                 "title": note.title,
#                 "snippet": snippet,
#                 "created_at": note.created_at.isoformat(),
#                 "match_in_title": query.lower() in note.title.lower(),
#             }
#         )

#     return jsonify({"query": query, "total_results": len(results), "results": results})


# # 2. Save Note
# @app.route("/save-note", methods=["POST"])
# def save_note():
#     data = request.get_json()
#     title = data.get("title", "Untitled")
#     markdown_text = data.get("markdown_text", "")
#     user_id = data.get("user_id")
#     new_note = Note(title=title, markdown_text=markdown_text, user_id=user_id)
#     db.session.add(new_note)
#     db.session.commit()
#     return jsonify({"message": "Note saved successfully", "note_id": new_note.id})


# # 3. List Notes
# @app.route("/list-notes", methods=["GET"])
# def list_notes():
#     notes = Note.query.order_by(Note.created_at.desc()).all()
#     return jsonify([note.to_dict() for note in notes])


# # 4. Render Note
# @app.route("/render-note/<int:note_id>", methods=["GET"])
# def render_note(note_id):
#     note = Note.query.get(note_id)
#     if not note:
#         return jsonify({"error": "Note not found"}), 404
#     html_content = markdown.markdown(note.markdown_text)
#     return html_content


# # 5. Individual Note Statistics
# @app.route("/note-stats/<int:note_id>", methods=["GET"])
# def note_stats(note_id):
#     note = Note.query.get(note_id)
#     if not note:
#         return jsonify({"error": "Note not found"}), 404

#     stats = calculate_note_stats(note.markdown_text)
#     stats["note_id"] = note_id
#     stats["title"] = note.title
#     stats["created_at"] = note.created_at.isoformat()

#     return jsonify(stats)


# # 6. Dashboard Statistics
# @app.route("/dashboard-stats", methods=["GET"])
# def dashboard_stats():
#     notes = Note.query.all()

#     if not notes:
#         return jsonify(
#             {
#                 "total_notes": 0,
#                 "total_words": 0,
#                 "average_words_per_note": 0,
#                 "most_recent_note": None,
#                 "oldest_note": None,
#             }
#         )

#     total_words = 0
#     all_words = []

#     for note in notes:
#         note_stats = calculate_note_stats(note.markdown_text)
#         total_words += note_stats["word_count"]
#         # Extract words for common words analysis
#         words = re.findall(r"\b\w+\b", note.markdown_text.lower())
#         all_words.extend(words)

#     # Find most common words (excluding common stop words)
#     stop_words = {
#         "the",
#         "a",
#         "an",
#         "and",
#         "or",
#         "but",
#         "in",
#         "on",
#         "at",
#         "to",
#         "for",
#         "of",
#         "with",
#         "by",
#         "is",
#         "are",
#         "was",
#         "were",
#     }
#     filtered_words = [
#         word for word in all_words if word not in stop_words and len(word) > 2
#     ]
#     common_words = Counter(filtered_words).most_common(10)

#     return jsonify(
#         {
#             "total_notes": len(notes),
#             "total_words": total_words,
#             "average_words_per_note": round(total_words / len(notes), 1),
#             "most_recent_note": (
#                 {
#                     "id": notes[0].id,
#                     "title": notes[0].title,
#                     "created_at": notes[0].created_at.isoformat(),
#                 }
#                 if notes
#                 else None
#             ),
#             "common_words": [
#                 {"word": word, "count": count} for word, count in common_words
#             ],
#         }
#     )


# Run the app
if __name__ == "__main__":
    app.run(debug=True)

