"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .check import check
from .parser import EnvFile, parse

EXAMPLE_NAMES = (".env.example", ".env.sample", ".env.template", ".env.dist", "example.env")


def _load(path: str | None) -> EnvFile | None:
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return parse(f.read(), path)


def _find_example(env_path: str) -> str | None:
    folder = os.path.dirname(env_path) or "."
    for name in EXAMPLE_NAMES:
        p = os.path.join(folder, name)
        if os.path.exists(p):
            return p if folder != "." else name
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="envguard", description="Catch .env mistakes: missing keys, typos, broken quotes and real secrets in .env.example.")
    ap.add_argument("--env", default=".env", help="the env file to check (default: .env)")
    ap.add_argument("--example", help="the documented template (default: auto-detect .env.example, .env.sample, ...)")
    ap.add_argument("--example-only", action="store_true", help="only lint the example file (useful in CI where .env does not exist)")
    ap.add_argument("--format", choices=("text", "json", "github"), default="text", help="output format; 'github' prints workflow annotations")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    ap.add_argument("--version", action="version", version=f"envguard {__version__}")
    args = ap.parse_args(argv)

    try:
        example_path = args.example or _find_example(args.env)
        if args.example_only:
            if not example_path:
                print("envguard: no example file found", file=sys.stderr)
                return 2
            env = None
        else:
            if not os.path.exists(args.env):
                print(f"envguard: {args.env} not found (use --example-only to lint just the example)", file=sys.stderr)
                return 2
            env = _load(args.env)
        example = _load(example_path)
    except OSError as e:
        print(f"envguard: {e}", file=sys.stderr)
        return 2

    problems = check(env, example)
    errors = sum(p.level == "error" for p in problems)
    warnings = len(problems) - errors

    if args.format == "json":
        print(json.dumps({"env": env.path if env else None, "example": example.path if example else None, "errors": errors, "warnings": warnings, "problems": [p.as_dict() for p in problems]}, indent=2))
    elif args.format == "github":
        for p in problems:
            loc = f"file={p.file}" + (f",line={p.line}" if p.line else "")
            print(f"::{p.level} {loc},title=envguard {p.code}::{p.message}")
    else:
        checked = " and ".join(x for x in (env.path if env else None, example.path if example else None) if x)
        for p in problems:
            loc = f"{p.file}:{p.line}" if p.line else p.file
            print(f"{p.level:<7} {loc:<22} {p.code:<20} {p.message}")
        if problems:
            print()
        status = "ok" if not problems else f"{errors} error{'s' if errors != 1 else ''}, {warnings} warning{'s' if warnings != 1 else ''}"
        note = "" if example else " (no example file found; only syntax was checked)"
        print(f"envguard: {checked}: {status}{note}")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
