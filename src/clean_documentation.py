import re


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


def clean_documentation(content: str) -> str:
    content = remove_directive_blocks(
        content, {"toctree", "galleryitem", "raw", "contents"}
    )
    content = clean_hyperlinks(content)
    content = remove_hyperlink_definitions(content)
    content = clean_inline_rst(content)
    return content
