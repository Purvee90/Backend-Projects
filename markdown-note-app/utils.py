import re

# Helper function to create search snippets


def create_snippet(text, query, max_length=150):
    """Create a snippet showing context around the search term"""
    query_lower = query.lower()
    text_lower = text.lower()

    # Find the first occurrence of the query
    index = text_lower.find(query_lower)

    if index == -1:
        # If not found, return beginning of text
        return text[:max_length] + ("..." if len(text) > max_length else "")

    # Calculate snippet start and end
    start = max(0, index - 50)
    end = min(len(text), index + len(query) + 50)

    snippet = text[start:end]

    # Add ellipsis if needed
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


def remove_markdown_formatting(text):
    """Remove markdown formatting to get plain text"""
    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    # Remove bold and italic
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", text)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove list markers
    text = re.sub(r"^\s*[-\*\+]\s+", "", text, flags=re.MULTILINE)

    return text.strip()
