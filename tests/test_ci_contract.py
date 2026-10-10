"""Evaluate the deployment guard and validate artifact handoff configuration."""

import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow():
    return yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)


def step(job, action):
    return next(s for s in job["steps"] if s.get("uses", "").startswith(action + "@"))


def test_ci_publishes_only_the_validated_public_artifact():
    config = workflow()
    assert config["permissions"] == {"contents": "read"}
    validate, deploy = config["jobs"]["validate"], config["jobs"]["deploy"]
    assert deploy["needs"] == "validate"
    assert deploy["permissions"] == {"contents": "write"}
    upload = step(validate, "actions/upload-artifact")["with"]
    download = step(deploy, "actions/download-artifact")["with"]
    assert upload["path"] == download["path"] == "docs/_site/"
    assert upload["name"] == download["name"]
    assert upload["include-hidden-files"] == "true"
    assert step(deploy, "quarto-dev/quarto-actions/publish")["with"] == {
        "target": "gh-pages",
        "path": "docs",
        "render": "false",
    }
    assert any(s.get("run") == "uv sync --frozen" for s in validate["steps"])
    assert any(s.get("run") == "uv run python -m tools.build_site" for s in validate["steps"])
    assert step(validate, "actions/checkout")["with"]["persist-credentials"] == "false"


def test_newer_same_ref_runs_supersede_old_validation():
    config = workflow()
    assert "github.ref" in config["concurrency"]["group"]
    assert config["concurrency"]["cancel-in-progress"] == "true"
    assert config["jobs"]["deploy"]["concurrency"]["cancel-in-progress"] == "false"


def test_deployment_guard_matrix():
    expression = workflow()["jobs"]["deploy"]["if"].strip()
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = expression.replace("github.event_name", "event").replace("github.ref", "ref")
    tree = ast.parse(expression, mode="eval")
    allowed = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.Compare,
        ast.Eq,
        ast.Name,
        ast.Load,
        ast.Constant,
    )
    assert all(isinstance(node, allowed) for node in ast.walk(tree))
    assert {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} <= {"event", "ref"}
    compiled = compile(tree, "<deployment guard>", "eval")
    for event in ("push", "workflow_dispatch", "pull_request"):
        for ref in ("refs/heads/main", "refs/heads/release", "refs/heads/feature", "refs/tags/v1"):
            actual = eval(compiled, {"__builtins__": {}}, {"event": event, "ref": ref})
            expected = event in {"push", "workflow_dispatch"} and ref in {
                "refs/heads/main",
                "refs/heads/release",
            }
            assert actual is expected
