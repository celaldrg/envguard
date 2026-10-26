import json

from envguard.cli import main

EXAMPLE = """# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app
REDIS_URL=redis://localhost:6379
STRIPE_KEY=your-stripe-key
SENTRY_DSN=
"""


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def test_ok(tmp_path, capsys):
    write(tmp_path, ".env.example", EXAMPLE)
    env = write(tmp_path, ".env", EXAMPLE.replace("your-stripe-key", "abc"))
    assert main(["--env", env]) == 0
    assert ": ok" in capsys.readouterr().out


def test_missing_key_is_error(tmp_path, capsys):
    write(tmp_path, ".env.example", EXAMPLE)
    env = write(tmp_path, ".env", "DATABASE_URL=x\nREDIS_URL=y\nSENTRY_DSN=\nEXTRA=1\n")
    assert main(["--env", env, "--format", "json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert {(p["code"], p.get("key")) for p in out["problems"]} == {("missing-key", "STRIPE_KEY"), ("undocumented-key", "EXTRA")}


def test_strict_fails_on_warnings(tmp_path):
    write(tmp_path, ".env.example", "A=1\n")
    env = write(tmp_path, ".env", "A=1\nB=2\n")
    assert main(["--env", env]) == 0
    assert main(["--env", env, "--strict"]) == 1


def test_secret_in_example(tmp_path, capsys):
    ex = write(tmp_path, ".env.example", "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nNAME=app\n")
    assert main(["--example", ex, "--example-only", "--format", "github"]) == 1
    out = capsys.readouterr().out
    assert "::error file=" in out and ",line=1," in out and "secret-in-example" in out


def test_missing_env_file(tmp_path, capsys):
    assert main(["--env", str(tmp_path / "nope")]) == 2
