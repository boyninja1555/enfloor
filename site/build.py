import os
import json
import sqlite3

OUT_ROOT = "dist"
WORDS_PER_PAGE = 5


def html_template(words, page_number: int, total_pages: int):
    items_html = ""
    for word in words:
        items_html += f"""
        <div class="word-card">
            <h2>{word[0]} <small>({word[4]})</small></h2>
            <p><strong>Definition:</strong> {word[1]}</p>
            <p><strong>Usage:</strong> {word[2] or "N/A"}</p>
            <p><strong>Root:</strong> {word[3] or "N/A"}</p>
        </div><hr>"""

    nav_html = ""
    if page_number > 1:
        prev_target = "index.html" if page_number == 2 else f"p.{page_number - 1}.html"
        nav_html += f'<a href="{prev_target}">Previous</a> '
    if page_number < total_pages:
        nav_html += f'<a href="p.{page_number + 1}.html">Next</a>'

    return f"""<!doctype html>
    <html lang="en">
    <head>
        <!-- Page Metadata -->
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="description" content="Enfloor lexicon, page {page_number}" />
        <title>Enfloor | Page {page_number}</title>
        <!-- Page Resources -->
    </head>
    <body>
        {items_html}
        <div class="nav">{nav_html}</div>
    </body>
    </html>"""


def search_index(pages: list[list]):
    search_index = []
    for i, page_words in enumerate(pages, 1):
        filename = "index.html" if i == 1 else f"p.{i}.html"
        for word_row in page_words:
            search_index.append(
                {
                    "w": word_row[0],
                    "u": filename,
                }
            )

    with open(f"{OUT_ROOT}/search.json", "w") as f:
        json.dump(search_index, f)


def build():
    conn = sqlite3.connect("enfloor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word, definition, usage, root, type FROM words")
    all_words = cursor.fetchall()

    os.makedirs("dist", exist_ok=True)
    chunk_size = WORDS_PER_PAGE
    pages = [
        all_words[i : i + chunk_size] for i in range(0, len(all_words), chunk_size)
    ]

    search_index(pages)
    for i, page_words in enumerate(pages, 1):
        content = html_template(page_words, i, len(pages))
        filename = "index.html" if i == 1 else f"p.{i}.html"
        with open(f"{OUT_ROOT}/{filename}", "w") as f:
            f.write(content)

    conn.close()


if __name__ == "__main__":
    build()
