from flask import Blueprint, request, jsonify, render_template
from models import db, Note
import markdown
from services.markdown_render import calculate_note_stats
from utils import create_snippet
from sqlalchemy import or_
from collections import Counter
import re

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/search-notes", methods=["GET"])
def search_notes():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Search query is required"})
    notes = (
        Note.query.filter(
            or_(Note.title.contains(query), Note.markdown_text.contains(query))
        )
        .order_by(Note.created_at.desc())
        .all()
    )
    results = []
    for note in notes:
        snippet = create_snippet(note.markdown_text, query)
        results.append(
            {
                "id": note.id,
                "title": note.title,
                "snippet": snippet,
                "created_at": note.created_at.isoformat(),
                "match_in_title": query.lower() in note.title.lower(),
            }
        )
    return jsonify({"query": query, "total_results": len(results), "results": results})


@notes_bp.route("/save-note", methods=["POST"])
def save_note():
    data = request.get_json()
    title = data.get("title", "Untitled")
    markdown_text = data.get("markdown_text", "")
    user_id = data.get("user_id")
    new_note = Note(title=title, markdown_text=markdown_text, user_id=user_id)
    db.session.add(new_note)
    db.session.commit()
    return jsonify({"message": "Note saved successfully", "note_id": new_note.id})


@notes_bp.route("/list-notes", methods=["GET"])
def list_notes():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])


@notes_bp.route("/render-note/<int:note_id>", methods=["GET"])
def render_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    html_content = markdown.markdown(note.markdown_text)
    return render_template("rendered_note.html", content=html_content, title=note.title)


@notes_bp.route("/note-stats/<int:note_id>", methods=["GET"])
def note_stats(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    stats = calculate_note_stats(note.markdown_text)
    stats["note_id"] = note_id
    stats["title"] = note.title
    stats["created_at"] = note.created_at.isoformat()
    return jsonify(stats)


@notes_bp.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    notes = Note.query.all()
    if not notes:
        return jsonify(
            {
                "total_notes": 0,
                "total_words": 0,
                "average_words_per_note": 0,
                "most_recent_note": None,
                "oldest_note": None,
            }
        )
    total_words = 0
    all_words = []
    for note in notes:
        note_stats = calculate_note_stats(note.markdown_text)
        total_words += note_stats["word_count"]
        words = re.findall(r"\b\w+\b", note.markdown_text.lower())
        all_words.extend(words)
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
    }
    filtered_words = [
        word for word in all_words if word not in stop_words and len(word) > 2
    ]
    common_words = Counter(filtered_words).most_common(10)
    return jsonify(
        {
            "total_notes": len(notes),
            "total_words": total_words,
            "average_words_per_note": round(total_words / len(notes), 1),
            "most_recent_note": (
                {
                    "id": notes[0].id,
                    "title": notes[0].title,
                    "created_at": notes[0].created_at.isoformat(),
                }
                if notes
                else None
            ),
            "common_words": [
                {"word": word, "count": count} for word, count in common_words
            ],
        }
    )
