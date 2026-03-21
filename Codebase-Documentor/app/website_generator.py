import uuid
from pathlib import Path
import markdown

STATIC_DIR = Path("static")


def create_static_site(content: str) -> str:
    STATIC_DIR.mkdir(exist_ok=True)

    file_id = str(uuid.uuid4())
    file_name = f"site_{file_id}.html"
    file_path = STATIC_DIR / file_name

    html_body = markdown.markdown(content)

    html = f"""
    <html>
    <head>
        <title>Project Documentation</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                max-width: 900px;
                margin: auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            h1,h2,h3 {{
                color: #222;
            }}
            pre {{
                background: #eee;
                padding: 10px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {html_body}
        </div>
    </body>
    </html>
    """

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    return f"http://localhost:8000/static/{file_name}"