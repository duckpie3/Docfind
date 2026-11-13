import ast
import os
import re
import warnings
from pathlib import Path
import pprint
from clean_documentation import clean_documentation
from document import Document

TUTORIALS_ROOT = Path(os.environ.get("DOCUMENTATION_DOWNLOAD_DIR", "/tmp/tutorials"))


def extract_passage(document: Document, heading_index: int) -> dict:

    def find_passage_end() -> int:
        next_index = heading_index + 1
        end = (
            document.headings[next_index]["line_number"] - 1
            if next_index < len(document.headings)
            else len(document.content.splitlines())
        )
        return end

    heading = document.headings[heading_index]
    end_line = find_passage_end()

    passage_lines = document.content.splitlines()[heading["line_number"] + 1 : end_line]
    passage = "\n".join(passage_lines).strip()

    return {
        "document_id": document.document_id,
        "source_path": str(document.source_path),
        "source_url": document.source_url,
        "title": heading["title"],
        "level": heading["level"],
        "parent_section": heading["parent_section"],
        "line_number": heading["line_number"],
        "content": passage,
    }


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
    # Add "_source" to first directory in the path
    parts = Path(reference.lstrip("/")).parts
    source_dir = f"{parts[0]}_source"
    file_path = TUTORIALS_ROOT / source_dir / Path(*parts[1:])
    return file_path


def generate_example_id(reference: str) -> str:
    # Generate a unique example ID based on the reference path
    # Remove leading slash and .py extension

    example_path = reference.removesuffix(".py").removeprefix("/")
    example_id = example_path.replace("/", "_")
    return example_id


def generate_source_url(reference: str) -> str:
    base_url = "https://pytorch.org/tutorials"

    reference = reference.removeprefix("/")
    reference = reference.removesuffix(".py")

    return f"{base_url}/{reference}.html"


def extract_code_record_from_reference(
    reference: str, document_id: str, section: str, parent_section: str
) -> dict:
    # Extracts record from includedoc directive reference
    # Example reference: `/beginner/examples_tensor/polynomial_numpy.py`
    record = {
        "source_url": generate_source_url(reference),
        "document_id": document_id,
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

    except FileNotFoundError as error:
        raise FileNotFoundError(f"Example file not found: {file_path}") from error
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


def extract_code_records_from_passage(passage: dict) -> list[dict]:
    records = []

    references = extract_code_references(passage["content"])

    for reference in references:
        record = extract_code_record_from_reference(
            reference,
            passage["document_id"],
            passage["title"],
            passage["parent_section"],
        )

        records.append(record)

    return records


def extract_all_code_records(document: Document) -> list[dict]:
    records = []

    for heading_index in range(len(document.headings)):
        passage = extract_passage(document, heading_index)

        if not passage["content"].strip():
            continue

        passage_records = extract_code_records_from_passage(passage)

        records.extend(passage_records)

    return records


rst_path = TUTORIALS_ROOT / "beginner_source/pytorch_with_examples.rst"
document = Document(str(rst_path))
passages = [extract_passage(document, i) for i in range(len(document.headings))]

example_records = extract_all_code_records(document)

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
