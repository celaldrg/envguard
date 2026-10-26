import pytest

from envguard.secrets import looks_secret

# Built at runtime so this file never contains a full token-shaped string.
GH = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
STRIPE = "sk_" + "live_" + "51Hx9QwErTyUiOpAsDfGh"


@pytest.mark.parametrize("value", [
    "AKIAIOSFODNN7EXAMPLE",
    GH,
    STRIPE,
    "-----BEGIN RSA PRIVATE KEY-----",
    "postgres://app:s3cr3tP4ss@db.internal:5432/app",
    "Zx81kQp0LmN4vB7cT2wR9yU5sE3a",
])
def test_detects(value):
    assert looks_secret(value)


@pytest.mark.parametrize("value", [
    "", "changeme", "your-api-key", "<your key>", "${API_KEY}", "xxxxxxxx", "sk_test_placeholder",
    "postgres://postgres:postgres@localhost:5432/app", "http://localhost:3000", "true", "debug",
    "https://example.com/some/long/path/segment", "my-app-name-for-local-development",
])
def test_ignores_placeholders(value):
    assert looks_secret(value) is None
