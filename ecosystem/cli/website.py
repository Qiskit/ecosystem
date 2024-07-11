"""CliWebsite class for controlling all CLI functions."""

from __future__ import annotations

import re
from pathlib import Path

NEW_URL = "https://ibm.com"


def build_website(output: str) -> None:
    """
    Generates a HTML redirect to the new ecosystem web page.
    """
    html = f"""
    <!DOCTYPE HTML>
    <html lang="en-US">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="0; url={NEW_URL}">
            <script type="text/javascript">
                window.location.href = "{NEW_URL}"
            </script>
            <title>Qiskit ecosystem</title>
        </head>
        <body>
            If you are not redirected automatically, go to <a href="{NEW_URL}">{NEW_URL}</a>.
        </body>
    </html>
    """
    html = re.sub(r"\n\s*", "", html)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html)
