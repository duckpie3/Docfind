import ast
import re
import warnings
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
    end = (
        headings[next_index]["line_number"] - 1
        if next_index < len(headings)
        else len(content.splitlines())
    )

    return end

def generate_document_url(document_path: Path) -> str:
    base_url = "https://pytorch.org/tutorials"
    relative_path = document_path.relative_to(Path("/tmp/tutorials"))
    # Remove the "_source" suffix from the first directory in the path
    parts = relative_path.parts
    if parts[0].endswith("_source"):
        parts = (parts[0][:-7],) + parts[1:]
        relative_path = Path(*parts)
    url_path = relative_path.with_suffix(".html")
    return f"{base_url}/{url_path}"

def extract_passage(content: str, headings: list[dict], heading_index: int, document_path: Path) -> dict:
    heading = headings[heading_index]
    end_line = find_passage_end(headings, heading_index)

    passage_lines = content.splitlines()[heading["line_number"] + 1 : end_line]
    passage = "\n".join(passage_lines).strip()
    tutorials_root = Path("/tmp/tutorials")
    relative_path = document_path.relative_to(tutorials_root)

    url = generate_document_url(document_path)

    return {
        "document_id": generate_document_id(document_path),
        "source_path": str(relative_path),
        "source_url": url,
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


def clean_inline_rst(text: str) -> str:
    pattern = r":math:`(.*?)`"
    return re.sub(pattern, r"\1", text)


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


def resolve_example_path(reference: str) -> Path:
    tutorials_root = Path("/tmp/tutorials/")
    # Add "_source" to first directory in the path
    parts = Path(reference.lstrip("/")).parts
    source_dir = f"{parts[0]}_source"
    file_path = tutorials_root / source_dir / Path(*parts[1:])
    return file_path


def generate_example_id(reference: str) -> str:
    # Generate a unique example ID based on the reference path
    # Remove leading slash and .py extension

    example_path = reference.removesuffix(".py").removeprefix("/")
    example_id = example_path.replace("/", "_")
    return example_id


def generate_document_id(source_path: Path) -> str:
    # Generate a unique document ID based on the source path
    document_id = source_path.stem
    return document_id


def generate_source_url(reference: str) -> str:
    base_url = "https://pytorch.org/tutorials"

    reference = reference.removeprefix("/")
    reference = reference.removesuffix(".py")

    return f"{base_url}/{reference}.html"


def extract_code_record_from_reference(
    reference: str, document_path: Path, section: str, parent_section: str
) -> dict:
    # Extracts record from includedoc directive reference
    # Example reference: `/beginner/examples_tensor/polynomial_numpy.py`
    record = {
        "source_url": generate_source_url(reference),
        "document_id": generate_document_id(document_path),
        "example_id": generate_example_id(reference),
        "title": "",
        "section": section,
        "parent_section": parent_section,
        "source_path": "",
        "source_type": "python_example",
        "docstring": "",
        "code": "",
    }

    file_path = resolve_example_path(reference)
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        code_example = extract_python_example(content)

    except FileNotFoundError:
        raise FileNotFoundError("Example file not found.")
    parts = Path(reference.lstrip("/")).parts
    source_dir = f"{parts[0]}_source"
    source_path = source_dir / Path(*parts[1:])

    if code_example["docstring"]:
        record["title"] = code_example["docstring"].splitlines()[0].strip()
    record["source_path"] = str(source_path)
    record["docstring"] = code_example["docstring"]
    record["cleaned_docstring"] = clean_documentation(code_example["docstring"])
    record["code"] = code_example["code"]
    record["cleaned_code"] = code_example["code"]

    return record


def extract_code_references(passage_content: str) -> list[str]:
    pattern = r"\.\. includenodoc::\s+(.+)"
    return re.findall(pattern, passage_content)


def extract_code_records_from_passage(
    passage: dict,
    document_path: Path,
) -> list[dict]:
    records = []

    references = extract_code_references(passage["content"])

    for reference in references:
        record = extract_code_record_from_reference(
            reference,
            document_path,
            passage["title"],
            passage["parent_section"],
        )

        records.append(record)

    return records


def extract_all_code_records(
    content: str,
    document_path: Path,
) -> list[dict]:
    headings = extract_headings(content)
    records = []

    for heading_index, heading in enumerate(headings):
        passage = extract_passage(content, headings, heading_index, document_path)

        if not passage["content"].strip():
            continue

        passage_records = extract_code_records_from_passage(
            passage,
            document_path,
        )

        records.extend(passage_records)

    return records


def clean_documentation(content: str) -> str:
    content = remove_directive_blocks(
        content, {"toctree", "galleryitem", "raw", "contents", "includenodoc"}
    )
    content = clean_hyperlinks(content)
    content = remove_hyperlink_definitions(content)
    content = clean_inline_rst(content)
    return content


rst_path = Path("/tmp/tutorials/beginner_source/pytorch_with_examples.rst")
content = rst_path.read_text(encoding="utf-8")
cleaned_content = clean_documentation(content)
headings = extract_headings(cleaned_content)
passages = [extract_passage(cleaned_content, headings, i, rst_path) for i in range(len(headings))]

example_records = extract_all_code_records(content, rst_path)

print("Total passages extracted:", len(passages))
print("Total example records extracted:", len(example_records))
print("=" * 40)
for passage in passages:
    print("Document ID:", passage["document_id"])
    print("Source Path:", passage["source_path"])
    print("Source URL:", passage["source_url"])
    print(f"Title: {passage['title']}")
    print(f"Level: {passage['level']}")
    print(f"Parent Section: {passage['parent_section']}")
    print(f"Line Number: {passage['line_number']}")
    print("Content:")
    print(passage["content"])
    print("-" * 40)

for record in example_records:
    print(f"Source URL: {record['source_url']}")
    print(f"Document ID: {record['document_id']}")
    print(f"Example ID: {record['example_id']}")
    print(f"Title: {record['title']}")
    print(f"Section: {record['section']}")
    print(f"Parent Section: {record['parent_section']}")
    print(f"Source Path: {record['source_path']}")
    print(f"Source Type: {record['source_type']}")
    print("-" * 40)
