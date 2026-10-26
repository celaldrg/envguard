from envguard.parser import parse


def codes(env):
    return [p.code for p in env.problems]


def test_basic_values_and_comments():
    env = parse("# comment\nA=1\nexport B=two\nC='single # not a comment'\nD=\"x\\ny\"\nE=plain # trailing comment\nF=\n")
    k = env.keys
    assert k["A"].value == "1"
    assert k["B"].value == "two"
    assert k["C"].value == "single # not a comment"
    assert k["D"].value == "x\ny"
    assert k["E"].value == "plain"
    assert k["F"].value == ""
    assert env.problems == []


def test_multiline_double_quotes():
    env = parse('KEY="-----BEGIN-----\nline2\n-----END-----"\nNEXT=1\n')
    assert env.keys["KEY"].value == "-----BEGIN-----\nline2\n-----END-----"
    assert env.keys["NEXT"].line == 4


def test_unterminated_quote():
    env = parse("A='oops\nB=2\n")
    assert "unterminated-quote" in codes(env)
    assert "B" in env.keys


def test_syntax_and_invalid_keys():
    env = parse("JUSTAWORD\n1BAD=x\nGOOD-NAME=y\n")
    assert codes(env) == ["syntax", "invalid-key", "invalid-key"]


def test_duplicates_last_wins():
    env = parse("A=1\nA=2\n")
    assert env.keys["A"].value == "2"
    assert codes(env) == ["duplicate-key"]
    assert "line 1" in env.problems[0].message


def test_warnings_for_spaces():
    env = parse("A = 1\nB=hello world\n")
    assert codes(env) == ["spaces-around-equals", "unquoted-whitespace"]


def test_text_after_closing_quote():
    env = parse('A="x" y\n')
    assert codes(env) == ["syntax"]
