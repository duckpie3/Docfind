import os
from pathlib import Path

from clean_documentation import clean_documentation


class Document:
    def __init__(self, path: str):
        self.path = Path(path)
        tutorials_root = Path(
            os.environ.get("DOCUMENTATION_DOWNLOAD_DIR", "/tmp/tutorials")
        )
        self.source_path = self.path.relative_to(tutorials_root)
        self.document_id = str(self.source_path.with_suffix("")).replace("/", "_")
        self.source_url = self._generate_document_url()
        self.content = self.path.read_text(encoding="utf-8")
        self.cleaned_content = clean_documentation(self.content)
        self.headings = self._extract_headings()

    def _generate_document_url(self) -> str:
        base_url = "https://pytorch.org/tutorials"
        # Remove the "_source" suffix from the first directory in the path
        parts = self.source_path.parts
        if parts[0].endswith("_source"):
            parts = (parts[0][:-7],) + parts[1:]
        relative_path = Path(*parts)
        url_path = relative_path.with_suffix(".html")
        return f"{base_url}/{url_path}"

    def _is_heading_underline(self, line: str) -> bool:
        line = line.strip()

        if not line:
            return False

        if set(line) not in ({"="}, {"~"}, {"-"}):
            return False

        return len(line) >= 3

    def _get_heading_level(self, title: str, underline: str) -> str | None:
        if not title.strip():
            return None

        if not self._is_heading_underline(underline):
            return None

        underline_char = underline.strip()[0]

        if underline_char == "=":
            return "title"
        elif underline_char == "~":
            return "section"
        elif underline_char == "-":
            return "subsection"

        return None

    def _extract_headings(self) -> list[dict]:
        lines = self.content.splitlines()
        headings = []
        current_section = None

        for i in range(len(lines) - 1):
            title = lines[i].strip()
            underline = lines[i + 1]

            level = self._get_heading_level(title, underline)

            if level is None:
                continue

            if level == "section":
                current_section = title

            headings.append(
                {
                    "title": title,
                    "level": level,
                    "parent_section": current_section,
                    "line_number": i + 1,
                }
            )

        return headings

    def __str__(self) -> str:
        return (
            "Document(\n"
            f"  path={self.path},\n"
            f"  document_id={self.document_id},\n"
            f"  source_path={self.source_path},\n"
            f"  source_url={self.source_url}\n"
            ")"
        )


document = Document("/tmp/tutorials/beginner_source/pytorch_with_examples.rst")
print(document)
