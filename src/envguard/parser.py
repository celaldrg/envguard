"""A strict .env parser that reports problems instead of silently guessing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


@dataclass
class Entry:
    key: str
    value: str
    line: int
    quoted: bool = False


@dataclass
class Problem:
    level: str  # "error" | "warning"
    code: str
    message: str
    file: str
    line: int | None = None
    key: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EnvFile:
    path: str
    entries: list[Entry] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)

    @property
    def keys(self) -> dict[str, Entry]:
        # last definition wins, like most loaders
        return {e.key: e for e in self.entries}


_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$"}


def _unescape(s: str) -> str:
    return re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), "\\" + m.group(1)), s)


def parse(text: str, path: str = ".env") -> EnvFile:
    """Parse dotenv text. Supports `export`, single/double quotes, multi-line double quotes and inline comments."""
    env = EnvFile(path)
    lines = text.splitlines()
    i = 0
    seen: dict[str, int] = {}
    while i < len(lines):
        raw = lines[i]
        lineno = i + 1
        i += 1
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        if "=" not in stripped:
            env.problems.append(Problem("error", "syntax", f"expected KEY=VALUE, got {stripped[:40]!r}", path, lineno))
            continue
        key, rest = stripped.split("=", 1)
        if key != key.rstrip() or rest != rest.lstrip():
            env.problems.append(Problem("warning", "spaces-around-equals", "spaces around '=' are not supported by every loader (e.g. docker --env-file)", path, lineno, key.strip()))
        key = key.strip()
        rest = rest.strip()
        if not KEY_RE.match(key):
            env.problems.append(Problem("error", "invalid-key", f"invalid variable name {key!r}", path, lineno, key))
            continue
        quoted = False
        if rest[:1] in ("'", '"'):
            q = rest[0]
            quoted = True
            body = rest[1:]
            # find closing quote (not escaped for double quotes), possibly across lines
            buf = body
            start_line = lineno
            while True:
                end = _find_close(buf, q)
                if end != -1:
                    value = buf[:end]
                    after = buf[end + 1:].strip()
                    if after and not after.startswith("#"):
                        env.problems.append(Problem("error", "syntax", f"unexpected text after closing quote: {after[:30]!r}", path, start_line, key))
                    break
                if q == "'" or i >= len(lines):
                    env.problems.append(Problem("error", "unterminated-quote", f"value of {key} opens a {q} quote that never closes", path, start_line, key))
                    value = body
                    break
                buf += "\n" + lines[i]
                i += 1
            if q == '"':
                value = _unescape(value)
        else:
            value = re.split(r"\s+#", rest, maxsplit=1)[0].rstrip()
            if re.search(r"\s", value):
                env.problems.append(Problem("warning", "unquoted-whitespace", f"value of {key} contains spaces but is not quoted", path, lineno, key))
        if key in seen:
            env.problems.append(Problem("warning", "duplicate-key", f"{key} is also defined on line {seen[key]}; the last one wins", path, lineno, key))
        seen[key] = lineno
        env.entries.append(Entry(key, value, lineno, quoted))
    return env


def _find_close(s: str, q: str) -> int:
    j = 0
    while j < len(s):
        if q == '"' and s[j] == "\\":
            j += 2
            continue
        if s[j] == q:
            return j
        j += 1
    return -1
