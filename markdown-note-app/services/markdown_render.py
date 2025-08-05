# markdown_render.py

import re
from utils import remove_markdown_formatting


def calculate_note_stats(markdown_text):
    """Calculate various statistics for a markdown note"""
    plain_text = remove_markdown_formatting(markdown_text)
    words = plain_text.split()
    word_count = len(words)
    char_count = len(plain_text)
    char_count_no_spaces = len(plain_text.replace(" ", ""))
    reading_time = max(1, round(word_count / 200))

    headers = len(re.findall(r"^#+\s", markdown_text, re.MULTILINE))
    links = len(re.findall(r"\[.*?\]\(.*?\)", markdown_text))
    images = len(re.findall(r"!\[.*?\]\(.*?\)", markdown_text))
    code_blocks = len(re.findall(r"```", markdown_text)) // 2
    lists = len(re.findall(r"^\s*[-\*\+]\s", markdown_text, re.MULTILINE))

    return {
        "word_count": word_count,
        "character_count": char_count,
        "character_count_no_spaces": char_count_no_spaces,
        "reading_time_minutes": reading_time,
        "markdown_elements": {
            "headers": headers,
            "links": links,
            "images": images,
            "code_blocks": code_blocks,
            "list_items": lists,
        },
    }
