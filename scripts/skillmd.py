"""Parse SKILL.md frontmatter, including YAML block scalars.

The importers used to split each frontmatter line on its first colon, which turns
    description: >
      Multi-line text...
into the literal description ">". This parser understands folded (>) and literal (|)
block scalars, quoted scalars, and plain scalars. It deliberately covers only the
frontmatter shapes SKILL.md files use; it is not a YAML parser.
"""
import re

_KEY = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
QUOTES = "\"'"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Return (frontmatter fields, body). Fields are strings; missing frontmatter gives {}."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end < 0:
        return {}, content
    fm_text = content[3:end]
    body = content[end + 4:].lstrip("\n")
    fields: dict[str, str] = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        match = _KEY.match(lines[i])
        if not match:
            i += 1
            continue
        key, rest = match.group(1), match.group(2).strip()
        # Some aggregators re-serialise the indicator as a quoted string ('">"') and leave
        # the block below it; treat that exactly like the bare indicator.
        if rest and rest.strip(QUOTES) in (">", ">-", "|", "|-"):
            rest = rest.strip(QUOTES)
        if rest in (">", ">-", "|", "|-"):
            block: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or lines[i].strip() == ""):
                block.append(lines[i].strip())
                i += 1
            joined = "\n".join(block).strip() if rest.startswith("|") else " ".join(b for b in block if b).strip()
            fields[key] = joined
            continue
        if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in "\"'":
            rest = rest[1:-1].replace('\\"', '"')
        fields[key] = rest
        i += 1
    return fields, body.strip()
