"""Compare a .env file against its .env.example and find mistakes."""

from __future__ import annotations

from .parser import EnvFile, Problem
from .secrets import looks_secret


def check(env: EnvFile | None, example: EnvFile | None, *, secrets_in_example: bool = True) -> list[Problem]:
    problems: list[Problem] = []
    for f in (example, env):
        if f is not None:
            problems.extend(f.problems)

    if env is not None and example is not None:
        have = env.keys
        want = example.keys
        for key, entry in want.items():
            if key not in have:
                problems.append(Problem("error", "missing-key", f"{key} is in {example.path} but missing from {env.path}", env.path, None, key))
            elif have[key].value == "" and entry.value != "":
                problems.append(Problem("warning", "empty-value", f"{key} is empty in {env.path} (example has a value)", env.path, have[key].line, key))
        for key, entry in have.items():
            if key not in want:
                problems.append(Problem("warning", "undocumented-key", f"{key} is set in {env.path} but not documented in {example.path}", env.path, entry.line, key))

    if example is not None and secrets_in_example:
        for e in example.entries:
            reason = looks_secret(e.value)
            if reason:
                problems.append(Problem("error", "secret-in-example", f"{e.key} in {example.path} looks like a real credential ({reason}); example files are usually committed", example.path, e.line, e.key))

    order = {"error": 0, "warning": 1}
    problems.sort(key=lambda p: (order[p.level], p.file, p.line or 0))
    return problems
