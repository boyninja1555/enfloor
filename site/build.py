from collections import defaultdict
import os
import json
import sqlite3

OUT_ROOT = "dist"
WORDS_PER_PAGE = 5


def generate_nav(current, total):
    if total <= 1:
        return ""

    links = []
    if current > 1:
        target = "index.html" if current == 2 else f"p.{current - 1}.html"
        links.append(f'<a href="{target}">« Previous</a>')
    if current < total:
        links.append(f'<a href="p.{current + 1}.html">Next »</a>')

    return f'<nav class="pagination">{" | ".join(links)}</nav>'


def html_template(words, page_number: int, total_pages: int, word_to_url: str):
    items_html = ""
    for w_name, w_def, w_usage, w_root, w_type in words:
        root_display = w_root or "N/A"
        if w_root and w_root.lower() in word_to_url:
            root_display = f'<a href="{word_to_url[w_root.lower()]}">{w_root}</a>'

        items_html += f"""
        <article class="word-card">
            <header>
                <h2>{w_name} <kbd>{w_type}</kbd></h2>
            </header>
            <section>
                <p><strong>Definition:</strong> {w_def}</p>
                <p><strong>Usage:</strong> <em>{w_usage or "N/A"}</em></p>
                <footer><strong>Root:</strong> {root_display}</footer>
            </section>
        </article><hr>"""

    return f"""<!doctype html>
    <html lang="en">
    <head>
        <!-- Page Metadata -->
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="description" content="Enfloor lexicon, page {page_number}" />
        <title>Enfloor | Page {page_number}</title>
        <!-- Page Resources -->
        <style>
            body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
            .word-card {{ margin-bottom: 2rem; }}
            kbd {{ background: #eee; padding: 2px 4px; border-radius: 3px; font-size: 0.8em; }}
            .search-container {{ margin-bottom: 2rem; position: relative; }}
            #results {{ position: absolute; background: white; border: 1px solid #ccc; width: 100%; z-index: 10; display: none; }}
            .result-item {{ padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; }}
            .result-item:hover {{ background: #f0f0f0; }}
        </style>
    </head>
    <body>
        <header>
            <h1>Enfloor Lexicon</h1>
            <div class="search-container">
                <input type="text" id="search-input" placeholder="Search words..." style="width:100%; padding:10px;">
                <div id="results"></div>
            </div>
        </header>
        <main>{items_html}</main>

        {generate_nav(page_number, total_pages)}

        <script>
            const input = document.getElementById('search-input')
            const resDiv = document.getElementById('results')
            let shard = null, lastChar = ""
            input.onkeyup = async () => {{
                const q = input.value.toLowerCase()
                if (q.length < 1) {{ resDiv.style.display = 'none'; return }}
                const char = q[0]
                if (char !== lastChar) {{
                    try {{
                        const r = await fetch(`search/${{char}}.json`)
                        shard = r.ok ? await r.json() : {{}}
                        lastChar = char
                    }} catch {{ shard = {{}} }}
                }}
                const matches = Object.keys(shard).filter(w => w.startsWith(q)).slice(0, 5)
                resDiv.innerHTML = matches.map(w => `<div class="result-item" onclick="location.href='${{shard[w]}}'">${{w}}</div>`).join('')
                resDiv.style.display = matches.length ? 'block' : 'none'
            }}
        </script>
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
    cursor.execute(
        "SELECT word, definition, usage, root, type FROM words ORDER BY word ASC"
    )
    all_words = cursor.fetchall()
    conn.close()
    os.makedirs(f"{OUT_ROOT}/search", exist_ok=True)

    word_to_url = {{}}  # type: ignore
    pages = [
        all_words[i : i + WORDS_PER_PAGE]
        for i in range(0, len(all_words), WORDS_PER_PAGE)
    ]

    for i, chunk in enumerate(pages, 1):
        url = "index.html" if i == 1 else f"p.{i}.html"
        for row in chunk:
            word_to_url[row[0].lower()] = url  # type: ignore

    shards = defaultdict(dict)
    for word, url in word_to_url.items():  # type: ignore
        first_char = word[0] if word else "_"
        shards[first_char][word] = url

    for char, data in shards.items():
        with open(f"{OUT_ROOT}/search/{char}.json", "w") as f:
            json.dump(data, f)

    total = len(pages)
    for i, chunk in enumerate(pages, 1):
        filename = "index.html" if i == 1 else f"p.{i}.html"
        content = html_template(chunk, i, total, word_to_url)  # type: ignore
        with open(f"{OUT_ROOT}/{filename}", "w") as f:
            f.write(content)


if __name__ == "__main__":
    build()
