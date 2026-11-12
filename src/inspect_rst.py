from pathlib import Path
import re
import ast, warnings


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
    end = (
        headings[next_index]["line_number"] - 1
        if next_index < len(headings)
        else len(content.splitlines())
    )

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


def clean_hyperlinks(text: str) -> str:
    pattern = r"`([^`]+?)\s<https?://[^>]+>`__?"

    return re.sub(pattern, r"\1", text)


def get_indentation(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_indented_block_line(line: str, base_indent: int) -> bool:
    return get_indentation(line) > base_indent or line.strip() == ""


def remove_directive_blocks(content: str, directive_names: set[str]) -> str:
    lines = content.splitlines()
    new_lines = []
    skip_block = False
    base_indent = 0

    for line in lines:
        if line.strip().startswith(tuple(f".. {name}::" for name in directive_names)):
            skip_block = True
            base_indent = get_indentation(line)
            continue

        if skip_block:
            if is_indented_block_line(line, base_indent):
                continue
            else:
                skip_block = False

        new_lines.append(line)

    return "\n".join(new_lines)


def remove_hyperlink_definitions(content: str) -> str:
    pattern = r"^\s*\.\. _[^:]+:(?:\s*https?://[^\s]+)?$"
    return re.sub(pattern, "", content, flags=re.MULTILINE)


def extract_python_docstring(source: str) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            module = ast.parse(source)
        docstring = ast.get_docstring(module)
        return docstring if docstring is not None else ""
    except SyntaxError:
        return ""


def extract_python_code(source: str) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            module = ast.parse(source)
        if module.body:
            first_node = module.body[0]
            # Check if the first node is a docstring
            if isinstance(first_node, ast.Expr) and isinstance(
                first_node.value, ast.Constant
            ):
                # Remove the docstring from the source code
                docstring = ast.get_docstring(module)
                if docstring is not None:
                    # Split the source code into lines
                    source_lines = source.splitlines()
                    # Remove the lines corresponding to the docstring
                    code_lines = (
                        source_lines[: first_node.lineno - 1]
                        + source_lines[first_node.end_lineno :]
                    )
                    return "\n".join(code_lines).strip()
        return source.strip()
    except SyntaxError:
        return ""


def extract_python_example(source: str) -> dict:
    docstring = extract_python_docstring(source)
    code = extract_python_code(source)
    return {"docstring": docstring, "code": code}


def clean_documentation(content: str) -> str:
    content = remove_directive_blocks(
        content, {"toctree", "galleryitem", "raw", "contents"}
    )
    content = clean_hyperlinks(content)
    content = remove_hyperlink_definitions(content)
    return content


rst_path = Path(
    "/home/david/tutorials/beginner_source/examples_tensor/polynomial_numpy.py"
)

content = rst_path.read_text(encoding="utf-8")
# content = clean_documentation(content)
example = extract_python_example(content)
print(f"Docstring:\n{example['docstring']}\n\nCode:\n{example['code']}\n\n")
# headings = extract_headings(content)

# passages = [extract_passage(content, headings, i) for i in range(len(headings))]

# for passage in passages:
#     print(
#         f"Title: {passage['title']}\n Level: {passage['level']}\n length: {len(passage['content'])} characters\n Preview: {passage['content'][:100]}...\n\n"
#     )
