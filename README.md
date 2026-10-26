# envguard

**Catch `.env` mistakes before they ship.** envguard compares your `.env` with `.env.example` and finds missing keys, broken quotes, duplicates, values that different loaders read differently, and real credentials accidentally committed to the example file.

[![CI](https://github.com/celaldrg/envguard/actions/workflows/ci.yml/badge.svg)](https://github.com/celaldrg/envguard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

Pure Python standard library, no dependencies. Works locally, in pre-commit and in CI (with GitHub annotations).

## Example

Given this `.env.example`:

```dotenv
# App
APP_URL=http://localhost:3000
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=your-stripe-key
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
SENTRY_DSN=
```

and this `.env`:

```dotenv
APP_URL=http://localhost:3000
DATABASE_URL = postgres://app:app@localhost:5432/app
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY='sk_test_123
SENTRY_DSN=
SENTRY_DSN=https://abc@o1.ingest.sentry.io/1
FEATURE_FLAGS=new-ui beta-api
```

running `envguard` prints (real output):

```text
error   .env                   missing-key          AWS_ACCESS_KEY_ID is in .env.example but missing from .env
error   .env:4                 unterminated-quote   value of STRIPE_SECRET_KEY opens a ' quote that never closes
error   .env.example:6         secret-in-example    AWS_ACCESS_KEY_ID in .env.example looks like a real credential (AWS access key); example files are usually committed
warning .env:2                 spaces-around-equals spaces around '=' are not supported by every loader (e.g. docker --env-file)
warning .env:6                 duplicate-key        SENTRY_DSN is also defined on line 5; the last one wins
warning .env:7                 unquoted-whitespace  value of FEATURE_FLAGS contains spaces but is not quoted
warning .env:7                 undocumented-key     FEATURE_FLAGS is set in .env but not documented in .env.example

envguard: .env and .env.example: 3 errors, 4 warnings
```

(`AKIAIOSFODNN7EXAMPLE` is AWS's documentation sample key; envguard flags anything with the shape of a real AWS key.) The exit code is 1 when there are errors, so it fails CI.

In GitHub Actions, `--format github` turns problems into inline annotations:

```text
::error file=.env.example,line=6,title=envguard secret-in-example::AWS_ACCESS_KEY_ID in .env.example looks like a real credential (AWS access key); example files are usually committed
```

## Install

Not on PyPI yet. Install from GitHub:

```bash
pipx install git+https://github.com/celaldrg/envguard
# or
pip install git+https://github.com/celaldrg/envguard
```

## Usage

```bash
envguard                         # check .env against .env.example (auto-detected)
envguard --env .env.production --example .env.example
envguard --example-only          # lint only the example (CI, where .env does not exist)
envguard --format json           # machine-readable
envguard --format github         # GitHub Actions annotations
envguard --strict                # fail on warnings too
```

The example file is found automatically: `.env.example`, `.env.sample`, `.env.template`, `.env.dist` or `example.env`.

Exit codes: `0` clean, `1` errors (or warnings with `--strict`), `2` usage error / file not found.

### pre-commit

```yaml
repos:
  - repo: https://github.com/celaldrg/envguard
    rev: v0.1.0
    hooks:
      - id: envguard
```

### GitHub Actions

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- run: pip install git+https://github.com/celaldrg/envguard@v0.1.0
- run: envguard --example-only --format github
```

## What it checks

| Code | Level | What |
|---|---|---|
| `missing-key` | error | A key documented in the example is not set in `.env` |
| `secret-in-example` | error | A value in the (committed) example looks like a real credential: AWS, GitHub, Slack, Stripe live, OpenAI-style and Google keys, private keys, JWTs, passwords in URLs, high-entropy strings |
| `unterminated-quote` | error | A quote is opened and never closed |
| `syntax` | error | Not `KEY=VALUE`, or text after a closing quote |
| `invalid-key` | error | Name is not a valid variable name (e.g. `MY-KEY`, `1KEY`) |
| `undocumented-key` | warning | Set in `.env` but missing from the example, so teammates won't know about it |
| `empty-value` | warning | Empty in `.env` while the example has a value |
| `duplicate-key` | warning | Defined twice; the last one wins |
| `spaces-around-equals` | warning | `KEY = value` works in some loaders but not in `docker --env-file` |
| `unquoted-whitespace` | warning | `KEY=a b` without quotes is read differently by different tools |

Placeholders such as `changeme`, `your-api-key`, `<key>`, `${VAR}`, `xxxx` and default local URLs like `postgres://postgres:postgres@localhost` are not reported as secrets.

The parser supports `export KEY=...`, single and double quotes, multi-line double-quoted values, escape sequences (`\n`, `\t`, `\"`) and inline `#` comments.

## Why

`.env` problems are cheap to make and expensive to find: a key added by one developer and never documented, a missing quote that silently swallows the next line, a real API key pasted into `.env.example` and pushed. Secret scanners cover the last case for whole repositories; envguard is the small, fast check for the env files themselves, including the "works on my machine" cases.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e . pytest
pytest
```

## License

[MIT](LICENSE) © Celalettin Durğaç
