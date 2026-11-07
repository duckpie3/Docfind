from pathlib import Path


def is_heading_underline(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if set(line) not in ({"="}, {"~"}, {"-"}):
        return False

    return len(line) >= 3


def get_heading_level(title: str, underline: str) -> str | None:
    if not title.strip():
        return None

    if not is_heading_underline(underline):
        return None

    underline_char = underline.strip()[0]

    if underline_char == "=":
        return "title"
    elif underline_char == "~":
        return "section"
    elif underline_char == "-":
        return "subsection"

    return None


def extract_headings(content: str) -> list[dict]:
    lines = content.splitlines()
    headings = []
    current_section = None

    for i in range(len(lines) - 1):
        title = lines[i].strip()
        underline = lines[i + 1]

        level = get_heading_level(title, underline)

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


def get_level_number(level: str) -> int:
    levels = {
        "title": 0,
        "section": 1,
        "subsection": 2,
    }

    return levels[level]


def find_passage_end(headings: list[dict], current_index: int) -> int:
    next_index = current_index + 1
    end = headings[next_index]["line_number"] - 1 if next_index < len(headings) else len(content.splitlines())

    return end


def extract_passage(content: str, headings: list[dict], heading_index: int) -> dict:
    heading = headings[heading_index]
    end_line = find_passage_end(headings, heading_index)

    passage_lines = content.splitlines()[heading["line_number"] + 1 : end_line]
    passage = "\n".join(passage_lines).strip()

    return {
        "title": heading["title"],
        "level": heading["level"],
        "parent_section": heading["parent_section"],
        "line_number": heading["line_number"],
        "content": passage,
    }

rst_path = Path("/home/david/tutorials/beginner_source/pytorch_with_examples.rst")

content = rst_path.read_text(encoding="utf-8")
headings = extract_headings(content)

passages = [extract_passage(content, headings, i) for i in range(len(headings))]

for passage in passages:
    print(f"Title: {passage['title']}, Level: {passage['level']}, length: {len(passage['content'])} characters")