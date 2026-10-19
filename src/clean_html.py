
import re
from pathlib import Path

from bs4 import BeautifulSoup


BLOCK_TAGS = [
    "address",
    "article",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
]

REMOVE_SELECTORS = (
    "script, style, nav, footer, .rating, .bd-sidebar-secondary"
)


def extract_text(html_path: Path) -> str:
    """Extract readable article text while preserving document structure."""
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find(id="main-content")
    if main is None:
        raise ValueError(f"Could not find main-content in {html_path}")

    for element in main.select(REMOVE_SELECTORS):
        element.decompose()

    # Add boundaries around block elements, not inline elements.
    # This prevents words from being split at <code>, <a>, or <span> tags.
    for element in main.find_all(BLOCK_TAGS):
        element.insert_before("\n")
        element.insert_after("\n")

    text = main.get_text(separator="", strip=False)

    # Normalize whitespace within each line while preserving meaningful
    # paragraph, heading, list, and code-line boundaries.
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    # Remove empty lines and collapse consecutive duplicate boundaries.
    cleaned_lines = []
    previous_blank = True

    for line in lines:
        if line:
            cleaned_lines.append(line)
            previous_blank = False
        elif not previous_blank:
            cleaned_lines.append("")
            previous_blank = True

    return "\n".join(cleaned_lines).strip()


def main() -> None:
    raw_dir = Path("data/raw")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    for html_path in raw_dir.glob("*.html"):
        text = extract_text(html_path)
        output_path = output_dir / f"{html_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")

        print(f"{html_path} -> {output_path} ({len(text):,} characters)")


if __name__ == "__main__":
    main()
